import React, { useState } from 'react';
import { useTerminalStore, useSignalStore } from '../store';
import GlobalGlobe from '../components/GlobalGlobe';
import GlobalMap2D from '../components/GlobalMap2D';
import * as Lucide from 'lucide-react';

const Activity = Lucide.Activity || Lucide.Zap;

const WorldView = () => {
  const { 
    Crosshair, 
    Layers, 
    ZoomIn, 
    ZoomOut, 
    Map: MapIcon, 
    Globe: GlobeIcon, 
    Search,
    Target,
    Zap,
    ShieldAlert
  } = Lucide;
  
  const { activeLayers, toggleLayer, updateZoom, mapMode, toggleMapMode } = useTerminalStore();
  const { signals, conflicts, indices } = useSignalStore();
  const [temporalIndex, setTemporalIndex] = useState(100);

  const gtfi = indices.find(i => i.id === 'GTFI');

  const targets = [
    ...(conflicts || []).map((c: any) => ({
      name: c.country,
      lat: c.lat || 0,
      lng: c.lon || 0,
      type: 'CONFLICT',
      metric: c.severity,
      color: 'text-bear'
    })),
    ...(signals || []).map((s: any) => ({
      name: s.name,
      lat: parseFloat(s.location.split(',')[0]) || 0,
      lng: parseFloat(s.location.split(',')[1]) || 0,
      type: 'THERMAL',
      metric: s.status.toUpperCase(),
      color: s.status === 'bullish' ? 'text-bull' : 'text-bear'
    })),
  ].slice(0, 15);

  return (
    <div className="w-full h-full relative overflow-hidden flex flex-col">
      {/* HUD: TOP STATUS */}
      <div className="absolute top-6 left-6 right-6 flex justify-between items-start z-20 pointer-events-none">
        <div className="flex flex-col gap-4 pointer-events-auto">
          <div className="glass-panel px-4 py-2 flex items-center gap-3 neo-border rounded-sm">
            <Crosshair size={14} className="text-accent-primary" />
            <span className="font-display text-lg tracking-widest text-white">ORBITAL_KERNEL_v3</span>
            <div className="h-4 w-px bg-white/10 mx-2" />
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse shadow-[0_0_8px_#10b981]" />
              <span className="text-[10px] font-mono font-bold text-bull uppercase">Live Stream</span>
            </div>
          </div>
          
          <div className="glass-panel px-4 py-2 flex items-center gap-6 border-white/5 rounded-sm">
            <div className="flex flex-col">
              <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Active Const</span>
              <span className="text-[10px] font-mono text-slate-300 font-bold">SENTINEL-2A/B</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Alt Range</span>
              <span className="text-[10px] font-mono text-slate-300 font-bold">786.4 KM</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-4 pointer-events-auto">
          <div className="flex gap-2">
            {['AIRCRAFT', 'THERMAL', 'VESSELS', 'CONFLICTS'].map(layer => (
              <button
                key={layer}
                onClick={() => toggleLayer(layer)}
                className={`px-3 py-1.5 rounded-sm border text-[9px] font-mono font-bold transition-all ${
                  activeLayers.includes(layer)
                    ? 'bg-accent-primary text-slate-950 border-accent-primary shadow-[0_0_15px_#38bdf844]'
                    : 'bg-slate-900/60 text-slate-400 border-white/10 hover:border-white/20'
                }`}
              >
                {layer}
              </button>
            ))}
          </div>

          <button
            onClick={toggleMapMode}
            className="glass-panel px-4 py-2 flex items-center gap-3 neo-border rounded-sm text-accent-primary hover:bg-white/5 transition-all"
          >
            {mapMode === '3D' ? <MapIcon size={14} /> : <GlobeIcon size={14} />}
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest">
              Switch to {mapMode === '3D' ? '2D Map' : '3D Globe'}
            </span>
          </button>
        </div>
      </div>

      {/* MAP/GLOBE VIEWPORT */}
      <div className="flex-1 relative z-0">
        {mapMode === '3D' ? <GlobalGlobe /> : <GlobalMap2D />}
      </div>

      {/* LEFT PANEL: TARGETS */}
      <div className="absolute top-32 left-6 bottom-32 w-64 z-10 pointer-events-none">
        <div className="glass-panel h-full flex flex-col neo-border pointer-events-auto rounded-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-white/10 bg-white/5 flex justify-between items-center">
            <span className="text-[10px] font-bold text-white uppercase tracking-[0.2em] flex items-center gap-2">
              <Target size={12} className="text-accent-primary" /> Priority Targets
            </span>
            <span className="text-[9px] font-mono text-slate-500">#{targets.length}</span>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {targets.map((t, i) => (
              <div key={i} className="px-4 py-3 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer group">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-[11px] font-bold text-slate-200 group-hover:text-accent-primary transition-colors truncate w-32">{t.name}</span>
                  <span className={`text-[8px] font-mono font-bold px-1 rounded-sm border border-current ${t.color}`}>{t.type}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[9px] font-mono text-slate-500">{t.lat.toFixed(2)}N, {Math.abs(t.lng).toFixed(2)}W</span>
                  <span className={`text-[10px] font-bold ${t.color}`}>{t.metric}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: GTFI */}
      <div className="absolute top-32 right-6 w-64 z-10 pointer-events-none">
        <div className="glass-panel p-6 neo-border pointer-events-auto rounded-sm space-y-6">
          <div className="flex justify-between items-start">
            <div className="flex flex-col">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Trade Flow Index</span>
              <span className="text-3xl font-display text-white tracking-tighter">{gtfi?.value || '100.0'}</span>
            </div>
            <Activity size={24} className="text-accent-primary animate-pulse" />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-[9px] font-mono font-bold">
              <span className="text-slate-500">SYSTEMIC STABILITY</span>
              <span className={gtfi?.status === 'bullish' ? 'text-bull' : 'text-bear'}>
                {gtfi?.change.toUpperCase() || 'OPTIMAL'}
              </span>
            </div>
            <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-1000 ${gtfi?.status === 'bullish' ? 'bg-bull' : 'bg-bear'}`}
                style={{ width: `${gtfi?.value || 100}%` }}
              />
            </div>
          </div>

          <p className="text-[9px] text-slate-400 font-medium leading-relaxed uppercase tracking-widest border-t border-white/5 pt-4">
            Aggregated health score of 2,142 maritime agents reacting to live kinetic and industrial seeds.
          </p>
        </div>
      </div>

      {/* BOTTOM HUD: CONTROLS */}
      <div className="absolute bottom-6 left-6 right-6 flex justify-between items-end z-20 pointer-events-none">
        <div className="glass-panel px-6 py-4 flex flex-col gap-3 neo-border pointer-events-auto rounded-sm min-w-[400px]">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-white uppercase tracking-widest flex items-center gap-2">
              <Zap size={12} className="text-accent-primary" /> Temporal Scrubber
            </span>
            <span className="text-[10px] font-mono text-accent-primary font-bold">T - {100 - temporalIndex}m</span>
          </div>
          <input 
            type="range" 
            min="0" max="100" 
            value={temporalIndex} 
            onChange={(e) => setTemporalIndex(parseInt(e.target.value))}
            className="w-full h-1 bg-slate-800 appearance-none cursor-pointer accent-accent-primary"
          />
          <div className="flex justify-between text-[8px] font-mono text-slate-500 uppercase tracking-widest">
            <span>Historical</span>
            <span>Real-Time</span>
          </div>
        </div>

        <div className="flex flex-col gap-2 pointer-events-auto">
          <div className="glass-panel flex flex-col border-white/5 rounded-sm overflow-hidden">
            <button 
              onClick={() => updateZoom(0.5)}
              className="p-3 text-slate-400 hover:text-white hover:bg-white/5 transition-all border-b border-white/5"
            >
              <ZoomIn size={16} />
            </button>
            <button 
              onClick={() => updateZoom(-0.5)}
              className="p-3 text-slate-400 hover:text-white hover:bg-white/5 transition-all"
            >
              <ZoomOut size={16} />
            </button>
          </div>
          <button className="glass-panel px-4 py-2 text-[10px] font-mono font-bold text-slate-400 hover:text-white rounded-sm uppercase tracking-widest transition-all">
            Reset Camera
          </button>
        </div>
      </div>

      {/* FRAME ACCENTS */}
      <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-accent-primary/20 pointer-events-none" />
      <div className="absolute top-0 right-0 w-12 h-12 border-t-2 border-r-2 border-accent-primary/20 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-12 h-12 border-b-2 border-l-2 border-accent-primary/20 pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-accent-primary/20 pointer-events-none" />
    </div>
  );
};

export default WorldView;
