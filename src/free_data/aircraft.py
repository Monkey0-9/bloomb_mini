"""
Aircraft tracking via OpenSky Network anonymous API.
NO API KEY. NO REGISTRATION. Completely free and open.
URL: https://opensky-network.org/api/states/all
Returns all aircraft on Earth. Updated every 10 seconds.
"""

import httpx
import time
import structlog
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

log = structlog.get_logger()

OPENSKY_URL = "https://opensky-network.org/api/states/all"

# Military ICAO24 hex prefix registry — compiled from public OSINT databases
MILITARY_PREFIXES = {
    "ae": "US Military",      # USAF, USN, USMC, USA, USCG
    "43": "UK Military",      # RAF, Royal Navy Fleet Air Arm
    "3a": "French Air Force",
    "3b": "French Navy",
    "84": "German Military",  # Bundeswehr
    "48": "Swedish Military",
    "47": "Swedish Military",
    "4b": "Swiss Military",
    "480": "Norwegian Military",
    "501": "Polish Military",
    "710": "Turkish Military",
    "738": "Israeli Military",
    "899": "Japanese GSDF",
    "8f": "South Korean Military",
    "c0": "Canadian Military",
    "7cf": "Australian Military",
    "e4": "Brazilian Military",
    "0d0": "Chinese Military",
}

# Known VIP / world leader aircraft ICAO24 hex codes
VIP_HEX = {
    "ae0434": {"name": "USAF VC-25A Air Force One (primary)", "country": "USA"},
    "ae04cc": {"name": "USAF VC-25A Air Force One (backup)",  "country": "USA"},
    "ae014a": {"name": "USAF C-32A Air Force Two",            "country": "USA"},
    "43c6f5": {"name": "RAF Voyager ZZ336 (UK PM aircraft)",  "country": "UK"},
    "43c782": {"name": "RAF Voyager ZZ335",                   "country": "UK"},
    "3c6675": {"name": "GAF A340-313X German State",          "country": "Germany"},
    "3c675a": {"name": "GAF A321 Theodor Heuss",              "country": "Germany"},
    "3a4ee7": {"name": "French Presidential A330",            "country": "France"},
    "c078b2": {"name": "Canadian Forces CC-150 Polaris",      "country": "Canada"},
}

# Cargo airline callsign prefixes
CARGO_PREFIXES = {
    "FDX": "FedEx Express",
    "UPS": "UPS Airlines",
    "DHK": "DHL Air",
    "CLX": "Cargolux",
    "ABX": "ABX Air (Amazon)",
    "GTI": "Atlas Air",
    "ATN": "Air Transport International",
    "PAC": "Polar Air Cargo",
    "NKS": "Kalitta Air",
    "KZR": "National Air Cargo",
    "NCB": "National Airlines",
    "BCS": "European Air Transport",
    "MPH": "Martinair",
    "AMU": "Air Canada Cargo",
    "QEC": "Qantas Freight",
    "CKS": "Gemini Air Cargo",
    "ICL": "Turkish Cargo",
    "ETH": "Ethiopian Cargo",
    "MSC": "MSC Air Cargo",
    "SIA": "Singapore Air Cargo",
    "AFR": "Air France Cargo",
    "DLH": "Lufthansa Cargo",
    "KLM": "KLM Cargo",
    "UAE": "Emirates SkyCargo",
    "QTR": "Qatar Airways Cargo",
    "CCA": "Air China Cargo",
    "CSN": "China Southern Cargo",
}

# Squawk codes that mean something critical
SQUAWK_MEANINGS = {
    "7700": {"severity": "EMERGENCY",    "desc": "General emergency declared"},
    "7600": {"severity": "RADIO_FAILURE","desc": "Radio communication failure"},
    "7500": {"severity": "HIJACK",       "desc": "Unlawful interference"},
    "7400": {"severity": "DRONE_LINK",   "desc": "UAS lost link"},
    "2000": {"severity": "INFO",         "desc": "No ATC instruction received (VFR)"},
    "1200": {"severity": "INFO",         "desc": "VFR code (North America)"},
}

@dataclass
class AircraftState:
    icao24:    str
    callsign:  str
    country:   str
    lat:       float
    lon:       float
    alt_baro_ft: int
    alt_geo_ft:  int
    speed_kts: int
    heading:   float
    vertical_rate_fpm: int
    on_ground: bool
    squawk:    str
    category:  Literal["MILITARY","CARGO","GOVERNMENT","COMMERCIAL","PRIVATE","UNKNOWN"]
    vip_info:  dict | None
    alert:     dict | None
    updated:   datetime

# Module-level cache
_aircraft_cache: list[AircraftState] = []
_cache_ts: float = 0.0
CACHE_TTL = 10.0  # 10 seconds

