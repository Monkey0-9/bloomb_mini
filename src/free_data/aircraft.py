"""
Global Aircraft Intelligence — Zero-key OpenSky tracking.
Discovers military and cargo aircraft movements impacting finance.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"

# Military ICAO24 hex ranges (public data)
MILITARY_PREFIXES = {
    "ae0": "USAF", "ae1": "USAF", "ae2": "USAF", "ae3": "USAF", "ae4": "US Navy", "ae5": "USMC", "ae6": "US Army",
    "43c": "RAF", "3a4": "French AF", "84f": "Luftwaffe", "7c4": "RAAF", "0d0": "PLAAF"
}
# Cargo operator callsign prefixes
CARGO_PREFIXES = {"FDX": "FedEx", "UPS": "UPS", "DHK": "DHL", "CLX": "Cargolux", "GTI": "Atlas Air"}

@dataclass
class AircraftEvent:
    icao24: str
    callsign: str
    category: str
    lat: float
    lon: float
    alt_ft: float
    squawk: str
    operator: str
    is_emergency: bool = False

async def get_live_aircraft() -> list[AircraftEvent]:
    """Fetch all aircraft globally and filter/categorize."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(OPENSKY_URL)
            data = resp.json()
            states = data.get("states", [])

            events = []
            for s in states:
                # v[5]=lon, v[6]=lat, v[0]=icao24, v[1]=callsign, v[7]=alt, v[14]=squawk
                if not s[5] or not s[6]: continue

                icao = (s[0] or "").lower()
                call = (s[1] or "").strip().upper()
                squawk = str(s[14]).strip() if s[14] else ""

                category = "COMMERCIAL"
                operator = "Civilian"

                if any(icao.startswith(p) for p in MILITARY_PREFIXES):
                    category = "MILITARY"
                    operator = MILITARY_PREFIXES[next(p for p in MILITARY_PREFIXES if icao.startswith(p))]
                elif any(call.startswith(p) for p in CARGO_PREFIXES):
                    category = "CARGO"
                    operator = CARGO_PREFIXES[call[:3]]

                is_emergency = squawk in ["7700", "7600", "7500"]

                if category != "COMMERCIAL" or is_emergency:
                    events.append(AircraftEvent(
                        icao24=icao, callsign=call, category=category,
                        lat=float(s[6]), lon=float(s[5]),
                        alt_ft=float(s[7] or 0) * 3.28084,
                        squawk=squawk, operator=operator, is_emergency=is_emergency
                    ))

            return events
    except Exception as e:
        logger.error(f"Aircraft tracking error: {e}")
        return []
