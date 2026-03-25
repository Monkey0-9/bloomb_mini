"""
Global Seismic Intelligence — USGS live earthquake tracking.
Maps earthquakes to commodity and industrial impact.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"

CHOKEPOINTS = [
    {"name": "Strait of Hormuz", "lat": 26.6, "lon": 56.3, "radius_km": 300, "tickers": ["XOM", "CVX", "LNG"]},
    {"name": "Suez Canal", "lat": 30.5, "lon": 32.3, "radius_km": 200, "tickers": ["AMKBY", "ZIM"]},
    {"name": "Bab el-Mandeb", "lat": 12.6, "lon": 43.3, "radius_km": 250, "tickers": ["ZIM", "LNG"]},
]

@dataclass
class SeismicEvent:
    id: str
    mag: float
    place: str
    time: datetime
    lat: float
    lon: float
    depth_km: float
    impact_tickers: list[str]
    is_near_chokepoint: bool = False

def _haversine(lat1, lon1, lat2, lon2):
    import math
    R = 6371  # Radius of earth in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

async def get_latest_quakes() -> list[SeismicEvent]:
    """Fetch M4.5+ earthquakes and compute financial chokepoint proximity."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(USGS_URL)
            data = resp.json()
            features = data.get("features", [])
            
            events = []
            for f in features:
                props = f["properties"]
                geom = f["geometry"]
                lon, lat, depth = geom["coordinates"]
                
                impact_tickers = []
                is_choke = False
                for cp in CHOKEPOINTS:
                    dist = _haversine(lat, lon, cp["lat"], cp["lon"])
                    if dist < cp["radius_km"]:
                        impact_tickers.extend(cp["tickers"])
                        is_choke = True
                
                events.append(SeismicEvent(
                    id=f["id"], mag=float(props["mag"]),
                    place=props["place"],
                    time=datetime.fromtimestamp(props["time"]/1000, tz=timezone.utc),
                    lat=float(lat), lon=float(lon), depth_km=float(depth),
                    impact_tickers=list(set(impact_tickers)),
                    is_near_chokepoint=is_choke
                ))
            
            return events
    except Exception as e:
        logger.error(f"Seismic tracking error: {e}")
        return []
