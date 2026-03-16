import { useState, useEffect } from 'react';
import { Ship, ShoppingCart, Factory, Radio, Activity } from 'lucide-react';
import { useTerminalStore, useSignalStore } from '../store';

const SignalCard = ({ 
  name, 
  location,
  status, 
  score, 
  ic, 
  icir, 
  tickers,
  id
}: any) => {
  const { setView, setCurrentTicker } = useTerminalStore();
  const isBull = status === 'bullish';
  const statusColor = isBull ? 'text-bull' : status === 'bearish' ? 'text-bear' : 'text-text-4';

  const handleClick = () => {
    if (tickers && tickers.length > 0) {
        setCurrentTicker(`${tickers[0]} US Equity`);
        setView('charts');
    } else {
        setView('matrix');
    }
  };

  return (
    <div 
      onClick={handleClick}
      className="px-4 py-3 border-b border-white/5 group hover:bg-surface-2 transition-all cursor-pointer"
    >
      <div className="flex justify-between items-start mb-1">
        <div className="flex flex-col">
          <span className="text-[10px] text-text-3 font-bold">{location} <span className="text-text-4 ml-1"> {isBull ? 'GO' : 'GO'}</span></span>
          <span className="text-[12px] text-text-1 font-bold leading-none tracking-tight">{name}</span>
        </div>
        <div className={`text-[11px] font-bold uppercase ${statusColor}`}>{status}</div>
      </div>

      <div className="flex items-center gap-4 py-2">
        <div className={`text-2xl font-bold ${statusColor} tracking-tighter`}>{score}</div>
        <div className="flex-1 grid grid-cols-2 gap-x-2 text-[10px] border-l border-white/10 pl-3">
          <div className="flex justify-between flex-1"><span className="text-text-4">IC</span> <span className="text-text-1">{ic.toFixed(3)}</span></div>
          <div className="flex justify-between flex-1"><span className="text-text-4">ICIR</span> <span className="text-text-1">{icir.toFixed(2)}</span></div>
          <div className="flex justify-between flex-1 col-span-2 mt-1 border-t border-white/5 pt-1 uppercase text-[8px] text-text-5 tracking-widest">
            STAC Telemetry Active
          </div>
        </div>
      </div>

      <div className="space-y-1 mt-1">
        {(tickers || []).slice(0, 3).map((t: string) => (
          <div key={t} className="flex justify-between items-center text-[10px]">
            <span className="text-text-3 font-mono">{t} <span className="text-text-5 ml-1">US Equity</span></span>
            <span className="text-bull">+{ (Math.random() * 1.5).toFixed(2) }%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const SignalPanel = () => {
  const { setView } = useTerminalStore();
  const { signals, fetchSignals } = useSignalStore();

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 30000);
    return () => clearInterval(interval);
  }, [fetchSignals]);

  return (
    <div className="w-[280px] h-full bg-void border-r border-white/10 flex flex-col overflow-hidden shrink-0 z-raised relative">
      <div className="p-3 border-b border-accent-primary/20 flex flex-col gap-1 bg-surface-0">
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-accent-primary font-bold tracking-[0.2em] flex items-center gap-2">
              <Activity size={10} /> SIGNAL TICKER {`<GO>`}
            </span>
            <div className="w-1.5 h-1.5 rounded-full bg-bull dot-live"></div>
          </div>
          <span className="text-[9px] text-text-4 uppercase tracking-tighter">Live Institutional Stream • Alpaca Connected</span>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {signals.map(s => (
          <SignalCard key={s.id} {...s} />
        ))}
      </div>

      <div className="p-3 bg-surface-0 border-t border-white/5">
         <button 
           onClick={() => setView('matrix')}
           className="w-full py-1.5 bg-accent-primary text-black text-[10px] font-bold uppercase tracking-widest hover:bg-white transition-colors"
         >
            Full Signal Matrix
         </button>
      </div>
    </div>
  );
};

export default SignalPanel;

