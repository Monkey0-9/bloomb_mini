"""
Real satellite orbital positions from Celestrak TLE data.
NO API KEY. NO REGISTRATION. Celestrak is a publicly funded resource.
All URLs are completely open. No rate limits for reasonable use.
Uses sgp4 Python library (open source, free) for orbital propagation.
"""

import httpx
import math
import time
import structlog
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from sgp4.api import Satrec, jday

log = structlog.get_logger()

SATELLITE_TLE_CATALOG = {
    # Earth Observation satellites
    "Sentinel-2A":  ("40697", "https://celestrak.org/satcat/tle.php?CATNR=40697"),
    "Sentinel-2B":  ("42063", "https://celestrak.org/satcat/tle.php?CATNR=42063"),
    "Sentinel-1A":  ("39634", "https://celestrak.org/satcat/tle.php?CATNR=39634"),
    "Sentinel-1B":  ("41456", "https://celestrak.org/satcat/tle.php?CATNR=41456"),
    "Landsat-8":    ("39084", "https://celestrak.org/satcat/tle.php?CATNR=39084"),
    "Landsat-9":    ("49260", "https://celestrak.org/satcat/tle.php?CATNR=49260"),
    "NOAA-20":      ("43013", "https://celestrak.org/satcat/tle.php?CATNR=43013"),
    "NOAA-21":      ("54234", "https://celestrak.org/satcat/tle.php?CATNR=54234"),
    "Terra-MODIS":  ("25994", "https://celestrak.org/satcat/tle.php?CATNR=25994"),
    "Aqua-MODIS":   ("27424", "https://celestrak.org/satcat/tle.php?CATNR=27424"),
    # ISS
    "ISS":          ("25544", "https://celestrak.org/satcat/tle.php?CATNR=25544"),
    # Commercial EO
    "Planet-Dove-1":("43792", "https://celestrak.org/satcat/tle.php?CATNR=43792"),
}

EO_GROUP_URL = "https://celestrak.org/SOCRATES/query.php?GROUP=earth-resources&FORMAT=TLE"

@dataclass
class SatellitePosition:
    lat:     float
    lon:     float
    alt_km:  float
    timestamp: datetime
    minutes_from_now: int

@dataclass
class SatelliteOrbit:
    name:          str
    catalog_number: str
    current_pos:   SatellitePosition
    ground_track:  list[SatellitePosition]
    next_passes:   list[dict]
    orbital_period_min: float
    inclination_deg: float
    altitude_km:   float
    last_tle_update: datetime

_tle_cache: dict[str, tuple[str, str]] = {}
_tle_ts: dict[str, float] = {}
TLE_CACHE_TTL = 3600 * 6

def _fetch_tle(name: str, url: str) -> tuple[str, str] | None:
    global _tle_cache, _tle_ts
    now = time.time()
    if name in _tle_cache and (now - _tle_ts.get(name, 0)) < TLE_CACHE_TTL:
        return _tle_cache[name]
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        lines = [l.strip() for l in resp.text.strip().split("\n") if l.strip()]
        tle1 = next((l for l in lines if l.startswith("1 ")), None)
        tle2 = next((l for l in lines if l.startswith("2 ")), None)
        if tle1 and tle2:
            _tle_cache[name] = (tle1, tle2)
            _tle_ts[name] = now
            log.info("tle_fetched", satellite=name)
            return tle1, tle2
    except Exception as e:
        log.error("tle_fetch_error", satellite=name, error=str(e))
    return None

def _eci_to_geodetic(r: list[float], dt: datetime) -> tuple[float, float, float]:
    x, y, z = r
    theta_gst = _greenwich_sidereal_time(dt)
    lon = math.degrees(math.atan2(y, x)) - theta_gst
    lon = ((lon + 180) % 360) - 180
    r_mag = math.sqrt(x**2 + y**2 + z**2)
    lat = math.degrees(math.asin(z / r_mag))
    alt = r_mag - 6371.0
    return lat, lon, alt

def _greenwich_sidereal_time(dt: datetime) -> float:
    j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    days = (dt - j2000).total_seconds() / 86400.0
    gmst = 280.46061837 + 360.98564736629 * days
    return gmst % 360

def get_orbit(name: str) -> SatelliteOrbit | None:
    catalog = SATELLITE_TLE_CATALOG.get(name)
    if not catalog:
        return None
    cat_num, url = catalog
    tle = _fetch_tle(name, url)
    if not tle:
        return None
    tle1, tle2 = tle
    satellite = Satrec.twoline2rv(tle1, tle2)
    now = datetime.now(timezone.utc)
    positions = []
    for min_offset in range(0, 121, 1):
        t = now + timedelta(minutes=min_offset)
        jd, fr = jday(t.year, t.month, t.day,
                      t.hour, t.minute, t.second + t.microsecond/1e6)
        e, r, v = satellite.sgp4(jd, fr)
        if e != 0:
            continue
        lat, lon, alt = _eci_to_geodetic(r, t)
        positions.append(SatellitePosition(
            lat=round(lat, 4), lon=round(lon, 4), alt_km=round(alt, 1),
            timestamp=t, minutes_from_now=min_offset))
    if not positions:
        return None
    try:
        parts = tle2.split()
        inclination = float(parts[2])
        period_min = 1440.0 / float(parts[7])
    except (IndexError, ValueError):
        inclination = 98.0
        period_min = 100.0
    KEY_LOCATIONS = {
        "Rotterdam": (51.96, 4.05), "Singapore": (1.27, 103.82),
        "Shanghai": (31.23, 121.47), "Los Angeles": (33.73,-118.26),
        "Hamburg": (53.55, 9.99), "Dunkirk": (51.04, 2.38),
        "Sabine Pass": (29.73, -93.87), "Pohang": (36.04, 129.43),
    }
    passes = []
    for pos in positions:
        for loc_name, (loc_lat, loc_lon) in KEY_LOCATIONS.items():
            dist = _haversine(pos.lat, pos.lon, loc_lat, loc_lon)
            if dist < 1200:
                passes.append({
                    "location": loc_name, "distance_km": round(dist),
                    "minutes_from_now": pos.minutes_from_now,
                    "time": pos.timestamp.isoformat(),
                    "sat_lat": pos.lat, "sat_lon": pos.lon, "alt_km": pos.alt_km,
                })
    return SatelliteOrbit(
        name=name, catalog_number=cat_num, current_pos=positions[0],
        ground_track=positions, next_passes=passes[:20],
        orbital_period_min=round(period_min, 1), inclination_deg=inclination,
        altitude_km=positions[0].alt_km, last_tle_update=now,
    )

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.asin(math.sqrt(a))
