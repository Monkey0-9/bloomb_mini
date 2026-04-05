import { create } from 'zustand';

export interface Signal {
  id: string;
  name: string;
  location: string;
  score: number;
  status: 'bullish' | 'bearish' | 'neutral';
  delta: number;
  ic: number;
  icir: number;
  description: string;
  tickers: string[];
  lastUpdate: string;
  observations: number;
  as_of: string;
}

export interface TerminalEvent {
  id: string;
  timestamp: string;
  message: string;
  type: 'market' | 'satellite' | 'system';
  url?: string;
}

export interface MarketIndex {
  id: string;
  name: string;
  value: string;
  change: string;
  status: 'bullish' | 'bearish' | 'neutral';
}

interface SignalState {
  signals: Signal[];
  indices: MarketIndex[];
  events: TerminalEvent[];
  satFeed: any[];
  workflows: any;
  conflicts: any[];
  setSignals: (signals: Signal[]) => void;
  setIndices: (indices: MarketIndex[]) => void;
  setEvents: (events: TerminalEvent[]) => void;
  addEvent: (event: TerminalEvent) => void;
  fetchSignals: () => Promise<void>;
  fetchSatFeed: () => Promise<void>;
  fetchWorkflows: () => Promise<void>;
  fetchConflicts: () => Promise<void>;
  handleWSUpdate: (msg: any) => void;
}

export const useSignalStore = create<SignalState>((set) => ({
  signals: [],
  satFeed: [],
  conflicts: [],
  workflows: { active: [], completed: [], system: { ingest_rate: '0 GB/s', compute: '0%', status: 'LOADING' } },
  indices: [],
  events: [],
  setSignals: (signals) => set({ signals }),
  setIndices: (indices) => set({ indices }),
  setEvents: (events) => set({ events }),
  addEvent: (event) => set((state) => ({ events: [event, ...state.events].slice(0, 100) })),
  fetchSignals: async () => {
    try {
      // Parallel fetch for optimal terminal performance
      const [sigRes, newsRes, swarmRes, conflictRes] = await Promise.all([
        fetch('/api/intelligence/thermal'),
        fetch('/api/news/live'),
        fetch('/api/intelligence/swarm'),
        fetch('/api/conflicts')
      ]);

      if (sigRes.ok) {
        const sigData = await sigRes.json();
        const signals = (sigData.clusters || sigData || []).map((s: any) => ({
          id: s.id || `${s.lat}-${s.lon}`,
          name: s.name || s.facility_name,
          location: `${s.lat.toFixed(2)}, ${s.lon.toFixed(2)}`,
          score: s.sigma || s.anomaly_sigma,
          status: (s.signal ? s.signal.toLowerCase() : 'neutral') as 'bullish' | 'bearish' | 'neutral',
          delta: s.frp_avg || 0,
          ic: 0.12,
          icir: 1.4,
          description: s.reason || `Thermal Anomaly (Sigma: ${s.sigma})`,
          tickers: s.tickers || [],
          lastUpdate: 'LIVE',
          observations: s.hotspots || 24,
          as_of: s.ts || new Date().toISOString()
        }));
        set({ signals });
      }

      if (newsRes.ok) {
        const nData = await newsRes.json();
        const newsEvents = (nData.articles || []).map((n: any, idx: number) => ({
          id: `news-${idx}`,
          timestamp: n.time,
          message: `${n.source}: ${n.text}`,
          url: n.url,
          type: 'market' as const
        }));
        set((state) => ({ events: [...newsEvents, ...state.events].slice(0, 100) }));
      }

      if (swarmRes.ok) {
        const swarmData = await swarmRes.json();
        set((state) => ({
          indices: [
            ...state.indices.filter(i => i.id !== 'GTFI'),
            { 
              id: 'GTFI', 
              name: 'GLOBAL TRADE FLOW', 
              value: (swarmData.gtfi_score * 100).toFixed(1), 
              change: swarmData.gtfi_score > 0.8 ? 'Optimal' : 'Disrupted',
              status: swarmData.gtfi_score > 0.8 ? 'bullish' : 'bearish' 
            }
          ]
        }));
        
        const swarmEvents = (swarmData.predictions || []).map((p: any, idx: number) => ({
          id: `swarm-${idx}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          message: `[SWARM] ${p.prediction} (Conf: ${p.confidence}%)`,
          type: 'system' as const
        }));
        set((state) => ({ events: [...swarmEvents, ...state.events].slice(0, 100) }));
      }

      if (conflictRes.ok) {
        const cData = await conflictRes.json();
        set({ conflicts: cData.events || [] });
      }
    } catch (err) {
      console.error('Failed to fetch intelligence data:', err);
    }
  },
  fetchConflicts: async () => {
    try {
      const resp = await fetch('/api/conflicts');
      if (resp.ok) {
        const data = await resp.json();
        set({ conflicts: data.events || [] });
      }
    } catch (err) {
      console.error('Failed to fetch conflicts:', err);
    }
  },
  fetchSatFeed: async () => {
    try {
      const resp = await fetch('/api/satfeed');
      if (resp.ok) {
        const data = await resp.json();
        set({ satFeed: data.feed || [] });
      }
    } catch (err) {
      console.error('Failed to fetch sat feed:', err);
    }
  },
  fetchWorkflows: async () => {
    try {
      const resp = await fetch('/api/workflows');
      if (resp.ok) {
        const data = await resp.json();
        set({ workflows: data });
      }
    } catch (err) {
      console.error('Failed to fetch workflows:', err);
    }
  },
  handleWSUpdate: (msg) => {
    if (msg.type === 'signal_update' && msg.id) {
      set((state) => ({
        signals: state.signals.map(s => s.id === msg.id ? { ...s, score: msg.score, status: msg.status, delta: msg.delta } : s)
      }));
    } else if (msg.type === 'new_event' && msg.event) {
      set((state) => ({ events: [msg.event, ...state.events].slice(0, 100) }));
    }
  }
}));
