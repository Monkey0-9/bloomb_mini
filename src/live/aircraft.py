import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

import httpx
import structlog
from dotenv import load_dotenv

load_dotenv()

log = structlog.get_logger()

OPENSKY_USER = os.getenv("OPENSKY_USERNAME")
OPENSKY_PASS = os.getenv("OPENSKY_PASSWORD")

# Military ICAO24 hex prefixes — compiled from public OSINT/academic sources
MILITARY_HEX_PREFIXES = {
    "ae": "US Military",       # USAF/USN/USMC/Army/Coast Guard
    "43": "UK Military",       # RAF/Royal Navy Fleet Air Arm
    "3a": "French Air Force",
    "3b": "French Navy",
    "84": "German Luftwaffe",
    "48": "Swedish Air Force",
    "47": "Swedish Air Force",
    "4b": "Swiss Air Force",
    "50": "Polish Air Force",
    "71": "Turkish Air Force",
    "73": "Israeli Air Force",
    "89": "Japan ASDF",
    "8f": "South Korean Air Force",
    "c0": "Canadian Forces",
    "7c": "Australian RAAF",
    "e4": "Brazilian Air Force",
    "0d": "Chinese PLA Air Force",
    "6a": "Indian Air Force",
    "0a": "Russian Air Force",
    "0b": "Russian Air Force",
}

# Specific VIP/government ICAO24 hex codes — public OSINT knowledge
VIP_AIRCRAFT = {
    "ae0434": "Air Force One (USAF VC-25A primary)",
    "ae04cc": "Air Force One (USAF VC-25A backup)",
    "ae014a": "Air Force Two (USAF C-32A)",
    "43c6f5": "UK RAF Voyager (Prime Minister aircraft)",
    "43c782": "UK RAF Voyager (Royal Family)",
    "3c6675": "German State Aircraft A340",
    "3a4ee7": "French Presidential A330",
}

# Cargo carrier callsign prefixes
CARGO_PREFIXES = {
    "FDX": "FedEx Express",
    "UPS": "UPS Airlines",
    "DHK": "DHL Air",
    "CLX": "Cargolux",
    "ABX": "ABX Air (Amazon)",
    "GTI": "Atlas Air",
    "ATN": "Air Transport International",
    "QEC": "Qantas Freight",
    "UAE": "Emirates SkyCargo",
    "QTR": "Qatar Airways Cargo",
    "ICL": "Turkish Cargo",
    "ETH": "Ethiopian Cargo",
    "MSC": "MSC Air Cargo",
    "SIA": "Singapore Airlines Cargo",
    "CCA": "Air China Cargo",
    "CSN": "China Southern Cargo",
    "KAL": "Korean Air Cargo",
}

# Critical squawk codes
SQUAWK_ALERTS = {
    "7700": {"level": "EMERGENCY",     "desc": "General emergency declared"},
    "7600": {"level": "RADIO_FAILURE", "desc": "Radio communication failure"},
    "7500": {"level": "HIJACK",        "desc": "Unlawful interference/hijack"},
    "7400": {"level": "DRONE_LOST",    "desc": "UAS lost link"},
}

@dataclass
class Aircraft:
    icao24:    str
    callsign:  str
    country:   str
    lat:       float
    lon:       float
    alt_ft:    int
    speed_kts: int
    heading:   float
    on_ground: bool
    squawk:    str
    category:  Literal["MILITARY","CARGO","GOVERNMENT","EMERGENCY","UNKNOWN"]
    operator:  str
    vip:       str | None
    alert:     dict | None
    ts:        str

_cache: list = []
_cache_ts: float = 0.0
CACHE_TTL = 10.0

def get_simulated_aircraft() -> list[Aircraft]:
    """Generates high-fidelity simulated aircraft on major global routes."""
    routes = [
        {"name": "Trans-Atlantic", "start": (40, -74), "end": (51, 0), "cat": "CARGO"}, # JFK to LHR
        {"name": "Euro-Asia", "start": (48, 2), "end": (35, 139), "cat": "CARGO"}, # CDG to HND
        {"name": "Pacific Transit", "start": (37, -122), "end": (31, 121), "cat": "CARGO"}, # SFO to PVG
        {"name": "Gulf Corridor", "start": (25, 55), "end": (51, 0), "cat": "GOVERNMENT"}, # DXB to LHR
    ]
    
    sim_aircraft = []
    for i, route in enumerate(routes):
        for j in range(5):
            icao = f"sim{i}{j}"
            progress = ((time.time() / 1800) + j/5) % 1.0
            lat = route["start"][0] + (route["end"][0] - route["start"][0]) * progress
            lon = route["start"][1] + (route["end"][1] - route["start"][1]) * progress
            
            sim_aircraft.append(Aircraft(
                icao24 = icao,
                callsign = f"SIM{route['cat'][0]}{i}{j}",
                country = "International",
                lat = lat,
                lon = lon,
                alt_ft = 35000,
                speed_kts = 450,
                heading = 90,
                on_ground = False,
                squawk = "",
                category = route["cat"],
                operator = "SatTrade Simulated",
                vip = None,
                alert = None,
                ts = datetime.now(UTC).isoformat()
            ))
    return sim_aircraft

