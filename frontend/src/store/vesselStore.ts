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
  handleWSUpdate: (msg: any) => void;
}

const API_BASE = (import.meta.env.VITE_API_URL as string) || '';

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
      const response = await fetch(`${API_BASE}/api/intelligence/ships`);
      const data = await response.json();
      const vessels = (data.ships || []).map((f: any) => ({
        ...f,
        mmsi: f.id,
        position: {
          lat: f.lat,
          lon: f.lon,
          timestamp: new Date().toISOString(),
          speed_knots: f.velocity || 0,
          heading_degrees: f.heading || 0,
          navigational_status: f.status || "Under Way",
          course_over_ground: f.heading || 0,
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
  handleWSUpdate: (msg) => {
    if (msg.data && Array.isArray(msg.data)) {
      set({ vessels: msg.data.map((v: any) => ({
        ...v,
        position: {
          lat: v.lat, lon: v.lon, speed_knots: v.speed_knots, heading_degrees: v.heading, course_over_ground: v.heading, navigational_status: v.nav_status, timestamp: new Date().toISOString()
        }
      })) });
    } else if (msg.mmsi && msg.lat && msg.lon) {
      set((state) => ({
        vessels: state.vessels.map(v => v.mmsi === msg.mmsi ? { ...v, position: { ...v.position, lat: msg.lat, lon: msg.lon } } : v)
      }));
    }
  }
}));
