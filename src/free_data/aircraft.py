"""
Real-time aircraft tracking via OpenSky Network (100% free, no API key).
Enriches raw data with category classification, operator lookup, and alert logic.
"""
import httpx
import random
import time
import structlog
from datetime import datetime, timezone
from dataclasses import dataclass

log = structlog.get_logger()

# ── Caching ─────────────────────────────────────────────────────────────────
_aircraft_cache: list = []
_aircraft_ts: float = 0
AIRCRAFT_TTL = 45  # seconds

# ── Operator / airline code prefixes ────────────────────────────────────────
AIRLINE_PREFIXES = {
    "AAL":"American Airlines","DAL":"Delta Air Lines","UAL":"United Airlines",
    "SWA":"Southwest","BAW":"British Airways","DLH":"Lufthansa","AFR":"Air France",
    "UAE":"Emirates","QTR":"Qatar Airways","SIA":"Singapore Airlines","KAL":"Korean Air",
    "ANA":"All Nippon Airways","JAL":"Japan Airlines","CCA":"Air China",
    "CSN":"China Southern","CES":"China Eastern","FDX":"FedEx Express",
    "UPS":"UPS Airlines","CLX":"Cargolux","GTI":"Atlas Air","BOX":"West Atlantic",
    "RYR":"Ryanair","EZY":"easyJet","VLG":"Vueling","IBK":"Norwegian Air",
    "THY":"Turkish Airlines","SVA":"Saudi Arabian Airlines","ETH":"Ethiopian Airlines",
    "MSR":"EgyptAir","RAM":"Royal Air Maroc","KQA":"Kenya Airways",
    "RFR":"Ryanair (FR)","WJA":"WestJet","ACA":"Air Canada","LAN":"LATAM Airlines",
    "AVA":"Avianca","VIV":"VivaAerobus","AMX":"Aeromexico",
}

MILITARY_SQUAWKS = {"7700", "7600", "7500"}
MILITARY_CALLSIGN_PREFIXES = {
    "RCH","MMF","CFC","NVY","NAVY","USAF","ARMY","USCG","RRR","XCH",
    "AME","GAF","RAF","FAF","IAF","RAAF","RCAF","ROKAF","IDF","HKAF",
    "MAGMA","LAGR","HOMER","JAKE","ATLAS","REACH","IRON","ANVIL",
}

CARGO_PREFIXES = {"FDX","UPS","CLX","GTI","BOX","ABX","ATN","NCR","SWQ","LOG"}

@dataclass
class AircraftState:
    icao24: str
    callsign: str
    country: str
    lat: float
    lon: float
    alt_ft: int
    speed_knots: int
    heading: float
    category: str        # MILITARY / CARGO / COMMERCIAL / PRIVATE / GOVERNMENT
    operator: str
    alert_level: str     # NONE / INFO / WARNING / CRITICAL
    squawk: str
    on_ground: bool
    last_seen: datetime


def _classify(callsign: str, country: str, squawk: str, alt_ft: int) -> tuple[str, str, str]:
    """Returns (category, operator, alert_level)."""
    cs = (callsign or "").strip().upper()
    prefix = cs[:3]
    sq = (squawk or "").strip()

    # Alert
    alert = "CRITICAL" if sq in MILITARY_SQUAWKS else "NONE"
    if alt_ft < 500 and alt_ft > 0:
        alert = "WARNING"  # Extremely low altitude

    # Category
    if any(cs.startswith(p) for p in MILITARY_CALLSIGN_PREFIXES):
        return "MILITARY", f"{country} Military", alert
    if prefix in CARGO_PREFIXES:
        return "CARGO", AIRLINE_PREFIXES.get(prefix, "Cargo Operator"), alert
    if country in ("United States", "China", "Russia", "United Kingdom", "France", "India"):
        if cs.startswith(("EXEC","VIP","STATE","GOV","GOVT")):
            return "GOVERNMENT", f"{country} Government", alert
    if prefix in AIRLINE_PREFIXES:
        return "COMMERCIAL", AIRLINE_PREFIXES[prefix], alert

    return "COMMERCIAL", AIRLINE_PREFIXES.get(prefix, f"{country} Civil Aviation"), alert


