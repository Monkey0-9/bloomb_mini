import { Plus } from 'lucide-react';
import { motion } from 'framer-motion';

const WatchlistRow = ({ ticker, name, price, change, signal }: any) => {
  const isUp = change >= 0;
  
  return (
    <div className="h-[60px] border-b border-border-0 hover:bg-surface-2 transition-all cursor-pointer group flex items-center px-3 relative">
      <div className="flex-1 min-w-0 pr-4">
        <div className="flex items-baseline gap-2 mb-0.5">
          <span className="type-data-md font-bold text-accent-primary group-hover:text-text-0 tracking-tight uppercase">{ticker}</span>
          <span className="type-ui-sm text-text-4 truncate max-w-[120px] uppercase tracking-tighter group-hover:text-text-3">{name}</span>
        </div>
        <div className="flex items-baseline gap-2 leading-none">
          <span className="type-data-md text-text-1">${price.toFixed(2)}</span>
          <span className={`type-data-xs font-medium ${isUp ? 'text-text-bull' : 'text-text-bear'}`}>
            {isUp ? '+' : ''}{change.toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="w-[100px] flex flex-col items-end gap-1.5">
        <span className={`type-data-xs px-2 py-0.5 rounded-[2px] font-bold border tracking-[0.05em] shadow-sm ${
          signal === 'STRONG' ? 'bg-bull-08 text-bull border-bull-60 shadow-glow-bull' : 
          signal === 'BULLISH' ? 'bg-bull-08 text-bull border-bull-20' : 
          signal === 'BEARISH' ? 'bg-bear-08 text-bear border-bear-60' : 
          'bg-surface-3 text-text-4 border-border-1'
        }`}>
          {signal === 'STRONG' ? '↑↑ STRONG' : signal === 'BULLISH' ? '↑ MEDIUM' : signal === 'BEARISH' ? '↓↓ STRONG' : '— NO DATA'}
        </span>

        {/* MICRO SPARKLINE */}
        <div className="w-full h-4 overflow-hidden flex items-end gap-[1.5px] opacity-40 group-hover:opacity-100 transition-all duration-300">
          {Array.from({ length: 15 }).map((_, i) => (
            <div 
              key={i} 
              className={`flex-1 rounded-[0.5px] ${isUp ? 'bg-bull' : 'bg-bear'}`} 
              style={{ height: `${20 + Math.random() * 80}%` }}
            ></div>
          ))}
        </div>
      </div>

      {/* Tooltip hint appearing on right - implied by specification */}
      <div className="absolute right-0 top-0 bottom-0 w-[2px] bg-accent-primary opacity-0 group-hover:opacity-100 transition-opacity"></div>
    </div>
  );
};

const WatchlistPanel = () => {
  return (
    <div className="w-[280px] bg-surface-0 border-l border-border-1 flex flex-col shrink-0">
      {/* PANEL HEADER */}
      <div className="h-11 border-b border-border-subtle flex items-center justify-between px-4 shrink-0 bg-surface-0/80 backdrop-blur-sm">
        <span className="type-h1 text-sm tracking-widest text-text-1">WATCHLIST</span>
        <button className="flex items-center gap-1.5 px-2 py-1 border border-border-3 rounded-sm type-ui-sm text-text-3 hover:border-accent-primary hover:text-accent-primary transition-all">
          <Plus size={14} strokeWidth={2.5} />
          <span className="font-bold tracking-widest uppercase text-[10px]">Add</span>
        </button>
      </div>

      {/* TABS ROW */}
      <div className="h-8 border-b border-border-ghost flex items-center px-4 gap-6 shrink-0 bg-void/20">
         <button className="type-ui-sm font-bold tracking-[0.08em] uppercase text-text-1 border-b-2 border-accent-primary h-full px-1">My List</button>
         <button className="type-ui-sm font-bold tracking-[0.08em] uppercase text-text-4 hover:text-text-2 transition-colors">Top Signals</button>
         <button className="type-ui-sm font-bold tracking-[0.08em] uppercase text-text-4 hover:text-text-2 transition-colors">Movers</button>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar bg-surface-0">
        <WatchlistRow ticker="AMKBY" name="AP Møller-Maersk" price={128.40} change={1.86} signal="STRONG" />
        <WatchlistRow ticker="ZIM" name="ZIM Integrated" price={14.22} change={0.94} signal="BULLISH" />
        <WatchlistRow ticker="TGT" name="Target Corp" price={142.10} change={-0.33} signal="BEARISH" />
        <WatchlistRow ticker="MATX" name="Matson Inc" price={88.24} change={0.12} signal="BULLISH" />
        <WatchlistRow ticker="WMT" name="Walmart Inc" price={158.30} change={1.22} signal="STRONG" />
        <WatchlistRow ticker="HLAG" name="Hapag-Lloyd" price={165.40} change={0.45} signal="BULLISH" />
        <WatchlistRow ticker="FDX" name="FedEx Corp" price={245.12} change={-1.12} signal="BEARISH" />
        <WatchlistRow ticker="UPS" name="United Parcel Service" price={143.25} change={-0.44} signal="BEARISH" />
        <WatchlistRow ticker="COST" name="Costco Wholesale" price={724.11} change={0.88} signal="BULLISH" />
      </div>

      {/* ALERT CONFIGURE */}
      <div className="p-sp-3 border-t border-border-subtle bg-void/40 shrink-0">
        <button className="w-full py-2 rounded-sm bg-surface-2 border border-border-2 type-data-xs text-text-3 hover:text-text-1 hover:border-accent-primary transition-all uppercase tracking-[0.15em] font-medium shadow-sm active:scale-[0.98]">
          Configure Alert Hub
        </button>
      </div>
    </div>
  );
};

export default WatchlistPanel;
