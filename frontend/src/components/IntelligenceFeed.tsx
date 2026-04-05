import React, { useEffect, useState } from 'react';
import * as Lucide from 'lucide-react';
import { useSignalStore, useTerminalStore, useFlightStore, useVesselStore } from '../store';

const Activity = Lucide.Activity || Lucide.Zap;

const getEventColor = (type: string) => {
  switch (type.toUpperCase()) {
    case 'CONFLICT': return 'text-bear border-bear/30 shadow-glow-bear';
    case 'EARTHQUAKE': return 'text-amber-500 border-amber-500/30';
    case 'AIRCRAFT': return 'text-sky-400 border-sky-400/30';
    case 'VESSEL': return 'text-bull border-bull/30 shadow-glow-bull';
    case 'THERMAL': return 'text-orange-500 border-orange-500/30';
    default: return 'text-accent-primary border-accent-primary/30 shadow-glow-sky';
  }
};

const getEventIcon = (type: string) => {
  const { ShieldAlert, Navigation, Flame, Radio } = Lucide;
  switch (type.toUpperCase()) {
    case 'CONFLICT': return <ShieldAlert size={12} />;
    case 'EARTHQUAKE': return <Activity size={12} />;
    case 'AIRCRAFT': return <Navigation size={12} />;
    case 'VESSEL': return <Navigation size={12} className="rotate-180" />;
    case 'THERMAL': return <Flame size={12} />;
    default: return <Radio size={12} />;
  }
};

const formatTime = (dateStr: string | null) => {
  if (!dateStr) return new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    return d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  } catch {
    return new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  }
};

const getTimestamp = (dateStr: string | null) => {
  if (!dateStr) return Date.now();
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? Date.now() : d.getTime();
};

