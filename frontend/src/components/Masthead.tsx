import React, { useState, useEffect } from 'react';
import { useSignalStore } from '../store';
import { Activity, Shield, Cpu, Globe, Zap, Clock } from 'lucide-react';

const Masthead = () => {
  const [time, setTime] = useState(new Date());
  const { indices } = useSignalStore();

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const systemStatus = [
    { label: 'ORBITAL', val: 'SYNC', color: 'text-accent-primary' },
    { label: 'KERNEL', val: 'L7_ACTIVE', color: 'text-bull' },
    { label: 'LATENCY', val: '42ms', color: 'text-bull' },
    { label: 'LOAD', val: '12%', color: 'text-bull' },
  ];

  return (
    <header className="h-12 bg-slate-950 border-b border-white/5 flex items-center px-6 shrink-0 relative z-50">
      {/* BRANDING */}
      <div className="flex items-center gap-4 mr-8">
        <div className="flex items-baseline gap-1">
          <span className="font-display text-2xl text-accent-primary tracking-tighter">SAT</span>
          <span className="font-display text-2xl text-white tracking-widest uppercase">TRADE</span>
        </div>
        <div className="h-6 w-px bg-white/10" />
        <div className="flex flex-col">
          <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-widest leading-none">PRIME_TERMINAL</span>
          <span className="text-[8px] font-mono text-accent-primary/60 uppercase leading-none mt-1">v3.1.0 // MULTI-AGENT</span>
        </div>
      </div>

      {/* SYSTEM STATUS LEDS */}
      <div className="flex items-center gap-6 border-l border-white/5 pl-8">
        {systemStatus.map((s) => (
          <div key={s.label} className="flex flex-col">
            <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">{s.label}</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div className={`w-1 h-1 rounded-full bg-current ${s.color} animate-pulse shadow-[0_0_8px_currentColor]`} />
              <span className={`text-[10px] font-mono font-black uppercase tracking-tighter ${s.color}`}>{s.val}</span>
            </div>
          </div>
        ))}
      </div>

      {/* TICKER STRIP */}
      <div className="flex-1 mx-12 overflow-hidden relative">
        <div className="absolute inset-y-0 left-0 w-8 bg-gradient-to-r from-slate-950 to-transparent z-10" />
        <div className="absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-slate-950 to-transparent z-10" />
        
        <div className="flex gap-12 whitespace-nowrap items-center h-full animate-marquee hover:[animation-play-state:paused]">
          {[...indices, ...indices].map((idx, i) => (
            <div key={i} className="flex items-center gap-2 cursor-pointer hover:bg-white/5 px-2 py-1 transition-colors">
              <span className="text-[10px] text-slate-400 font-bold tracking-tight">{idx.name}</span>
              <span className="text-[11px] text-white font-mono font-bold">{idx.value}</span>
              <span className={`text-[10px] font-mono font-bold ${idx.status === 'bullish' ? 'text-bull' : 'text-bear'}`}>
                {idx.change}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* TIME & USER */}
      <div className="flex items-center gap-6 border-l border-white/5 pl-8">
        <div className="flex flex-col items-end">
          <span className="text-[11px] text-white font-mono font-bold leading-none">
            {time.toLocaleTimeString('en-US', { hour12: false })}
          </span>
          <span className="text-[8px] text-slate-500 font-bold uppercase mt-1 tracking-widest">
            {time.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })} UTC
          </span>
        </div>
        <div className="flex items-center gap-3 bg-white/5 px-3 py-1.5 border border-white/10 rounded-sm">
          <div className="w-5 h-5 bg-accent-primary text-slate-950 rounded-full flex items-center justify-center text-[10px] font-black">OP</div>
          <span className="text-[10px] font-bold text-white uppercase tracking-widest">Surgical-Ops</span>
        </div>
      </div>

      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation: marquee 60s linear infinite;
        }
      `}</style>
    </header>
  );
};

export default Masthead;
