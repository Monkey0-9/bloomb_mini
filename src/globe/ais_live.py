import csv
import io
import os
import zipfile
import httpx
import structlog
from datetime import datetime, timezone, timedelta
from pathlib import Path

log = structlog.get_logger()

# NOAA AIS daily zone files — completely free, no registration
# Zones 1-17 cover different US coastal areas
NOAA_AIS_BASE = "https://coast.noaa.gov/htdata/CMSP/AISDataHandler"
NOAA_ZONES = {
    "los_angeles": 10,     # Zone 10: California coast
    "houston": 8,          # Zone 8: Gulf of Mexico
    "new_york": 1,         # Zone 1: Northeast
    "savannah": 5,         # Zone 5: Southeast
    "seattle": 9,          # Zone 9: Pacific Northwest
}


def download_noaa_ais_zone(zone: int, date: datetime | None = None) -> list[dict]:
    """
    Download NOAA AIS data for a specific zone and date.
    Completely free. No registration. Direct download.
    Data is typically 1-2 days delayed.
    """
    if date is None:
        date = datetime.now(timezone.utc) - timedelta(days=2)

    year = date.year
    date_str = date.strftime("%Y%m%d")
    filename = f"AIS_{date_str}_Zone{zone:02d}.zip"
    url = f"{NOAA_AIS_BASE}/{year}/{filename}"

    cache_path = Path(f"data/cache/ais/{filename}")
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if not cache_path.exists():
        try:
            resp = httpx.get(url, timeout=120)
            if resp.status_code == 200:
                cache_path.write_bytes(resp.content)
                log.info("noaa_ais_downloaded", zone=zone, filename=filename)
            else:
                log.warning("noaa_ais_not_found", zone=zone, url=url, status=resp.status_code)
                return []
        except Exception as e:
            log.error("noaa_ais_error", zone=zone, error=str(e))
            return _generate_mock_vessels()

    vessels = []
    try:
        with zipfile.ZipFile(cache_path) as zf:
            csv_name = next((n for n in zf.namelist() if n.endswith(".csv")), None)
            if csv_name:
                with zf.open(csv_name) as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8",
                                                              errors="replace"))
                    seen_mmsi = set()
                    for row in reader:
                        mmsi = row.get("MMSI", "")
                        if mmsi and mmsi not in seen_mmsi:
                            seen_mmsi.add(mmsi)
                            vessels.append({
                                "mmsi": mmsi,
                                "vessel_name": row.get("VesselName", "").strip(),
                                "lat": float(row.get("LAT", 0)),
                                "lon": float(row.get("LON", 0)),
                                "sog": float(row.get("SOG", 0)),  # speed over ground
                                "cog": float(row.get("COG", 0)),  # course over ground
                                "heading": float(row.get("Heading", 0)),
                                "vessel_type": int(row.get("VesselType", 0)),
                                "length": float(row.get("Length", 0)),
                                "width": float(row.get("Width", 0)),
                                "draft": float(row.get("Draft", 0)),
                                "cargo": int(row.get("Cargo", 0)),
                                "status": row.get("Status", ""),
                                "timestamp": row.get("BaseDateTime", ""),
                            })
    except Exception as e:
        log.error("noaa_ais_parse_error", zone=zone, error=str(e))

    return vessels


def get_aishub_vessels(username: str | None = None,
                       bbox: dict | None = None) -> list[dict]:
    """
    Fetch real-time vessel positions from AISHub (free registration).
    bbox: {"latmin": 51.5, "latmax": 52.5, "lonmin": 3.5, "lonmax": 5.0}
    """
    username = username or os.environ.get("AISHUB_USERNAME")
    if not username:
        log.warning("aishub_no_username",
                    message="AISHub username not set. Register free at aishub.net")
        return []

    params = {
        "username": username,
        "format": 1,
        "output": "json",
        "compress": 0,
    }
    if bbox:
        params.update(bbox)

    try:
        resp = httpx.get("https://data.aishub.net/ws.php",
                         params=params, timeout=30)
        if resp.status_code != 200:
            return []
        data = resp.json()
        # AISHub returns list of vessel dicts
        return data[1] if isinstance(data, list) and len(data) > 1 else []
    except Exception as e:
        log.error("aishub_error", error=str(e))
        return []

def _generate_mock_vessels() -> list[dict]:
    """Fallback high-density mock vessel data."""
    import random
    import time
    vessels = []
    chokepoints = [
        {"name": "Suez Canal", "lat": 30.5, "lon": 32.3},
        {"name": "Strait of Hormuz", "lat": 26.5, "lon": 56.5},
        {"name": "Panama Canal", "lat": 9.1, "lon": -79.7},
        {"name": "Strait of Malacca", "lat": 1.3, "lon": 103.2},
    ]
    for i in range(100):
        cp = random.choice(chokepoints)
        mmsi = f"999{i:06d}"
        vessels.append({
            "mmsi": mmsi,
            "vessel_name": f"MOCK_VESSEL_{i}",
            "lat": cp["lat"] + random.uniform(-2, 2),
            "lon": cp["lon"] + random.uniform(-2, 2),
            "sog": random.uniform(5, 20),
            "cog": random.uniform(0, 360),
            "heading": random.uniform(0, 360),
            "vessel_type": 70, # Cargo
            "length": 250,
            "width": 32,
            "draft": 12,
            "cargo": 0,
            "status": "UnderWay",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return vessels
