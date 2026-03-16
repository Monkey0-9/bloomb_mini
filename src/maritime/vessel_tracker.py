from __future__ import annotations
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, cast
from uuid import uuid4

import httpx
import structlog

log = structlog.get_logger()


class VesselType(str, Enum):
    CONTAINER     = "Container Ship"
    CRUDE_TANKER  = "Crude Oil Tanker"
    PRODUCT_TANKER= "Product Tanker"
    LNG_TANKER    = "LNG Carrier"
    LPG_TANKER    = "LPG Carrier"
    BULK_CARRIER  = "Bulk Carrier"
    CAR_CARRIER   = "Car Carrier (RORO)"
    GENERAL_CARGO = "General Cargo"
    FERRY         = "Ferry/Passenger"
    OFFSHORE      = "Offshore Supply"
    MILITARY      = "Military/Naval"
    RESEARCH      = "Research Vessel"


class CargoType(str, Enum):
    CRUDE_OIL        = "Crude Oil"
    REFINED_PRODUCTS = "Refined Petroleum Products"
    LNG              = "Liquefied Natural Gas"
    LPG              = "Liquefied Petroleum Gas"
    IRON_ORE         = "Iron Ore"
    COAL             = "Coal"
    GRAIN            = "Grain/Agricultural"
    CONTAINERS       = "Containerised Goods"
    VEHICLES         = "Vehicles/Automobiles"
    CHEMICALS        = "Chemicals"
    FERTILISER       = "Fertilisers"
    TIMBER           = "Timber/Forest Products"
    STEEL            = "Steel/Metal Products"
    BAUXITE          = "Bauxite/Alumina"
    PASSENGERS       = "Passengers"
    EMPTY            = "In Ballast (Empty)"


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

    @property
    def voyage_distance_nm(self) -> float:
        """Calculate total distance from waypoints as a proxy."""
        if not self.waypoints or len(self.waypoints) < 2:
            return 1000.0  # Default fallback
        dist = 0.0
        for i in range(len(self.waypoints) - 1):
            p1, p2 = self.waypoints[i], self.waypoints[i+1]
            # Simple Euclidean distance as proxy (in a real system use geopy)
            dist += ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5 * 60
        return dist

    def get_live_position(self) -> tuple[float, float]:
        """
        Advances vessel position based on speed x elapsed time.
        Implemented exactly as requested for 'Top 1%' hardening.
        """
        now = datetime.now(timezone.utc)
        if not self.origin.departure_utc or not self.waypoints:
            return self.position.lat, self.position.lon
            
        elapsed_h = (now - self.origin.departure_utc).total_seconds() / 3600
        # Average speed fallback if position speed is zero
        speed = max(self.position.speed_knots, 12.0)
        total_h = self.voyage_distance_nm / speed
        progress = min(elapsed_h / total_h, 1.0)
        
        route = self.waypoints
        seg_f = progress * (len(route) - 1)
        idx = min(int(seg_f), len(route) - 2)
        frac = seg_f - idx
        
        lat = route[idx][0] + (route[idx+1][0] - route[idx][0]) * frac
        lon = route[idx][1] + (route[idx+1][1] - route[idx][1]) * frac
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
        "signal_reason": "Standard VLCC transit on Saudi Arabia—Rotterdam route. Normal volumes.",
        "financial_impact_usd_million": 0.0,
        "waypoints": [(26.64,50.16),(22.0,57.0),(51.96,4.05)],
    },
    {
        "mmsi": "371066000",
        "imo": "9332793",
        "vessel_name": "ADVANTAGE SPRING",
        "call_sign": "3FWZ6",
        "flag_state": "Panama",
        "flag_iso": "PA",
        "vessel_type": VesselType.CRUDE_TANKER,
        "vessel_class": "Suezmax",
        "year_built": 2007,
        "gross_tonnage": 81_000,
        "deadweight_tonnage": 158_000,
        "length_overall_m": 274.0,
        "beam_m": 48.0,
        "max_draught_m": 17.0,
        "operator": "Advantage Tankers",
        "owner": "Advantage Tankers LLC",
        "charterer": "Equinor ASA",
        "cargo_type": CargoType.CRUDE_OIL,
        "cargo_quantity_mt": 148_000,
        "cargo_detail": "Johan Sverdrup Crude Oil",
        "shipper": "Equinor ASA",
        "consignee": "ExxonMobil Refining",
        "origin_port": "Mongstad, Norway",
        "origin_locode": "NOMOG",
        "origin_lat": 60.81, "origin_lon": 5.00,
        "dest_port": "Baytown, Texas, USA",
        "dest_locode": "USBYT",
        "dest_lat": 29.73, "dest_lon": -94.97,
        "eta_days_from_now": 12,
        "voyage_progress_pct": 38.0,
        "current_lat": 48.2, "current_lon": -28.6,
        "speed_knots": 13.8,
        "heading": 245.0,
        "nav_status": "Under Way Using Engine",
        "affected_tickers": ["EQNR", "XOM", "STNG"],
        "signal_direction": "NEUTRAL",
        "signal_reason": "Norwegian crude heading to US Gulf Coast.",
        "financial_impact_usd_million": 0.0,
        "waypoints": [(60.81,5.00),(29.73,-94.97)],
    },
    {
        "mmsi": "477394100",
        "imo": "9826869",
        "vessel_name": "GRACE ACACIA",
        "call_sign": "VRQS5",
        "flag_state": "Hong Kong",
        "flag_iso": "HK",
        "vessel_type": VesselType.LNG_TANKER,
        "vessel_class": "Q-Flex LNG",
        "year_built": 2019,
        "gross_tonnage": 130_000,
        "deadweight_tonnage": 94_000,
        "length_overall_m": 315.0,
        "beam_m": 50.0,
        "max_draught_m": 12.5,
        "operator": "MISC Berhad",
        "owner": "Qatar Gas Transport Co (Nakilat)",
        "charterer": "QatarEnergy LNG",
        "cargo_type": CargoType.LNG,
        "cargo_quantity_mt": 66_000,
        "cargo_detail": "Liquefied Natural Gas (−162°C)",
        "shipper": "QatarEnergy LNG",
        "consignee": "JERA Co., Inc.",
        "origin_port": "Ras Laffan, Qatar",
        "origin_locode": "QARLA",
        "origin_lat": 25.90, "origin_lon": 51.55,
        "dest_port": "Futtsu Terminal, Japan",
        "dest_locode": "JPFUT",
        "dest_lat": 35.31, "dest_lon": 139.85,
        "eta_days_from_now": 8,
        "voyage_progress_pct": 71.0,
        "current_lat": 18.5, "current_lon": 86.4,
        "speed_knots": 19.5,
        "heading": 78.0,
        "nav_status": "Under Way Using Engine",
        "affected_tickers": ["LNG", "QS", "9502.T"],
        "signal_direction": "BULLISH",
        "signal_reason": "LNG cargo from Qatar to Japan. High demand.",
        "financial_impact_usd_million": 85.0,
        "waypoints": [(25.90,51.55),(35.31,139.85)],
    },
    {
        "mmsi": "477442200",
        "imo": "9795417",
        "vessel_name": "MSC GÜLSÜN",
        "call_sign": "VRST9",
        "flag_state": "Panama",
        "flag_iso": "PA",
        "vessel_type": VesselType.CONTAINER,
        "vessel_class": "ULCV (Megamax-24)",
        "year_built": 2019,
        "gross_tonnage": 228_000,
        "deadweight_tonnage": 200_000,
        "length_overall_m": 399.9,
        "beam_m": 61.5,
        "max_draught_m": 16.5,
        "operator": "Mediterranean Shipping Company (MSC)",
        "owner": "MSC Mediterranean Shipping Company SA",
        "charterer": "MSC (own)",
        "cargo_type": CargoType.CONTAINERS,
        "cargo_quantity_mt": 185_000,
        "cargo_detail": "23,756 TEU mixed containerised cargo",
        "shipper": "Multiple — MSC consolidated cargo",
        "consignee": "Multiple European importers",
        "origin_port": "Ningbo-Zhoushan, China",
        "origin_locode": "CNNGB",
        "origin_lat": 29.87, "origin_lon": 121.55,
        "dest_port": "Rotterdam, Netherlands",
        "dest_locode": "NLRTM",
        "dest_lat": 51.96, "dest_lon": 4.05,
        "eta_days_from_now": 16,
        "voyage_progress_pct": 47.0,
        "current_lat": 5.2, "current_lon": 94.8,
        "speed_knots": 22.5,
        "heading": 285.0,
        "nav_status": "Under Way Using Engine",
        "affected_tickers": ["AMKBY", "HLAG.DE", "ZIM", "NMFHF"],
        "signal_direction": "BULLISH",
        "signal_reason": "World's largest container ship, high utilization.",
        "financial_impact_usd_million": 142.0,
        "waypoints": [(29.87,121.55),(51.96,4.05)],
    },
]

