from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Literal, Any
from uuid import uuid4

class FlightCategory(str, Enum):
    CARGO_FREIGHTER  = "Cargo Freighter"
    PRIVATE_JET      = "Private/Corporate Jet"
    GOVERNMENT       = "Government/State Aircraft"
    MILITARY         = "Military Aircraft"
    CHARTER_VIP      = "VIP Charter"

@dataclass
class Aircraft:
    registration: str; icao24: str; aircraft_type: str; year_built: int; operator: str; operator_country: str

@dataclass
class FlightPosition:
    lat: float; lon: float; altitude_ft: int; speed_knots: int; heading_degrees: float; vertical_rate_fpm: int; timestamp: datetime

@dataclass
class Flight:
    flight_id: str = field(default_factory=lambda: str(uuid4()))
    callsign: str = ""; flight_number: str = ""; category: FlightCategory = FlightCategory.CARGO_FREIGHTER
    aircraft: Aircraft = field(default_factory=lambda: Aircraft("","","",0,"",""))
    origin_iata: str = ""; origin_name: str = ""; origin_lat: float = 0.0; origin_lon: float = 0.0; origin_country: str = ""
    destination_iata: str = ""; destination_name: str = ""; destination_lat: float = 0.0; destination_lon: float = 0.0; destination_country: str = ""
    departure_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    eta_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    progress_pct: float = 0.0; current_position: FlightPosition = field(default_factory=lambda: FlightPosition(0,0,0,0,0,0,datetime.now(timezone.utc)))
    cargo_type: str = ""; cargo_weight_kg: int = 0; cargo_value_usd: int = 0; shipper: str = ""; consignee: str = ""
    importance_reason: str = ""; affected_tickers: list[str] = field(default_factory=list); signal_direction: str = "NEUTRAL"; signal_reason: str = ""
    waypoints: list[tuple[float, float]] = field(default_factory=list); last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

IMPORTANT_FLIGHTS: list[dict[str, Any]] = [
    {
        "callsign": "FDX1029", "flight_number": "FX1029", "category": FlightCategory.CARGO_FREIGHTER,
        "reg": "N886FD", "icao24": "ad5b57", "aircraft_type": "Boeing 777F", "year_built": 2014, "operator": "FedEx Express", "operator_country": "US",
        "origin_iata": "SZX", "origin_name": "Shenzhen Bao'an", "origin_lat": 22.64, "origin_lon": 113.81, "origin_country": "China",
        "dest_iata": "MEM", "dest_name": "Memphis Int (FedEx Hub)", "dest_lat": 35.04, "dest_lon": -89.97, "dest_country": "USA",
        "eta_hours_from_now": 6.5, "progress_pct": 72.0, "current_lat": 42.8, "current_lon": -178.4, "altitude_ft": 37000, "speed_knots": 510, "heading": 78.0,
        "cargo_type": "Electronics, Apple components", "cargo_weight_kg": 95000, "cargo_value_usd": 285000000, "shipper": "Foxconn", "consignee": "Apple Inc.",
        "importance_reason": "High-value Apple supply chain cargo.", "affected_tickers": ["FDX", "AAPL", "FOXC"], "signal_direction": "BULLISH",
        "waypoints": [(22.64,113.81),(42.8,-178.4),(35.04,-89.97)],
    },
    {
        "callsign": "UPS43", "flight_number": "5X43", "category": FlightCategory.CARGO_FREIGHTER,
        "reg": "N572UP", "icao24": "a95bf6", "aircraft_type": "Boeing 747-8F", "year_built": 2016, "operator": "UPS Airlines", "operator_country": "US",
        "origin_iata": "HKG", "origin_name": "Hong Kong Int", "origin_lat": 22.31, "origin_lon": 113.91, "origin_country": "Hong Kong",
        "dest_iata": "SDF", "dest_name": "Louisville (UPS Hub)", "dest_lat": 38.17, "dest_lon": -85.74, "dest_country": "USA",
        "eta_hours_from_now": 8.0, "progress_pct": 61.0, "current_lat": 38.5, "current_lon": 175.2, "altitude_ft": 39000, "speed_knots": 530, "heading": 82.0,
        "cargo_type": "Consumer electronics", "cargo_weight_kg": 120000, "cargo_value_usd": 180000000, "shipper": "Multiple HK", "consignee": "UPS Solutions",
        "importance_reason": "UPS 747F Trans-Pacific electronics.", "affected_tickers": ["UPS", "AMZN"], "signal_direction": "NEUTRAL",
        "waypoints": [(22.31,113.91),(38.5,175.2),(38.17,-85.74)],
    },
]