def get_live_aircraft(limit: int = 1500) -> list[dict]:
    """
    Fetch all live aircraft from OpenSky Network (free, no key).
    Returns enriched list with category, operator, route context.
    """
    global _aircraft_cache, _aircraft_ts
    now_ts = time.time()
    if _aircraft_cache and (now_ts - _aircraft_ts) < AIRCRAFT_TTL:
        return _aircraft_cache[:limit]

    try:
        resp = httpx.get(
            "https://opensky-network.org/api/states/all",
            timeout=20,
            headers={"User-Agent": "SatTrade-Intelligence/2.0"}
        )
        if resp.status_code != 200:
            log.warning("opensky_non_200", status=resp.status_code)
            return _fallback_aircraft(limit)

        states = resp.json().get("states") or []
        aircraft = []
        for s in states:
            if s[5] is None or s[6] is None:
                continue
            lat, lon = s[6], s[5]
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            alt_m = s[7] or 0
            alt_ft = int(alt_m * 3.281)
            speed_ms = s[9] or 0
            speed_kts = int(speed_ms * 1.944)
            callsign = (s[1] or "").strip()
            country = s[2] or "Unknown"
            squawk = s[14] or ""
            on_ground = bool(s[8])
            heading = s[10] or 0.0

            if on_ground:
                continue  # Skip ground traffic for map clarity

            cat, operator, alert = _classify(callsign, country, squawk, alt_ft)
            aircraft.append({
                "icao24": s[0],
                "callsign": callsign or f"N{s[0][:4].upper()}",
                "country": country,
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "alt_ft": alt_ft,
                "velocity": speed_kts,
                "heading": round(heading, 1),
                "category": cat,
                "operator": operator,
                "alert_level": alert,
                "squawk": squawk,
                "on_ground": on_ground,
                "position": {
                    "lat": round(lat, 4),
                    "lon": round(lon, 4),
                    "alt_ft": alt_ft,
                    "heading": round(heading, 1),
                    "speed_knots": speed_kts,
                },
                "source": "OpenSky Network (live, no key)",
                "ts": datetime.now(timezone.utc).isoformat(),
            })

        log.info("opensky_fetched", count=len(aircraft))
        _aircraft_cache = aircraft
        _aircraft_ts = now_ts
        return aircraft[:limit]

    except Exception as e:
        log.error("opensky_fetch_failed", error=str(e))
        return _fallback_aircraft(limit)


def _fallback_aircraft(limit: int) -> list[dict]:
    """Generate realistic fallback aircraft if OpenSky is down."""
    # Dense on real air corridors
    CORRIDORS = [
        (40, 65, -120, -60),  # North Atlantic
        (20, 45, -80, -20),   # Central Atlantic
        (30, 60, -10, 50),    # Europe
        (25, 50, 60, 120),    # Middle East / Asia
        (10, 40, 100, 150),   # East Asia
        (-30, 30, 100, 150),  # Pacific rim
        (25, 60, -125, -65),  # North America
    ]
    result = []
    random.seed(int(time.time() // 60))  # Stable per minute
    for i in range(min(limit, 800)):
        c = CORRIDORS[i % len(CORRIDORS)]
        lat = random.uniform(c[0], c[1])
        lon = random.uniform(c[2], c[3])
        cs_prefix = random.choice(list(AIRLINE_PREFIXES.keys()))
        cs = f"{cs_prefix}{random.randint(100,9999)}"
        cat, op, alert = _classify(cs, "Unknown", "", 35000)
        result.append({
            "icao24": f"ab{i:04x}",
            "callsign": cs,
            "country": "Unknown",
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "alt_ft": random.randint(28000, 41000),
            "velocity": random.randint(420, 520),
            "heading": round(random.uniform(0, 360), 1),
            "category": cat,
            "operator": op,
            "alert_level": alert,
            "squawk": "1200",
            "on_ground": False,
            "position": {"lat": round(lat, 4), "lon": round(lon, 4), "alt_ft": 35000, "heading": 0, "speed_knots": 460},
            "source": "SatTrade Fallback (OpenSky unavailable)",
            "ts": datetime.now(timezone.utc).isoformat(),
        })
    return result
