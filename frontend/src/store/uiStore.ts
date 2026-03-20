import { create } from 'zustand';

export type ViewType = 'world' | 'charts' | 'matrix' | 'feed' | 'portfolio' | 'terminal' | 'settings' | 'help' | 'research' | 'education' | 'launchpad' | 'economics' | 'earnings' | 'news' | 'satellite_feed' | 'global_equities' | 'alerts' | 'workflow';

interface UIState {
  selectedView: ViewType;
  sidebarExpanded: boolean;
  activeLayers: string[];
  zoomLevel: number;
  command: string;
  currentTicker: string;
  setView: (view: ViewType) => void;
  setSelectedView: (view: ViewType) => void;
  setSidebarExpanded: (expanded: boolean) => void;
  setCommand: (cmd: string) => void;
  setCurrentTicker: (ticker: string) => void;
  toggleLayer: (layer: string) => void;
  updateZoom: (delta: number) => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedView: 'world',
  sidebarExpanded: true,
  activeLayers: ['PORTS', 'VESSELS', 'THERMAL', 'FLIGHTS', 'SATELLITES'],
  zoomLevel: 2,
  command: '',
  currentTicker: 'AMKBY US Equity',
  setView: (view) => set({ selectedView: view }),
  setSelectedView: (view) => set({ selectedView: view }),
  setSidebarExpanded: (expanded) => set({ sidebarExpanded: expanded }),
  setCommand: (cmd) => set({ command: cmd }),
  setCurrentTicker: (ticker) => set({ currentTicker: ticker }),
  toggleLayer: (layer) => set((state) => ({
    activeLayers: state.activeLayers.includes(layer)
      ? state.activeLayers.filter((l) => l !== layer)
      : [...state.activeLayers, layer],
  })),
  updateZoom: (delta) => set((state) => ({
    zoomLevel: Math.max(1, Math.min(5, state.zoomLevel + delta)),
  })),
}));

export const useTerminalStore = useUIStore;
