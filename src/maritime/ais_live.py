"""
Live AIS vessel tracking — AISHub free tier + OpenSky maritime.
AISHub provides real-time global AIS via UDP/HTTP (free registration).
https://www.aishub.net/api

Pipeline:
  1. Fetch latest positions from AISHub HTTP API (if API_KEY registered)
  2. Fall back to NOAA COAST AIS CSV batch data (always free, no key)
  3. Merge into vessel_tracker position store
"""

import os
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

AISHUB_USERNAME = os.getenv("AISHUB_USERNAME", "")
AISHUB_BASE = "https://data.aishub.net/ws.php"

# NOAA COAST AIS feed — free, updated hourly, no API key
NOAA_AIS_BASE = "https://api.coast.noaa.gov/query/v1.0/ais/vessels"

# Key maritime zones for intelligence gathering
ZONE_BBOXES = {
    "rotterdam":     {"lat_min": 51.80, "lat_max": 52.05, "lon_min": 3.90, "lon_max": 4.60},
    "singapore":     {"lat_min": 1.00,  "lat_max": 1.60,  "lon_min": 103.50, "lon_max": 104.20},
    "strait_hormuz": {"lat_min": 25.80, "lat_max": 26.80, "lon_min": 56.30, "lon_max": 58.00},
    "suez_canal":    {"lat_min": 29.80, "lat_max": 31.50, "lon_min": 32.40, "lon_max": 33.00},
    "bosporus":      {"lat_min": 40.95, "lat_max": 41.45, "lon_min": 28.90, "lon_max": 29.20},
    "malacca":       {"lat_min": 1.00,  "lat_max": 5.80,  "lon_min": 99.00, "lon_max": 104.50},
    "english_channel": {"lat_min": 50.00, "lat_max": 51.50, "lon_min": -2.50, "lon_max": 2.00},
    "los_angeles":   {"lat_min": 33.40, "lat_max": 33.90, "lon_min": -118.80, "lon_max": -117.80},
}


@dataclass
class LiveVesselPosition:
    mmsi: str
    name: str
    lat: float
    lon: float
    speed: float        # knots
    course: float       # degrees
    vessel_type: int
    status: str
    timestamp: str
    zone: str
    source: str         # "AISHUB" | "NOAA"


