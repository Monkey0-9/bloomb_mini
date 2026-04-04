"""
Live cargo flight tracking via OpenSky Network (free, no key required).
Focuses on known cargo operators: FedEx, UPS, DHL, Amazon Air, Cargolux,
Atlas Air, Korean Air Cargo, Air France Cargo, Lufthansa Cargo.
No API key needed for OpenSky REST API at 10 req/minute.
"""
from datetime import UTC, datetime

import httpx

OPENSKY_BASE = "https://opensky-network.org/api"

# Known cargo airline ICAO prefixes and callsign prefixes
CARGO_OPERATORS = {
    "FDX": {"name": "FedEx", "tickers": ["FDX"], "commodity": "e-commerce/express"},
    "UPS": {"name": "UPS Airlines", "tickers": ["UPS"], "commodity": "e-commerce/express"},
    "DHK": {"name": "DHL Air", "tickers": ["DPSGY"], "commodity": "express/courier"},
    "GTI": {"name": "Atlas Air", "tickers": ["AAWW"], "commodity": "bulk_freight"},
    "CLX": {"name": "Cargolux", "tickers": None, "commodity": "heavy_freight"},
    "KAL": {"name": "Korean Air Cargo", "tickers": ["003490.KS"], "commodity": "mixed_cargo"},
    "AFR": {"name": "Air France Cargo", "tickers": ["AFRAF"], "commodity": "pharma/perishable"},
    "DLH": {"name": "Lufthansa Cargo", "tickers": ["DLAKY"], "commodity": "pharma/auto_parts"},
    "ABX": {"name": "ABX Air / Amazon Air", "tickers": ["AMZN"], "commodity": "e-commerce"},
    "SHK": {"name": "Silk Way Airlines", "tickers": None, "commodity": "oil_field/heavy"},
}

# Global cargo hub bounding boxes to focus API queries
CARGO_HUBS = {
    "memphis":       {"bbox": [-90.30, 34.80, -89.50, 35.25], "hub_for": "FedEx global"},
    "louisville":    {"bbox": [-86.00, 37.95, -85.40, 38.40], "hub_for": "UPS Worldport"},
    "cincinnati":    {"bbox": [-84.80, 39.00, -84.30, 39.40], "hub_for": "DHL Americas"},
    "hong_kong":     {"bbox": [113.80, 22.20, 114.30, 22.50], "hub_for": "Asia cargo hub"},
    "frankfurt":     {"bbox": [8.40,   49.90,  9.10,  50.30], "hub_for": "Europe main hub"},
    "dubai":         {"bbox": [55.00,  24.80,  55.50, 25.30], "hub_for": "Middle East hub"},
    "anchorage":     {"bbox": [-150.30, 61.10, -148.80, 61.60], "hub_for": "Trans-Pacific stop"},
}


def _fetch_opensky_bbox(bbox: list[float]) -> list[dict]:
    """Fetch all aircraft in bounding box from OpenSky API."""
    try:
        lon_min, lat_min, lon_max, lat_max = bbox
        resp = httpx.get(
            f"{OPENSKY_BASE}/states/all",
            params={
                "lamin": lat_min, "lamax": lat_max,
                "lomin": lon_min, "lomax": lon_max,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        states = data.get("states", []) or []
        aircraft = []
        for s in states:
            if s and len(s) >= 12:
                callsign = (s[1] or "").strip()
                if callsign:
                    aircraft.append({
                        "icao24": s[0],
                        "callsign": callsign,
                        "origin_country": s[2],
                        "lon": s[5],
                        "lat": s[6],
                        "altitude_m": s[7],
                        "velocity_ms": s[9],
                        "heading": s[10],
                        "on_ground": s[8],
                    })
        return aircraft
    except Exception:
        return []


def _identify_operator(callsign: str) -> dict | None:
    """Match a callsign prefix to a known cargo operator."""
    for prefix, meta in CARGO_OPERATORS.items():
        if callsign.upper().startswith(prefix):
            return {"prefix": prefix, **meta}
    return None


def get_cargo_flights(hubs: list[str] | None = None) -> dict:
    """
    Fetch live cargo flights at major global cargo hubs.
    Identifies cargo operators from callsign prefixes.
    """
    hubs_to_query = hubs or list(CARGO_HUBS.keys())
    all_flights = []

    for hub_key in hubs_to_query:
        hub = CARGO_HUBS[hub_key]
        aircraft = _fetch_opensky_bbox(hub["bbox"])
        for ac in aircraft:
            callsign = ac.get("callsign", "")
            operator = _identify_operator(callsign)
            if not operator:
                continue  # Only track known cargo ops

            all_flights.append({
                "callsign": callsign,
                "icao24": ac.get("icao24"),
                "operator": operator["name"],
                "operator_prefix": operator["prefix"],
                "tickers": operator.get("tickers"),
                "cargo_type": operator.get("commodity", "general"),
                "lat": ac.get("lat"),
                "lon": ac.get("lon"),
                "altitude_m": ac.get("altitude_m"),
                "velocity_ms": ac.get("velocity_ms"),
                "heading_deg": ac.get("heading"),
                "on_ground": ac.get("on_ground"),
                "hub": hub_key,
                "hub_desc": hub["hub_for"],
                "source": "OpenSky-Network",
                "timestamp": datetime.now(UTC).isoformat(),
            })

    # Aggregate by operator for signal computation
    operator_summary: dict[str, dict] = {}
    for f in all_flights:
        prefix = f["operator_prefix"]
        if prefix not in operator_summary:
            operator_summary[prefix] = {
                "operator": f["operator"],
                "tickers": f["tickers"],
                "total_flights": 0,
                "in_air": 0,
                "on_ground": 0,
            }
        operator_summary[prefix]["total_flights"] += 1
        if f["on_ground"]:
            operator_summary[prefix]["on_ground"] += 1
        else:
            operator_summary[prefix]["in_air"] += 1

    return {
        "flights": all_flights,
        "operator_summary": operator_summary,
        "total_cargo_flights": len(all_flights),
        "hubs_scanned": hubs_to_query,
        "as_of": datetime.now(UTC).isoformat(),
    }
