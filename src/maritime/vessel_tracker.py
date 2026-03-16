from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import cast
from uuid import uuid4
import random

import structlog

log = structlog.get_logger()


class VesselType(str, Enum):
    CONTAINER = "Container Ship"
    CRUDE_TANKER = "Crude Oil Tanker"
    PRODUCT_TANKER = "Product Tanker"
    LNG_TANKER = "LNG Carrier"
    LPG_TANKER = "LPG Carrier"
    BULK_CARRIER = "Bulk Carrier"
    CAR_CARRIER = "Car Carrier (RORO)"
    GENERAL_CARGO = "General Cargo"
    FERRY = "Ferry/Passenger"
    OFFSHORE = "Offshore Supply"
    MILITARY = "Military/Naval"
    RESEARCH = "Research Vessel"


class CargoType(str, Enum):
    CRUDE_OIL = "Crude Oil"
    REFINED_PRODUCTS = "Refined Petroleum Products"
    LNG = "Liquefied Natural Gas"
    LPG = "Liquefied Petroleum Gas"
    IRON_ORE = "Iron Ore"
    COAL = "Coal"
    GRAIN = "Grain/Agricultural"
    CONTAINERS = "Containerised Goods"
    VEHICLES = "Vehicles/Automobiles"
    CHEMICALS = "Chemicals"
    FERTILISER = "Fertilisers"
    TIMBER = "Timber/Forest Products"
    STEEL = "Steel/Metal Products"
    BAUXITE = "Bauxite/Alumina"
    PASSENGERS = "Passengers"
    EMPTY = "In Ballast (Empty)"


@dataclass
class VesselPosition:
    lat: float
    lon: float
    timestamp: datetime
    speed_knots: float
    heading_degrees: float
    navigational_status: str
    course_over_ground: float


@dataclass
class PortCall:
    port_name: str
    port_code: str
    country: str
    lat: float
    lon: float
    arrival_utc: datetime | None
    departure_utc: datetime | None
    is_estimated: bool


@dataclass
class CargoManifest:
    cargo_type: CargoType
    quantity_mt: float
    quantity_teu: int | None
    commodity_detail: str
    shipper: str
    consignee: str
    loading_port: str
    discharge_port: str
    bill_of_lading_date: datetime | None


