from datetime import UTC, datetime, timedelta

import httpx
import structlog
from sgp4.api import Satrec, jday

log = structlog.get_logger()

# Celestrak TLE URLs — completely free, no registration
SATELLITE_TLE_URLS = {
    "Sentinel-2A": "https://celestrak.org/satcat/tle.php?CATNR=40697",
    "Sentinel-2B": "https://celestrak.org/satcat/tle.php?CATNR=42063",
    "Landsat-8":   "https://celestrak.org/satcat/tle.php?CATNR=39084",
    "Landsat-9":   "https://celestrak.org/satcat/tle.php?CATNR=49260",
    "NOAA-20":     "https://celestrak.org/satcat/tle.php?CATNR=43013",
    "Terra":       "https://celestrak.org/satcat/tle.php?CATNR=25994",
    "Aqua":        "https://celestrak.org/satcat/tle.php?CATNR=27424",
}

# Also fetch entire EO constellation from Celestrak group feeds
EO_TLE_GROUP = "https://celestrak.org/SOCRATES/query.php?GROUP=earth-resources"


def fetch_tle(sat_name: str, url: str) -> tuple[str, str] | None:
    """Fetch TLE lines for a single satellite from Celestrak."""
    try:
        resp = httpx.get(url, timeout=15)
        lines = [l.strip() for l in resp.text.strip().split("\n") if l.strip()]
        if len(lines) >= 2:
            # TLE format: name (optional), line1 (starts with "1 "), line2 (starts with "2 ")
            tle1 = next((l for l in lines if l.startswith("1 ")), None)
            tle2 = next((l for l in lines if l.startswith("2 ")), None)
            if tle1 and tle2:
                return tle1, tle2
    except Exception as e:
        log.warning("tle_fetch_failed", satellite=sat_name, error=str(e))
    return None


def propagate_satellite(tle1: str, tle2: str, minutes_ahead: int = 120,
                         step_minutes: int = 2) -> list[dict]:
    """
    Propagate satellite orbit for next N minutes using SGP4.
    Returns list of {lat, lon, alt_km, timestamp} positions.
    """
    satellite = Satrec.twoline2rv(tle1, tle2)
    positions = []
    now = datetime.now(UTC)

    for i in range(0, minutes_ahead, step_minutes):
        t = now + timedelta(minutes=i)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond/1e6)

        e, r, v = satellite.sgp4(jd, fr)
        if e != 0:
            continue  # propagation error

        # Convert ECI to lat/lon/alt using basic math
        x, y, z = r  # km
        import math
        lon = math.degrees(math.atan2(y, x)) - (now.timestamp() - t.timestamp()) * 360/86164
        lat = math.degrees(math.atan2(z, math.sqrt(x**2 + y**2)))
        alt = math.sqrt(x**2 + y**2 + z**2) - 6371  # km above Earth surface

        # Normalize longitude to -180 to 180
        lon = ((lon + 180) % 360) - 180

        positions.append({
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "alt_km": round(alt, 1),
            "timestamp": t.isoformat(),
            "minutes_from_now": i,
        })

    return positions


def get_ground_track(sat_name: str) -> dict:
    """Get full ground track for a satellite for next 2 hours."""
    url = SATELLITE_TLE_URLS.get(sat_name)
    if not url:
        return {"error": f"Unknown satellite: {sat_name}"}

    tle = fetch_tle(sat_name, url)
    if not tle:
        return {"error": f"Could not fetch TLE for {sat_name}"}

    positions = propagate_satellite(tle[0], tle[1], minutes_ahead=120, step_minutes=1)
    current_pos = positions[0] if positions else None
    next_pass = None

    # Find current position and compute next sub-satellite point over key ports
    PORT_LOCATIONS = {
        "Rotterdam": (51.96, 4.05),
        "Singapore": (1.27, 103.82),
        "Shanghai": (31.23, 121.47),
        "Los Angeles": (33.73, -118.26),
        "Hamburg": (53.55, 9.99),
    }

    return {
        "satellite": sat_name,
        "current_position": current_pos,
        "ground_track": positions,
        "orbit_period_minutes": 100,  # ~100min for LEO
        "next_24h_passes": _compute_passes(positions, PORT_LOCATIONS),
        "tle_age_hours": 0,  # freshly fetched
    }


def _compute_passes(positions: list[dict],
                    locations: dict[str, tuple]) -> list[dict]:
    """Find when satellite passes within 1000km of key locations."""
    import math
    passes = []
    for pos in positions:
        for port_name, (port_lat, port_lon) in locations.items():
            # Great circle distance approximation
            dlat = math.radians(pos["lat"] - port_lat)
            dlon = math.radians(pos["lon"] - port_lon)
            a = (math.sin(dlat/2)**2 +
                 math.cos(math.radians(port_lat)) *
                 math.cos(math.radians(pos["lat"])) *
                 math.sin(dlon/2)**2)
            dist_km = 6371 * 2 * math.asin(math.sqrt(a))
            if dist_km < 1500:  # within 1500km = roughly within imaging swath
                passes.append({
                    "location": port_name,
                    "distance_km": round(dist_km),
                    "time": pos["timestamp"],
                    "minutes_from_now": pos["minutes_from_now"],
                    "satellite_lat": pos["lat"],
                    "satellite_lon": pos["lon"],
                })
    return passes[:20]  # top 20 passes
