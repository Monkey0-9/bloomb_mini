from __future__ import annotations
import asyncio
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4

import structlog

log = structlog.get_logger()

# --- CONSTANTS & MAPS ---

AIRLINE_TO_TICKERS = {
    "Delta Air Lines": ["DAL"],
    "American Airlines": ["AAL"],
    "United Airlines": ["UAL"],
    "Lufthansa": ["LHA.DE"],
    "Air France-KLM": ["AF.PA"],
    "FedEx": ["FDX"],
    "UPS": ["UPS"],
    "Amazon Air": ["AMZN"],
    "Atlas Air": ["AAWW"],
    "Cargolux": ["PRIVATE"]
}

MANUFACTURER_TO_TICKERS = {
    "Boeing": ["BA"],
    "Airbus": ["AIR.PA"],
    "Embraer": ["ERJ"],
    "Bombardier": ["BBD-B.TO"]
}

FLIGHT_CORRIDORS = {
    "north_atlantic": {"lat": 52.0, "lon": -35.0, "radius": 1500},
    "trans_pacific": {"lat": 35.0, "lon": 170.0, "radius": 2000},
    "intra_europe": {"lat": 48.0, "lon": 10.0, "radius": 800},
    "intra_asia": {"lat": 25.0, "lon": 115.0, "radius": 1200},
    "us_domestic": {"lat": 38.0, "lon": -95.0, "radius": 1500}
}

class FlightCategory(str, Enum):
    CARGO = "Cargo"
    COMMERCIAL = "Commercial"
    PRIVATE = "Private"
    MILITARY = "Military"
    GOVERNMENT = "Government"

# --- DATA CLASSES ---

@dataclass
class Aircraft:
    icao24: str
    registration: str
    model: str
    manufacturer: str
    operator: str

@dataclass
class FlightPosition:
    lat: float
    lon: float
    altitude_ft: int
    speed_knots: int
    heading: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Flight:
    flight_id: str
    callsign: str
    category: FlightCategory
    aircraft: Aircraft
    position: FlightPosition
    origin: str
    destination: str
    eta: datetime
    affected_tickers: List[str] = field(default_factory=list)
    signal_direction: str = "NEUTRAL"
    signal_reason: str = ""
    historical_track: List[FlightPosition] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

# --- CORE LOGIC ---

