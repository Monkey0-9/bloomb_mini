import React from 'react';
import * as Lucide from 'lucide-react';
import { useTerminalStore } from '../store';

const Activity = Lucide.Activity || Lucide.Zap;

const IntelligenceDetails: React.FC = () => {
  const { X, ExternalLink, MapPin, Clock, Info, AlertCircle, Shield, Plane, Ship, Flame, Target, MessageSquare } = Lucide;
  const { selectedIntelligenceEvent, setSelectedIntelligenceEvent } = useTerminalStore();

  if (!selectedIntelligenceEvent) return null;

  const ev = selectedIntelligenceEvent;

  return (
    <div className="fixed inset-y-0 right-0 w-[500px] bg-slate-950/95 backdrop-blur-3xl border-l border-white/10 z-[300] shadow-[-40px_0_100px_rgba(0,0,0,0.8)] flex flex-col font-mono animate-slide-in">
      <header className="h-20 border-b border-white/10 flex items-center justify-between px-8 bg-slate-900/40 relative overflow-hidden shrink-0">
        <div className="absolute inset-0 bg-gradient-to-r from-accent-primary/5 to-transparent pointer-events-none" />
        
        <div className="flex items-center gap-5 relative">
          <div className={`p-3 rounded-sm bg-white/5 border border-white/10 shadow-inner`}>
            {ev.type === 'THERMAL' && <Flame size={24} className="text-orange-500 shadow-glow-orange" />}
            {ev.type === 'AIRCRAFT' && <Plane size={24} className="text-sky-400 shadow-glow-sky" />}
            {ev.type === 'VESSEL' && <Ship size={24} className="text-bull shadow-glow-bull" />}
            {ev.type === 'CONFLICT' && <Shield size={24} className="text-bear shadow-glow-bear" />}
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-500 uppercase tracking-[0.4em] font-black">Intelligence_Node</span>
            <span className="font-display text-2xl text-white tracking-widest">{ev.type} ANALYTICS</span>
          </div>
        </div>
        
        <button 
          onClick={() => setSelectedIntelligenceEvent(null)}
          className="p-2.5 bg-white/5 border border-white/10 hover:bg-white/10 rounded-sm transition-all text-slate-400 hover:text-white group"
        >
          <X size={20} className="group-hover:rotate-90 transition-transform duration-300" />
        </button>
      </header>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-10 space-y-12 relative">
        <div className="absolute top-0 right-0 p-4 opacity-[0.03] pointer-events-none">
           <Lucide.Satellite size={200} />
        </div>

        <section className="space-y-6 relative">
          <div className="flex justify-between items-start gap-6">
            <h2 className="text-2xl font-bold text-white leading-tight font-sans tracking-tight">{ev.title}</h2>
            <div className={`px-3 py-1 rounded-sm text-[10px] font-black tracking-[0.2em] border shadow-2xl ${
              ev.severity === 'CRITICAL' || ev.severity === 'HIGH' ? 'bg-bear/10 text-bear border-bear/30 shadow-glow-bear' : 'bg-accent-primary/10 text-accent-primary border-accent-primary/30 shadow-glow-sky'
            }`}>
              {ev.severity}
            </div>
          </div>
          
          <div className="flex flex-wrap gap-6 border-y border-white/5 py-6">
            <div className="flex items-center gap-3">
              <MapPin size={14} className="text-accent-primary" /> 
              <span className="text-[11px] text-slate-300 uppercase tracking-widest font-bold">{ev.location}</span>
            </div>
            <div className="h-4 w-px bg-white/10" />
            <div className="flex items-center gap-3">
              <Clock size={14} className="text-accent-primary" /> 
              <span className="text-[11px] text-slate-300 uppercase tracking-widest font-bold font-mono">{ev.time} UTC</span>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-2 gap-4">
          <button className="flex items-center justify-center gap-3 py-4 bg-accent-primary text-slate-950 font-display text-lg tracking-[0.2em] rounded-sm hover:bg-white transition-all shadow-glow-sky group">
            <ExternalLink size={18} className="group-hover:scale-110 transition-transform" /> EXECUTE_ACTION
          </button>
          <button className="flex items-center justify-center gap-3 py-4 bg-white/5 border border-white/10 text-white font-display text-lg tracking-[0.2em] rounded-sm hover:bg-white/10 transition-all">
            <MessageSquare size={18} /> SWARM_DEBATE
          </button>
        </section>

        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-1.5 h-1.5 bg-accent-primary rounded-full shadow-[0_0_8px_#38bdf8]" />
            <span className="text-[11px] text-accent-primary font-black tracking-[0.3em] uppercase">RAW_TELEMETRY_DATAFRAME</span>
          </div>
          <div className="glass-panel rounded-sm overflow-hidden border-white/10 bg-slate-900/60">
            {Object.entries(ev.raw || {}).map(([key, val]: [string, any], i) => {
              if (typeof val === 'object' || key === 'id') return null;
              return (
                <div key={key} className={`flex justify-between p-4 text-[11px] ${i % 2 === 0 ? 'bg-white/[0.02]' : ''} border-b border-white/5 last:border-0 hover:bg-white/[0.05] transition-colors`}>
                  <span className="text-slate-500 uppercase tracking-widest font-bold">{key.replace(/_/g, ' ')}</span>
                  <span className="text-white font-mono font-bold">{String(val)}</span>
                </div>
              );
            })}
          </div>
        </section>

        <section className="space-y-6">
            <div className="flex items-center gap-3">
               <div className="w-1.5 h-1.5 bg-bull rounded-full shadow-[0_0_8px_#10b981]" />
               <span className="text-[11px] text-bull font-black tracking-[0.3em] uppercase font-display">MIROFISH_NEURAL_SYNTHESIS</span>
            </div>
            <div className="glass-panel p-8 rounded-sm text-[14px] text-slate-200 leading-relaxed font-sans italic border-bull/20 border-l-4 bg-bull/5 relative group overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-20 transition-opacity">
                 <Lucide.Brain size={60} className="text-bull" />
              </div>
              <p className="relative z-10">
                "Systematic correlation detected between this <span className="text-white font-bold">{ev.type}</span> event and regional trade flow. 
                High probability of supply chain friction within <span className="text-white font-bold underline decoration-bull">T+48h</span>. 
                Recommend increasing delta exposure to associated volatility indices and monitoring secondary chokepoints."
              </p>
              <div className="mt-6 flex justify-between items-center relative z-10">
                 <div className="flex -space-x-3">
                    {[1,2,3,4].map(n => (
                      <div key={n} className="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-950 flex items-center justify-center text-[10px] font-black text-accent-primary shadow-2xl">A{n}</div>
                    ))}
                 </div>
                 <span className="text-[10px] font-mono font-bold text-bull uppercase tracking-[0.2em] bg-bull/10 px-2 py-1 border border-bull/20">Confidence: 98.4%</span>
              </div>
            </div>
        </section>
      </div>

      <footer className="p-8 border-t border-white/10 bg-slate-900/60 shrink-0">
        <div className="flex justify-between items-center text-[9px] font-mono text-slate-600 uppercase tracking-[0.4em] font-bold">
          <div className="flex gap-6">
            <span>TERMINAL_ID: ST-OPS-77</span>
            <span>SEC_CLEARANCE: L4</span>
          </div>
          <span className="animate-pulse text-accent-primary/60">UPLINK_ENCRYPTED_GCM</span>
        </div>
      </footer>

      <style>{`
        @keyframes slide-in {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-in {
          animation: slide-in 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .shadow-glow-orange { filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.6)); }
      `}</style>
    </div>
  );
};

export default IntelligenceDetails;
