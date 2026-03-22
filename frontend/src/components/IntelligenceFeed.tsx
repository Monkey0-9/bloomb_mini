import React, { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Radio, ShieldAlert, Navigation, Flame, Zap } from 'lucide-react';
import { useTerminalStore, useSignalStore, useFlightStore, useVesselStore } from '../store';

const getEventColor = (type: string) => {
  switch (type.toUpperCase()) {
    case 'CONFLICT': return 'text-[#FF4560] border-[#FF4560] shadow-[0_0_10px_#FF456040]';
    case 'EARTHQUAKE': return 'text-[#FEB019] border-[#FEB019] shadow-[0_0_10px_#FEB01940]';
    case 'AIRCRAFT': return 'text-[#BD93F9] border-[#BD93F9] shadow-[0_0_10px_#BD93F940]';
    case 'VESSEL': return 'text-[#00E396] border-[#00E396] shadow-[0_0_10px_#00E39640]';
    case 'THERMAL': return 'text-[#FF7A3D] border-[#FF7A3D] shadow-[0_0_10px_#FF7A3D40]';
    default: return 'text-[#38bdf8] border-[#38bdf8] shadow-[0_0_10px_#38bdf840]';
  }
};

const getEventIcon = (type: string) => {
  switch (type.toUpperCase()) {
    case 'CONFLICT': return <ShieldAlert size={12} />;
    case 'EARTHQUAKE': return <Activity size={12} />;
    case 'AIRCRAFT': return <Navigation size={12} />;
    case 'VESSEL': return <Navigation size={12} className="rotate-180" />;
    case 'THERMAL': return <Flame size={12} />;
    default: return <Radio size={12} />;
  }
};