class FlightTracker:
    """
    Institutional Aviation Intelligence Engine.
    Tracks supply chain bottlenecks and high-value logistics signals.
    """
    def __init__(self):
        self._flights: Dict[str, Flight] = {}
        self._cache = {}

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2) -> float:
        """Distance in nautical miles."""
        R = 3440.065
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    async def update_flight(self, state_vector: Dict[str, Any]):
        """
        Processes real-time ADS-B / OpenSky state vectors.
        """
        icao24 = state_vector["icao24"]
        now = datetime.now(timezone.utc)
        
        # 1. Aircraft Metadata (Mocking DB lookup)
        operator = state_vector.get("operator", "Global Air")
        manufacturer = "Boeing" if random.random() > 0.4 else "Airbus"
        
        # 2. Ticker Mapping
        tickers = []
        tickers.extend(AIRLINE_TO_TICKERS.get(operator, []))
        tickers.extend(MANUFACTURER_TO_TICKERS.get(manufacturer, []))
        
        # 3. Signal Generation
        category = self._determine_category(state_vector)
        signal, reason = self._generate_signal(state_vector, category, operator)

        # 4. Update Record
        flight = Flight(
            flight_id=icao24,
            callsign=state_vector.get("callsign", "UNK"),
            category=category,
            aircraft=Aircraft(
                icao24=icao24,
                registration=state_vector.get("registration", f"N{random.randint(100,999)}G"),
                model="777-300ER" if manufacturer == "Boeing" else "A350-1000",
                manufacturer=manufacturer,
                operator=operator
            ),
            position=FlightPosition(
                lat=state_vector["lat"],
                lon=state_vector["lon"],
                altitude_ft=state_vector.get("altitude", 35000),
                speed_knots=state_vector.get("speed", 480),
                heading=state_vector.get("heading", 0.0)
            ),
            origin=state_vector.get("origin", "JFK"),
            destination=state_vector.get("destination", "LHR"),
            eta=now + timedelta(hours=random.uniform(1, 12)),
            affected_tickers=tickers,
            signal_direction=signal,
            signal_reason=reason
        )
        
        self._flights[icao24] = flight

    def _determine_category(self, data: Dict) -> FlightCategory:
        """Heuristic-based category assignment."""
        callsign = data.get("callsign", "")
        if any(p in callsign for p in ["FDX", "UPS", "GTI", "CLX"]):
            return FlightCategory.CARGO
        if any(p in callsign for p in ["DAL", "UAL", "AAL", "DLH"]):
            return FlightCategory.COMMERCIAL
        return FlightCategory.PRIVATE

    def _generate_signal(self, data: Dict, category: FlightCategory, operator: str) -> tuple[str, str]:
        """
        Identifies alpha signals (e.g. logistics bursts, supply chain anomalies).
        """
        if category == FlightCategory.CARGO and "Foxconn" in data.get("shipper", ""):
            return "BULLISH", "High-value electronics logistics burst detected (Foxconn -> Apple)"
        
        if data.get("altitude", 35000) < 5000 and data.get("status") == "Emergency":
            return "BEARISH", f"Critical operational anomaly detected for {operator} aircraft"
            
        return "NEUTRAL", "Standard operational flight path."

    def get_market_intelligence(self) -> List[Dict]:
        """Distills flight data into stock signals."""
        signals = []
        for f in self._flights.values():
            if f.signal_direction != "NEUTRAL":
                signals.append({
                    "ticker": f.affected_tickers[0] if f.affected_tickers else "GLOBAL",
                    "type": "AVIATION_INTEL",
                    "confidence": 0.85,
                    "headline": f.signal_reason,
                    "impact": f.signal_direction,
                    "metadata": {
                        "callsign": f.callsign,
                        "operator": f.aircraft.operator,
                        "category": f.category.value
                    }
                })
        return signals

# --- SYNTHETIC HIGH-DENSITY POPULATION ---

    async def populate_global_fleet(self):
        """
        Fetches live aircraft from OpenSky Network via adsb.py.
        100% Free. 100% Open Source.
        """
        from src.globe.adsb import fetch_all_aircraft
        log.info("FETCHING_OPENSKY_AIRCRAFT_INSTITUTIONAL")
        aircraft_list = await asyncio.to_thread(fetch_all_aircraft)
        
        for a in aircraft_list:
            # Map into our Flight internal format
            await self.update_flight({
                "icao24": a.icao24,
                "callsign": a.callsign,
                "lat": a.lat,
                "lon": a.lon,
                "altitude": a.altitude_ft,
                "speed": a.speed_knots,
                "heading": a.heading,
                "operator": a.origin_country, # Use country as operator proxy if unknown
                "category": a.aircraft_category,
                "status": "Emergency" if a.alert else "Normal"
            })

    def get_all_flights(self) -> List[Flight]:
        """Returns all flights in memory."""
        return list(self._flights.values())

    def get_flight(self, callsign: str) -> Optional[Flight]:
        """Lookup flight by callsign."""
        for f in self._flights.values():
            if f.callsign == callsign:
                return f
        return None

    def to_geojson_feature_collection(self) -> Dict[str, Any]:
        """
        Formats all flights as GeoJSON for the WorldView frontend.
        """
        features = []
        for f in self._flights.values():
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [f.position.lon, f.position.lat]
                },
                "properties": {
                    "icao24": f.flight_id,
                    "callsign": f.callsign,
                    "category": f.category.value,
                    "operator": f.aircraft.operator,
                    "altitude": f.position.altitude_ft,
                    "speed": f.position.speed_knots,
                    "impact": f.signal_direction,
                    "tickers": f.affected_tickers
                }
            })
        return {
            "type": "FeatureCollection",
            "features": features
        }

if __name__ == "__main__":
    tracker = FlightTracker()
    async def run_test():
        await tracker.populate_global_fleet(100)
        intel = tracker.get_market_intelligence()
        print(f"Captured {len(intel)} high-conviction aviation signals.")
        
    asyncio.run(run_test())
