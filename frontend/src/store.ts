import { create } from 'zustand';

export interface Signal {
  id: string;
  name: string;
  headline: string;
  implication: string;
  ticker: string;
  score: number;
  status: 'bullish' | 'bearish' | 'neutral';
  trend: number[];
  ic: number;
  icir: number;
  lastUpdate: string;
}

export interface TerminalEvent {
  id: string;
  timestamp: string;
  message: string;
  type: 'market' | 'satellite' | 'system';
}

export interface MarketIndex {
  id: string;
  name: string;
  value: string;
  change: string;
  status: 'bullish' | 'bearish' | 'neutral';
}

interface TerminalState {
  signals: Signal[];
  indices: MarketIndex[];
  events: TerminalEvent[];
  selectedView: 'world' | 'charts' | 'matrix' | 'feed' | 'portfolio' | 'terminal';
  command: string;
  setView: (view: TerminalState['selectedView']) => void;
  setSelectedView: (view: TerminalState['selectedView']) => void;
  setCommand: (cmd: string) => void;
}

export const useTerminalStore = create<TerminalState>((set) => ({
  indices: [
    { id: 'SPX', name: 'S&P 500', value: '5,123.42', change: '+1.22%', status: 'bullish' },
    { id: 'NDX', name: 'NASDAQ', value: '18,124.55', change: '+1.54%', status: 'bullish' },
    { id: 'DOW', name: 'DOW JONES', value: '38,984.12', change: '+0.88%', status: 'bullish' },
    { id: 'FTSE', name: 'FTSE 100', value: '7,640.33', change: '-0.12%', status: 'bearish' },
    { id: 'DAX', name: 'DAX', value: '17,842.10', change: '+0.45%', status: 'bullish' },
    { id: 'N225', name: 'NIKKEI 225', value: '39,124.40', change: '+2.12%', status: 'bullish' },
    { id: 'HSI', name: 'HANG SENG', value: '16,542.11', change: '-1.44%', status: 'bearish' },
    { id: 'NSE', name: 'SENSEX', value: '73,124.55', change: '+0.33%', status: 'bullish' },
    { id: 'BTC', name: 'BITCOIN', value: '64,124.00', change: '+3.44%', status: 'bullish' },
    { id: 'ETH', name: 'ETHEREUM', value: '3,442.10', change: '+2.88%', status: 'bullish' },
    { id: 'SOL', name: 'SOLANA', value: '142.45', change: '+5.12%', status: 'bullish' },
    { id: 'GC', name: 'GOLD', value: '2,142.10', change: '+0.77%', status: 'bullish' },
    { id: 'CL', name: 'OIL (WTI)', value: '78.42', change: '-0.33%', status: 'bearish' },
    { id: 'EUR', name: 'EUR/USD', value: '1.0922', change: '+0.11%', status: 'bullish' },
    { id: 'JPY', name: 'USD/JPY', value: '149.88', change: '-0.24%', status: 'bearish' },
    { id: 'SHCOMP', name: 'SHANGHAI COMP', value: '3,024.11', change: '+0.12%', status: 'bullish' },
    { id: 'CAC', name: 'CAC 40', value: '7,924.33', change: '+0.22%', status: 'bullish' },
    { id: 'ASX', name: 'S&P/ASX 200', value: '7,742.10', change: '+0.44%', status: 'bullish' },
    { id: 'TSX', name: 'S&P/TSX', value: '21,124.55', change: '+0.11%', status: 'bullish' }
  ],
  signals: Array.from({ length: 100 }).map((_, i) => ({
    id: `${i + 1}`,
    name: ['GLOBAL SHIPPING', 'RETAIL VELOCITY', 'SEMICONDUCTOR LOAD', 'ENERGY FLOW', 'AGRICULTURE YIELD'][i % 5],
    headline: ['Ports busy', 'Stores full', 'Fabs running high', 'Pipelines active', 'Crops steady'][i % 5],
    implication: 'Supply chains through Europe and Asia are healthy.',
    ticker: ['AMKBY', 'WMT', 'NVDA', 'XOM', 'ADR'][i % 5],
    score: Math.floor(Math.random() * 100),
    status: Math.random() > 0.5 ? 'bullish' : 'bearish',
    trend: [20, 25, 30, 34],
    ic: 0.047,
    icir: 0.62,
    lastUpdate: '5m ago'
  })),
  events: [
    { id: 'e1', timestamp: '14:31', message: 'Rotterdam port throughput +34%', type: 'satellite' }
  ],
  selectedView: 'world',
  command: '',
  setView: (view) => set({ selectedView: view }),
  setSelectedView: (view) => set({ selectedView: view }),
  setCommand: (cmd) => set({ command: cmd }),
}));
