import { useMemo, useState } from 'react';
import { useTerminalStore } from '../store';
import { motion, AnimatePresence } from 'framer-motion';

const GlobalEquitiesView = () => {
  const { signals } = useTerminalStore();
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  const filteredSignals = useMemo(() => {
    return signals.filter(s => {
      const matchesSearch = s.ticker.toLowerCase().includes(search.toLowerCase()) || 
                            s.name.toLowerCase().includes(search.toLowerCase());
      const matchesFilter = filter === 'ALL' || s.status.toUpperCase() === filter;
      return matchesSearch && matchesFilter;
    });
  }, [signals, search, filter]);

  return (
    <div className="flex-1 flex flex-col bg-surface-0 overflow-hidden">
      {/* EQUITIES HEADER: ALLX STYLE */}
      <div className="h-11 border-b border-white/5 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
               <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">GLOBAL EQUITIES</span>
            </div>
            <div className="h-6 w-[1px] bg-white/5 mx-2"></div>
            <div className="flex gap-2">
               {['ALL', 'BULLISH', 'BEARISH'].map(f => (
                  <button 
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`type-data-xs px-3 py-1 rounded-sm border transition-all ${
                       filter === f ? 'bg-accent-primary border-accent-primary text-void font-bold shadow-glow-bull' : 'border-white/10 text-text-4 hover:border-text-2'
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
               placeholder="FILTER BY TICKER..." 
               value={search}
               onChange={(e) => setSearch(e.target.value)}
               className="bg-transparent outline-none type-data-xs text-text-1 placeholder:text-text-5 w-40"
            />
         </div>
      </div>

      {/* EQUITIES GRID */}
      <div className="flex-1 overflow-auto custom-scrollbar tabular-nums">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-surface-1 z-10 border-b border-white/10">
            <tr>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest">Ticker</th>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest">Name</th>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest text-right">Price</th>
              <th className="px-6 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest text-right">Change</th>
              <th className="px-4 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest text-center">Sat Intel</th>
              <th className="px-8 py-3 type-data-xs text-text-3 font-bold uppercase tracking-widest text-right">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            <AnimatePresence>
              {filteredSignals.map((s) => (
                <motion.tr 
                  key={s.id}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="hover:bg-white/5 transition-colors cursor-pointer group h-14"
                >
                  <td className="px-6 py-3">
                    <span className="type-data-md text-accent-primary font-bold group-hover:text-text-0 transition-colors uppercase">{s.ticker}</span>
                  </td>
                  <td className="px-6 py-3">
                    <span className="type-data-xs text-text-2 uppercase group-hover:text-text-1 truncate max-w-[200px] inline-block">{s.name}</span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span className="type-data-md text-text-1 font-bold">128.40</span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span className={`type-data-xs font-bold ${s.status === 'bullish' ? 'text-bull' : 'text-bear'}`}>
                      {s.status === 'bullish' ? '+1.86%' : '-2.11%'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center">
                       <span className={`type-data-xs px-2 py-0.5 rounded-sm border font-bold tracking-widest text-[9px] ${
                          s.status === 'bullish' ? 'bg-bull/10 border-bull/50 text-bull' : 'bg-bear/10 border-bear/50 text-bear'
                       }`}>
                          {s.status.toUpperCase()} SIGNAL
                       </span>
                    </div>
                  </td>
                  <td className="px-8 py-3 text-right">
                     <div className="flex items-center justify-end gap-3 w-32 ml-auto">
                        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                           <div className={`h-full ${s.status === 'bullish' ? 'bg-[#00C8FF] shadow-[0_0_8px_rgba(0,200,255,0.5)]' : 'bg-bear shadow-[0_0_8px_rgba(255,59,48,0.5)]'}`} style={{ width: `${s.score}%` }}></div>
                        </div>
                        <span className="type-data-xs text-text-4 font-bold w-6">{s.score}</span>
                     </div>
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      {/* EQUITIES FOOTER STATUS */}
      <div className="h-8 border-t border-white/10 flex items-center justify-between px-4 bg-void shrink-0">
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Universe: <span className="text-text-1">100 Monitored Entities</span></span>
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Filter: <span className="text-accent-primary">{filter}</span></span>
      </div>
    </div>
  );
};

export default GlobalEquitiesView;
