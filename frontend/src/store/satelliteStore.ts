import { create } from 'zustand';

export interface Satellite {
  id: string;
  name: string;
  category: string;
  owner: string;
  altitude: string;
  velocity: string;
  orbit: string;
  symbol: string;
  color: string;
  lat: number;
  lon: number;
}

interface SatelliteState {
  satellites: Satellite[];
  isLoading: boolean;
  fetchSatellites: () => Promise<void>;
  handleWSUpdate: (msg: any) => void;
}

export const useSatelliteStore = create<SatelliteState>((set) => ({
  satellites: [],
  isLoading: false,
  fetchSatellites: async () => {
    set({ isLoading: true });
    try {
      const response = await fetch('/api/intelligence/orbits');
      const data = await response.json();
      const rawSats = Array.isArray(data) ? data : [];
      
      const satellites = rawSats.map((s: any) => ({
        id: s.name,
        name: s.name,
        category: 'EO',
        owner: 'Global',
        altitude: `${s.alt_km} km`,
        velocity: '7.5 km/s',
        orbit: 'LEO',
        symbol: 'S',
        color: '#38bdf8',
        lat: s.lat,
        lon: s.lon
      }));
      
      set({ satellites, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch satellites:', error);
      set({ isLoading: false });
    }
  },
  handleWSUpdate: (msg) => {
    if (msg.data && Array.isArray(msg.data)) {
      set({ satellites: msg.data });
    }
  }
}));