def fetch_aircraft(category_filter: list[str] | None = None) -> list[Aircraft]:
    global _cache, _cache_ts
    now = time.time()
    
    # Use cache if fresh
    if _cache and (now - _cache_ts) < CACHE_TTL:
        result = _cache
        if category_filter:
            result = [a for a in result if a.category in category_filter]
        return result

    # 1. Start with simulated aircraft for 'live' movement
    aircraft = get_simulated_aircraft()

    # 2. Try to fetch real OpenSky data
    auth = None
    if OPENSKY_USER and OPENSKY_PASS:
        auth = (OPENSKY_USER, OPENSKY_PASS)
        log.info("using_opensky_auth", user=OPENSKY_USER)

    try:
        resp = httpx.get(
            "https://opensky-network.org/api/states/all",
            auth=auth,
            timeout=25,
        )
        if resp.status_code != 429:
            resp.raise_for_status()
            states = resp.json().get("states", []) or []
            
            real_aircraft = []
            for s in states:
                if len(s) < 17 or s[5] is None or s[6] is None:
                    continue
                
                # ... mapping logic for real aircraft (simplified for brevity)
                # To keep it robust, we'll only add significant ones
                icao24 = (s[0] or "").strip().lower()
                if any(icao24.startswith(p) for p in MILITARY_HEX_PREFIXES) or icao24 in VIP_AIRCRAFT:
                     real_aircraft.append(Aircraft(
                        icao24    = icao24,
                        callsign  = (s[1] or "").strip().upper(),
                        country   = s[2] or "",
                        lat       = float(s[6]),
                        lon       = float(s[5]),
                        alt_ft    = int((s[7] or 0) * 3.281),
                        speed_kts = int((s[9] or 0) * 1.944),
                        heading   = float(s[10] or 0),
                        on_ground = bool(s[8]),
                        squawk    = (s[14] or "").strip(),
                        category  = "MILITARY" if any(icao24.startswith(p) for p in MILITARY_HEX_PREFIXES) else "GOVERNMENT",
                        operator  = "Real Tracking",
                        vip       = VIP_AIRCRAFT.get(icao24),
                        alert     = None,
                        ts        = datetime.now(UTC).isoformat()
                    ))
            aircraft.extend(real_aircraft)
            
    except Exception as e:
        log.error("opensky_error", error=str(e))

    _cache    = aircraft
    _cache_ts = now
    return aircraft

def get_squawk_alerts() -> list[dict]:
    return [a.alert for a in fetch_aircraft() if a.alert is not None]

def to_geojson(aircraft: list[Aircraft]) -> dict:
    color_map = {
        "GOVERNMENT": "#FFD700",
        "MILITARY":   "#E24B4A",
        "CARGO":      "#FF8C42",
        "EMERGENCY":  "#FF0000",
        "UNKNOWN":    "#888780",
    }
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [a.lon, a.lat]},
                "properties": {
                    "icao24":    a.icao24,
                    "callsign":  a.callsign,
                    "category":  a.category,
                    "operator":  a.operator,
                    "country":   a.country,
                    "alt_ft":    a.alt_ft,
                    "speed_kts": a.speed_kts,
                    "heading":   a.heading,
                    "on_ground": a.on_ground,
                    "squawk":    a.squawk,
                    "alert":     a.alert,
                    "vip":       a.vip,
                    "color":     color_map.get(a.category, "#888780"),
                    "size":      12 if a.category == "GOVERNMENT" else 6,
                },
            }
            for a in aircraft
        ],
        "meta": {
            "count":    len(aircraft),
            "military": sum(1 for a in aircraft if a.category=="MILITARY"),
            "cargo":    sum(1 for a in aircraft if a.category=="CARGO"),
            "govt":     sum(1 for a in aircraft if a.category=="GOVERNMENT"),
            "alerts":   sum(1 for a in aircraft if a.alert),
            "fetched":  datetime.now(UTC).isoformat(),
        },
    }
