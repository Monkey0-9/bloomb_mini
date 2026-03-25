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
  setSignals: (signals: Signal[]) => void;
  setIndices: (indices: MarketIndex[]) => void;
  setEvents: (events: TerminalEvent[]) => void;
  addEvent: (event: TerminalEvent) => void;
  fetchSignals: () => Promise<void>;
  handleWSUpdate: (msg: any) => void;
}

export const useSignalStore = create<SignalState>((set) => ({
  signals: [],
  indices: [
    { id: 'SPX', name: 'S&P 500', value: '5,123.42', change: '+1.22%', status: 'bullish' },
    { id: 'NDX', name: 'NASDAQ', value: '18,124.55', change: '+1.54%', status: 'bullish' },
    { id: 'DOW', name: 'DOW JONES', value: '38,984.12', change: '+0.88%', status: 'bullish' },
    { id: 'BTC', name: 'BITCOIN', value: '64,124.00', change: '+3.44%', status: 'bullish' },
    { id: 'CL', name: 'OIL (WTI)', value: '78.42', change: '-0.33%', status: 'bearish' },
  ],
  events: [
    { id: 'e1', timestamp: '14:31', message: 'Rotterdam port throughput +34%', type: 'satellite' }
  ],
  setSignals: (signals) => set({ signals }),
  setIndices: (indices) => set({ indices }),
  setEvents: (events) => set({ events }),
  addEvent: (event) => set((state) => ({ events: [event, ...state.events].slice(0, 100) })),
  fetchSignals: async () => {
    try {
      // Fetch Thermal Signals
      const sigResponse = await fetch('/api/intelligence/thermal');
      if (!sigResponse.ok) throw new Error(`Thermal API failed: ${sigResponse.status}`);
      const sigData = await sigResponse.json();
      
      const signals = (Array.isArray(sigData) ? sigData : []).map((s: any) => ({
        id: `${s.lat}-${s.lon}`,
        name: s.facility_name,
        location: `${s.lat.toFixed(2)}, ${s.lon.toFixed(2)}`,
        score: s.anomaly_sigma,
        status: (s.signal ? s.signal.toLowerCase() : 'neutral') as 'bullish' | 'bearish' | 'neutral',
        delta: s.frp_mw || 0,
        ic: 0.12, // Placeholder for dynamically computed IC
        icir: 1.4,
        description: `Thermal FRP: ${s.frp_mw}MW (Confidence: ${s.confidence})`,
        tickers: s.tickers || [],
        lastUpdate: 'LIVE',
        observations: 24,
        as_of: s.timestamp || new Date().toISOString()
      }));
      set({ signals });

      // Fetch Global News
      const response = await fetch(`/api/news/GLOBAL`);
      if (!response.ok) throw new Error('Failed to fetch news');
      const data = await response.json();
      const newsEvents = (data.news || data || []).map((n: any, idx: number) => ({
        id: `news-${idx}`,
        timestamp: n.pub_date,
        message: `${n.source}: ${n.title}`,
        url: n.link,
        type: 'market'
      }));
      set({ events: newsEvents });
      // Fetch Maritime Swarm Intelligence
      const vesselResponse = await fetch('/api/intelligence/vessels/swarm');
      if (vesselResponse.ok) {
        const vesselData = await vesselResponse.json();
        // Add Swarm Index to indices
        set((state) => ({
          indices: [
            ...state.indices.filter(i => i.id !== 'GTFI'),
            { 
              id: 'GTFI', 
              name: 'GLOBAL TRADE FLOW', 
              value: (vesselData.global_index * 100).toFixed(1), 
              change: vesselData.global_index > 0.8 ? 'Optimal' : 'Disrupted',
              status: vesselData.global_index > 0.8 ? 'bullish' : 'bearish' 
            }
          ]
        }));
        
        // Add Swarm Alerts to events
        const swarmEvents = (vesselData.alerts || []).map((a: any) => ({
          id: a.id,
          timestamp: new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          message: `[MARITIME SWARM] ${a.reason} (${a.location})`,
          type: 'system'
        }));
        set((state) => ({ events: [...swarmEvents, ...state.events].slice(0, 100) }));
      }
    } catch (err) {
      console.error('Failed to fetch intelligence data:', err);
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
