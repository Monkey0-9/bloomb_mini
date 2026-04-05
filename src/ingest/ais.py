"""
NOAA AIS Data Ingestor - Phase 1.1

Ingests Automatic Identification System (AIS) vessel position data
from NOAA Marine Cadastre for vessel tracking and port activity analysis.

Data source: https://marinecadastre.gov/ais/
License: Public Domain - commercial use permitted.

Used for Phase 4 AIS/RF Fusion: matching SAR vessel detections
with AIS identities for dark vessel flagging and port throughput estimation.
"""

from __future__ import annotations

import csv
import io
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

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
    vessel_name: str | None = None
    vessel_type: int | None = None
    imo: str | None = None
    cargo_type: int | None = None
    draught: float | None = None
    destination: str | None = None
    status: int | None = None  # Navigation status


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


# -- Major Asia-Pacific container ports for Phase 1 ----------------------
PHASE1_PORTS = [
    PortDefinition(
        port_id="CNSHA",
        port_name="Shanghai",
        country="CN",
        bbox=BoundingBox(
            min_lon=121.3, min_lat=30.6, max_lon=122.1, max_lat=31.5
        ),
    ),
    PortDefinition(
        port_id="SGSIN",
        port_name="Singapore",
        country="SG",
        bbox=BoundingBox(
            min_lon=103.6, min_lat=1.1, max_lon=104.1, max_lat=1.5
        ),
    ),
    PortDefinition(
        port_id="CNNGB",
        port_name="Ningbo-Zhoushan",
        country="CN",
        bbox=BoundingBox(
            min_lon=121.4, min_lat=29.7, max_lon=122.3, max_lat=30.2
        ),
    ),
    PortDefinition(
        port_id="CNSZN",
        port_name="Shenzhen",
        country="CN",
        bbox=BoundingBox(
            min_lon=113.8, min_lat=22.4, max_lon=114.4, max_lat=22.7
        ),
    ),
    PortDefinition(
        port_id="KRPUS",
        port_name="Busan",
        country="KR",
        bbox=BoundingBox(
            min_lon=128.9, min_lat=35.0, max_lon=129.2, max_lat=35.2
        ),
    ),
    PortDefinition(
        port_id="CNQIN",
        port_name="Qingdao",
        country="CN",
        bbox=BoundingBox(
            min_lon=120.1, min_lat=35.9, max_lon=120.5, max_lat=36.2
        ),
    ),
    PortDefinition(
        port_id="HKHKG",
        port_name="Hong Kong",
        country="HK",
        bbox=BoundingBox(
            min_lon=113.8, min_lat=22.2, max_lon=114.4, max_lat=22.5
        ),
    ),
    PortDefinition(
        port_id="TWKHH",
        port_name="Kaohsiung",
        country="TW",
        bbox=BoundingBox(
            min_lon=120.2, min_lat=22.5, max_lon=120.4, max_lat=22.7
        ),
    ),
]


