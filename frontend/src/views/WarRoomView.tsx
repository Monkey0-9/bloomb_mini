import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Target, Activity, Zap, Globe, Lock, Unlock, Crosshair } from 'lucide-react';
import { api } from '../api/client';

const WarRoomView = () => {
  const [isLocked, setIsLocked] = useState(true);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [seismicNote, setSeismicNote] = useState("Monitoring tectonic stability...");

  useEffect(() => {
    if (isLocked) return;

    const fetchData = async () => {
      try {
        const [conflictsData, swarmData] = await Promise.all([
          api.conflicts(),
          fetch('/api/intelligence/swarm').then(r => r.json())
        ]);
        
        const events = (conflictsData.events || []).slice(0, 10).map((e: any) => ({
          id: e.id,
          type: e.type,
          location: e.country,
          status: e.severity,
          time: 'LIVE',
          detail: e.description || `Conflict event in ${e.country} with ${e.fatalities} fatalities.`
        }));
        setIncidents(events);

        if (swarmData.gtfi_score < 0.8) {
           setSeismicNote(`GTFI Score degraded to ${swarmData.gtfi_score}. Systemic risk detected in maritime corridors.`);
        }
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
      <div className="flex-1 flex flex-col items-center justify-center bg-void font-mono">
        <div className="w-96 p-8 border border-white/10 bg-surface-1/40 backdrop-blur-xl rounded-sm text-center space-y-6">
          <div className="flex justify-center">
            <div className="p-4 rounded-full bg-white/5 border border-white/10 animate-pulse">
              <Lock size={48} className="text-accent-primary" />
            </div>
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-white tracking-[0.2em] uppercase">War Room Access</h2>
            <p className="text-[10px] text-white/40 uppercase tracking-widest leading-relaxed">
              This environment contains classified OSINT and real-time kinetic intelligence. Unauthorized access is strictly prohibited.
            </p>
          </div>
          <button 
            onClick={() => setIsLocked(false)}
            className="w-full py-3 bg-accent-primary text-void font-black uppercase tracking-[0.2em] rounded-sm hover:brightness-110 transition-all flex items-center justify-center gap-3"
          >
            <Unlock size={16} /> Decrypt & Access
          </button>
        </div>
        <div className="mt-8 flex items-center gap-4 text-[9px] text-white/20 font-bold uppercase tracking-[0.4em]">
           <span>Encrypted Tunnel: ST-SECURE-99</span>
           <div className="w-1 h-1 bg-white/20 rounded-full"></div>
           <span>Auth: Surgical-Ops</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden font-mono selection:bg-bear selection:text-white">
      {/* Header */}
      <div className="h-14 border-b border-white/10 flex items-center justify-between px-6 bg-surface-1/40 shrink-0">
        <div className="flex items-center gap-4">
          <Shield size={20} className="text-bear animate-pulse" />
          <div className="flex flex-col">
            <span className="text-[11px] font-bold text-white tracking-[0.3em] uppercase">War Room Surveillance</span>
            <span className="text-[8px] text-white/40 tracking-widest uppercase">Global Geopolitical Kinetic Intelligence HUB</span>
          </div>
        </div>
        <div className="flex items-center gap-6">
           <div className="flex flex-col items-end">
             <span className="text-[9px] text-white/40 uppercase tracking-widest">Threat Level</span>
             <span className="text-sm font-black text-bear tracking-tighter">DEFCON 3</span>
           </div>
           <div className="h-8 w-[1px] bg-white/10"></div>
           <button onClick={() => setIsLocked(true)} className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/40 hover:text-white">
             <Lock size={18} />
           </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Incident Feed */}
        <div className="w-[450px] border-r border-white/10 flex flex-col bg-void/50">
           <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/2">
              <span className="text-[10px] font-bold text-accent-primary tracking-[0.2em] uppercase">Active Kinetic Incidents</span>
              <span className="text-[9px] text-white/40 font-mono">COUNT: {incidents.length}</span>
           </div>
           <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
              {incidents.map(inc => (
                <div key={inc.id} className="group relative bg-white/5 border border-white/5 p-4 rounded-sm hover:bg-white/10 transition-all cursor-crosshair">
                   <div className="flex justify-between items-start mb-2">
                      <span className="text-[10px] font-black text-bear tracking-[0.1em] flex items-center gap-2">
                        <Target size={12} /> {inc.type}
                      </span>
                      <span className="text-[9px] text-white/40">{inc.time}</span>
                   </div>
                   <h3 className="text-xs font-bold text-white mb-2 uppercase tracking-wide">{inc.location}</h3>
                   <p className="text-[10px] text-white/60 leading-relaxed mb-3">{inc.detail}</p>
                   <div className="flex justify-between items-center">
                      <div className={`px-1.5 py-0.5 text-[8px] font-bold rounded-sm border ${
                        inc.status === 'CRITICAL' ? 'bg-bear/20 text-bear border-bear/30' : 'bg-accent-primary/20 text-accent-primary border-accent-primary/30'
                      }`}>
                        {inc.status}
                      </div>
                      <button className="text-[9px] text-white/30 hover:text-white transition-colors flex items-center gap-1 uppercase tracking-widest">
                        Intelligence Scan <Crosshair size={10} />
                      </button>
                   </div>
                </div>
              ))}
           </div>
        </div>

        {/* Center: Tactical Map/Assets */}
        <div className="flex-1 flex flex-col relative">
           <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_40%,rgba(0,0,0,0.4)_100%)] pointer-events-none z-10"></div>
           
           {/* HUD Overlays */}
           <div className="absolute top-6 left-6 z-20 space-y-4">
              <div className="bg-black/80 backdrop-blur-md border border-white/10 p-4 rounded-sm space-y-3 w-64 shadow-2xl">
                 <div className="flex items-center gap-2 text-[10px] font-bold text-accent-primary tracking-[0.2em] uppercase">
                    <Globe size={14} /> Satellite Coverage
                 </div>
                 <div className="space-y-2">
                    {[
                      { name: 'Sentinel-1A', status: 'ACTIVE', color: 'bg-bull' },
                      { name: 'SENTINEL-2B', status: 'ORBITAL', color: 'bg-bull' },
                      { name: 'USA-245 (KH-11)', status: 'LOCKED', color: 'bg-bear' },
                      { name: 'COSMO-SkyMed', status: 'TASKED', color: 'bg-accent-primary' }
                    ].map(sat => (
                      <div key={sat.name} className="flex justify-between items-center">
                         <span className="text-[9px] text-white/60 uppercase">{sat.name}</span>
                         <div className="flex items-center gap-2">
                            <span className="text-[8px] text-white/40 font-mono">{sat.status}</span>
                            <div className={`w-1.5 h-1.5 rounded-full ${sat.color} animate-pulse`}></div>
                         </div>
                      </div>
                    ))}
                 </div>
              </div>

              <div className="bg-black/80 backdrop-blur-md border border-white/10 p-4 rounded-sm space-y-3 w-64 shadow-2xl">
                 <div className="flex items-center gap-2 text-[10px] font-bold text-[#FEB019] tracking-[0.2em] uppercase">
                    <Activity size={14} /> Global Seismic Activity
                 </div>
                  <div className="p-2 bg-void/50 border border-white/5 text-[9px] text-white/40 leading-snug">
                    "{seismicNote}"
                  </div>
              </div>
           </div>

           {/* Tactical Visualizer Placeholder */}
           <div className="flex-1 flex items-center justify-center bg-[#040B16] overflow-hidden">
              <div className="relative w-full h-full flex items-center justify-center">
                 <div className="absolute w-[600px] h-[600px] border border-white/5 rounded-full animate-pulse"></div>
                 <div className="absolute w-[400px] h-[400px] border border-white/5 rounded-full"></div>
                 <div className="absolute w-[200px] h-[200px] border border-white/5 rounded-full"></div>
                 <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-[10px] text-white/20 uppercase tracking-[1em] font-black">Tactical Grid Engaged</div>
                 </div>
                 {/* Mock Targets */}
                 <div className="absolute top-1/3 left-1/4 group cursor-crosshair">
                    <div className="w-3 h-3 border border-bear rotate-45 animate-spin-slow"></div>
                    <div className="absolute left-4 top-0 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity bg-bear/90 text-void px-2 py-1 text-[8px] font-bold uppercase rounded-sm">
                       UNIDENTIFIED ASSET [KINETIC]
                    </div>
                 </div>
                 <div className="absolute bottom-1/4 right-1/3 group cursor-crosshair">
                    <div className="w-2 h-2 bg-bull shadow-[0_0_10px_#00FF9D]"></div>
                    <div className="absolute left-4 top-0 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity bg-bull/90 text-void px-2 py-1 text-[8px] font-bold uppercase rounded-sm">
                       USN CARRIER GROUP [CVN-78]
                    </div>
                 </div>
              </div>
           </div>

           {/* Bottom Bar: Action Triggers */}
           <div className="h-16 border-t border-white/10 bg-surface-1/40 flex items-center px-8 gap-4 shrink-0 z-20 backdrop-blur-md">
              <button className="px-6 py-2 bg-bear text-void text-[10px] font-black uppercase tracking-[0.2em] rounded-sm hover:brightness-110 transition-all flex items-center gap-2">
                 <Zap size={14} /> Dispatch Drone Surveillance
              </button>
              <button className="px-6 py-2 bg-white/5 border border-white/10 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-sm hover:bg-white/10 transition-all">
                 Request SAR Imagery
              </button>
              <button className="px-6 py-2 bg-white/5 border border-white/10 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-sm hover:bg-white/10 transition-all">
                 Task AI Intelligence
              </button>
           </div>
        </div>
      </div>

      <style>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 10s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default WarRoomView;