const IntelligenceFeed = () => {
  const { signals, fetchSignals } = useSignalStore();
  const { flights, fetchFlights } = useFlightStore();
  const { vessels, fetchVessels } = useVesselStore();
  
  // Create a unified master timeline of all global intel
  const [feed, setFeed] = useState<any[]>([]);

  useEffect(() => {
    fetchSignals();
    fetchFlights();
    fetchVessels();
  }, [fetchSignals, fetchFlights, fetchVessels]);

  useEffect(() => {
    // We synthesize a feed based on incoming stores
    const events: any[] = [];
    
    // Add thermal signals
    signals.forEach((s: any, i) => {
      if(i > 5) return;
      events.push({
        id: `th-${s.id}`,
        time: new Date(Date.now() - Math.random() * 3600000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        type: 'THERMAL',
        title: s.name,
        location: s.location || 'Unknown',
        detail: `Confidence: ${s.score.toFixed(1)} | Signal: ${s.signal}`,
        severity: s.score > 80 ? 'CRITICAL' : 'ELEVATED'
      });
    });

    // Add high-interest flights (military/cargo)
    let fCount = 0;
    flights.forEach((f: any) => {
      if(f.category !== 'COMMERCIAL' && fCount < 6) {
        events.push({
          id: `fl-${f.icao24}`,
          time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
          type: 'AIRCRAFT',
          title: `[${f.category}] ${f.callsign}`,
          location: f.route || 'Airspace',
          detail: `Operator: ${f.operator} | Alt: ${f.position?.alt_ft || f.alt_ft || 0}ft | Cargo: ${f.cargo || 'Unknown'}`,
          severity: f.category === 'MILITARY' ? 'HIGH' : 'INFO'
        });
        fCount++;
      }
    });

    // Add high-interest vessels (dark ships / tankers)
    let vCount = 0;
    vessels.forEach((v: any) => {
      if(v.cargo !== 'Unknown' && vCount < 6) {
        events.push({
          id: `vs-${v.id || v.mmsi}`,
          time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
          type: 'VESSEL',
          title: `[MARINE] MMSI ${v.id || v.mmsi}`,
          location: v.destination || 'Maritime Route',
          detail: `Status: ${v.status} | Cargo: ${v.cargo}`,
          severity: 'INFO'
        });
        vCount++;
      }
    });

    // Sort by "time" roughly (or just random weave for now)
    // To make it look dynamic, shuffle or sort
    events.sort(() => 0.5 - Math.random());
    setFeed(events);
  }, [signals, flights, vessels]);

  return (
    <div className="flex flex-col h-full bg-[#020617]/90 backdrop-blur-xl border-l border-white/5 font-mono select-none overflow-hidden relative">
      {/* Neo-Header */}
      <div className="p-3 border-b border-white/10 flex flex-col gap-1 bg-gradient-to-r from-white/5 to-transparent shrink-0">
          <div className="flex justify-between items-center">
            <span className="text-[11px] text-white font-bold tracking-[0.3em] flex items-center gap-2 uppercase font-sans">
              <Zap size={14} className="text-[#38bdf8]" /> GLOBAL INTELLIGENCE HUB
            </span>
            <div className="flex gap-1.5">
               <div className="w-1.5 h-1.5 rounded-full bg-[#FF4560] shadow-[0_0_8px_#FF4560] animate-pulse"></div>
               <div className="w-1.5 h-1.5 rounded-full bg-[#00E396] shadow-[0_0_8px_#00E396] animate-pulse" style={{animationDelay: '300ms'}}></div>
               <div className="w-1.5 h-1.5 rounded-full bg-[#38bdf8] shadow-[0_0_8px_#38bdf8] animate-pulse" style={{animationDelay: '600ms'}}></div>
            </div>
          </div>
          <div className="text-[9px] text-slate-400 tracking-widest mt-1 uppercase">Live Unified Threat & Assets Stream</div>
      </div>
      
      {/* Event Timeline */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3">
        {feed.length === 0 && (
          <div className="w-full h-full flex items-center justify-center text-slate-500 text-xs tracking-widest animate-pulse">
            ACQUIRING SATELLITE UPLINK...
          </div>
        )}
        
        {feed.map((ev, i) => {
          const colorClass = getEventColor(ev.type);
          return (
            <div key={`${ev.id}-${i}`} className="relative pl-4 group">
              {/* Timeline Stem */}
              <div className="absolute left-[7px] top-4 bottom-[-10px] w-px bg-white/10 group-last:hidden"></div>
              
              {/* Timeline Node */}
              <div className={`absolute left-0 top-1.5 w-[15px] h-[15px] rounded-full bg-[#020617] border-2 flex items-center justify-center z-10 transition-transform group-hover:scale-125 ${colorClass}`}>
                <div className="w-1 h-1 bg-current rounded-full" />
              </div>

              {/* Event Card */}
              <div className="bg-white/5 border border-white/5 rounded p-2.5 hover:bg-white/10 hover:border-white/20 transition-all cursor-crosshair ml-2 overflow-hidden relative">
                <div className={`absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-current to-transparent opacity-0 group-hover:opacity-100 transition-opacity ${colorClass.split(' ')[0]}`}></div>
                
                <div className="flex justify-between items-start mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className={`text-[9px] font-bold tracking-widest flex items-center gap-1 uppercase ${colorClass.split(' ')[0]}`}>
                      {getEventIcon(ev.type)} {ev.type}
                    </span>
                  </div>
                  <span className="text-[9px] text-slate-500 tracking-wider">
                    {ev.time}
                  </span>
                </div>

                <div className="text-[11px] text-slate-200 font-bold font-sans tracking-wide leading-tight mb-1">
                  {ev.title}
                </div>
                
                <div className="text-[9px] text-slate-400 tracking-widest uppercase mb-1.5 flex items-center gap-1.5">
                  <div className="w-1 h-1 bg-slate-400 rounded-full"></div> {ev.location}
                </div>
                
                <div className="bg-black/40 border border-white/5 p-1.5 text-[9px] text-slate-300 font-mono tracking-tight flex justify-between items-center rounded-sm">
                   <div className="truncate pr-2">{ev.detail}</div>
                   <div className={`px-1 rounded-sm text-[8px] tracking-widest font-bold ${ev.severity === 'CRITICAL' || ev.severity === 'HIGH' ? 'bg-[#FF4560]/20 text-[#FF4560]' : 'bg-[#38bdf8]/20 text-[#38bdf8]'}`}>
                     {ev.severity}
                   </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default IntelligenceFeed;
