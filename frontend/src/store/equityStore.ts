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
    (set) => ({
      equities: [],
      watchlist: ['AMKBY', 'ZIM', 'SHEL', 'LNG', 'MT'],
      setEquities: (equities) => set({ equities }),
      addToWatchlist: (ticker) => set((state) => ({ 
        watchlist: [...new Set([...state.watchlist, ticker.toUpperCase()])] 
      })),
      removeFromWatchlist: (ticker) => set((state) => ({ 
        watchlist: state.watchlist.filter(t => t !== ticker) 
      })),
      fetchEquities: async () => {
        try {
          const response = await fetch('http://localhost:8000/api/equities');
          if (!response.ok) throw new Error('Network response was not ok');
          const data = await response.json();
          set({ equities: data.equities });
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
