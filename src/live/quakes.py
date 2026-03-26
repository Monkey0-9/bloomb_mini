"""
Real-time earthquake data from USGS.
Zero key needed. Free, public data.
"""
import time
import httpx
import structlog
from dataclasses import dataclass
from datetime import datetime, timezone

log = structlog.get_logger()

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"

@dataclass
class Quake:
    id:        str
    place:     str
    mag:       float
    lat:       float
    lon:       float
    depth_km:  float
    ts:        str

_quake_cache: list[Quake] = []
_quake_ts: float = 0.0
QUAKE_TTL = 300  # 5 minutes

def get_latest_quakes() -> list[Quake]:
    global _quake_cache, _quake_ts
    now = time.time()
    if _quake_cache and (now - _quake_ts) < QUAKE_TTL:
        return _quake_cache

    try:
        resp = httpx.get(USGS_URL, timeout=15)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        
        quakes = []
        for f in features:
            props = f.get("properties", {})
            geom = f.get("geometry", {}).get("coordinates", [0, 0, 0])
            
            # Convert timestamp ms to isoformat
            time_ms = props.get("time", 0)
            if time_ms:
                ts_str = datetime.fromtimestamp(time_ms / 1000.0, timezone.utc).isoformat()
            else:
                ts_str = datetime.now(timezone.utc).isoformat()

            quakes.append(Quake(
                id       = f.get("id", ""),
                place    = props.get("place", "Unknown"),
                mag      = float(props.get("mag", 0.0)),
                lat      = float(geom[1]),
                lon      = float(geom[0]),
                depth_km = float(geom[2]),
                ts       = ts_str,
            ))
            
        _quake_cache = sorted(quakes, key=lambda q: q.mag, reverse=True)
        _quake_ts = now
        log.info("quakes_fetched", count=len(_quake_cache))
        return _quake_cache
    except Exception as e:
        log.error("usgs_error", error=str(e))
        return _quake_cache
