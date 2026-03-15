"""
AIS / RF Fusion — Phase 4.4

Join vessel detections (SAR) with AIS vessel identities on:
[timestamp ± 15 min] AND [spatial distance < 500m]

Dark vessel flag: SAR detection with no matching AIS record.

Output features:
  - vessel_count_per_berth
  - avg_dwell_time_hours
  - cargo_tonnage_estimate
  - dark_vessel_ratio
  - port_utilisation_rate
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.ingest.ais import PortDefinition, VesselPosition

logger = logging.getLogger(__name__)


@dataclass
class SARVesselDetection:
    """Vessel detected in SAR imagery."""

    detection_id: str
    tile_id: str
    latitude: float
    longitude: float
    acquisition_utc: datetime
    length_m: float | None = None
    width_m: float | None = None
    heading_deg: float | None = None
    confidence: float = 0.5


@dataclass
class FusedVessel:
    """SAR detection matched with AIS identity."""

    detection_id: str
    ais_mmsi: str | None = None
    vessel_name: str | None = None
    vessel_type: int | None = None
    is_dark: bool = False  # No AIS match = dark vessel
    spatial_distance_m: float = 0.0
    temporal_distance_min: float = 0.0
    match_confidence: float = 0.0
    sar_detection: SARVesselDetection | None = None
    ais_position: VesselPosition | None = None


@dataclass
class PortFusionFeatures:
    """Fused feature output for a port at a specific timestamp."""

    port_id: str
    feature_timestamp: datetime
    vessel_count_per_berth: float = 0.0
    avg_dwell_time_hours: float = 0.0
    cargo_tonnage_estimate: float = 0.0
    dark_vessel_ratio: float = 0.0
    port_utilisation_rate: float = 0.0
    total_vessels_detected: int = 0
    matched_vessels: int = 0
    dark_vessels: int = 0
    container_ships: int = 0
    tankers: int = 0
    source_tile_ids: list[str] = field(default_factory=list)


# Constants
TEMPORAL_WINDOW_MINUTES = 15
SPATIAL_DISTANCE_THRESHOLD_M = 500
EARTH_RADIUS_M = 6_371_000


class AISFusionEngine:
    """
    Fuse SAR vessel detections with AIS position reports.

    The fusion matches detections using spatial and temporal windows,
    then computes port-level features for the signal pipeline.
    """

    def __init__(
        self,
        temporal_window_min: float = TEMPORAL_WINDOW_MINUTES,
        spatial_threshold_m: float = SPATIAL_DISTANCE_THRESHOLD_M,
    ) -> None:
        self._temporal_window = timedelta(minutes=temporal_window_min)
        self._spatial_threshold = spatial_threshold_m

    def fuse(
        self,
        sar_detections: list[SARVesselDetection],
        ais_positions: list[VesselPosition],
    ) -> list[FusedVessel]:
        """
        Match SAR detections with AIS positions.

        Matching criteria:
        - Temporal: [timestamp ± 15 min]
        - Spatial: [distance < 500m]

        Unmatched SAR detections are flagged as dark vessels.
        """
        fused: list[FusedVessel] = []

        for det in sar_detections:
            best_match: VesselPosition | None = None
            best_distance = float("inf")
            best_temporal = float("inf")

            for ais in ais_positions:
                # Temporal check
                time_diff = abs((det.acquisition_utc - ais.timestamp_utc).total_seconds())
                if time_diff > self._temporal_window.total_seconds():
                    continue

                # Spatial check
                spatial_dist = self._haversine_distance(
                    det.latitude,
                    det.longitude,
                    ais.latitude,
                    ais.longitude,
                )
                if spatial_dist > self._spatial_threshold:
                    continue

                # Find best match (closest spatial + temporal)
                combined_score = spatial_dist + time_diff * 10  # Weight time
                if combined_score < best_distance + best_temporal * 10:
                    best_match = ais
                    best_distance = spatial_dist
                    best_temporal = time_diff / 60  # Convert to minutes

            if best_match:
                fused.append(
                    FusedVessel(
                        detection_id=det.detection_id,
                        ais_mmsi=best_match.mmsi,
                        vessel_name=best_match.vessel_name,
                        vessel_type=best_match.vessel_type,
                        is_dark=False,
                        spatial_distance_m=best_distance,
                        temporal_distance_min=best_temporal,
                        match_confidence=self._compute_match_confidence(
                            best_distance, best_temporal
                        ),
                        sar_detection=det,
                        ais_position=best_match,
                    )
                )
            else:
                # Dark vessel: SAR detection with no AIS match
                fused.append(
                    FusedVessel(
                        detection_id=det.detection_id,
                        is_dark=True,
                        match_confidence=0.0,
                        sar_detection=det,
                    )
                )

        dark_count = sum(1 for f in fused if f.is_dark)
        logger.info(
            f"Fused {len(sar_detections)} SAR detections: "
            f"{len(fused) - dark_count} matched, {dark_count} dark vessels"
        )
        return fused

    def compute_port_features(
        self,
        port: PortDefinition,
        fused_vessels: list[FusedVessel],
        ais_positions: list[VesselPosition],
        observation_time: datetime,
    ) -> PortFusionFeatures:
        """
        Compute port-level features from fused vessel data.

        Features per spec:
        - vessel_count_per_berth
        - avg_dwell_time_hours
        - cargo_tonnage_estimate
        - dark_vessel_ratio
        - port_utilisation_rate
        """
        # Filter to port bbox
        port_vessels = [
            fv
            for fv in fused_vessels
            if fv.sar_detection
            and self._in_bbox(fv.sar_detection.latitude, fv.sar_detection.longitude, port.bbox)
        ]

        total = len(port_vessels)
        matched = sum(1 for v in port_vessels if not v.is_dark)
        dark = sum(1 for v in port_vessels if v.is_dark)

        # Container ships and tankers
        containers = sum(1 for v in port_vessels if v.vessel_type and 70 <= v.vessel_type < 73)
        tankers = sum(1 for v in port_vessels if v.vessel_type and 80 <= v.vessel_type < 90)

        # Estimate berth count (from port definition or default)
        n_berths = max(len(port.berth_zones), 5)  # Default 5 berths
        vessels_per_berth = total / n_berths if n_berths > 0 else 0

        # Utilisation rate
        utilisation = min(vessels_per_berth / 2.0, 1.0)  # Assume 2 vessels/berth = full

        # Dwell time from AIS data
        dwell_hours = self._estimate_dwell_from_ais(ais_positions, port)

        # Tonnage estimate (rough: container ship ~40k DWT, tanker ~60k DWT)
        tonnage = containers * 40_000 + tankers * 60_000

        # Dark vessel ratio
        dark_ratio = dark / total if total > 0 else 0.0

        # Collect source tile IDs
        tile_ids = list(set(v.sar_detection.tile_id for v in port_vessels if v.sar_detection))

        return PortFusionFeatures(
            port_id=port.port_id,
            feature_timestamp=observation_time,
            vessel_count_per_berth=vessels_per_berth,
            avg_dwell_time_hours=dwell_hours,
            cargo_tonnage_estimate=tonnage,
            dark_vessel_ratio=dark_ratio,
            port_utilisation_rate=utilisation,
            total_vessels_detected=total,
            matched_vessels=matched,
            dark_vessels=dark,
            container_ships=containers,
            tankers=tankers,
            source_tile_ids=tile_ids,
        )

    def _estimate_dwell_from_ais(
        self,
        ais_positions: list[VesselPosition],
        port: PortDefinition,
    ) -> float:
        """Estimate average vessel dwell time in port from AIS tracks."""
        port_positions = [
            p for p in ais_positions if self._in_bbox(p.latitude, p.longitude, port.bbox)
        ]

        mmsi_tracks: dict[str, list[datetime]] = {}
        for p in port_positions:
            if p.mmsi not in mmsi_tracks:
                mmsi_tracks[p.mmsi] = []
            mmsi_tracks[p.mmsi].append(p.timestamp_utc)

        dwells = []
        for mmsi, times in mmsi_tracks.items():
            if len(times) >= 2:
                times_sorted = sorted(times)
                hours = (times_sorted[-1] - times_sorted[0]).total_seconds() / 3600
                if 0 < hours < 720:  # Cap at 30 days
                    dwells.append(hours)

        return float(np.mean(dwells)) if dwells else 0.0

    @staticmethod
    def _haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Compute great-circle distance between two points in meters."""
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return EARTH_RADIUS_M * c

    @staticmethod
    def _compute_match_confidence(distance_m: float, temporal_min: float) -> float:
        """Compute match confidence from spatial and temporal distances."""
        spatial_conf = max(0, 1.0 - distance_m / SPATIAL_DISTANCE_THRESHOLD_M)
        temporal_conf = max(0, 1.0 - temporal_min / TEMPORAL_WINDOW_MINUTES)
        return spatial_conf * 0.6 + temporal_conf * 0.4

    @staticmethod
    def _in_bbox(lat: float, lon: float, bbox: Any) -> bool:
        return bbox.west <= lon <= bbox.east and bbox.south <= lat <= bbox.north
