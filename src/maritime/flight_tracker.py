from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Literal, Any
from uuid import uuid4
import random

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
    lat: float; lon: float; altitude_ft: int; speed_knots: int; heading_degrees: float
    vertical_rate_fpm: int = 0
    squawk: str = "0000"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Flight:
    flight_id: str = field(default_factory=lambda: str(uuid4()))
    callsign: str = ""; flight_number: str = ""; category: FlightCategory = FlightCategory.CARGO_FREIGHTER
    aircraft: Aircraft = field(default_factory=lambda: Aircraft("","","",0,"",""))
    origin_iata: str = ""; origin_name: str = ""; origin_lat: float = 0.0; origin_lon: float = 0.0; origin_country: str = ""
    destination_iata: str = ""; destination_name: str = ""; destination_lat: float = 0.0; destination_lon: float = 0.0; destination_country: str = ""
    departure_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    eta_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    progress_pct: float = 0.0
    current_position: FlightPosition = field(default_factory=lambda: FlightPosition(0,0,0,0,0))
    cargo_type: str = ""; cargo_weight_kg: int = 0; cargo_value_usd: int = 0; shipper: str = ""; consignee: str = ""
    importance_reason: str = ""; affected_tickers: list[str] = field(default_factory=list); signal_direction: str = "NEUTRAL"; signal_reason: str = ""
    waypoints: list[tuple[float, float]] = field(default_factory=list)
    historical_track: list[FlightPosition] = field(default_factory=list)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class FlightTracker:
    def __init__(self) -> None:
        self._flights: dict[str, Flight] = {}
        self._populate_synthetic_flights(200)

    def _populate_synthetic_flights(self, count: int = 200) -> None:
        """Generates high-density synthetic flights for global coverage."""
        cats = list(FlightCategory)
        corridors = [
            ("North Atlantic", 50.0, -30.0), ("Trans-Pacific", 35.0, 160.0),
            ("Europe-Asia", 45.0, 60.0), ("US Transcon", 38.0, -100.0),
            ("Intra-China", 30.0, 110.0), ("Middle East Hub", 25.0, 55.0),
            ("South East Asia", 10.0, 105.0)
        ]
        now = datetime.now(timezone.utc)
        for i in range(count):
            name, base_lat, base_lon = random.choice(corridors)
            fid = str(uuid4())
            lat = base_lat + random.uniform(-10, 10)
            lon = base_lon + random.uniform(-20, 20)
            f = Flight(
                flight_id=fid, callsign=f"FL-{i+100}", flight_number=f"F{i+1000}",
                category=random.choice(cats),
                aircraft=Aircraft(f"N{i}A","icao-"+str(i), "Boeing 777F", 2015, "Global Cargo", "US"),
                origin_iata="XYZ", origin_name="Origin Hub", origin_lat=lat-5, origin_lon=lon-5, origin_country="US",
                destination_iata="ABC", destination_name="Dest Hub", destination_lat=lat+5, destination_lon=lon+5, destination_country="EU",
                departure_utc=now - timedelta(hours=3), eta_utc=now + timedelta(hours=5),
                progress_pct=random.uniform(10, 90),
                current_position=FlightPosition(lat, lon, random.randint(30000, 41000), random.randint(450, 550), random.uniform(0,360)),
                cargo_type="High-Value Tech", cargo_weight_kg=100000, cargo_value_usd=50000000, shipper="Foxconn", consignee="Apple",
                importance_reason=f"Standard {name} corridor flight.", affected_tickers=["AAPL", "FDX"], 
                signal_direction=random.choice(["BULLISH", "NEUTRAL", "BEARISH"]), signal_reason="Normal schedule verification.",
                waypoints=[(lat-5, lon-5), (lat+5, lon+5)], historical_track=[]
            )
            self._flights[fid] = f

    def get_all_flights(self) -> list[Flight]:
        return list(self._flights.values())

    def to_geojson_feature_collection(self) -> dict:
        features = []
        for f in self._flights.values():
            color = "#00C8FF" if f.signal_direction == "BULLISH" else "#FFB900" if f.signal_direction == "BEARISH" else "#C084FC"
            features.append({
                "type": "Feature", "geometry": {"type": "Point", "coordinates": [f.current_position.lon, f.current_position.lat]},
                "properties": {
                    "flight_id": f.flight_id, "callsign": f.callsign, "symbol": "plane", "type": f.category.value, "color": color,
                    "altitude": f.current_position.altitude_ft, "speed": f.current_position.speed_knots, "heading": f.current_position.heading_degrees
                },
            })
        return {"type": "FeatureCollection", "features": features, "generated_at": datetime.now(timezone.utc).isoformat()}
