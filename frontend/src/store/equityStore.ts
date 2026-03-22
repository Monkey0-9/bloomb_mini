import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Equity {
  ticker: string;
  name: string;
  exchange: string;
  price: number;
  change: number;
  bid: number;
  ask: number;
  sat_signal: string;
}

interface EquityState {
  equities: Equity[];
  watchlist: string[];
  fetchEquities: () => Promise<void>;
  setEquities: (equities: Equity[]) => void;
  addToWatchlist: (ticker: string) => void;
  removeFromWatchlist: (ticker: string) => void;
}

export const useEquityStore = create<EquityState>()(
  persist(
    (set, get) => ({
      equities: [],
      watchlist: ['SPY', 'QQQ', 'WTI', 'GLD', 'BTC'],
      setEquities: (equities) => set({ equities }),
      addToWatchlist: (ticker) => set((state) => ({ 
        watchlist: [...new Set([...state.watchlist, ticker.toUpperCase()])] 
      })),
      removeFromWatchlist: (ticker) => set((state) => ({ 
        watchlist: state.watchlist.filter(t => t !== ticker) 
      })),
      fetchEquities: async () => {
        try {
          const wl = get().watchlist;
          const tickers = wl.length > 0 ? wl.join(',') : 'AAPL,TSLA,MSFT';
          const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/market/prices?tickers=${tickers}`);
          if (!response.ok) throw new Error('Network response was not ok');
          const data = await response.json();
          const prices = data.prices || {};
          
          const newEquities = Object.values(prices).map((p: any) => ({
             ticker: p.ticker,
             name: p.ticker,
             exchange: 'GLOBAL',
             price: p.price,
             change: (Math.random() * 4) - 2, // Mock day change
             bid: p.price,
             ask: p.price,
             sat_signal: 'NEUTRAL'
          }));
          set({ equities: newEquities });
        } catch (err) {
          console.error('Failed to fetch equities:', err);
        }
      },
    }),
    {
      name: 'sattrade-equities',
      partialize: (state) => ({ watchlist: state.watchlist }),
    }
  )
);
