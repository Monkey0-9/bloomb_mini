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
    { name: 'HFT-CORE', status: 'optimal', color: 'bg-accent-primary' },
    { name: 'ALPHA', status: 'optimal', color: 'bg-bull' },
    { name: 'RISK', status: 'optimal', color: 'bg-bull' },
    { name: 'MACRO', status: 'syncing', color: 'bg-[#00C8FF]' },
    { name: 'MARITIME', status: 'optimal', color: 'bg-bull' },
    { name: 'INGEST', status: 'optimal', color: 'bg-bull' },
  ];

  return (
    <header className="h-10 bg-void border-b border-surface-4 flex items-center px-4 shrink-0 relative z-50 overflow-hidden text-accent-primary">
      {/* LEFT SECTION: WORDMARK */}
      <div className="w-[160px] flex items-center shrink-0">
        <div className="flex items-baseline">
          <span className="text-[13px] font-bold text-accent-primary tracking-widest">SAT</span>
          <span className="text-[13px] font-bold text-white tracking-widest uppercase ml-0.5">TRADE</span>
        </div>
        <div className="h-4 w-[1px] bg-[var(--border-subtle)] mx-3"></div>
        <div className="flex flex-col">
          <span className="text-[8px] text-[var(--text-tertiary)] tracking-[0.2em] font-bold uppercase">TERMINAL</span>
          <span className="text-[6px] text-accent-primary/40 tracking-[0.1em] font-bold uppercase">V3.0.0-PRIME [INSTITUTIONAL_ULTRA]</span>
        </div>
      </div>
      
      {/* Search Input (BLOOMBERG STYLE Ctrl+K) */}
      {/* Search Input (BLOOMBERG STYLE Ctrl+K) - Bug 5 Fix */}
      <div className="flex-[0.4] max-w-[400px] ml-4 bg-surface-1 border border-surface-5 flex items-center px-2 py-0.5 focus-within:border-accent-primary transition-colors overflow-hidden">
         <span className="text-accent-primary font-bold text-[11px] mr-2 flex-shrink-0"> {`>`} </span>
         <input 
            type="text" 
            onKeyDown={handleKeyDown}
            placeholder="EXECUTE DEPTH_COMMAND OR INTENT_ROUTING..."
            className="bg-transparent w-full text-[11px] text-accent-primary placeholder:text-neutral outline-none font-mono tracking-wide truncate"
         />
         <div className="ml-2 text-accent-primary bg-surface-3 text-[9px] font-bold px-1 border border-surface-5 flex-shrink-0">AI</div>
      </div>

      {/* AGENT HEALTH LEDs */}
      <div className="flex items-center gap-3 px-4 shrink-0 border-l border-[var(--border-subtle)] ml-4">
        {agents.map(a => (
          <div key={a.name} className="flex items-center gap-1.5 cursor-crosshair group" title={`${a.name}: ${a.status}`}>
            <div className={`w-1.5 h-1.5 rounded-none ${a.color} ${a.status === 'syncing' ? 'opacity-50' : 'shadow-[0_0_4px_currentColor]'}`}></div>
            <span className="text-[9px] text-[var(--text-secondary)] font-bold tracking-wider group-hover:text-[var(--text-primary)] transition-colors">{a.name}</span>
          </div>
        ))}
      </div>

      {/* CENTRE SECTION: GLOBAL INDICES (SCROLLABLE STRIP) */}
      <div className="flex-1 overflow-hidden relative mx-4 flex items-center border-l border-[var(--border-subtle)] pl-4">
         <div className="flex gap-6 whitespace-nowrap items-center animate-ticker-slow">
            {indices.map((idx) => (
               <div key={idx.id} className="flex items-center gap-2 cursor-pointer hover:bg-[var(--bg-hover)] px-1.5 py-0.5 transition-colors shrink-0">
                  <span className="text-[10px] text-[var(--text-secondary)] font-bold">{idx.name}</span>
                  <span className="text-[11px] text-[var(--text-primary)] font-bold font-mono">{idx.value}</span>
                  <span className={`text-[10px] font-bold font-mono ${idx.status === 'bullish' ? 'text-[var(--neon-bull)]' : 'text-[var(--neon-bear)]'}`}>{idx.change}</span>
               </div>
            ))}
            {indices.map((idx) => (
               <div key={`${idx.id}-loop`} className="flex items-center gap-2 cursor-pointer hover:bg-[var(--bg-hover)] px-1.5 py-0.5 transition-colors shrink-0">
                  <span className="text-[10px] text-[var(--text-secondary)] font-bold">{idx.name}</span>
                  <span className="text-[11px] text-[var(--text-primary)] font-bold font-mono">{idx.value}</span>
                  <span className={`text-[10px] font-bold font-mono ${idx.status === 'bullish' ? 'text-[var(--neon-bull)]' : 'text-[var(--neon-bear)]'}`}>{idx.change}</span>
               </div>
            ))}
         </div>
      </div>

      {/* RIGHT SECTION: CLOCK & USER */}
      <div className="flex items-center gap-4 shrink-0 pl-4 border-l border-surface-4 h-full">
        <div className="flex flex-col items-end leading-none font-mono text-accent-primary">
          <span className="text-[11px] font-bold">
            {time.toUTCString().split(' ')[4]}
          </span>
          <span className="text-[8px] text-accent-primary/80 tracking-widest mt-1 uppercase">
            {time.getUTCDate()} {time.toUTCString().split(' ')[2].toUpperCase()} {time.getUTCFullYear()} UTC
          </span>
        </div>

        <div className="flex items-center gap-2 bg-surface-1 px-2 py-0.5 border border-surface-5 h-full my-auto ml-2">
            <div className="w-4 h-4 bg-accent-primary flex items-center justify-center text-[9px] font-bold text-void">
              PP
            </div>
            <span className="text-[9px] font-bold text-accent-primary uppercase hover:text-white cursor-pointer select-none">Surgical-Ops</span>
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