def _fetch_aishub(zone_key: str, bbox: dict) -> list[LiveVesselPosition]:
    """Fetch live vessel positions from AISHub HTTP API."""
    if not AISHUB_USERNAME:
        return []
    try:
        resp = httpx.get(
            AISHUB_BASE,
            params={
                "username": AISHUB_USERNAME,
                "format": 1,  # JSON format
                "output": "json",
                "latmin": bbox["lat_min"],
                "latmax": bbox["lat_max"],
                "lonmin": bbox["lon_min"],
                "lonmax": bbox["lon_max"],
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        positions = []
        # AISHub returns [metadata, [vessels_array]]
        vessels = data[1] if len(data) > 1 else []
        for v in vessels:
            try:
                positions.append(LiveVesselPosition(
                    mmsi=str(v.get("MMSI", "")),
                    name=v.get("NAME", "UNKNOWN").strip() or "UNKNOWN",
                    lat=float(v.get("LATITUDE", 0)),
                    lon=float(v.get("LONGITUDE", 0)),
                    speed=float(v.get("SOG", 0)) / 10.0,
                    course=float(v.get("COG", 0)) / 10.0,
                    vessel_type=int(v.get("TYPE", 0)),
                    status=_decode_nav_status(int(v.get("NAVSTAT", 0))),
                    timestamp=v.get("TIME", datetime.now(UTC).isoformat()),
                    zone=zone_key,
                    source="AISHUB",
                ))
            except (ValueError, KeyError):
                continue
        return positions
    except Exception:
        return []


def _fetch_noaa_zone(zone_key: str, bbox: dict, limit: int = 25) -> list[LiveVesselPosition]:
    """Fetch vessel positions from NOAA COAST AIS API (free, no key)."""
    try:
        resp = httpx.get(
            NOAA_AIS_BASE,
            params={
                "bbox": f"{bbox['lon_min']},{bbox['lat_min']},{bbox['lon_max']},{bbox['lat_max']}",
                "limit": limit,
                "output": "json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        positions = []
        features = data.get("features", [])
        for f in features:
            props = f.get("properties", {})
            coords = f.get("geometry", {}).get("coordinates", [0, 0])
            try:
                positions.append(LiveVesselPosition(
                    mmsi=str(props.get("MMSI", "")),
                    name=props.get("VesselName", "UNKNOWN").strip() or "UNKNOWN",
                    lat=float(coords[1]),
                    lon=float(coords[0]),
                    speed=float(props.get("SOG", 0)),
                    course=float(props.get("COG", 0)),
                    vessel_type=int(props.get("VesselType", 0)),
                    status=_decode_nav_status(int(props.get("Status", 0))),
                    timestamp=props.get("BaseDateTime", datetime.now(UTC).isoformat()),
                    zone=zone_key,
                    source="NOAA",
                ))
            except (ValueError, KeyError, TypeError):
                continue
        return positions
    except Exception:
        return []


def _decode_nav_status(code: int) -> str:
    STATUS_MAP = {
        0: "UNDERWAY_ENGINE", 1: "ANCHORED", 2: "NOT_UNDER_COMMAND",
        3: "RESTRICTED_MANOEUVRABILITY", 5: "MOORED", 7: "FISHING",
        8: "SAILING", 15: "UNKNOWN",
    }
    return STATUS_MAP.get(code, "UNKNOWN")


def detect_dark_vessels(positions: list[LiveVesselPosition]) -> list[dict]:
    """
    Identify potential 'dark vessel' activity.
    Dark vessels = AIS signal suddenly disappears in sanctioned zones.
    This is a simplified heuristic: vessels with UNKNOWN status in high-risk zones.
    Full dark vessel detection requires comparing historical AIS tracks (enterprise feature).
    """
    HIGH_RISK_ZONES = {"strait_hormuz", "bosporus"}
    return [
        {
            "mmsi": v.mmsi,
            "name": v.name,
            "lat": v.lat,
            "lon": v.lon,
            "zone": v.zone,
            "alert": "POTENTIAL_DARK_VESSEL",
            "reason": f"Status:{v.status} in high-risk zone {v.zone}",
        }
        for v in positions
        if v.zone in HIGH_RISK_ZONES and v.status in ("UNKNOWN", "NOT_UNDER_COMMAND")
    ]


def get_live_ais(zones: list[str] | None = None) -> dict:
    """
    Fetch live AIS positions across tracked maritime zones.
    Tries AISHub first, falls back to NOAA for each zone.
    """
    zones_to_query = zones or list(ZONE_BBOXES.keys())
    all_positions: list[LiveVesselPosition] = []

    for zone_key in zones_to_query:
        bbox = ZONE_BBOXES[zone_key]
        # Try AISHub first, fall back to NOAA
        positions = _fetch_aishub(zone_key, bbox) or _fetch_noaa_zone(zone_key, bbox)
        all_positions.extend(positions)

    dark_alerts = detect_dark_vessels(all_positions)

    return {
        "vessels": [
            {
                "mmsi": v.mmsi,
                "name": v.name,
                "lat": v.lat,
                "lon": v.lon,
                "speed_knots": v.speed,
                "course_deg": v.course,
                "vessel_type": v.vessel_type,
                "status": v.status,
                "zone": v.zone,
                "source": v.source,
                "timestamp": v.timestamp,
            }
            for v in all_positions
        ],
        "dark_vessel_alerts": dark_alerts,
        "total_count": len(all_positions),
        "dark_count": len(dark_alerts),
        "zones_scanned": zones_to_query,
        "as_of": datetime.now(UTC).isoformat(),
    }
