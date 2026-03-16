import { create } from 'zustand';
import { Vessel } from '../types/maritime';

interface VesselState {
  vessels: Vessel[];
  selectedVessel: Vessel | null;
  isLoading: boolean;
  error: string | null;
  setVessels: (vessels: Vessel[]) => void;
  setSelectedVessel: (vessel: Vessel | null) => void;
  fetchVessels: () => Promise<void>;
  updateVesselPosition: (mmsi: string, lat: number, lon: number) => void;
}

export const useVesselStore = create<VesselState>((set) => ({
  vessels: [],
  selectedVessel: null,
  isLoading: false,
  error: null,
  setVessels: (vessels) => set({ vessels }),
  setSelectedVessel: (selectedVessel) => set({ selectedVessel }),
  fetchVessels: async () => {
    set({ isLoading: true });
    try {
      const response = await fetch('http://localhost:8000/api/vessels');
      const data = await response.json();
      // data is GeoJSON, we want the objects for the store or just store the features
      // For the store, we'll extract the properties and geometry
      const vessels = data.features.map((f: any) => ({
        ...f.properties,
        position: {
          lat: f.geometry.coordinates[1],
          lon: f.geometry.coordinates[0],
          timestamp: new Date().toISOString(),
          speed_knots: f.properties.speed_knots || 0,
          heading_degrees: f.properties.heading || 0,
          navigational_status: "Under Way",
          course_over_ground: f.properties.heading || 0,
        }
      }));
      set({ vessels, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },
  updateVesselPosition: (mmsi, lat, lon) => set((state) => ({
    vessels: state.vessels.map((v) => 
      v.mmsi === mmsi ? { ...v, position: { ...v.position, lat, lon } } : v
    )
  })),
}));
