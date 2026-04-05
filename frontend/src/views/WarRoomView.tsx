import React, { useState, useEffect } from 'react';
import * as Lucide from 'lucide-react';
import { api } from '../api/client';
import { useSignalStore, useTerminalStore, useFlightStore, useVesselStore } from '../store';

const Activity = Lucide.Activity || Lucide.Zap;

const PERSONAS = [
  { id: 'Standard', label: 'Standard', color: 'text-bull' },
  { id: 'Cautious', label: 'Cautious', color: 'text-accent-primary' },
  { id: 'Aggressive', label: 'Aggressive', color: 'text-bear' },
  { id: 'Weather-Sensitive', label: 'Weather', color: 'text-sky-400' },
  { id: 'Economic-Sensitive', label: 'Macro', color: 'text-amber-400' }
];

const WarRoomView = () => {
  const { 
    Shield, ShieldAlert, Lock, Unlock, Target, Zap, 
    Crosshair, Loader2, Sparkles, Users, Info, Bell
  } = Lucide;
  
  const [isLocked, setIsLocked] = useState(true);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [activePersona, setActivePersona] = useState('Standard');
  const [missionRequirement, setMissionRequirement] = useState('Assess global trade stability and equity risk based on current kinetic incidents.');
  const [report, setReport] = useState<any>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isGodMode, setIsGodMode] = useState(false);

  const generateIntelligence = async () => {
    setIsSynthesizing(true);
    try {
      const endpoint = isGodMode ? '/api/intelligence/godmode' : '/api/intelligence/mirofish-forecast';
      const response = await fetch(endpoint + (isGodMode ? '' : `?requirement=${encodeURIComponent(missionRequirement)}&persona=${activePersona}`), {
        method: isGodMode ? 'POST' : 'GET',
        headers: { 'Content-Type': 'application/json' },
        body: isGodMode ? JSON.stringify({ query: missionRequirement }) : undefined
      });
      const data = await response.json();
      setReport(data);
    } catch (err) {
      console.error("Intel synthesis fail:", err);
    } finally {
      setIsSynthesizing(false);
    }
  };

  useEffect(() => {
    if (isLocked) return;

    const fetchData = async () => {
      try {
        const conflictsData = await api.conflicts();
        const events = (conflictsData.events || []).slice(0, 10).map((e: any) => ({
          id: e.id,
          type: e.type,
          location: e.country,
          status: e.severity,
          time: 'LIVE',
          detail: e.description || `Conflict event in ${e.country} with ${e.fatalities} fatalities.`
        }));
        setIncidents(events);
      } catch (err) {
        console.error("WarRoom data fetch fail:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [isLocked]);

  if (isLocked) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-slate-950 font-mono">
        <div className="w-[450px] p-12 glass-panel neo-border rounded-sm text-center space-y-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none" />
          
          <div className="flex justify-center relative">
            <div className="p-6 rounded-full bg-accent-primary/10 border border-accent-primary/20 animate-pulse-soft">
              <Lock size={64} className="text-accent-primary" />
            </div>
            <div className="absolute inset-0 blur-2xl text-accent-primary/40 flex items-center justify-center">
              <Lock size={80} />
            </div>
          </div>
          
          <div className="space-y-3 relative">
            <h2 className="font-display text-3xl text-white tracking-[0.3em] uppercase">Security_Override</h2>
            <p className="text-[11px] text-slate-400 uppercase tracking-widest leading-relaxed">
              Tactical Geopolitical Kinetic Intelligence Node.<br/>
              Access Restricted to Level-4 Operators Only.
            </p>
          </div>
          
          <button 
            onClick={() => setIsLocked(false)}
            className="w-full py-4 bg-accent-primary text-slate-950 font-display text-xl tracking-[0.2em] rounded-sm hover:bg-white transition-all flex items-center justify-center gap-4 shadow-glow-sky"
          >
            <Unlock size={20} /> DECRYPT_SESSION
          </button>
        </div>
        
        <div className="mt-12 flex items-center gap-6 text-[10px] font-mono text-slate-600 font-bold uppercase tracking-[0.4em]">
           <span>CHANNEL: ST-WAR-LINK-01</span>
           <div className="w-1 h-1 bg-slate-800 rounded-full"></div>
           <span>ENC: RSA_4096_GCM</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 overflow-hidden font-mono selection:bg-bear/30 selection:text-white">
      <header className="h-14 border-b border-white/5 flex items-center justify-between px-8 bg-slate-900/40 backdrop-blur-md shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
             <Shield size={20} className="text-bear animate-pulse shadow-glow-bear" />
             <div className="flex flex-col">
               <h1 className="font-display text-xl tracking-[0.2em] text-white leading-none">WAR_ROOM_SURVEILLANCE</h1>
               <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mt-1">Direct Kinetic Intelligence Ingest</span>
             </div>
          </div>
          <div className="h-6 w-px bg-white/10" />
          <div className="flex items-center gap-3 glass-panel px-3 py-1 border-white/10 rounded-sm">
             <div className="w-1.5 h-1.5 rounded-full bg-bear animate-ping" />
             <span className="text-[10px] font-black text-bear uppercase tracking-widest">DEFCON 2: ELEVATED</span>
          </div>
        </div>
        <button 
          onClick={() => setIsLocked(true)}
          className="p-2 text-slate-500 hover:text-white transition-colors flex items-center gap-2"
        >
          <span className="text-[9px] font-bold uppercase tracking-widest">Terminate Session</span>
          <Lock size={16} />
        </button>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* LEFT: INCIDENT STREAM */}
        <aside className="w-[450px] border-r border-white/5 flex flex-col bg-slate-900/10 backdrop-blur-sm">
           <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/2">
              <span className="text-[11px] font-bold text-accent-primary tracking-[0.3em] uppercase flex items-center gap-2">
                 <Bell size={12} /> Live Threat Vector
              </span>
              <span className="text-[9px] font-mono text-slate-500 bg-white/5 px-1.5 rounded-sm">POOL_SIZE: {incidents.length}</span>
           </div>
           <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
              {incidents.map(inc => (
                <div key={inc.id} className="glass-panel p-5 neo-border group hover:bg-white/5 transition-all cursor-crosshair relative">
                   <div className="flex justify-between items-start mb-3">
                      <div className={`px-2 py-0.5 rounded-sm border ${inc.status === 'CRITICAL' ? 'bg-bear/10 border-bear/30 text-bear' : 'bg-accent-primary/10 border-accent-primary/30 text-accent-primary'} text-[9px] font-black tracking-widest`}>
                        {inc.status}
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">{inc.time} UTC</span>
                   </div>
                   <h3 className="text-sm font-black text-white mb-2 uppercase tracking-wider group-hover:text-accent-primary transition-colors">{inc.location}</h3>
                   <p className="text-[12px] text-slate-400 leading-relaxed italic border-l-2 border-white/10 pl-3 mb-4">"{inc.detail}"</p>
                   <div className="flex justify-between items-center pt-2 border-t border-white/5">
                      <span className="text-[9px] font-mono text-slate-600 uppercase tracking-widest">{inc.type} EVENT</span>
                      <button className="text-[10px] text-accent-primary font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-all flex items-center gap-1">
                        Analyze Node <Crosshair size={10} />
                      </button>
                   </div>
                </div>
              ))}
           </div>
        </aside>

        {/* CENTER: MISSION CONTROL */}
        <main className="flex-1 flex flex-col bg-[#020617] relative">
           <div className="absolute inset-0 opacity-[0.05] pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle, #38bdf8 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
           
           <header className="h-16 border-b border-white/5 bg-slate-900/40 backdrop-blur-md flex items-center px-8 gap-8 z-20 shrink-0">
              <div className="flex-1 flex items-center gap-4 bg-slate-950/80 border border-white/10 px-5 py-2.5 rounded-sm group focus-within:border-accent-primary transition-all">
                 <Target size={18} className="text-slate-600 group-focus-within:text-accent-primary" />
                 <input 
                   type="text" 
                   value={missionRequirement}
                   onChange={(e) => setMissionRequirement(e.target.value)}
                   className="flex-1 bg-transparent border-none outline-none text-[12px] text-white font-bold uppercase tracking-widest placeholder:text-slate-700"
                   placeholder="SPECIFY TACTICAL MISSION DIRECTIVE..."
                 />
              </div>
              <div className="flex items-center gap-2">
                 {PERSONAS.map(p => (
                   <button 
                     key={p.id}
                     onClick={() => { setActivePersona(p.id); setIsGodMode(false); }}
                     className={`px-4 py-2 border text-[10px] font-black uppercase tracking-widest transition-all ${
                       activePersona === p.id && !isGodMode 
                       ? 'bg-accent-primary text-slate-950 border-accent-primary shadow-glow-sky' 
                       : 'bg-white/5 border-white/10 text-slate-500 hover:text-white'
                     }`}
                   >
                     {p.label}
                   </button>
                 ))}
                 <div className="h-8 w-px bg-white/10 mx-4" />
                 <button 
                   onClick={() => setIsGodMode(!isGodMode)}
                   className={`px-6 py-2 border text-[10px] font-black uppercase tracking-[0.2em] transition-all flex items-center gap-2 ${
                     isGodMode 
                     ? 'bg-bear text-white border-bear shadow-glow-bear' 
                     : 'bg-white/5 border-white/10 text-slate-500'
                   }`}
                 >
                   <Sparkles size={14} /> GOD_MODE
                 </button>
              </div>
           </header>

           <div className="flex-1 overflow-y-auto custom-scrollbar p-12 z-10">
              {!report && !isSynthesizing ? (
                <div className="h-full flex flex-col items-center justify-center opacity-20">
                   <Users size={120} className="mb-8 animate-pulse text-white" />
                   <h2 className="font-display text-4xl tracking-[1em] text-white uppercase">Waiting_On_Intel</h2>
                </div>
              ) : isSynthesizing ? (
                <div className="h-full flex flex-col items-center justify-center gap-8">
                   <div className="relative">
                      <div className="w-32 h-32 border-4 border-accent-primary/10 rounded-full border-t-accent-primary animate-spin" />
                      <div className="absolute inset-0 flex items-center justify-center">
                         <Sparkles size={48} className="text-accent-primary animate-pulse" />
                      </div>
                   </div>
                   <div className="text-center space-y-3">
                      <h2 className="font-display text-3xl text-accent-primary tracking-[0.4em] uppercase animate-pulse">Orchestrating Swarm</h2>
                      <p className="text-[11px] font-mono text-slate-500 uppercase tracking-widest">Simulating 2,142 multi-persona agents in parallel...</p>
                   </div>
                </div>
              ) : (
                <div className="max-w-5xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-1000">
                   {isGodMode && report.responses ? (
                     <div className="grid grid-cols-2 gap-8">
                        {Object.entries(report.responses).map(([p, r]: [string, any]) => (
                          <div key={p} className="glass-panel p-8 neo-border rounded-sm relative group overflow-hidden">
                             <div className="text-[11px] font-black text-accent-primary uppercase tracking-[0.4em] mb-6 flex items-center gap-3">
                                <div className="w-2 h-2 rounded-full bg-accent-primary animate-pulse shadow-[0_0_8px_#38bdf8]" />
                                {p} VECTOR PERCEPTION
                             </div>
                             <div className="text-[13px] text-slate-200 leading-relaxed font-mono whitespace-pre-wrap italic opacity-80 group-hover:opacity-100 transition-opacity">
                                {typeof r === 'string' ? r : r.report || "Vector Synthesis Fault"}
                             </div>
                             <div className="mt-8 pt-6 border-t border-white/5 flex justify-between items-center">
                                <div className="flex flex-col">
                                   <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Signal Confidence</span>
                                   <span className="text-lg font-mono font-black text-white">{r.confidence || 94}%</span>
                                </div>
                                <button className="px-4 py-2 bg-white/5 border border-white/10 text-[9px] font-black uppercase tracking-widest hover:bg-white/10 transition-all rounded-sm">Inspect Model</button>
                             </div>
                          </div>
                        ))}
                     </div>
                   ) : (
                     <article className="glass-panel p-16 neo-border rounded-sm shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-16 h-16 border-t-2 border-l-2 border-accent-primary/30" />
                        <div className="absolute bottom-0 right-0 w-16 h-16 border-b-2 border-r-2 border-accent-primary/30" />
                        
                        <header className="flex justify-between items-start mb-12 border-b border-white/10 pb-8">
                           <div className="space-y-3">
                              <div className="flex items-center gap-4">
                                 <span className="px-3 py-1 bg-bear text-white text-[10px] font-black uppercase tracking-[0.2em] shadow-glow-bear">Top Secret</span>
                                 <h2 className="font-display text-4xl text-white tracking-widest uppercase">Intelligence Consensus Report</h2>
                              </div>
                              <p className="text-xs text-slate-500 uppercase tracking-[0.3em] font-bold">Vector Archetype: {activePersona} // Core: MiroFish-2.1</p>
                           </div>
                           <div className="flex flex-col items-end">
                              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">GTFI_SYSTEMIC_STABILITY</span>
                              <span className={`text-4xl font-display tracking-tighter ${report.gtfi > 0.8 ? 'text-bull' : 'text-bear'}`}>{(report.gtfi * 100).toFixed(1)}%</span>
                           </div>
                        </header>

                        <div className="prose prose-invert max-w-none prose-sm font-sans leading-relaxed text-slate-200">
                           <div className="whitespace-pre-wrap text-lg italic leading-relaxed opacity-90 border-l-4 border-accent-primary/20 pl-8 py-4">
                              {report.report || report.consensus_report}
                           </div>
                        </div>

                        <footer className="mt-16 pt-8 border-t border-white/10 flex justify-between items-center text-[10px] font-mono text-slate-600 font-bold uppercase tracking-[0.4em]">
                           <div className="flex gap-8">
                              <span>Origin: SWARM_CORE_L7</span>
                              <span>Hash: 0x93F2...44A2</span>
                           </div>
                           <span>{new Date().toISOString()}</span>
                        </footer>
                     </article>
                   )}
                </div>
              )}
           </div>

           <footer className="h-20 border-t border-white/5 bg-slate-900/60 backdrop-blur-xl flex items-center px-12 gap-6 z-30 shrink-0">
              <button 
                onClick={generateIntelligence}
                disabled={isSynthesizing}
                className="px-12 h-12 bg-accent-primary text-slate-950 font-display text-xl tracking-[0.3em] rounded-sm hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-4 shadow-glow-sky shrink-0"
              >
                {isSynthesizing ? <Loader2 size={20} className="animate-spin" /> : <Zap size={20} />}
                SYNTHESIZE_ALPHA
              </button>
              
              <div className="flex-1 flex items-center gap-6 overflow-hidden px-8">
                 <div className="flex items-center gap-3 text-bear animate-pulse shrink-0">
                    <Shield size={16} />
                    <span className="text-[10px] font-black uppercase tracking-widest">Ready_To_Alert</span>
                 </div>
                 <div className="h-6 w-px bg-white/10 shrink-0" />
                 <div className="flex gap-8 whitespace-nowrap overflow-hidden italic text-slate-500 text-xs">
                    {[1,2,3].map(i => (
                      <span key={i}>SATELLITE_LINK_STABLE_BAND_KA_{i}</span>
                    ))}
                 </div>
              </div>

              <div className="flex items-center gap-4 shrink-0">
                 <div className="flex flex-col items-end">
                    <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Logic Node</span>
                    <span className="text-[11px] text-bull font-bold font-mono">SYNCHRONIZED</span>
                 </div>
                 <div className="w-2 h-2 rounded-full bg-bull shadow-[0_0_8px_#10b981]" />
              </div>
           </footer>
        </main>
      </div>
    </div>
  );
};

export default WarRoomView;
