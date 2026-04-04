"""
Real satellite orbital positions from Celestrak TLE data.
Fetches ALL Earth Observation satellites — not just 3 hardcoded ones.
Propagates using sgp4 Python library (open source, free).
"""
import math
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
import structlog
from sgp4.api import Satrec, jday

log = structlog.get_logger()

# Celestrak group TLE — all Earth Resources satellites at once
CELESTRAK_EO_GROUP = "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle"

# Key satellites with individual URLs for guaranteed availability
KEY_SATELLITES = {
    "Sentinel-2A":  "https://celestrak.org/satcat/tle.php?CATNR=40697",
    "Sentinel-2B":  "https://celestrak.org/satcat/tle.php?CATNR=42063",
    "Landsat-8":    "https://celestrak.org/satcat/tle.php?CATNR=39084",
    "Landsat-9":    "https://celestrak.org/satcat/tle.php?CATNR=49260",
    "NOAA-20":      "https://celestrak.org/satcat/tle.php?CATNR=43013",
    "Terra":        "https://celestrak.org/satcat/tle.php?CATNR=25994",
    "Aqua":         "https://celestrak.org/satcat/tle.php?CATNR=27424",
    "ISS":          "https://celestrak.org/satcat/tle.php?CATNR=25544",
}

@dataclass
class SatPosition:
    name:     str
    lat:      float
    lon:      float
    alt_km:   float
    ts:       str

@dataclass
class SatOrbit:
    name:         str
    current:      SatPosition
    ground_track: list[SatPosition]   # next 120 minutes
    period_min:   float
    inclination:  float
    altitude_km:  float

    @property
    def lat(self) -> float:
        return self.current.lat

    @property
    def lon(self) -> float:
        return self.current.lon

_tle_cache: dict[str, tuple[str, str]] = {}
_tle_ts:    dict[str, float] = {}
_all_sats:  list[SatOrbit] = []
_all_sats_ts: float = 0.0
TLE_TTL = 3600 * 6   # 6 hours
ORBIT_TTL = 30       # 30 seconds (positions change constantly)

def _fetch_tle(name: str, url: str) -> tuple[str, str] | None:
    now = time.time()
    if name in _tle_cache and (now - _tle_ts.get(name, 0)) < TLE_TTL:
        return _tle_cache[name]
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        lines = [l.strip() for l in resp.text.split("\n") if l.strip()]
        tle1 = next((l for l in lines if l.startswith("1 ")), None)
        tle2 = next((l for l in lines if l.startswith("2 ")), None)
        if tle1 and tle2:
            _tle_cache[name] = (tle1, tle2)
            _tle_ts[name]    = now
            return tle1, tle2
    except Exception as e:
        log.warning("tle_fetch_failed", satellite=name, error=str(e))
    return None

def _gmst(jd: float, fr: float) -> float:
    """Greenwich Mean Sidereal Time in degrees."""
    days = jd + fr - 2451545.0
    return (280.46061837 + 360.98564736629 * days) % 360

def _eci_to_geodetic(r: list[float], jd: float, fr: float) -> tuple[float, float, float]:
    """Convert ECI position vector to lat, lon, altitude."""
    x, y, z = r
    theta = _gmst(jd, fr)
    lon = (math.degrees(math.atan2(y, x)) - theta + 180) % 360 - 180
    r_mag = math.sqrt(x**2 + y**2 + z**2)
    lat = math.degrees(math.asin(z / r_mag))
    alt = r_mag - 6371.0
    return lat, lon, alt

def propagate_orbit(name: str, tle1: str, tle2: str,
                    minutes: int = 120) -> SatOrbit | None:
    """Propagate satellite orbit for next N minutes."""
    try:
        sat = Satrec.twoline2rv(tle1, tle2)
        now = datetime.now(UTC)
        track = []

        for i in range(0, minutes + 1, 1):
            t = now + timedelta(minutes=i)
            jd, fr = jday(t.year, t.month, t.day,
                          t.hour, t.minute, t.second + t.microsecond / 1e6)
            e, r, v = sat.sgp4(jd, fr)
            if e != 0:
                continue

            lat, lon, alt = _eci_to_geodetic(r, jd, fr)
            track.append(SatPosition(
                name  = name,
                lat   = round(lat, 4),
                lon   = round(lon, 4),
                alt_km= round(alt, 1),
                ts    = t.isoformat(),
            ))

        if not track:
            return None

        # Parse inclination from TLE2
        try:
            inclination = float(tle2.split()[2])
            mean_motion = float(tle2.split()[7])
            period_min  = 1440.0 / mean_motion
        except Exception:
            inclination = 98.0
            period_min  = 100.0

        return SatOrbit(
            name         = name,
            current      = track[0],
            ground_track = track,
            period_min   = round(period_min, 1),
            inclination  = round(inclination, 2),
            altitude_km  = round(track[0].alt_km, 0),
        )
    except Exception as e:
        log.error("orbit_propagation_error", satellite=name, error=str(e))
        return None

def get_all_eo_satellites() -> list[SatOrbit]:
    """Fetch ALL EO satellites from Celestrak group TLE and propagate positions."""
    global _all_sats, _all_sats_ts

    now = time.time()
    if _all_sats and (now - _all_sats_ts) < ORBIT_TTL:
        return _all_sats

    # First try the group TLE (all EO satellites at once)
    orbits = []
    try:
        headers = {"User-Agent": "SatTrade/2.0 research@sattrade.io"}
        resp = httpx.get(CELESTRAK_EO_GROUP, timeout=20, headers=headers)
        lines = [l.strip() for l in resp.text.split("\n") if l.strip()]

        i = 0
        while i < len(lines) - 2:
            if lines[i].startswith("1 ") or lines[i].startswith("2 "):
                i += 1
                continue
            name = lines[i].strip()
            tle1 = lines[i+1] if (i+1 < len(lines) and lines[i+1].startswith("1 ")) else None
            tle2 = lines[i+2] if (i+2 < len(lines) and lines[i+2].startswith("2 ")) else None
            if tle1 and tle2:
                orbit = propagate_orbit(name, tle1, tle2, minutes=90)
                if orbit:
                    orbits.append(orbit)
            i += 3

    except Exception as e:
        log.warning("celestrak_group_error", error=str(e))

    # Fall back to individual key satellites if group failed
    if not orbits:
        for sat_name, url in KEY_SATELLITES.items():
            tle = _fetch_tle(sat_name, url)
            if tle:
                orbit = propagate_orbit(sat_name, tle[0], tle[1], minutes=120)
                if orbit:
                    orbits.append(orbit)

    _all_sats    = orbits
    _all_sats_ts = now
    log.info("orbits_computed", count=len(orbits))
    return orbits
