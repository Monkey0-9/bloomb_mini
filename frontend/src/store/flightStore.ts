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
      const response = await fetch('http://localhost:8000/api/flights');
      const data = await response.json();
      const flights = data.features.map((f: any) => ({
        ...f.properties,
        position: {
          lat: f.geometry.coordinates[1],
          lon: f.geometry.coordinates[0],
          alt_ft: f.properties.alt_ft || 0,
          speed_kts: f.properties.speed_kts || 0,
          heading: f.properties.heading || 0,
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
    if (msg.icao24 && msg.lat && msg.lon) {
      set((state) => ({
        flights: state.flights.map((f) => 
          f.icao24 === msg.icao24 ? { ...f, position: { ...f.position, lat: msg.lat, lon: msg.lon, alt_ft: msg.alt_ft || f.position.alt_ft } } : f
        )
      }));
    }
  }
}));