const IntelligenceFeed = () => {
  const { Zap, ChevronRight, RefreshCw } = Lucide;
  const { signals, fetchSignals } = useSignalStore();
  const { flights, fetchFlights } = useFlightStore();
  const { vessels, fetchVessels } = useVesselStore();
  const { setSelectedIntelligenceEvent } = useTerminalStore();
  
  const [feed, setFeed] = useState<any[]>([]);

  useEffect(() => {
    fetchSignals();
    fetchFlights();
    fetchVessels();
  }, [fetchSignals, fetchFlights, fetchVessels]);

  useEffect(() => {
    const events: any[] = [];
    
    signals.forEach((s: any, i) => {
      if(i > 15) return;
      events.push({
        id: `th-${s.id}`,
        time: formatTime(s.detected_at || s.as_of),
        timestamp: getTimestamp(s.detected_at || s.as_of),
        type: 'THERMAL',
        title: s.name,
        location: s.location || 'Unknown',
        detail: `Confidence: ${s.score?.toFixed(1) || '0.0'} | Signal: ${s.signal || 'NEUTRAL'}`,
        severity: (s.score || 0) > 80 ? 'CRITICAL' : 'ELEVATED',
        raw: s
      });
    });

    flights.forEach((f: any) => {
      if(f.category !== 'COMMERCIAL') {
        events.push({
          id: `fl-${f.icao24}`,
          time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
          timestamp: Date.now(),
          type: 'AIRCRAFT',
          title: `[${f.category}] ${f.callsign}`,
          location: f.route || 'Airspace',
          detail: `Operator: ${f.operator} | Alt: ${f.position?.alt_ft || f.alt_ft || 0}ft`,
          severity: f.category === 'MILITARY' ? 'HIGH' : 'INFO',
          raw: f
        });
      }
    });

    vessels.forEach((v: any) => {
      const isHighInterest = v.dark || ['Cargo', 'Tanker'].includes(v.type);
      if (isHighInterest) {
        events.push({
          id: `vs-${v.mmsi || v.id}`,
          time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
          timestamp: Date.now(),
          type: 'VESSEL',
          title: `[MARINE] ${v.name || 'VESSEL'}`,
          location: v.destination || 'Maritime Route',
          detail: `Status: ${v.status || 'Under Way'} | Cargo: ${v.cargo || 'General'}`,
          severity: v.dark ? 'HIGH' : 'INFO',
          raw: v
        });
      }
    });

    events.sort((a, b) => b.timestamp - a.timestamp);
    setFeed(events);
  }, [signals, flights, vessels]);

  return (
    <div className="flex flex-col h-full bg-slate-950/60 backdrop-blur-xl border-l border-white/5 font-mono select-none overflow-hidden relative">
      <header className="p-4 border-b border-white/10 flex flex-col gap-2 bg-slate-900/40 shrink-0">
          <div className="flex justify-between items-center">
            <span className="text-[11px] text-white font-black tracking-[0.3em] flex items-center gap-2 uppercase font-display">
              <Zap size={14} className="text-accent-primary animate-pulse" /> Unified_Intelligence
            </span>
            <div className="flex gap-1.5 items-center">
               <div className="w-1.5 h-1.5 rounded-full bg-bear shadow-glow-bear animate-pulse" />
               <div className="w-1.5 h-1.5 rounded-full bg-bull shadow-glow-bull animate-pulse" style={{animationDelay: '300ms'}} />
            </div>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[9px] text-slate-500 tracking-[0.2em] uppercase font-bold">L7_SYNTHETIC_STREAM</span>
            <span className="text-[8px] font-mono text-accent-primary opacity-60">INGEST_RATE: 4.2 Gbps</span>
          </div>
      </header>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
        {feed.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-20">
            <RefreshCw size={32} className="animate-spin text-white" />
            <span className="text-[10px] font-bold uppercase tracking-[0.4em]">Acquiring_Uplink</span>
          </div>
        ) : (
          feed.map((ev, i) => {
            const colorClass = getEventColor(ev.type);
            return (
              <div key={`${ev.id}-${i}`} className="relative pl-6 group cursor-crosshair" onClick={() => setSelectedIntelligenceEvent(ev)}>
                {/* Timeline Stem */}
                <div className="absolute left-[7px] top-6 bottom-[-16px] w-px bg-white/5 group-last:hidden" />
                
                {/* Timeline Node */}
                <div className={`absolute left-0 top-1.5 w-[16px] h-[16px] rounded-sm bg-slate-950 border flex items-center justify-center z-10 transition-all group-hover:scale-110 group-hover:border-white/40 ${colorClass.split(' ')[0]} ${colorClass.split(' ')[1]}`}>
                  {getEventIcon(ev.type)}
                </div>

                <div className="glass-panel p-4 neo-border rounded-sm group-hover:bg-white/5 transition-all relative overflow-hidden">
                  <div className={`absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-current to-transparent opacity-0 group-hover:opacity-40 transition-opacity ${colorClass.split(' ')[0]}`} />
                  
                  <div className="flex justify-between items-start mb-2">
                    <span className={`text-[9px] font-black tracking-widest uppercase ${colorClass.split(' ')[0]}`}>
                      {ev.type} // {ev.severity}
                    </span>
                    <span className="text-[9px] font-mono text-slate-500 font-bold tracking-tighter">
                      {ev.time}
                    </span>
                  </div>

                  <h4 className="text-[12px] text-white font-bold tracking-tight mb-2 group-hover:text-accent-primary transition-colors leading-tight">{ev.title}</h4>
                  
                  <div className="flex items-center gap-2 mb-3">
                    <Lucide.MapPin size={10} className="text-slate-600" />
                    <span className="text-[9px] text-slate-500 uppercase font-bold tracking-widest">{ev.location}</span>
                  </div>
                  
                  <div className="bg-black/40 border border-white/5 p-2 rounded-sm flex justify-between items-center group-hover:border-white/10 transition-colors">
                     <span className="text-[10px] text-slate-400 font-mono truncate pr-4">{ev.detail}</span>
                     <ChevronRight size={12} className="text-slate-700 group-hover:text-accent-primary transition-colors" />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default IntelligenceFeed;
