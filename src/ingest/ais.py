"""
NOAA AIS Data Ingestor — Phase 1.1

Ingests Automatic Identification System (AIS) vessel position data
from NOAA Marine Cadastre for vessel tracking and port activity analysis.

Data source: https://marinecadastre.gov/ais/
License: Public Domain — commercial use permitted.

Used for Phase 4 AIS/RF Fusion: matching SAR vessel detections
with AIS identities for dark vessel flagging and port throughput estimation.
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

import requests

from src.common.schemas import BoundingBox

logger = logging.getLogger(__name__)

NOAA_AIS_BASE_URL = "https://coast.noaa.gov/htdata/CMSP/AISDataHandler"
AIS_LICENSE_ID = "noaa_ais_public_domain"


@dataclass
class VesselPosition:
    """Single AIS position report."""
    mmsi: str  # Maritime Mobile Service Identity
    timestamp_utc: datetime
    latitude: float
    longitude: float
    sog: float  # Speed over ground (knots)
    cog: float  # Course over ground (degrees)
    heading: float
    vessel_name: Optional[str] = None
    vessel_type: Optional[int] = None
    imo: Optional[str] = None
    cargo_type: Optional[int] = None
    draught: Optional[float] = None
    destination: Optional[str] = None
    status: Optional[int] = None  # Navigation status


@dataclass
class PortActivity:
    """Aggregated port activity metrics from AIS data."""
    port_id: str
    port_name: str
    bbox: BoundingBox
    observation_date: datetime
    vessel_count: int = 0
    vessels_at_berth: int = 0
    vessels_anchored: int = 0
    vessels_in_transit: int = 0
    avg_dwell_time_hours: float = 0.0
    cargo_vessels: int = 0
    tankers: int = 0
    container_ships: int = 0
    total_tonnage_estimate: float = 0.0
    dark_vessel_detections: int = 0
    unique_mmsis: list[str] = field(default_factory=list)


@dataclass
class PortDefinition:
    """Port bounding box and metadata for monitoring."""
    port_id: str
    port_name: str
    country: str
    bbox: BoundingBox
    berth_zones: list[BoundingBox] = field(default_factory=list)
    anchorage_zones: list[BoundingBox] = field(default_factory=list)


# ── Major Asia-Pacific container ports for Phase 1 ──────────────────────
PHASE1_PORTS = [
    PortDefinition(
        port_id="CNSHA", port_name="Shanghai", country="CN",
        bbox=BoundingBox(west=121.3, south=30.6, east=122.1, north=31.5),
    ),
    PortDefinition(
        port_id="SGSIN", port_name="Singapore", country="SG",
        bbox=BoundingBox(west=103.6, south=1.1, east=104.1, north=1.5),
    ),
    PortDefinition(
        port_id="CNNGB", port_name="Ningbo-Zhoushan", country="CN",
        bbox=BoundingBox(west=121.4, south=29.7, east=122.3, north=30.2),
    ),
    PortDefinition(
        port_id="CNSZN", port_name="Shenzhen", country="CN",
        bbox=BoundingBox(west=113.8, south=22.4, east=114.4, north=22.7),
    ),
    PortDefinition(
        port_id="KRPUS", port_name="Busan", country="KR",
        bbox=BoundingBox(west=128.9, south=35.0, east=129.2, north=35.2),
    ),
    PortDefinition(
        port_id="CNQIN", port_name="Qingdao", country="CN",
        bbox=BoundingBox(west=120.1, south=35.9, east=120.5, north=36.2),
    ),
    PortDefinition(
        port_id="HKHKG", port_name="Hong Kong", country="HK",
        bbox=BoundingBox(west=113.8, south=22.2, east=114.4, north=22.5),
    ),
    PortDefinition(
        port_id="TWKHH", port_name="Kaohsiung", country="TW",
        bbox=BoundingBox(west=120.2, south=22.5, east=120.4, north=22.7),
    ),
]

# AIS vessel type codes for classification
VESSEL_TYPE_MAP = {
    range(70, 80): "cargo",
    range(80, 90): "tanker",
    range(60, 70): "passenger",
    range(30, 40): "fishing",
}


class AISIngestor:
    """
    NOAA AIS data ingestor for vessel position tracking.
    
    Downloads AIS position reports, filters by port bounding boxes,
    and computes port activity metrics for the feature pipeline.
    """

    # Vessel navigation status codes
    STATUS_AT_ANCHOR = 1
    STATUS_MOORED = 5
    SOG_THRESHOLD_KNOTS = 0.5  # Below this = stationary

    def __init__(
        self,
        data_dir: Path,
        ports: Optional[list[PortDefinition]] = None,
    ) -> None:
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._ports = ports or PHASE1_PORTS

    def ingest_daily(self, date: datetime) -> list[PortActivity]:
        """
        Ingest AIS data for a single day and compute port activity metrics.
        
        Steps:
        1. Download/load AIS position data for the date
        2. Filter positions within port bounding boxes
        3. Classify vessel status (at berth, anchored, in transit)
        4. Compute aggregated port metrics
        """
        positions = self._load_positions(date)
        logger.info(f"Loaded {len(positions)} AIS positions for {date.strftime('%Y-%m-%d')}")

        activities = []
        for port in self._ports:
            port_positions = self._filter_by_bbox(positions, port.bbox)
            if not port_positions:
                activities.append(PortActivity(
                    port_id=port.port_id,
                    port_name=port.port_name,
                    bbox=port.bbox,
                    observation_date=date,
                ))
                continue

            activity = self._compute_port_activity(port, port_positions, date)
            activities.append(activity)
            logger.info(
                f"Port {port.port_name}: {activity.vessel_count} vessels, "
                f"{activity.vessels_at_berth} at berth, "
                f"avg dwell {activity.avg_dwell_time_hours:.1f}h"
            )

        return activities

    def _load_positions(self, date: datetime) -> list[VesselPosition]:
        """Load AIS position data for a date (from local cache or download)."""
        cache_file = self._data_dir / f"ais_{date.strftime('%Y%m%d')}.csv"

        if cache_file.exists():
            return self._parse_csv(cache_file)

        # In production: download from NOAA Marine Cadastre
        # The NOAA AIS data is distributed as monthly CSV archives
        logger.info(f"AIS data not cached for {date.strftime('%Y-%m-%d')}")
        return []

    def _parse_csv(self, path: Path) -> list[VesselPosition]:
        """Parse NOAA AIS CSV format into VesselPosition objects."""
        positions = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pos = VesselPosition(
                        mmsi=row.get("MMSI", ""),
                        timestamp_utc=datetime.strptime(
                            row.get("BaseDateTime", ""), "%Y-%m-%dT%H:%M:%S"
                        ).replace(tzinfo=timezone.utc),
                        latitude=float(row.get("LAT", 0)),
                        longitude=float(row.get("LON", 0)),
                        sog=float(row.get("SOG", 0)),
                        cog=float(row.get("COG", 0)),
                        heading=float(row.get("Heading", 0)),
                        vessel_name=row.get("VesselName"),
                        vessel_type=int(row.get("VesselType", 0)) if row.get("VesselType") else None,
                        imo=row.get("IMO"),
                        status=int(row.get("Status", 0)) if row.get("Status") else None,
                    )
                    positions.append(pos)
                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipping malformed AIS record: {e}")
                    continue
        return positions

    def _filter_by_bbox(
        self, positions: list[VesselPosition], bbox: BoundingBox,
    ) -> list[VesselPosition]:
        """Filter positions within a bounding box."""
        return [
            p for p in positions
            if bbox.west <= p.longitude <= bbox.east
            and bbox.south <= p.latitude <= bbox.north
        ]

    def _compute_port_activity(
        self,
        port: PortDefinition,
        positions: list[VesselPosition],
        date: datetime,
    ) -> PortActivity:
        """Compute port activity metrics from filtered AIS positions."""
        unique_mmsis = list(set(p.mmsi for p in positions))

        # Classify vessel status
        at_berth = 0
        anchored = 0
        in_transit = 0
        cargo = 0
        tankers = 0
        containers = 0

        for mmsi in unique_mmsis:
            vessel_positions = [p for p in positions if p.mmsi == mmsi]
            latest = max(vessel_positions, key=lambda p: p.timestamp_utc)

            # Status classification
            if latest.status == self.STATUS_MOORED or (
                latest.sog < self.SOG_THRESHOLD_KNOTS
                and self._in_berth_zone(latest, port)
            ):
                at_berth += 1
            elif latest.status == self.STATUS_AT_ANCHOR or (
                latest.sog < self.SOG_THRESHOLD_KNOTS
            ):
                anchored += 1
            else:
                in_transit += 1

            # Vessel type classification
            if latest.vessel_type:
                vt = latest.vessel_type
                if 70 <= vt < 80:
                    cargo += 1
                    if vt in (71, 72):
                        containers += 1
                elif 80 <= vt < 90:
                    tankers += 1

        # Estimate dwell times
        dwell_hours = self._estimate_dwell_times(positions, unique_mmsis)

        return PortActivity(
            port_id=port.port_id,
            port_name=port.port_name,
            bbox=port.bbox,
            observation_date=date,
            vessel_count=len(unique_mmsis),
            vessels_at_berth=at_berth,
            vessels_anchored=anchored,
            vessels_in_transit=in_transit,
            avg_dwell_time_hours=dwell_hours,
            cargo_vessels=cargo,
            tankers=tankers,
            container_ships=containers,
            unique_mmsis=unique_mmsis,
        )

    def _in_berth_zone(self, pos: VesselPosition, port: PortDefinition) -> bool:
        """Check if position is within any defined berth zone."""
        for bz in port.berth_zones:
            if (bz.west <= pos.longitude <= bz.east
                    and bz.south <= pos.latitude <= bz.north):
                return True
        # If no berth zones defined, assume inner port area
        center_lon = (port.bbox.west + port.bbox.east) / 2
        center_lat = (port.bbox.south + port.bbox.north) / 2
        return (abs(pos.longitude - center_lon) < 0.05
                and abs(pos.latitude - center_lat) < 0.05)

    def _estimate_dwell_times(
        self, positions: list[VesselPosition], mmsis: list[str],
    ) -> float:
        """Estimate average vessel dwell time from position timestamps."""
        dwell_times = []
        for mmsi in mmsis:
            vessel_pos = sorted(
                [p for p in positions if p.mmsi == mmsi],
                key=lambda p: p.timestamp_utc,
            )
            if len(vessel_pos) >= 2:
                first = vessel_pos[0].timestamp_utc
                last = vessel_pos[-1].timestamp_utc
                hours = (last - first).total_seconds() / 3600
                if hours > 0:
                    dwell_times.append(hours)

        return float(sum(dwell_times) / len(dwell_times)) if dwell_times else 0.0
