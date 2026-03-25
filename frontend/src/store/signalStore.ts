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
      // Fetch Signals
      const sigResponse = await fetch('/api/signals');
      if (!sigResponse.ok) throw new Error(`Signals API failed: ${sigResponse.status}`);
      const sigData = await sigResponse.json();
      
      const signals = sigData.signals ? Object.entries(sigData.signals).map(([key, s]: [string, any]) => ({
        id: key,
        name: s.signal_name,
        location: s.location || 'Global',
        score: s.score,
        status: (s.direction ? s.direction.toLowerCase() : 'neutral') as 'bullish' | 'bearish' | 'neutral',
        delta: s.delta || 0,
        ic: s.ic || 0,
        icir: s.icir || 0,
        description: s.description || '',
        tickers: s.tickers || [],
        lastUpdate: 'LIVE',
        observations: s.observations || 0,
        as_of: s.as_of || new Date().toISOString()
      })) : [];
      set({ signals });

      // Fetch News for Feed
      const response = await fetch(`/api/alpha/news`); // Assuming API_BASE is defined or empty
      if (!response.ok) throw new Error('Failed to fetch news');
      const data = await response.json();
      const newsEvents = (data.news || data || []).map((n: any) => ({
        id: `news-${n.id}`,
        timestamp: n.time,
        message: n.text,
        url: n.url,
        type: n.impact === 'bullish' || n.impact === 'bearish' ? 'market' : 'system'
      }));
      set({ events: newsEvents });
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