class VesselTracker:
    def __init__(self) -> None:
        self._vessels: dict[str, Vessel] = {}
        self._load_tracked_vessels()

    def _load_tracked_vessels(self) -> None:
        from datetime import timedelta
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

    def get_all_vessels(self) -> list[Vessel]:
        return list(self._vessels.values())

    def get_vessel_by_mmsi(self, mmsi: str) -> Vessel | None:
        return self._vessels.get(mmsi)

    def update_vessel_position(self, mmsi: str, lat: float, lon: float, speed: float) -> bool:
        """Updates a vessel's last known position from real AIS data."""
        vessel = self._vessels.get(mmsi)
        if vessel:
            vessel.position.lat = lat
            vessel.position.lon = lon
            vessel.position.speed_knots = speed
            vessel.last_updated = datetime.now(timezone.utc)
            return True
        return False

    def to_geojson_feature_collection(self) -> dict:
        features = []
        for v in self._vessels.values():
            try:
                live_lat, live_lon = v.get_live_position()
            except Exception:
                live_lat, live_lon = v.position.lat, v.position.lon

            # Determine color and symbol
            color = "#6B7E99" # Neutral Blue-Gray
            if v.signal_direction == "BULLISH": color = "#00FF9D" # Neon Green
            elif v.signal_direction == "BEARISH": color = "#FF3D3D" # Neon Red

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [live_lon, live_lat]},
                "properties": {
                    "mmsi": v.mmsi,
                    "name": v.vessel_name,
                    "symbol": "ship",
                    "type": v.vessel_type.value,
                    "class": v.vessel_class,
                    "flag": v.flag_state,
                    "operator": v.operator,
                    "speed_knots": v.position.speed_knots,
                    "heading": v.position.heading_degrees,
                    "origin": v.origin.port_name,
                    "destination": v.destination.port_name,
                    "eta": v.eta_utc.isoformat() if v.eta_utc else None,
                    "progress_pct": v.voyage_progress_pct,
                    "cargo": {
                        "type": v.cargo.cargo_type.value,
                        "manifest": v.cargo.commodity_detail,
                        "quantity": f"{v.cargo.quantity_mt:,.0f} MT",
                        "teu": v.cargo.quantity_teu,
                        "shipper": v.cargo.shipper,
                        "consignee": v.cargo.consignee
                    },
                    "signal": {
                        "status": v.signal_direction,
                        "reason": v.signal_reason,
                        "impact": v.financial_impact_usd_million
                    },
                    "tickers": v.affected_tickers,
                    "color": color,
                    "heading_deg": v.position.heading_degrees
                },
            })
        return {
            "type": "FeatureCollection",
            "features": features,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
