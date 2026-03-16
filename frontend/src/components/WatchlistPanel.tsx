import { useState } from 'react';
import { Plus } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTerminalStore, useSignalStore } from '../store';
import { useEquityStore } from '../store/equityStore';

const WatchlistRow = ({ ticker, name, price, change, signal, onRemove }: any) => {
  const isUp = change >= 0;
  const { setView, setCurrentTicker } = useTerminalStore();
  
  return (
    <div 
      className="h-10 border-b border-white/5 hover:bg-surface-2 transition-all cursor-pointer group flex items-center px-3 relative"
      onClick={() => {
        setCurrentTicker(`${ticker} US Equity`);
        setView('charts');
      }}
    >
      <div className="flex-1 min-w-0 pr-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="type-data-sm font-bold text-accent-primary tracking-tight group-hover:text-text-0 transition-colors">{ticker}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="type-data-sm text-text-0 font-mono tracking-tighter group-hover:text-accent-primary transition-colors">${(price || 0).toFixed(2)}</span>
          <span className={`type-data-xs font-mono font-bold w-12 text-right ${isUp ? 'text-bull' : 'text-bear'}`}>
            {isUp ? '+' : ''}{(change || 0).toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="w-24 flex items-center justify-end gap-2 shrink-0 border-l border-white/5 pl-2">
            <span className={`text-[9px] px-1 py-0.5 font-bold uppercase tracking-widest ${
              signal === 'STRONG' ? 'bg-bull/20 text-bull border-bull/30' : 
              signal === 'BULLISH' ? 'bg-bull/10 text-bull border-bull/20' : 
              signal === 'BEARISH' ? 'bg-bear/20 text-bear border-bear/30' : 
              'bg-surface-3 text-text-4 border-border-1'
            } border`}>
              {signal === 'STRONG' ? '↑ STRONG' : signal === 'BULLISH' ? '↑ LONG' : signal === 'BEARISH' ? '↓ SHORT' : '— FLAT'}
            </span>
            <button 
              onClick={(e) => { e.stopPropagation(); onRemove(ticker); }}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-text-5 hover:text-bear transition-all w-4 h-4 rounded hover:bg-bear/10 flex items-center justify-center"
            >
              ×
            </button>
      </div>
      <div className="absolute right-0 top-0 bottom-0 w-[2px] bg-accent-primary opacity-0 group-hover:opacity-100 transition-opacity"></div>
    </div>
  );
};

const WatchlistPanel = () => {
  const [isAdding, setIsAdding] = useState(false);
  const [newTicker, setNewTicker] = useState('');
  const { signals } = useSignalStore();
  const { equities, watchlist, addToWatchlist, removeFromWatchlist } = useEquityStore();

  const watchlistEquities = equities.filter(e => watchlist.includes(e.ticker));
  
  return (
    <div className="w-[300px] bg-surface-0 border-l border-border-1 flex flex-col shrink-0 font-sans z-10 shadow-[-10px_0_20px_rgba(0,0,0,0.5)]">
      
      {/* HEADER */}
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-3 shrink-0 bg-surface-base">
        <span className="type-h1 text-sm tracking-widest text-text-0 uppercase">Watchlist</span>
        {!isAdding ? (
          <button 
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-1.5 px-2 py-0.5 border border-border-3 bg-surface-1 type-ui-sm text-text-3 hover:border-accent-primary hover:text-accent-primary transition-colors group"
          >
            <Plus size={12} strokeWidth={3} className="group-hover:text-accent-primary text-text-5" />
            <span className="font-bold tracking-widest uppercase text-[9px]">Add</span>
          </button>
        ) : (
          <div className="flex gap-1 animate-in fade-in slide-in-from-right-2 duration-200">
             <input 
               autoFocus
               type="text"
               value={newTicker}
               onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
               onKeyDown={(e) => {
                 if (e.key === 'Enter') {
                   if (newTicker) addToWatchlist(newTicker);
                   setIsAdding(false);
                   setNewTicker('');
                 } else if (e.key === 'Escape') {
                   setIsAdding(false);
                 }
               }}
               className="w-24 bg-surface-2 border border-accent-primary/50 px-2 py-0.5 text-[10px] uppercase font-mono text-accent-primary outline-none"
               placeholder="TICKER"
             />
          </div>
        )}
      </div>

      {/* FILTER TABS */}
      <div className="h-8 border-b border-white/5 flex items-center px-1 shrink-0 bg-surface-1">
         <button className="text-[9px] font-bold tracking-[0.1em] uppercase text-text-0 border-b-2 border-accent-primary h-full px-3 transition-colors bg-surface-0">CORE</button>
         <button className="text-[9px] font-bold tracking-[0.1em] uppercase text-text-4 hover:text-text-0 hover:bg-surface-2 transition-colors h-full px-3">ALPHA</button>
         <button className="text-[9px] font-bold tracking-[0.1em] uppercase text-text-4 hover:text-text-0 hover:bg-surface-2 transition-colors h-full px-3">MOVERS</button>
      </div>

      {/* LIST HEADER */}
      <div className="h-6 border-b border-white/5 flex items-center justify-between px-3 shrink-0 bg-surface-0 shadow-sm">
          <span className="text-[8px] font-bold uppercase tracking-widest text-text-5 w-12">Ticker</span>
          <div className="flex gap-[34px] mr-12">
            <span className="text-[8px] font-bold uppercase tracking-widest text-text-5">Last</span>
            <span className="text-[8px] font-bold uppercase tracking-widest text-text-5">Chg %</span>
          </div>
          <span className="text-[8px] font-bold uppercase tracking-widest text-text-5 w-16 text-right">Inference</span>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar bg-void pt-1">
        {watchlistEquities.length > 0 ? (
          watchlistEquities.map((e: any, i) => (
            <motion.div
                initial={{ opacity: 0, x: 5 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                key={e.ticker}
            >
                <WatchlistRow 
                    ticker={e.ticker} 
                    name={e.name} 
                    price={e.price} 
                    change={e.change} 
                    onRemove={removeFromWatchlist}
                    signal={signals.find(s => (s.tickers || []).includes(e.ticker))?.status.toUpperCase() || e.sat_signal} 
                />
            </motion.div>
          ))
        ) : (
          <div className="p-8 text-center text-[10px] text-text-5 font-mono uppercase tracking-widest">AWAITING INPUT</div>
        )}
      </div>

      {/* FOOTER ACTION */}
      <div className="h-9 border-t border-border-1 bg-surface-base shrink-0 flex items-center justify-center cursor-pointer hover:bg-surface-2 transition-colors border-x-0 border-b-0 outline-none group px-4">
        <span className="text-[10px] text-text-4 uppercase tracking-[0.2em] font-bold group-hover:text-accent-primary transition-colors flex items-center gap-2">
           <div className="w-1.5 h-1.5 bg-accent-primary rounded-[1px] opacity-50 group-hover:opacity-100 group-hover:animate-pulse"></div>
           CONFIGURE ALERT WEBHOOKS
        </span>
      </div>
    </div>
  );
};

export default WatchlistPanel;