class AISIngestor:
    """
    NOAA AIS data ingestor for vessel position tracking.
    """

    STATUS_AT_ANCHOR = 1
    STATUS_MOORED = 5
    SOG_THRESHOLD_KNOTS = 0.5

    def __init__(
        self,
        data_dir: Path,
        ports: list[PortDefinition] | None = None,
    ) -> None:
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._ports = ports or PHASE1_PORTS

    async def ingest_daily(self, date: datetime) -> list[PortActivity]:
        """Ingest AIS data and compute port metrics."""
        positions = await self._load_positions(date)
        logger.info(
            f"Loaded {len(positions)} AIS positions for "
            f"{date.strftime('%Y-%m-%d')}"
        )

        activities = []
        for port in self._ports:
            port_positions = self._filter_by_bbox(positions, port.bbox)
            if not port_positions:
                activities.append(
                    PortActivity(
                        port_id=port.port_id,
                        port_name=port.port_name,
                        bbox=port.bbox,
                        observation_date=date,
                    )
                )
                continue

            activity = self._compute_port_activity(port, port_positions, date)
            activities.append(activity)
            logger.info(
                f"Port {port.port_name}: {activity.vessel_count} vessels"
            )

        return activities

    async def _load_positions(self, date: datetime) -> list[VesselPosition]:
        """Load positions from cache or download from NOAA."""
        cache_file = self._data_dir / f"ais_{date.strftime('%Y%m%d')}.csv"
        if cache_file.exists():
            return self._parse_csv(cache_file)

        target_date = date
        max_attempts = 5
        for i in range(max_attempts):
            check_date = target_date - timedelta(days=i)
            year = check_date.year
            month = check_date.strftime("%m")
            day = check_date.strftime("%d")

            url = f"{NOAA_AIS_BASE_URL}/{year}/AIS_{year}_{month}_{day}.zip"
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(url)
                if resp.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        csvs = [n for n in z.namelist() if n.endswith('.csv')]
                        if not csvs:
                            continue
                        with z.open(csvs[0]) as f:
                            content = f.read().decode('utf-8')
                            with open(cache_file, 'w', encoding='utf-8') as cf:
                                cf.write(content)
                    return self._parse_csv(cache_file)
            except Exception as e:
                logger.error(f"AIS download error: {e}")

        return []

    def _parse_csv(self, path: Path) -> list[VesselPosition]:
        """Parse NOAA AIS CSV format."""
        positions: list[VesselPosition] = []
        try:
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        v_type_str = row.get("VesselType", "")
                        v_type = int(v_type_str) if v_type_str else None
                        stat_str = row.get("Status", "")
                        stat = int(stat_str) if stat_str else None
                        dt_s = row.get("BaseDateTime", "")
                        dt = datetime.strptime(
                            dt_s, "%Y-%m-%dT%H:%M:%S"
                        ).replace(tzinfo=UTC)

                        positions.append(VesselPosition(
                            mmsi=row.get("MMSI", ""),
                            timestamp_utc=dt,
                            latitude=float(row.get("LAT", 0)),
                            longitude=float(row.get("LON", 0)),
                            sog=float(row.get("SOG", 0)),
                            cog=float(row.get("COG", 0)),
                            heading=float(row.get("Heading", 0)),
                            vessel_name=row.get("VesselName"),
                            vessel_type=v_type,
                            imo=row.get("IMO"),
                            status=stat,
                        ))
                    except (ValueError, KeyError, TypeError):
                        continue
        except Exception as e:
            logger.error(f"Error reading AIS cache {path}: {e}")
        return positions

    def _filter_by_bbox(
        self,
        positions: list[VesselPosition],
        bbox: BoundingBox,
    ) -> list[VesselPosition]:
        """Filter positions within a bounding box."""
        return [
            p for p in positions
            if bbox.min_lon <= p.longitude <= bbox.max_lon and
            bbox.min_lat <= p.latitude <= bbox.max_lat
        ]

    def _compute_port_activity(
        self,
        port: PortDefinition,
        positions: list[VesselPosition],
        date: datetime,
    ) -> PortActivity:
        """Compute port activity metrics."""
        unique_mmsis = list(set(p.mmsi for p in positions))
        at_berth = 0
        anchored = 0
        in_transit = 0
        cargo = 0
        tankers = 0
        containers = 0

        for mmsi in unique_mmsis:
            v_pos = [p for p in positions if p.mmsi == mmsi]
            latest = max(v_pos, key=lambda p: p.timestamp_utc)

            if latest.status == self.STATUS_MOORED or (
                latest.sog < self.SOG_THRESHOLD_KNOTS and
                self._in_berth_zone(latest, port)
            ):
                at_berth += 1
            elif latest.status == self.STATUS_AT_ANCHOR or (
                latest.sog < self.SOG_THRESHOLD_KNOTS
            ):
                anchored += 1
            else:
                in_transit += 1

            if latest.vessel_type:
                vt = latest.vessel_type
                if 70 <= vt < 80:
                    cargo += 1
                    if vt in (71, 72):
                        containers += 1
                elif 80 <= vt < 90:
                    tankers += 1

        dwell_h = self._estimate_dwell_times(positions, unique_mmsis)
        return PortActivity(
            port_id=port.port_id,
            port_name=port.port_name,
            bbox=port.bbox,
            observation_date=date,
            vessel_count=len(unique_mmsis),
            vessels_at_berth=at_berth,
            vessels_anchored=anchored,
            vessels_in_transit=in_transit,
            avg_dwell_time_hours=dwell_h,
            cargo_vessels=cargo,
            tankers=tankers,
            container_ships=containers,
            unique_mmsis=unique_mmsis,
        )

    def _in_berth_zone(self, pos: VesselPosition, port: PortDefinition) -> bool:
        """Check if position is within any defined berth zone."""
        for bz in port.berth_zones:
            if bz.min_lon <= pos.longitude <= bz.max_lon and \
               bz.min_lat <= pos.latitude <= bz.max_lat:
                return True
        c_lon = (port.bbox.min_lon + port.bbox.max_lon) / 2
        c_lat = (port.bbox.min_lat + port.bbox.max_lat) / 2
        return abs(pos.longitude - c_lon) < 0.05 and \
               abs(pos.latitude - c_lat) < 0.05

    def _estimate_dwell_times(
        self,
        positions: list[VesselPosition],
        mmsis: list[str],
    ) -> float:
        """Estimate average vessel dwell time."""
        dwells: list[float] = []
        for mmsi in mmsis:
            v_p = sorted(
                [p for p in positions if p.mmsi == mmsi],
                key=lambda p: p.timestamp_utc,
            )
            if len(v_p) >= 2:
                hrs = (v_p[-1].timestamp_utc -
                       v_p[0].timestamp_utc).total_seconds() / 3600
                if hrs > 0:
                    dwells.append(hrs)
        return float(sum(dwells) / len(dwells)) if dwells else 0.0
