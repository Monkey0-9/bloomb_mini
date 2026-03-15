import React, { useState, useEffect } from 'react';
import { executeCommand } from '../lib/commandEngine';
import { useTerminalStore, MarketIndex } from '../store';

const Masthead = () => {
  const [time, setTime] = useState(new Date());
  const { indices } = useTerminalStore();

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      executeCommand(e.currentTarget.value);
      e.currentTarget.value = '';
    }
  };

  return (
    <header className="h-12 bg-void border-b border-white/10 flex items-center px-4 shrink-0 relative z-floating overflow-hidden">
      {/* Surgical top light leak */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-accent-primary/40 to-transparent"></div>

      {/* LEFT SECTION: WORDMARK */}
      <div className="w-[200px] flex items-center shrink-0">
        <div className="flex items-baseline">
          <span className="type-h1 text-accent-primary tracking-widest">SAT</span>
          <span className="type-h1 text-text-1 tracking-widest uppercase">TRADE</span>
        </div>
        <div className="h-5 w-[1px] bg-border-3 mx-3"></div>
        <div className="flex flex-col">
          <span className="type-data-xs text-text-4 tracking-[0.25em] -mb-0.5 uppercase">TERMINAL</span>
        </div>
      </div>
      
      {/* CENTRE SECTION: GLOBAL INDICES (SCROLLABLE STRIP) */}
      <div className="flex-1 overflow-hidden relative mx-6 flex items-center">
         <div className="absolute inset-y-0 left-0 w-8 bg-gradient-to-r from-void to-transparent z-10"></div>
         <div className="absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-void to-transparent z-10"></div>
         
         <div className="flex gap-8 whitespace-nowrap items-center animate-ticker-slow">
            {indices.map((idx) => (
               <div key={idx.id} className="flex items-center gap-2 group cursor-pointer hover:bg-white/5 px-2 py-1 rounded transition-colors shrink-0">
                  <span className="type-data-xs text-text-4 group-hover:text-accent-primary transition-colors">{idx.name}</span>
                  <span className="type-data-md text-text-1 font-bold">{idx.value}</span>
                  <span className={`type-data-xs font-bold ${idx.status === 'bullish' ? 'text-bull' : 'text-bear'}`}>{idx.change}</span>
               </div>
            ))}
            {/* Loop for seamless scroll */}
            {indices.slice(0, 10).map((idx) => (
               <div key={`${idx.id}-loop`} className="flex items-center gap-2 group cursor-pointer hover:bg-white/5 px-2 py-1 rounded transition-colors shrink-0">
                  <span className="type-data-xs text-text-4 group-hover:text-accent-primary transition-colors">{idx.name}</span>
                  <span className="type-data-md text-text-1 font-bold">{idx.value}</span>
                  <span className={`type-data-xs font-bold ${idx.status === 'bullish' ? 'text-bull' : 'text-bear'}`}>{idx.change}</span>
               </div>
            ))}
         </div>
      </div>

      {/* SEARCH BOX (BLOOMBERG STYLE) */}
      <div className="w-[300px] px-2">
         <div className="flex items-center bg-surface-1 border border-white/5 px-3 py-1 hover:border-accent-primary transition-all rounded-sm group">
            <span className="text-accent-primary opacity-50 font-bold type-data-md mr-2">&gt;</span>
            <input 
               type="text" 
               onKeyDown={handleKeyDown}
               placeholder="NAVIGATE: AAPL, RTX, CRYPTO"
               className="bg-transparent w-full type-data-md text-text-1 placeholder:text-text-4 outline-none"
            />
         </div>
      </div>

      {/* RIGHT SECTION: CLOCK & USER */}
      <div className="flex items-center gap-6 shrink-0 pl-4 border-l border-white/5 ml-4">
        <div className="flex flex-col items-end leading-none tabular-nums">
          <span className="type-data-md text-text-0 font-bold tracking-tight">
            {time.toUTCString().split(' ')[4]}
          </span>
          <span className="type-data-xs text-text-3 tracking-widest mt-1 opacity-60">
            {time.getUTCDate()} {time.toUTCString().split(' ')[2].toUpperCase()} {time.getUTCFullYear()} UTC
          </span>
        </div>

        <div className="relative group cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-surface-3 border border-white/10 flex items-center justify-center type-ui-body text-text-2 group-hover:border-accent-primary transition-all">
              PP
            </div>
            <div className="absolute -top-1 -right-1 px-1 bg-accent-primary text-[8px] font-bold text-void rounded-sm tracking-tighter">INST</div>
        </div>
      </div>

      <style>{`
        @keyframes ticker-scroll {
           0% { transform: translateX(0); }
           100% { transform: translateX(-50%); }
        }
        .animate-ticker-slow {
           animation: ticker-scroll 60s linear infinite;
        }
        .animate-ticker-slow:hover {
           animation-play-state: paused;
        }
      `}</style>
    </header>
  );
};

export default Masthead;
