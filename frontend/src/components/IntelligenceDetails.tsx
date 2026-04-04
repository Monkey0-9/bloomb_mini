import React from 'react';
import { X, ExternalLink, MapPin, Clock, Info, AlertCircle, Shield, Plane, Ship, Flame, Activity } from 'lucide-react';
import { useTerminalStore } from '../store';

const IntelligenceDetails: React.FC = () => {
  const { selectedIntelligenceEvent, setSelectedIntelligenceEvent } = useTerminalStore();

  if (!selectedIntelligenceEvent) return null;

  const ev = selectedIntelligenceEvent;

  return (
    <div className="fixed inset-y-0 right-0 w-[450px] bg-void/95 backdrop-blur-2xl border-l border-white/10 z-[300] shadow-[-20px_0_50px_rgba(0,0,0,0.5)] flex flex-col font-mono animate-slide-in">
      {/* Header */}
      <div className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-surface-1/40">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-sm bg-white/5 border border-white/10`}>
            {ev.type === 'THERMAL' && <Flame size={18} className="text-[#FF7A3D]" />}
            {ev.type === 'AIRCRAFT' && <Plane size={18} className="text-[#BD93F9]" />}
            {ev.type === 'VESSEL' && <Ship size={18} className="text-[#00E396]" />}
            {ev.type === 'CONFLICT' && <Shield size={18} className="text-[#FF4560]" />}
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-white/40 uppercase tracking-[0.2em] font-bold">Signal Intelligence</span>
            <span className="text-xs text-white font-bold tracking-wider">{ev.type} ANALYTICS</span>
          </div>
        </div>
        <button 
          onClick={() => setSelectedIntelligenceEvent(null)}
          className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/40 hover:text-white"
        >
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
        {/* Title & Status */}
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <h2 className="text-xl font-bold text-white leading-tight flex-1 pr-4">{ev.title}</h2>
            <div className={`px-2 py-1 rounded-sm text-[10px] font-bold tracking-widest ${
              ev.severity === 'CRITICAL' || ev.severity === 'HIGH' ? 'bg-[#FF4560]/20 text-[#FF4560] border border-[#FF4560]/30' : 'bg-[#38bdf8]/20 text-[#38bdf8] border border-[#38bdf8]/30'
            }`}>
              {ev.severity}
            </div>
          </div>
          
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2 text-[10px] text-white/60 uppercase tracking-widest bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
              <MapPin size={12} className="text-accent-primary" /> {ev.location}
            </div>
            <div className="flex items-center gap-2 text-[10px] text-white/60 uppercase tracking-widest bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
              <Clock size={12} className="text-accent-primary" /> {ev.time}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <button className="flex items-center justify-center gap-2 py-3 bg-accent-primary text-void text-[10px] font-black uppercase tracking-[0.2em] rounded-sm hover:brightness-110 transition-all shadow-[0_0_20px_rgba(56,189,248,0.2)]">
            <ExternalLink size={14} /> Execute Trade
          </button>
          <button className="flex items-center justify-center gap-2 py-3 bg-white/5 border border-white/10 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-sm hover:bg-white/10 transition-all">
            <Info size={14} /> Swarm Debate
          </button>
        </div>

        {/* Data Grid */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-[10px] text-accent-primary font-bold tracking-[0.3em] uppercase">
            <AlertCircle size={12} /> Raw Telemetry Data
          </div>
          <div className="bg-void/50 border border-white/5 rounded-sm overflow-hidden">
            {Object.entries(ev.raw || {}).map(([key, val]: [string, any], i) => {
              if (typeof val === 'object' || key === 'id') return null;
              return (
                <div key={key} className={`flex justify-between p-3 text-[10px] ${i % 2 === 0 ? 'bg-white/2' : ''} border-b border-white/5 last:border-0`}>
                  <span className="text-white/40 uppercase tracking-widest font-bold">{key.replace(/_/g, ' ')}</span>
                  <span className="text-white font-mono">{String(val)}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI Analysis */}
        <div className="space-y-4">
            <div className="flex items-center gap-2 text-[10px] text-[#00E396] font-bold tracking-[0.3em] uppercase">
              <Activity size={12} /> Neural Synthesis
            </div>
            <div className="bg-[#00E396]/5 border border-[#00E396]/20 p-4 rounded-sm text-[11px] text-[#00E396]/90 leading-relaxed italic border-l-2">
              "Systematic correlation detected between this {ev.type} event and regional trade flow. High probability of supply chain friction within T+48h. Recommend increasing delta exposure to associated volatility indices."
            </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-6 border-t border-white/10 bg-surface-1/40">
        <div className="flex justify-between items-center text-[8px] text-white/30 uppercase tracking-[0.3em] font-bold">
          <span>Source: SatTrade Multi-Agent Engine</span>
          <span>Security Level: Tier-1</span>
        </div>
      </div>

      <style>{`
        @keyframes slide-in {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-in {
          animation: slide-in 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
      `}</style>
    </div>
  );
};

export default IntelligenceDetails;