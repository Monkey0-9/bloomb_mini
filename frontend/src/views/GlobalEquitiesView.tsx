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
    <div className="flex-1 flex flex-col bg-void overflow-hidden text-accent-primary font-mono select-none">
      {/* EQUITIES HEADER: BLOOMBERG STYLE */}
      <div className="h-7 border-b border-surface-4 flex items-center justify-between px-2 shrink-0 bg-void">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
               <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">GLOBAL EQUITIES MONITOR</span>
               <div className="w-2 h-2 rounded-full bg-bull animate-pulse"></div>
            </div>
            <div className="h-6 w-[1px] bg-white/5 mx-2"></div>
            <div className="flex gap-1">
               {['ALL', 'BULLISH', 'BEARISH', 'NEUTRAL'].map(f => (
                  <button 
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`text-[10px] px-2 py-0 border transition-none uppercase ${
                       filter === f ? 'bg-accent-primary text-void font-bold border-accent-primary' : 'border-surface-4 text-neutral hover:border-accent-primary hover:text-accent-primary'
                    }`}
                  >
                    {f}
                  </button>
               ))}
            </div>
         </div>
         
         <div className="flex items-center bg-surface-1 border border-surface-4 px-2 py-0 focus-within:border-accent-primary">
            <span className="text-[10px] mr-1 text-neutral">ticker:</span>
            <input 
               type="text" 
               placeholder="SRCH..." 
               value={search}
               onChange={(e) => setSearch(e.target.value)}
               className="bg-transparent outline-none text-[11px] text-accent-primary placeholder:text-neutral w-24 font-mono uppercase"
            />
         </div>
      </div>

      {/* BLOOMBERG EQUITIES GRID */}
      <div className="flex-1 overflow-auto custom-scrollbar tabular-nums">
        <table className="w-full text-left border-collapse table-fixed">
          <thead className="sticky top-0 bg-surface-1 z-10 border-b border-surface-4 shadow-sm">
            <tr>
              <th className="px-2 py-1 text-[10px] text-neutral font-bold uppercase w-20">TICKER</th>
              <th className="px-2 py-1 text-[10px] text-neutral font-bold uppercase w-48 truncate">SECURITY NAME</th>
              <th className="px-2 py-1 text-[10px] text-neutral font-bold uppercase text-right w-24">LAST PX</th>
              <th className="px-2 py-1 text-[10px] text-neutral font-bold uppercase text-right w-24">CHG %</th>
              <th className="px-2 py-1 text-[10px] text-neutral font-bold uppercase text-center w-28">SAT ALPHA</th>
              <th className="px-2 py-1 text-[10px] text-neutral font-bold uppercase text-right w-24">EXCH</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-4">
            <AnimatePresence mode="popLayout">
              {filteredEquities.map((e) => (
                <motion.tr 
                  key={e.ticker}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="hover:bg-surface-3 transition-colors cursor-pointer group h-5"
                >
                  <td className="px-2 py-0">
                    <span className="text-[11px] text-accent-primary font-bold uppercase">{e.ticker}</span>
                  </td>
                  <td className="px-2 py-0">
                    <span className="text-[11px] text-accent-primary/80 uppercase truncate block">{e.name}</span>
                  </td>
                  <td className="px-2 py-0 text-right">
                    <span className="text-[11px] text-accent-primary font-bold">{(e.price || 0).toFixed(2)}</span>
                  </td>
                  <td className="px-2 py-0 text-right">
                    <span className={`text-[11px] font-bold ${(e.change || 0) >= 0 ? 'text-bull' : 'text-bear'}`}>
                      {(e.change || 0) >= 0 ? '+' : ''}{(e.change || 0).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-2 py-0 text-center">
                     <span className={`text-[9px] px-1 py-0 uppercase ${
                        (e.sat_signal || 'NEUTRAL').toUpperCase() === 'BULLISH' ? 'bg-bull text-void' : 
                        (e.sat_signal || 'NEUTRAL').toUpperCase() === 'BEARISH' ? 'bg-bear text-void' : 
                        'text-neutral'
                     }`}>
                        {e.sat_signal || 'NEUTRAL'}
                     </span>
                  </td>
                  <td className="px-2 py-0 text-right">
                    <span className="text-[10px] text-neutral uppercase">{e.exchange}</span>
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      {/* EQUITIES FOOTER STATUS */}
      <div className="h-6 border-t border-surface-4 flex items-center justify-between px-2 bg-void shrink-0">
         <span className="text-[9px] text-neutral uppercase">LIVE EQTY FEED: <span className="text-bull">CONNECTED</span></span>
         <span className="text-[9px] text-neutral uppercase">ROWS: <span className="text-accent-primary">{filteredEquities.length}</span></span>
      </div>
    </div>
  );
};

export default GlobalEquitiesView;
