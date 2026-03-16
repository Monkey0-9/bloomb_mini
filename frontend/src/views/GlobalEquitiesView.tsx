import { useMemo, useState } from 'react';
import { useEquityStore } from '../store/equityStore';
import { motion, AnimatePresence } from 'framer-motion';

const GlobalEquitiesView = () => {
  const { equities } = useEquityStore();
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  const filteredEquities = useMemo(() => {
    return (equities || []).filter(e => {
      const matchesSearch = (e.ticker || '').toLowerCase().includes(search.toLowerCase()) || 
                            (e.name || '').toLowerCase().includes(search.toLowerCase());
      const signal = (e.sat_signal || 'NEUTRAL').toUpperCase();
      const matchesFilter = filter === 'ALL' || signal === filter;
      return matchesSearch && matchesFilter;
    });
  }, [equities, search, filter]);

  return (
    <div className="flex-1 flex flex-col bg-surface-0 overflow-hidden">
      {/* EQUITIES HEADER: ALLX STYLE */}
      <div className="h-11 border-b border-white/5 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
               <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">GLOBAL EQUITIES MONITOR</span>
               <div className="w-2 h-2 rounded-full bg-bull animate-pulse"></div>
            </div>
            <div className="h-6 w-[1px] bg-white/5 mx-2"></div>
            <div className="flex gap-2">
               {['ALL', 'BULLISH', 'BEARISH', 'NEUTRAL'].map(f => (
                  <button 
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`type-data-xs px-3 py-1 rounded-sm border transition-all ${
                       filter === f ? 'bg-accent-primary border-accent-primary text-void font-bold shadow-[0_0_10px_rgba(0,200,255,0.3)]' : 'border-white/10 text-text-4 hover:border-text-2'
                    }`}
                  >
                    {f}
                  </button>
               ))}
            </div>
         </div>
         
         <div className="flex items-center bg-surface-2 border border-white/5 px-3 py-1 rounded-sm group focus-within:border-accent-primary transition-all">
            <input 
               type="text" 
               placeholder="SEARCH TICKERS..." 
               value={search}
               onChange={(e) => setSearch(e.target.value)}
               className="bg-transparent outline-none type-data-xs text-text-1 placeholder:text-text-5 w-40 font-mono"
            />
         </div>
      </div>

      {/* EQUITIES GRID */}
      <div className="flex-1 overflow-auto custom-scrollbar tabular-nums">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-surface-1 z-10 border-b border-white/10">
            <tr>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest">Ticker</th>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest">Security Name</th>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest text-right">Last Price</th>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest text-right">Change</th>
              <th className="px-4 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest text-center">Satellite Alpha</th>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest text-right">Market</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            <AnimatePresence mode="popLayout">
              {filteredEquities.map((e) => (
                <motion.tr 
                  key={e.ticker}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="hover:bg-white/5 transition-colors cursor-pointer group h-14"
                >
                  <td className="px-6 py-3">
                    <span className="type-data-md text-accent-primary font-bold group-hover:text-text-0 transition-colors uppercase font-mono">{e.ticker}</span>
                  </td>
                  <td className="px-6 py-3">
                    <span className="type-data-xs text-text-2 uppercase group-hover:text-text-1 truncate max-w-[200px] inline-block font-mono tracking-tight">{e.name}</span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span className="type-data-md text-text-1 font-bold font-mono">${(e.price || 0).toFixed(2)}</span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span className={`type-data-xs font-bold font-mono ${(e.change || 0) >= 0 ? 'text-bull' : 'text-bear'}`}>
                      {(e.change || 0) >= 0 ? '+' : ''}{(e.change || 0).toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                     <span className={`type-data-xs px-2 py-0.5 rounded-sm border font-bold tracking-widest text-[9px] ${
                        (e.sat_signal || 'NEUTRAL').toUpperCase() === 'BULLISH' ? 'bg-bull/10 border-bull/50 text-bull' : 
                        (e.sat_signal || 'NEUTRAL').toUpperCase() === 'BEARISH' ? 'bg-bear/10 border-bear/50 text-bear' : 
                        'bg-surface-2 border-white/10 text-text-4'
                     }`}>
                        {e.sat_signal || 'NEUTRAL'}
                     </span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span className="type-data-xs text-text-5 uppercase font-mono">{e.exchange}</span>
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      {/* EQUITIES FOOTER STATUS */}
      <div className="h-8 border-t border-white/10 flex items-center justify-between px-4 bg-void shrink-0">
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Live Telemetry: <span className="text-bull">Feed Optimal</span></span>
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Signals: <span className="text-accent-primary">{filteredEquities.length} Active</span></span>
      </div>
    </div>
  );
};

export default GlobalEquitiesView;