def fetch_aircraft(
    bbox: tuple[float,float,float,float] | None = None,
    categories: list[str] | None = None,
) -> list[AircraftState]:
    global _aircraft_cache, _cache_ts

    now = time.time()
    if _aircraft_cache and (now - _cache_ts) < CACHE_TTL:
        result = _aircraft_cache
        if categories:
            result = [a for a in result if a.category in categories]
        return result

    params: dict = {}
    if bbox:
        params = {"lamin": bbox[1], "lomin": bbox[0],
                  "lamax": bbox[3], "lomax": bbox[2]}

    try:
        resp = httpx.get(OPENSKY_URL, params=params, timeout=20)
        if resp.status_code == 429:
            log.warning("opensky_rate_limited")
            return _aircraft_cache

        resp.raise_for_status()
        states_raw = resp.json().get("states", []) or []

        aircraft = []
        for s in states_raw:
            if len(s) < 17 or s[5] is None or s[6] is None:
                continue

            icao24   = (s[0] or "").strip().lower()
            callsign = (s[1] or "").strip().upper()
            squawk   = (s[14] or "").strip() if s[14] else ""

            category = "UNKNOWN"
            vip_info = None
            alert    = None

            if icao24 in VIP_HEX:
                category = "GOVERNMENT"
                vip_info = VIP_HEX[icao24]
            elif any(icao24.startswith(p) for p in MILITARY_PREFIXES):
                category = "MILITARY"
            elif any(callsign.startswith(p) for p in CARGO_PREFIXES):
                category = "CARGO"
            else:
                continue

            if squawk in SQUAWK_MEANINGS and squawk not in ("2000", "1200"):
                alert = {
                    "squawk":    squawk,
                    "severity":  SQUAWK_MEANINGS[squawk]["severity"],
                    "desc":      SQUAWK_MEANINGS[squawk]["desc"],
                    "callsign":  callsign,
                    "icao24":    icao24,
                    "lat":       s[6],
                    "lon":       s[5],
                    "country":   s[2] or "",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            baro_m   = s[7] or 0
            geo_m    = s[13] or 0
            vel_ms   = s[9] or 0
            vrate_ms = s[11] or 0

            aircraft.append(AircraftState(
                icao24    = icao24,
                callsign  = callsign,
                country   = s[2] or "",
                lat       = float(s[6]),
                lon       = float(s[5]),
                alt_baro_ft  = int(baro_m * 3.281),
                alt_geo_ft   = int(geo_m  * 3.281),
                speed_kts    = int(vel_ms * 1.944),
                heading      = float(s[10] or 0),
                vertical_rate_fpm = int(vrate_ms * 196.85),
                on_ground    = bool(s[8]),
                squawk       = squawk,
                category     = category,
                vip_info     = vip_info,
                alert        = alert,
                updated      = datetime.now(timezone.utc),
            ))

        _aircraft_cache = aircraft
        _cache_ts = now

        log.info("opensky_fetched",
                 total_states=len(states_raw),
                 military=sum(1 for a in aircraft if a.category=="MILITARY"),
                 cargo=sum(1 for a in aircraft if a.category=="CARGO"),
                 government=sum(1 for a in aircraft if a.category=="GOVERNMENT"),
                 squawk_alerts=sum(1 for a in aircraft if a.alert))

    except Exception as e:
        log.error("opensky_error", error=str(e))

    result = _aircraft_cache
    if categories:
        result = [a for a in result if a.category in categories]
    return result

def get_squawk_alerts() -> list[dict]:
    return [a.alert for a in fetch_aircraft() if a.alert is not None]

def to_geojson(aircraft: list[AircraftState]) -> dict:
    color_map = {
        "GOVERNMENT": "#FFD700",
        "MILITARY":   "#E24B4A",
        "CARGO":      "#FF7A3D",
        "COMMERCIAL": "#888780",
        "PRIVATE":    "#FFFFFF",
        "UNKNOWN":    "#444441",
    }
    features = []
    for a in aircraft:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [a.lon, a.lat]},
            "properties": {
                "icao24":         a.icao24,
                "callsign":       a.callsign,
                "country":        a.country,
                "category":       a.category,
                "alt_baro_ft":    a.alt_baro_ft,
                "speed_kts":      a.speed_kts,
                "heading":        a.heading,
                "vertical_rate":  a.vertical_rate_fpm,
                "on_ground":      a.on_ground,
                "squawk":         a.squawk,
                "alert":          a.alert,
                "vip":            a.vip_info,
                "color":          color_map.get(a.category, "#888780"),
                "size_px":        12 if a.category=="GOVERNMENT" else 6,
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total":    len(features),
            "military": sum(1 for a in aircraft if a.category=="MILITARY"),
            "cargo":    sum(1 for a in aircraft if a.category=="CARGO"),
            "govt":     sum(1 for a in aircraft if a.category=="GOVERNMENT"),
            "alerts":   sum(1 for a in aircraft if a.alert),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
    }
