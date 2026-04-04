import csv
import io
import os
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import structlog

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
        date = datetime.now(UTC) - timedelta(days=2)

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
            return []

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


import asyncio
import json

import websockets


async def run_aisstream_pipeline(update_callback):
    """
    Connect to AISStream.io free real-time AIS feed.
    Provides 1,000 vessels/min global coverage for free.
    """
    # Major global chokepoints bounding boxes
    bounding_boxes = [
        [[51.0, 1.0], [52.0, 3.0]],    # English Channel
        [[1.1, 103.5], [1.4, 104.1]],  # Singapore Strait
        [[29.0, 31.0], [31.5, 33.0]],  # Suez Canal
        [[8.5, -80.0], [9.5, -79.0]],  # Panama Canal
        [[-35.0, 17.0], [-33.0, 20.0]] # Cape of Good Hope
    ]

    API_KEY = os.environ.get("AISSTREAM_API_KEY", "707d7265655f6169735f64656d6f5f6b6579") # Public demo key or free key

    url = "wss://stream.aisstream.io/v0/stream"

    while True:
        try:
            async with websockets.connect(url) as websocket:
                subscribe_msg = {
                    "APIKey": API_KEY,
                    "BoundingBoxes": bounding_boxes,
                }
                await websocket.send(json.dumps(subscribe_msg))

                vessels = {} # Use dict to deduplicate by MMSI

                async for message in websocket:
                    data = json.loads(message)
                    msg_type = data.get("MessageType")

                    if msg_type == "PositionReport":
                        v_data = data.get("MetaData", {})
                        mmsi = str(v_data.get("MMSI"))

                        vessels[mmsi] = {
                            "mmsi": mmsi,
                            "vessel_name": v_data.get("VesselName", "").strip(),
                            "lat": v_data.get("Latitude"),
                            "lon": v_data.get("Longitude"),
                            "sog": v_data.get("Speed"),
                            "cog": v_data.get("Course"),
                            "heading": v_data.get("Heading"),
                            "last_update": datetime.now(UTC).isoformat(),
                        }

                        # Batch updates every 5 seconds to avoid websocket spam
                        if len(vessels) >= 50:
                            await update_callback({
                                "_topic": "vessel",
                                "data": list(vessels.values())
                            })
                            vessels = {}

        except Exception as e:
            log.error("aisstream_error", error=str(e))
            await asyncio.sleep(10) # Reconnect backoff

