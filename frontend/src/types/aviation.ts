export enum FlightType {
  CARGO = "Cargo/Logistics",
  COMMERCIAL = "Commercial Passenger",
  PRIVATE_JET = "Private/Corporate",
  MILITARY = "Military/Transport",
  GOVERNMENT = "Government/Diplomatic",
  SPECIAL_OPS = "Special Operations",
}

export enum Importance {
  CRITICAL = "Critical",
  HIGH = "High",
  MEDIUM = "Medium",
  LOW = "Low",
}

export interface FlightPosition {
  lat: number;
  lon: number;
  alt_ft: number;
  speed_kts: number;
  heading: number;
  timestamp: string;
}

export interface Airport {
  name: string;
  iata: string;
  icao: string;
  city: string;
  country: string;
  lat: number;
  lon: number;
}

export interface CargoDetails {
  type: string;
  weight_kg: number;
  value_usd_million: number;
  priority: string;
}

export interface Flight {
  icao24: string;
  callsign: string;
  registration: string;
  operator: string;
  aircraft_type: string;
  flight_type: FlightType;
  importance: Importance;
  mission_description: string;
  origin: Airport;
  destination: Airport;
  departure_time: string;
  arrival_time_est: string;
  progress_pct: number;
  position: FlightPosition;
  cargo: CargoDetails | null;
  affected_tickers: string[];
  signal_direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  signal_reason: string;
  financial_impact_usd_million: number;
  flight_id: string;
  last_updated: string;
  data_source: string;
}
