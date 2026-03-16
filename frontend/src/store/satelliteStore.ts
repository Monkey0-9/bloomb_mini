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
}

export const useSatelliteStore = create<SatelliteState>((set) => ({
  satellites: [],
  isLoading: false,
  fetchSatellites: async () => {
    set({ isLoading: true });
    try {
      const response = await fetch('http://localhost:8000/api/alpha/satellites');
      const data = await response.json();
      const features = data.satellites.features;
      
      const satellites = features.map((f: any) => ({
        id: f.properties.id,
        ...f.properties,
        lat: f.geometry.coordinates[1],
        lon: f.geometry.coordinates[0]
      }));
      
      set({ satellites, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch satellites:', error);
      set({ isLoading: false });
    }
  },
}));
