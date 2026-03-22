import { create } from 'zustand';
import { Flight } from '../types/aviation';

interface FlightState {
  flights: Flight[];
  selectedFlight: Flight | null;
  isLoading: boolean;
  error: string | null;
  setFlights: (flights: Flight[]) => void;
  setSelectedFlight: (flight: Flight | null) => void;
  fetchFlights: () => Promise<void>;
  updateFlightPosition: (icao24: string, lat: number, lon: number, alt: number) => void;
  handleWSUpdate: (msg: any) => void;
}

const API_BASE = (import.meta.env.VITE_API_URL as string) || '';

export const useFlightStore = create<FlightState>((set) => ({
  flights: [],
  selectedFlight: null,
  isLoading: false,
  error: null,
  setFlights: (flights) => set({ flights }),
  setSelectedFlight: (selectedFlight) => set({ selectedFlight }),
  fetchFlights: async () => {
    set({ isLoading: true });
    try {
      const response = await fetch(`${API_BASE}/api/intelligence/aircraft`);
      const data = await response.json();
      const flights = (data.aircraft || []).map((f: any) => ({
        ...f,
        position: {
          lat: f.lat,
          lon: f.lon,
          alt_ft: f.alt_ft || 0,
          speed_kts: f.speed_kts || 0,
          heading: f.heading || 0,
          timestamp: new Date().toISOString(),
        }
      }));
      set({ flights, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },
  updateFlightPosition: (icao24, lat, lon, alt_ft) => set((state) => ({
    flights: state.flights.map((f) => 
      f.icao24 === icao24 ? { ...f, position: { ...f.position, lat, lon, alt_ft } } : f
    )
  })),
  handleWSUpdate: (msg) => {
    if (msg.flights) {
      set({ flights: msg.flights.map((f: any) => ({
        ...f,
        position: {
          lat: f.lat, lon: f.lon, alt_ft: f.alt || (f.altitude_m ? f.altitude_m * 3.28084 : 0), speed_kts: f.speed || (f.velocity_ms ? f.velocity_ms * 1.94384 : 0), heading: f.heading || f.heading_deg || 0, timestamp: new Date().toISOString()
        }
      })) });
    } else if (msg.icao24 && msg.lat && msg.lon) {
      set((state) => ({
        flights: state.flights.map((f) => 
          f.icao24 === msg.icao24 ? { ...f, position: { ...f.position, lat: msg.lat, lon: msg.lon, alt_ft: msg.alt_ft || f.position.alt_ft } } : f
        )
      }));
    }
  }
}));