@dataclass
class Vessel:
    mmsi: str
    imo: str
    vessel_name: str
    call_sign: str
    flag_state: str
    flag_iso: str
    vessel_type: VesselType
    vessel_class: str
    year_built: int
    gross_tonnage: int
    deadweight_tonnage: int
    length_overall_m: float
    beam_m: float
    max_draught_m: float
    operator: str
    owner: str
    charterer: str
    position: VesselPosition
    origin: PortCall
    destination: PortCall
    eta_utc: datetime | None
    voyage_progress_pct: float
    cargo: CargoManifest
    affected_tickers: list[str]
    signal_direction: str
    signal_reason: str
    financial_impact_usd_million: float
    waypoints: list[tuple[float, float]]
    historical_track: list[VesselPosition]
    vessel_id: str = field(default_factory=lambda: str(uuid4()))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_source: str = "simulated"
    sar_validated: bool = False
    sar_backscatter_db: float | None = None
    port_history: list[PortCall] = field(default_factory=list)

    def _calculate_haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in nautical miles."""
        import math
        R = 3440.065 # Earth radius in NM
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    @property
    def voyage_distance_nm(self) -> float:
        """Calculate high-precision distance using Haversine."""
        if not self.waypoints or len(self.waypoints) < 2:
            return self._calculate_haversine(self.origin.lat, self.origin.lon, self.destination.lat, self.destination.lon)
        
        dist = 0.0
        for i in range(len(self.waypoints) - 1):
            p1, p2 = self.waypoints[i], self.waypoints[i+1]
            dist += self._calculate_haversine(p1[0], p1[1], p2[0], p2[1])
        return dist

    def get_live_position(self) -> tuple[float, float]:
        """
        Advances vessel position based on speed and updates historical track.
        """
        now = datetime.now(timezone.utc)
        if not self.origin.departure_utc or not self.waypoints:
            return self.position.lat, self.position.lon
            
        elapsed_h = (now - self.origin.departure_utc).total_seconds() / 3600
        speed = max(self.position.speed_knots, 12.0)
        total_h = self.voyage_distance_nm / speed
        progress = min(elapsed_h / total_h, 1.0)
        
        route = self.waypoints
        seg_f = progress * (len(route) - 1)
        idx = min(int(seg_f), len(route) - 2)
        frac = seg_f - idx
        
        lat = route[idx][0] + (route[idx+1][0] - route[idx][0]) * frac
        lon = route[idx][1] + (route[idx+1][1] - route[idx][1]) * frac
        
        # Update historical track (keep last 50)
        new_pos = VesselPosition(lat, lon, now, speed, self.position.heading_degrees, self.position.navigational_status, self.position.heading_degrees)
        if not self.historical_track or (now - self.historical_track[-1].timestamp).total_seconds() > 600: # Every 10 mins
            self.historical_track.append(new_pos)
            if len(self.historical_track) > 50:
                self.historical_track.pop(0)
                
        return round(lat, 4), round(lon, 4)

TRACKED_VESSELS: list[dict] = [
    {
        "mmsi": "477097100",
        "imo": "9786731",
        "vessel_name": "HONG KONG SPIRIT",
        "call_sign": "VRDN7",
        "flag_state": "Hong Kong",
        "flag_iso": "HK",
        "vessel_type": VesselType.CRUDE_TANKER,
        "vessel_class": "VLCC",
        "year_built": 2017,
        "gross_tonnage": 157_833,
        "deadweight_tonnage": 298_000,
        "length_overall_m": 333.0,
        "beam_m": 60.0,
        "max_draught_m": 22.5,
        "operator": "Euronav",
        "owner": "Euronav NV",
        "charterer": "Shell International Trading",
        "cargo_type": CargoType.CRUDE_OIL,
        "cargo_quantity_mt": 285_000,
        "cargo_detail": "Arab Light Crude Oil (Saudi Aramco)",
        "shipper": "Saudi Aramco",
        "consignee": "Shell Nederland Raffinaderij B.V.",
        "origin_port": "Ras Tanura, Saudi Arabia",
        "origin_locode": "SARTS",
        "origin_lat": 26.64, "origin_lon": 50.16,
        "dest_port": "Rotterdam, Netherlands",
        "dest_locode": "NLRTM",
        "dest_lat": 51.96, "dest_lon": 4.05,
        "eta_days_from_now": 18,
        "voyage_progress_pct": 42.0,
        "current_lat": 12.8, "current_lon": 57.4,
        "speed_knots": 14.2,
        "heading": 312.0,
        "nav_status": "Under Way Using Engine",
        "affected_tickers": ["SHEL", "IMO", "FRO"],
        "signal_direction": "NEUTRAL",
        "signal_reason": "Standard VLCC transit on Saudi Arabiaâ€”Rotterdam route. Normal volumes.",
        "financial_impact_usd_million": 0.0,
        "waypoints": [(26.64,50.16),(22.0,57.0),(51.96,4.05)],
    },
]

class VesselTracker:
    def __init__(self) -> None:
        self._vessels: dict[str, Vessel] = {}
        self._load_tracked_vessels()
        self._populate_synthetic_vessels(200)

    def _load_tracked_vessels(self) -> None:
        now = datetime.now(timezone.utc)
        for v in TRACKED_VESSELS:
            days_to_eta = cast(float, v["eta_days_from_now"])
            eta = now + timedelta(days=days_to_eta)
            origin_arrival = now - timedelta(days=30)
            vessel = Vessel(
                mmsi=v["mmsi"], imo=v["imo"], vessel_name=v["vessel_name"],
                call_sign=v["call_sign"], flag_state=v["flag_state"], flag_iso=v["flag_iso"],
                vessel_type=v["vessel_type"], vessel_class=v["vessel_class"],
                year_built=v["year_built"], gross_tonnage=v["gross_tonnage"],
                deadweight_tonnage=v["deadweight_tonnage"], length_overall_m=v["length_overall_m"],
                beam_m=v["beam_m"], max_draught_m=v["max_draught_m"],
                operator=v["operator"], owner=v["owner"], charterer=v["charterer"],
                position=VesselPosition(
                    lat=v["current_lat"], lon=v["current_lon"], timestamp=now,
                    speed_knots=v["speed_knots"], heading_degrees=v["heading"],
                    navigational_status=v["nav_status"], course_over_ground=v["heading"],
                ),
                origin=PortCall(
                    port_name=v["origin_port"], port_code=v["origin_locode"],
                    country=v["origin_port"].split(",")[-1].strip(),
                    lat=v["origin_lat"], lon=v["origin_lon"],
                    arrival_utc=origin_arrival, departure_utc=origin_arrival + timedelta(days=2),
                    is_estimated=False,
                ),
                destination=PortCall(
                    port_name=v["dest_port"], port_code=v["dest_locode"],
                    country=v["dest_port"].split(",")[-1].strip(),
                    lat=v["dest_lat"], lon=v["dest_lon"],
                    arrival_utc=eta, departure_utc=None, is_estimated=True,
                ),
                eta_utc=eta, voyage_progress_pct=v["voyage_progress_pct"],
                cargo=CargoManifest(
                    cargo_type=v["cargo_type"], quantity_mt=v["cargo_quantity_mt"],
                    quantity_teu=(int(v["cargo_detail"].split()[0].replace(",","")) if "TEU" in v["cargo_detail"] else None),
                    commodity_detail=v["cargo_detail"], shipper=v["shipper"], consignee=v["consignee"],
                    loading_port=v["origin_port"], discharge_port=v["dest_port"], bill_of_lading_date=origin_arrival,
                ),
                affected_tickers=v["affected_tickers"], signal_direction=v["signal_direction"],
                signal_reason=v["signal_reason"], financial_impact_usd_million=v["financial_impact_usd_million"],
                waypoints=v["waypoints"], historical_track=[],
            )
            self._vessels[vessel.mmsi] = vessel

    def _populate_synthetic_vessels(self, count: int = 200) -> None:
        """Generates high-density synthetic vessels for global coverage."""
        vessel_types = list(VesselType)
        cargo_types = list(CargoType)
        clusters = [
            ("Suez Route", 15.0, 45.0), ("Malacca Strait", 1.3, 103.0),
            ("Panama Canal", 9.0, -79.0), ("Rotterdam Approach", 52.0, 3.5),
            ("Singapore Anchorage", 1.2, 103.8), ("Persian Gulf", 26.0, 52.0),
            ("US East Coast", 35.0, -74.0), ("US West Coast", 33.0, -118.0),
            ("China Coast", 31.0, 122.0)
        ]
        now = datetime.now(timezone.utc)
        for i in range(count):
            cluster_name, base_lat, base_lon = random.choice(clusters)
            mmsi = str(300000000 + i)
            lat = base_lat + random.uniform(-5, 5)
            lon = base_lon + random.uniform(-5, 5)
            vessel = Vessel(
                mmsi=mmsi, imo=str(9000000 + i), vessel_name=f"VSE-{i+1000}",
                call_sign=f"C-{i}", flag_state="Panama", flag_iso="PA",
                vessel_type=random.choice(vessel_types), vessel_class="Handymax",
                year_built=random.randint(2005, 2024), gross_tonnage=random.randint(20000, 80000),
                deadweight_tonnage=random.randint(30000, 120000), length_overall_m=200.0, beam_m=32.0, max_draught_m=12.0,
                operator="Global Ship Management", owner="Logistics Ltd", charterer="N/A",
                position=VesselPosition(lat, lon, now, random.uniform(10, 20), random.uniform(0, 360), "Under Way", random.uniform(0, 360)),
                origin=PortCall("Synthetic Start", "S1", "INTL", lat-1, lon-1, now - timedelta(days=5), now - timedelta(days=4), True),
                destination=PortCall("Synthetic End", "E1", "INTL", lat+2, lon+2, now + timedelta(days=5), None, True),
                eta_utc=now + timedelta(days=5), voyage_progress_pct=random.uniform(10, 90),
                cargo=CargoManifest(random.choice(cargo_types), 50000, None, "Bulk Commodity", "Shipper X", "Consignee Y", "S1", "E1", now),
                affected_tickers=["GLOBAL"], signal_direction="NEUTRAL", signal_reason="Simulated transit",
                financial_impact_usd_million=1.5, waypoints=[(lat-1, lon-1), (lat+2, lon+2)], historical_track=[]
            )
            self._vessels[mmsi] = vessel

    def get_all_vessels(self) -> list[Vessel]:
        return list(self._vessels.values())

    def to_geojson_feature_collection(self) -> dict:
        features = []
        for v in self._vessels.values():
            try: live_lat, live_lon = v.get_live_position()
            except: live_lat, live_lon = v.position.lat, v.position.lon
            color = "#00FF9D" if v.signal_direction == "BULLISH" else "#FF3D3D" if v.signal_direction == "BEARISH" else "#6B7E99"
            features.append({
                "type": "Feature", "geometry": {"type": "Point", "coordinates": [live_lon, live_lat]},
                "properties": {
                    "mmsi": v.mmsi, "name": v.vessel_name, "symbol": "ship", "type": v.vessel_type.value, "color": color, 
                    "heading": v.position.heading_degrees, "speed": v.position.speed_knots, "destination": v.destination.port_name
                },
            })
        return {"type": "FeatureCollection", "features": features, "generated_at": datetime.now(timezone.utc).isoformat()}
