import React, { useState, useEffect } from 'react';
import { executeCommand } from '../lib/commandEngine';
import { useSignalStore } from '../store';

const Masthead = () => {
  const [time, setTime] = useState(new Date());
  const { indices } = useSignalStore();

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

  const agents = [
    { name: 'ALPHA', status: 'optimal', color: 'bg-bull' },
    { name: 'RISK', status: 'optimal', color: 'bg-bull' },
    { name: 'MACRO', status: 'syncing', color: 'bg-[#00C8FF]' },
    { name: 'MARITIME', status: 'optimal', color: 'bg-bull' },
    { name: 'INGEST', status: 'optimal', color: 'bg-bull' },
  ];

  return (
    <header className="h-12 bg-void border-b border-accent-primary/20 flex items-center px-4 shrink-0 relative z-floating overflow-hidden">
      {/* Surgical top light leak */}
      <div className="absolute top-0 left-0 right-0 h-[8px] bg-gradient-to-b from-accent-primary/10 to-transparent opacity-50"></div>

      {/* LEFT SECTION: WORDMARK */}
      <div className="w-[180px] flex items-center shrink-0">
        <div className="flex items-baseline">
          <span className="text-[14px] font-bold text-accent-primary tracking-widest">SAT</span>
          <span className="text-[14px] font-bold text-text-1 tracking-widest uppercase ml-0.5">TRADE</span>
        </div>
        <div className="h-5 w-[1px] bg-white/10 mx-3"></div>
        <div className="flex flex-col">
          <span className="text-[9px] text-text-4 tracking-[0.3em] font-bold uppercase underline decoration-accent-primary/50 underline-offset-4">TERMINAL</span>
        </div>
      </div>
      
      {/* Search Input (BLOOMBERG STYLE) */}
      <div className="flex-[0.4] min-w-[300px] ml-4">
         <div className="flex items-center bg-surface-1 border border-white/10 px-3 py-1 hover:border-accent-primary transition-all rounded-sm group shadow-inner relative">
            <span className="text-accent-primary font-bold text-[12px] mr-2"> {`>`} </span>
            <input 
               type="text" 
               onKeyDown={handleKeyDown}
               placeholder="CLAUDE 4.6 INTENT ROUTING ACTIVE..."
               className="bg-transparent w-full text-[12px] text-text-1 placeholder:text-text-4 outline-none font-mono tracking-widest"
            />
            {/* AI Sparkle Icon */}
            <div className="absolute right-2 text-accent-primary animate-pulse type-data-xs opacity-50 font-bold">AI</div>
         </div>
      </div>

      {/* AGENT HEALTH LEDs */}
      <div className="flex items-center gap-3 px-6 shrink-0 border-l border-white/10 ml-6">
        {agents.map(a => (
          <div key={a.name} className="flex items-center gap-1.5 group cursor-help" title={`Agent: ${a.name} | Status: ${a.status}`}>
            <div className={`w-1.5 h-1.5 rounded-full ${a.color} shadow-[0_0_5px_currentColor] ${a.status === 'syncing' ? 'animate-pulse' : ''}`}></div>
            <span className="text-[9px] text-text-4 font-bold tracking-widest">{a.name}</span>
          </div>
        ))}
      </div>

      {/* CENTRE SECTION: GLOBAL INDICES (SCROLLABLE STRIP) */}
      <div className="flex-1 overflow-hidden relative mx-6 flex items-center border-l border-white/10 pl-4">
         <div className="flex gap-8 whitespace-nowrap items-center animate-ticker-slow">
            {indices.map((idx) => (
               <div key={idx.id} className="flex items-center gap-2 group cursor-pointer hover:bg-white/5 px-2 py-1 rounded transition-colors shrink-0">
                  <span className="text-[10px] text-text-4 group-hover:text-accent-primary transition-colors font-bold">{idx.name}</span>
                  <span className="text-[11px] text-text-1 font-bold font-mono">{idx.value}</span>
                  <span className={`text-[10px] font-bold ${idx.status === 'bullish' ? 'text-bull' : 'text-bear'}`}>{idx.change}</span>
               </div>
            ))}
            {indices.map((idx) => (
               <div key={`${idx.id}-loop`} className="flex items-center gap-2 group cursor-pointer hover:bg-white/5 px-2 py-1 rounded transition-colors shrink-0">
                  <span className="text-[10px] text-text-4 group-hover:text-accent-primary transition-colors font-bold">{idx.name}</span>
                  <span className="text-[11px] text-text-1 font-bold font-mono">{idx.value}</span>
                  <span className={`text-[10px] font-bold ${idx.status === 'bullish' ? 'text-bull' : 'text-bear'}`}>{idx.change}</span>
               </div>
            ))}
         </div>
      </div>

      {/* RIGHT SECTION: CLOCK & USER */}
      <div className="flex items-center gap-4 shrink-0 pl-4 border-l border-white/10">
        <div className="flex flex-col items-end leading-none tabular-nums font-mono">
          <span className="text-[11px] text-text-1 font-bold">
            {time.toUTCString().split(' ')[4]}
          </span>
          <span className="text-[8px] text-text-4 tracking-widest mt-1 uppercase">
            {time.getUTCDate()} {time.toUTCString().split(' ')[2].toUpperCase()} {time.getUTCFullYear()} UTC
          </span>
        </div>

        <div className="flex items-center gap-2 bg-surface-2 px-2 py-1 border border-white/5 rounded-sm">
            <div className="w-6 h-6 rounded-sm bg-accent-primary flex items-center justify-center text-[10px] font-bold text-void">
              PP
            </div>
            <span className="text-[9px] font-bold text-text-3 tracking-tighter uppercase">Surgical-Ops</span>
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
