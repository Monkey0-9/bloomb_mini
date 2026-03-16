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
      const sigResponse = await fetch('http://localhost:8000/api/signals');
      const sigData = await sigResponse.json();
      const signals = Object.entries(sigData.signals).map(([key, s]: [string, any]) => ({
        id: key,
        name: s.signal_name,
        location: s.location,
        score: s.score,
        status: s.direction.toLowerCase() as 'bullish' | 'bearish' | 'neutral',
        delta: s.delta,
        ic: s.ic,
        icir: s.icir,
        description: s.description,
        tickers: s.tickers || [],
        lastUpdate: 'LIVE',
        observations: s.observations || 0,
        as_of: s.as_of
      }));
      set({ signals });

      // Fetch News for Feed
      const newsResponse = await fetch('http://localhost:8000/api/alpha/news');
      const newsData = await newsResponse.json();
      const newsEvents = (newsData.news || []).map((n: any) => ({
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
  }
}));
