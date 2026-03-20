import httpx
import structlog
from dataclasses import dataclass
from datetime import datetime, timezone

log = structlog.get_logger()

@dataclass
class Aircraft:
    icao24: str
    callsign: str
    origin_country: str
    lat: float
    lon: float
    altitude_ft: int
    speed_knots: int
    heading: float

def fetch_aircraft() -> list[Aircraft]:
    """
    Fetch all aircraft from OpenSky Network.
    Anonymous access allowed.
    """
    try:
        resp = httpx.get("https://opensky-network.org/api/states/all", timeout=15)
        if resp.status_code != 200:
            return []
        
        states = resp.json().get("states") or []
        aircraft_list = []
        for s in states:
            if s[5] is None or s[6] is None:
                continue
            aircraft_list.append(Aircraft(
                icao24=s[0],
                callsign=s[1].strip() if s[1] else "UNKNOWN",
                origin_country=s[2],
                lon=s[5],
                lat=s[6],
                altitude_ft=int(s[7] * 3.281) if s[7] else 0,
                speed_knots=int(s[9] * 1.944) if s[9] else 0,
                heading=s[10] or 0.0
            ))
        return aircraft_list
    except Exception as e:
        log.error("fetch_aircraft_failed", error=str(e))
        return []

if __name__ == "__main__":
    flights = fetch_aircraft()
    print(f"Fetched {len(flights)} aircraft.")