class FlightTracker:
    def __init__(self) -> None:
        self._flights: dict[str, Flight] = {}
        self._load_flights()

    async def _fetch_opensky_flights(self) -> list[dict[str, Any]]:
        """
        Implementation of Step 5: Fetch active cargo flights from OpenSky Network.
        No API key required for basic access.
        """
        import httpx
        url = "https://opensky-network.org/api/states/all"
        cargo_prefixes = {"FDX", "UPS", "DHK", "CLX", "ABX", "GTI"}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10.0)
                if resp.status_code != 200:
                    return []
                
                states = resp.json().get("states", [])
                cargo_flights = []
                for s in states:
                    callsign = (s[1] or "").strip()
                    if any(callsign.startswith(p) for p in cargo_prefixes) and s[6] is not None:
                        cargo_flights.append({
                            "callsign": callsign,
                            "icao24": s[0],
                            "lat": s[6],
                            "lon": s[5],
                            "altitude_ft": int((s[7] or 0) * 3.281),
                            "speed_knots": int((s[9] or 0) * 1.944),
                            "heading": s[10] or 0,
                            "on_ground": s[8],
                            "operator": "Cargo Operator" # Would resolve from database in prod
                        })
                return cargo_flights[:50]
        except Exception:
            return []

    def _load_flights(self) -> None:
        """Original mock loader for baseline."""
        now = datetime.now(timezone.utc)
        for f in IMPORTANT_FLIGHTS:
            # ... existing mock logic ...
            eta_hours = float(f["eta_hours_from_now"])
            progress = float(f["progress_pct"])
            eta = now + timedelta(hours=eta_hours)
            dep = now - timedelta(hours=eta_hours * (100 / progress) - eta_hours)
            flight = Flight(
                callsign=str(f["callsign"]), flight_number=str(f["flight_number"]), category=f["category"],
                aircraft=Aircraft(str(f["reg"]), str(f["icao24"]), str(f["aircraft_type"]), int(f["year_built"]), str(f["operator"]), str(f["operator_country"])),
                origin_iata=str(f["origin_iata"]), origin_name=str(f["origin_name"]), origin_lat=float(f["origin_lat"]), origin_lon=float(f["origin_lon"]), origin_country=str(f["origin_country"]),
                destination_iata=str(f["dest_iata"]), destination_name=str(f["dest_name"]), destination_lat=float(f["dest_lat"]), destination_lon=float(f["dest_lon"]), destination_country=str(f["dest_country"]),
                departure_utc=dep, eta_utc=eta, progress_pct=progress,
                current_position=FlightPosition(float(f["current_lat"]), float(f["current_lon"]), int(f["altitude_ft"]), int(f["speed_knots"]), float(f["heading"]), 0, now),
                cargo_type=str(f["cargo_type"]), cargo_weight_kg=int(f["cargo_weight_kg"]), cargo_value_usd=int(f["cargo_value_usd"]), shipper=str(f["shipper"]), consignee=str(f["consignee"]),
                importance_reason=str(f["importance_reason"]), affected_tickers=list(f["affected_tickers"]), signal_direction=str(f["signal_direction"]), waypoints=list(f["waypoints"]),
            )
            self._flights[flight.callsign] = flight

    async def update_live_positions(self) -> None:
        """Updates internal state with real OpenSky data."""
        opensky_data = await self._fetch_opensky_flights()
        for osf in opensky_data:
            callsign = osf["callsign"]
            if callsign not in self._flights:
                # Create shadow flight for real-world aircraft
                self._flights[callsign] = Flight(
                    callsign=callsign,
                    category=FlightCategory.CARGO_FREIGHTER,
                    current_position=FlightPosition(
                        osf["lat"], osf["lon"], osf["altitude_ft"], 
                        osf["speed_knots"], osf["heading"], 0, datetime.now(timezone.utc)
                    ),
                    cargo_type="Mixed Freight",
                    operator_country="INTL",
                    signal_direction="NEUTRAL"
                )
            else:
                # Update existing tracked flight
                f = self._flights[callsign]
                f.current_position = FlightPosition(
                    osf["lat"], osf["lon"], osf["altitude_ft"], 
                    osf["speed_knots"], osf["heading"], 0, datetime.now(timezone.utc)
                )
                f.last_updated = datetime.now(timezone.utc)

    def get_all_flights(self) -> list[Flight]: return list(self._flights.values())
    def get_flight(self, callsign: str) -> Flight | None: return self._flights.get(callsign)
    def to_geojson_feature_collection(self) -> dict[str, Any]:
        features: list[dict[str, Any]] = []
        for f in self._flights.values():
            # Heuristic for "What they are carrying" for OpenSky live flights
            cargo_desc = f.cargo_type
            if not cargo_desc or cargo_desc == "Unknown":
                if "FedEx" in f.aircraft.operator: cargo_desc = "High-Priority Express Parcels"
                elif "UPS" in f.aircraft.operator: cargo_desc = "E-commerce Logistics Payload"
                elif "DHL" in f.aircraft.operator: cargo_desc = "International Air Freight"
                elif "Cargolux" in f.aircraft.operator: cargo_desc = "Heavy Industrial Equipment"
                else: cargo_desc = "General Air Cargo"

            # Determine color and symbol
            color = "#6B7E99"
            if f.signal_direction == "BULLISH": color = "#00FF9D"
            elif f.signal_direction == "BEARISH": color = "#FF3D3D"

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [f.current_position.lon, f.current_position.lat]},
                "properties": {
                    "callsign": f.callsign,
                    "symbol": "flight",
                    "operator": f.aircraft.operator,
                    "type": f.aircraft.aircraft_type,
                    "origin": f.origin_iata if f.origin_iata else "Unknown",
                    "destination": f.destination_iata if f.destination_iata else "Unknown",
                    "speed_knots": f.current_position.speed_knots,
                    "altitude_ft": f.current_position.altitude_ft,
                    "heading": f.current_position.heading_degrees,
                    "cargo": {
                        "type": cargo_desc,
                        "weight": f"{f.cargo_weight_kg:,.0f} kg" if f.cargo_weight_kg > 0 else "N/A",
                        "value": f"${f.cargo_value_usd:,.0f}" if f.cargo_value_usd > 0 else "N/A",
                        "shipper": f.shipper,
                        "consignee": f.consignee
                    },
                    "signal": {
                        "status": f.signal_direction,
                        "reason": f.signal_reason
                    },
                    "tickers": f.affected_tickers,
                    "color": color
                },
            })
        return {
            "type": "FeatureCollection",
            "features": features,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
