import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useTerminalStore, useSignalStore } from '../store';
import { useEquityStore } from '../store/equityStore';

const WatchlistRow = ({ ticker, price, change, signal, onRemove }: any) => {
  const isUp = change >= 0;
  const { setView, setCurrentTicker } = useTerminalStore();
  
  return (
    <div 
      className="h-8 border-b border-[var(--border-subtle)] hover:bg-[var(--bg-hover)] transition-all cursor-crosshair group flex items-center px-2 relative"
      onClick={() => {
        setCurrentTicker(`${ticker} US Equity`);
        setView('charts');
      }}
    >
      <div className="flex-1 min-w-0 flex items-center justify-between mr-2">
        <span className="text-[11px] font-bold text-[var(--neon-bull)] tracking-tight font-mono">{ticker}</span>
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-[var(--text-primary)] font-mono tracking-tighter group-hover:text-[var(--neon-signal)] transition-colors">${(price || 0).toFixed(2)}</span>
          <span className={`text-[10px] font-mono font-bold w-12 text-right ${isUp ? 'text-[var(--neon-bull)]' : 'text-[var(--neon-bear)]'}`}>
            {isUp ? '+' : ''}{(change || 0).toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="w-20 flex items-center justify-end gap-2 shrink-0 border-l border-[var(--border-subtle)] pl-2">
            <span className={`text-[9px] px-1 font-bold uppercase tracking-widest leading-none flex items-center h-5 border ${
              signal === 'STRONG' ? 'bg-[var(--neon-dim-bull)] text-[var(--neon-bull)] border-[var(--neon-bull)]' : 
              signal === 'BULLISH' ? 'bg-[var(--neon-dim-bull)] text-[var(--neon-bull)] border-[var(--neon-bull)]/50' : 
              signal === 'BEARISH' ? 'bg-[var(--neon-dim-bear)] text-[var(--neon-bear)] border-[var(--neon-bear)]' : 
              'bg-[var(--bg-card)] text-[var(--text-tertiary)] border-[var(--border-subtle)]'
            }`}>
              {signal === 'STRONG' ? '↑ STRONG' : signal === 'BULLISH' ? '↑ LONG' : signal === 'BEARISH' ? '↓ SHORT' : '— FLAT'}
            </span>
            <button 
              onClick={(e) => { e.stopPropagation(); onRemove(ticker); }}
              className="opacity-0 group-hover:opacity-100 text-[var(--text-tertiary)] hover:text-[var(--neon-bear)] transition-all"
            >
              ×
            </button>
      </div>
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
    <div className="flex flex-col h-full bg-[var(--bg-base)] overflow-hidden">
      
      {/* HEADER */}
      <div className="h-8 border-b border-[var(--border-subtle)] flex items-center justify-between px-3 shrink-0 bg-[var(--bg-surface)]">
        <span className="text-[10px] tracking-widest text-[var(--text-primary)] font-bold uppercase">Watchlist</span>
        {!isAdding ? (
          <button 
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-1.5 px-2 py-0.5 border border-[var(--border-subtle)] bg-[var(--bg-base)] hover:border-[var(--neon-signal)] transition-colors group"
          >
            <Plus size={10} className="text-[var(--text-tertiary)] group-hover:text-[var(--neon-signal)]" />
            <span className="font-bold tracking-widest uppercase text-[8px] text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">Add</span>
          </button>
        ) : (
          <div className="flex gap-1">
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
               className="w-20 bg-[var(--bg-base)] border border-[var(--neon-signal)] px-2 py-0.5 text-[10px] uppercase font-mono text-[var(--neon-signal)] outline-none"
               placeholder="TICKER"
             />
          </div>
        )}
      </div>

      {/* LIST HEADER */}
      <div className="h-6 border-b border-[var(--border-subtle)] flex items-center px-3 shrink-0 bg-[var(--bg-surface)]">
          <span className="text-[8px] font-bold uppercase tracking-widest text-[var(--text-tertiary)] w-14">Ticker</span>
          <div className="flex-1 flex justify-center gap-10">
            <span className="text-[8px] font-bold uppercase tracking-widest text-[var(--text-tertiary)]">Price</span>
            <span className="text-[8px] font-bold uppercase tracking-widest text-[var(--text-tertiary)]">Change</span>
          </div>
          <span className="text-[8px] font-bold uppercase tracking-widest text-[var(--text-tertiary)] w-16 text-right mr-6">Alpha</span>
      </div>

      <div className="flex-1 overflow-y-auto bg-[var(--bg-base)]">
        {watchlistEquities.length > 0 ? (
          watchlistEquities.map((e: any) => (
            <WatchlistRow 
              key={e.ticker}
              ticker={e.ticker}
              price={e.price}
              change={e.change}
              onRemove={removeFromWatchlist}
              signal={signals.find(s => (s.tickers || []).includes(e.ticker))?.status.toUpperCase() || e.sat_signal} 
            />
          ))
        ) : (
          <div className="p-8 text-center text-[9px] text-[var(--text-tertiary)] font-mono uppercase tracking-widest">Awaiting Selections</div>
        )}
      </div>

      {/* FOOTER ACTION */}
      <div className="h-8 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] shrink-0 flex items-center justify-center cursor-pointer hover:bg-[var(--bg-hover)] transition-colors group">
        <span className="text-[9px] text-[var(--text-secondary)] uppercase tracking-[0.1em] font-bold group-hover:text-[var(--text-primary)] transition-colors flex items-center gap-2">
           <div className="w-1.5 h-1.5 bg-[var(--neon-bull)] shadow-[0_0_4px_var(--neon-bull)]"></div>
           Configure Alert Webhooks
        </span>
      </div>
    </div>
  );
};

export default WatchlistPanel;
