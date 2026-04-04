from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

import httpx
import structlog

log = structlog.get_logger()

# Known military ICAO24 hex prefixes by country
# Source: ADSBexchange, OpenSky research papers, public OSINT databases
MILITARY_HEX_PREFIXES = {
    "AE": "US Military",    # USAF, USN, USMC, USA, USCG
    "43": "UK Military",    # RAF, RN
    "3A": "French Military", # Armée de l'Air
    "84": "German Military", # Luftwaffe
    "AMF": "NATO AWACS",
    "4B": "Swiss Military",
    "47": "Swedish Military",
    "48": "Swedish Military",
}

# Specific high-interest ICAO24 hex codes for world leader aircraft
VIP_AIRCRAFT = {
    "ae0434": {"name": "Air Force One (primary)", "country": "USA", "icon": "⭐"},
    "ae04cc": {"name": "Air Force One (backup)", "country": "USA", "icon": "⭐"},
    "43c6f5": {"name": "RAF Voyager (UK PM)", "country": "UK", "icon": "⭐"},
    "3c6675": {"name": "German Air Force One", "country": "Germany", "icon": "⭐"},
    "3a4ee7": {"name": "French Presidential", "country": "France", "icon": "⭐"},
}

# Cargo airline callsign prefixes for cargo aircraft filter
CARGO_CALLSIGNS = {"FDX","UPS","DHK","CLX","ABX","GTI","ATN","PAC","NCB","BCS","KZR"}

# Squawk codes of interest
SQUAWK_ALERTS = {
    "7700": {"level": "EMERGENCY", "description": "General emergency", "color": "#E24B4A"},
    "7600": {"level": "RADIO FAILURE", "description": "Radio communication failure", "color": "#EF9F27"},
    "7500": {"level": "HIJACK", "description": "Unlawful interference", "color": "#E24B4A"},
    "7400": {"level": "DRONE LOST LINK", "description": "UAS lost link", "color": "#EF9F27"},
}


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
    on_ground: bool
    squawk: str
    last_contact: datetime
    aircraft_category: Literal["MILITARY","CARGO","COMMERCIAL","PRIVATE","GOVERNMENT","UNKNOWN"]
    vip_info: dict | None
    alert: dict | None


def fetch_all_aircraft() -> list[Aircraft]:
    """
    Fetch all aircraft from OpenSky Network via our unified aircraft module.
    """
    from src.live.aircraft import fetch_aircraft as fetch_real_aircraft
    try:
        real_aircraft = fetch_real_aircraft()
        aircraft = []
        for a in real_aircraft:
            aircraft.append(Aircraft(
                icao24=a.icao24,
                callsign=a.callsign,
                origin_country=a.country,
                lat=a.lat,
                lon=a.lon,
                altitude_ft=a.alt_ft,
                speed_knots=a.speed_kts,
                heading=a.heading,
                on_ground=a.on_ground,
                squawk=a.squawk,
                last_contact=datetime.now(UTC), # Approximate
                aircraft_category=a.category,
                vip_info={"name": a.vip, "country": a.country} if a.vip else None,
                alert=a.alert,
            ))
        return aircraft
    except Exception as e:
        log.error("opensky_unified_fetch_error", error=str(e))
        return fetch_adsb_fi_aircraft()

def fetch_adsb_fi_aircraft() -> list[Aircraft]:
    """
    Fallback: Fetch all aircraft from adsb.fi.
    """
    try:
        resp = httpx.get("https://api.adsb.fi/v1/aircraft", timeout=30)
        if resp.status_code != 200:
            log.warning("adsb_fi_failed", status=resp.status_code)
            return []

        data = resp.json().get("aircraft", [])
        aircraft = []
        for a in data:
            icao24 = (a.get("hex") or "").strip().lower()
            callsign = (a.get("flight") or "").strip().upper()
            squawk = (a.get("squawk") or "").strip()

            lat = a.get("lat")
            lon = a.get("lon")
            if lat is None or lon is None:
                continue

            # Determine category
            category = "UNKNOWN"
            vip_info = None
            alert = None

            if icao24 in VIP_AIRCRAFT:
                category = "GOVERNMENT"
                vip_info = VIP_AIRCRAFT[icao24]
            elif any(icao24.startswith(p.lower()) for p in MILITARY_HEX_PREFIXES):
                category = "MILITARY"
            elif any(callsign.startswith(p) for p in CARGO_CALLSIGNS):
                category = "CARGO"

            # Check squawk alerts
            if squawk in SQUAWK_ALERTS:
                alert = {
                    "squawk": squawk,
                    **SQUAWK_ALERTS[squawk],
                    "callsign": callsign,
                    "lat": lat,
                    "lon": lon,
                }

            # Filter for high-interest or alerts
            if category in ("MILITARY","CARGO","GOVERNMENT") or alert:
                aircraft.append(Aircraft(
                    icao24=icao24,
                    callsign=callsign,
                    origin_country="", # adsb.fi doesn't always provide country
                    lat=lat,
                    lon=lon,
                    altitude_ft=int(a.get("alt_baro", 0)),
                    speed_knots=int(a.get("gs", 0)),
                    heading=float(a.get("track", 0)),
                    on_ground=bool(a.get("ground")),
                    squawk=squawk,
                    last_contact=datetime.now(UTC),
                    aircraft_category=category,
                    vip_info=vip_info,
                    alert=alert,
                ))

        log.info("adsb_fi_fetched", count=len(aircraft))
        return aircraft
    except Exception as e:
        log.error("adsb_fi_error", error=str(e))
        return []

# Mock aircraft generation removed for production-grade real-time fidelity.


def get_squawk_alerts(aircraft: list[Aircraft]) -> list[dict]:
    """Extract and return all active squawk alerts."""
    return [a.alert for a in aircraft if a.alert is not None]


def aircraft_to_geojson(aircraft: list[Aircraft]) -> dict:
    """Convert aircraft list to GeoJSON for globe rendering."""
    features = []
    for a in aircraft:
        color = (
            "#FFD700" if a.aircraft_category == "GOVERNMENT"
            else "#FF3D3D" if a.aircraft_category == "MILITARY"
            else "#FF7A3D" if a.aircraft_category == "CARGO"
            else "#FFFFFF"
        )
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [a.lon, a.lat]},
            "properties": {
                "icao24": a.icao24,
                "callsign": a.callsign,
                "country": a.origin_country,
                "category": a.aircraft_category,
                "altitude_ft": a.altitude_ft,
                "speed_knots": a.speed_knots,
                "heading": a.heading,
                "on_ground": a.on_ground,
                "squawk": a.squawk,
                "alert": a.alert,
                "vip": a.vip_info,
                "color": color,
                "size": 8 if a.aircraft_category == "GOVERNMENT" else 5,
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
        "fetched_at": datetime.now(UTC).isoformat(),
        "counts": {
            "military": sum(1 for a in aircraft if a.aircraft_category=="MILITARY"),
            "cargo": sum(1 for a in aircraft if a.aircraft_category=="CARGO"),
            "government": sum(1 for a in aircraft if a.aircraft_category=="GOVERNMENT"),
            "squawk_alerts": sum(1 for a in aircraft if a.alert),
        },
    }
