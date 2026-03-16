export enum VesselType {
  CONTAINER = "Container Ship",
  CRUDE_TANKER = "Crude Oil Tanker",
  PRODUCT_TANKER = "Product Tanker",
  LNG_TANKER = "LNG Carrier",
  LPG_TANKER = "LPG Carrier",
  BULK_CARRIER = "Bulk Carrier",
  CAR_CARRIER = "Car Carrier (RORO)",
  GENERAL_CARGO = "General Cargo",
  FERRY = "Ferry/Passenger",
  OFFSHORE = "Offshore Supply",
  MILITARY = "Military/Naval",
  RESEARCH = "Research Vessel",
}

export enum CargoType {
  CRUDE_OIL = "Crude Oil",
  REFINED_PRODUCTS = "Refined Petroleum Products",
  LNG = "Liquefied Natural Gas",
  LPG = "Liquefied Petroleum Gas",
  IRON_ORE = "Iron Ore",
  COAL = "Coal",
  GRAIN = "Grain/Agricultural",
  CONTAINERS = "Containerised Goods",
  VEHICLES = "Vehicles/Automobiles",
  CHEMICALS = "Chemicals",
  FERTILISER = "Fertilisers",
  TIMBER = "Timber/Forest Products",
  STEEL = "Steel/Metal Products",
  BAUXITE = "Bauxite/Alumina",
  PASSENGERS = "Passengers",
  EMPTY = "In Ballast (Empty)",
}

export interface VesselPosition {
  lat: number;
  lon: number;
  timestamp: string;
  speed_knots: number;
  heading_degrees: number;
  navigational_status: string;
  course_over_ground: number;
}

export interface PortCall {
  port_name: string;
  port_code: string;
  country: string;
  lat: number;
  lon: number;
  arrival_utc: string | null;
  departure_utc: string | null;
  is_estimated: boolean;
}

export interface CargoManifest {
  cargo_type: CargoType;
  quantity_mt: number;
  quantity_teu: number | null;
  commodity_detail: string;
  shipper: string;
  consignee: string;
  loading_port: string;
  discharge_port: string;
  bill_of_lading_date: string | null;
}

export interface Vessel {
  mmsi: string;
  imo: string;
  vessel_name: string;
  call_sign: string;
  flag_state: string;
  flag_iso: string;
  vessel_type: VesselType;
  vessel_class: string;
  year_built: number;
  gross_tonnage: number;
  deadweight_tonnage: number;
  length_overall_m: number;
  beam_m: number;
  max_draught_m: number;
  operator: string;
  owner: string;
  charterer: string;
  position: VesselPosition;
  origin: PortCall;
  destination: PortCall;
  eta_utc: string | null;
  voyage_progress_pct: number;
  cargo: CargoManifest;
  affected_tickers: string[];
  signal_direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  signal_reason: string;
  financial_impact_usd_million: number;
  waypoints: [number, number][];
  historical_track: VesselPosition[];
  vessel_id: string;
  last_updated: string;
  data_source: string;
}
