import { useTerminalStore } from '../store';
import GlobalGlobe from '../components/GlobalGlobe';
import GlobalMap2D from '../components/GlobalMap2D';
import { Crosshair, Target, Zap, Layers, ZoomIn, ZoomOut, Map as MapIcon, Globe as GlobeIcon } from 'lucide-react';

const WorldView = () => {
  const { activeLayers, toggleLayer, updateZoom, mapMode, toggleMapMode } = useTerminalStore();

  return (
    <div className="w-full h-full relative bg-[var(--bg-base)] overflow-hidden select-none">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_40%,rgba(0,0,0,0.7)_100%)] pointer-events-none z-10"></div>
      
      {/* HUD OVERLAY: TOP CONTROLS */}
      <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-start z-20 pointer-events-none">
        
        {/* TOP LEFT: SYSTEM STATUS */}
        <div className="flex flex-col gap-2 pointer-events-auto">
           <div className="flex items-center gap-3 mb-1 bg-[#040B16]/80 backdrop-blur-md px-4 py-2 rounded-full border border-[#38bdf8]/30 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
              <Crosshair size={14} className="text-[#38bdf8]" />
              <span className="text-[11px] tracking-[0.25em] text-[#38bdf8] font-bold uppercase drop-shadow-[0_0_5px_rgba(56,189,248,0.8)]">WORLD MONITOR KERNEL</span>
              <div className="ml-2 px-2.5 py-1 bg-[#00FF9D]/10 border border-[#00FF9D]/40 flex items-center gap-2 rounded-full shadow-[0_0_10px_rgba(0,255,157,0.2)]">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00FF9D] shadow-[0_0_8px_#00FF9D] animate-pulse"></div>
                  <span className="text-[9px] text-[#00FF9D] font-bold tracking-widest uppercase">Live Telemetry</span>
              </div>
           </div>
           
           <div className="flex gap-4 text-[10px] text-slate-400 font-mono uppercase tracking-[0.15em] bg-[#040B16]/60 backdrop-blur-md px-4 py-1.5 rounded-full border border-slate-800/50 w-fit">
               <span className="border-r border-slate-700 pr-4 drop-shadow-md">
                   Const: <span className="text-slate-200 font-bold">S2A/S2B/L8/L9</span>
               </span>
               <span className="border-r border-slate-700 pr-4 drop-shadow-md">
                   Alt: <span className="text-slate-200 font-bold">786 KM (SSO)</span>
               </span>
               <span className="drop-shadow-md">
                   Next: <span className="text-[#38bdf8] font-bold drop-shadow-[0_0_5px_#38bdf8]">T- 04m 12s</span>
               </span>
           </div>
        </div>

        {/* TOP RIGHT: LAYER TOGGLES */}
        <div className="flex flex-col items-end gap-2 pointer-events-auto">
           <div className="flex items-center gap-2 bg-[#040B16]/80 backdrop-blur-sm px-3 py-1.5 rounded-full border border-slate-800/50">
               <Layers size={11} className="text-[#38bdf8]" />
               <span className="text-[9px] text-slate-300 uppercase tracking-[0.2em] font-bold">Data Planes</span>
           </div>
           <div className="flex gap-1.5 flex-wrap justify-end max-w-[400px]">
             {['AIRCRAFT', 'THERMAL', 'SATELLITES', 'QUAKES', 'CONFLICTS', 'PORTS', 'VESSELS'].map((l) => {
                 const isActive = activeLayers.includes(l);
                 return (
                 <button 
                    key={l}
                    onClick={() => toggleLayer(l)}
                    className={`text-[9px] px-3.5 py-1.5 border transition-all uppercase tracking-[0.15em] font-bold ${
                      isActive 
                      ? 'bg-[#040B16] text-[#38bdf8] border-[#38bdf8] shadow-[0_0_15px_rgba(56,189,248,0.3)]' 
                      : 'bg-black/60 backdrop-blur-md border-[#38bdf8]/20 text-slate-500 hover:border-[#38bdf8]/50 hover:text-[#38bdf8]/80'
                    }`}
                 >
                   {l}
                 </button>
             )})}
           </div>
           <div className="flex flex-col items-end gap-1.5 pointer-events-auto mt-2">
            <button
               onClick={toggleMapMode}
               className="flex items-center gap-2 px-3 py-1 border transition-all uppercase tracking-[0.1em] font-bold bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:border-[var(--neon-bull)] hover:text-[var(--neon-bull)]"
            >
               {mapMode === '3D' ? <MapIcon size={12} /> : <GlobeIcon size={12} />}
               <span className="text-[9px]">{mapMode === '3D' ? 'SWITCH TO 2D FLAT' : 'SWITCH TO 3D GLOBE'}</span>
            </button>
         </div>
      </div>
      </div>

      {/* LEFT PANEL: ACTIVE SURVEILLANCE TARGETS */}
      <div className="absolute top-24 left-4 z-[20] pointer-events-none w-64 flex flex-col gap-2">
         <div className="bg-black/60 backdrop-blur-md border border-[#38bdf8]/30 shadow-[0_0_20px_rgba(56,189,248,0.15)] overflow-hidden flex flex-col max-h-[360px] pointer-events-auto rounded-sm">
             <div className="px-3 py-2 border-b border-[#38bdf8]/30 bg-[#040B16]/80 flex items-center justify-between">
                 <span className="text-[10px] text-[#38bdf8] uppercase  tracking-[0.2em] font-bold flex items-center gap-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.6)]">
                     <Target size={12} className="animate-pulse" /> Priority Targets
                 </span>
                 <span className="text-[9px] font-mono text-[#00FF9D] bg-[#00FF9D]/10 px-1.5 py-0.5 border border-[#00FF9D]/30 shadow-[0_0_8px_rgba(0,255,157,0.2)]">TRACKING 5</span>
             </div>
             
             <div className="flex-1 overflow-y-auto p-0.5">
                {[
                  { name: 'NLRTM (Rotterdam)', lat: 51.9, lng: 4.5, type: 'PORT', metric: '94% Cap' },
                  { name: 'SGSIN (Singapore)', lat: 1.3, lng: 103.8, type: 'PORT', metric: '88% Cap' },
                  { name: 'CNSHG (Shanghai)', lat: 31.2, lng: 121.5, type: 'PORT', metric: '102% Cap' },
                  { name: 'Freeport LNG', lat: 28.9, lng: -95.3, type: 'FACILITY', metric: 'Offline' },
                  { name: 'Gatun Locks (Panama)', lat: 9.2, lng: -79.9, type: 'CHOKE', metric: '-40% T' }
                ].map(p => (
                  <button 
                    key={p.name}
                    onClick={() => updateZoom(3)} 
                    className="w-full text-left px-2 py-1.5 hover:bg-[var(--bg-hover)] transition-colors flex flex-col gap-0.5 border-b border-[var(--border-subtle)] last:border-0 group"
                  >
                    <div className="flex justify-between items-center">
                        <span className="text-[10px] text-[var(--text-primary)] font-bold tracking-tight group-hover:text-[var(--neon-bull)] transition-colors">{p.name}</span>
                        <span className={`text-[8px] font-bold tracking-widest px-1 border ${
                            p.type === 'PORT' ? 'text-[var(--neon-signal)] bg-[var(--neon-dim-signal)] border-[var(--neon-signal)]/20' :
                            p.type === 'CHOKE' ? 'text-[var(--neon-bear)] bg-[var(--neon-dim-bear)] border-[var(--neon-bear)]/20' : 'text-[var(--neon-bull)] bg-[var(--neon-dim-bull)] border-[var(--neon-bull)]/20'
                        }`}>{p.type}</span>
                    </div>
                    <div className="flex justify-between items-center text-[8px] font-mono text-[var(--text-tertiary)] group-hover:text-[var(--text-secondary)]">
                        <span>{p.lat.toFixed(2)}°N {Math.abs(p.lng).toFixed(2)}°{p.lng < 0 ? 'W':'E'}</span>
                        <span className="font-bold text-[var(--text-secondary)]">{p.metric}</span>
                    </div>
                  </button>
                ))}
             </div>
         </div>
      </div>

      {mapMode === '3D' ? <GlobalGlobe /> : <GlobalMap2D />}

      {/* BOTTOM RIGHT: CAMERA CONTROLS */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-2 z-20 pointer-events-auto">
         <div className="bg-[#040B16]/80 backdrop-blur-md border border-slate-700/50 flex flex-col shadow-[0_0_15px_rgba(0,0,0,0.5)] rounded-sm overflow-hidden">
            <button 
              onClick={() => updateZoom(-0.5)}
              className="w-10 h-10 flex items-center justify-center text-slate-400 hover:text-[#38bdf8] hover:bg-[#38bdf8]/10 transition-colors border-b border-slate-800/50"
              title="Zoom In"
            >
                <ZoomIn size={16} />
            </button>
            <button 
              onClick={() => updateZoom(0.5)}
              className="w-10 h-10 flex items-center justify-center text-slate-400 hover:text-[#38bdf8] hover:bg-[#38bdf8]/10 transition-colors"
              title="Zoom Out"
            >
                <ZoomOut size={16} />
            </button>
         </div>
         <button className="h-8 px-2 flex items-center justify-center bg-[#040B16]/80 backdrop-blur-md border border-slate-700/50 text-[9px] font-bold text-slate-400 hover:text-[#38bdf8] hover:bg-[#38bdf8]/10 transition-colors uppercase tracking-[0.2em] rounded-sm shadow-xl">
             Reset
         </button>
      </div>

      {/* FOOTER LEGEND */}
      <div className="absolute bottom-6 left-6 z-20 pointer-events-none w-[calc(100%-100px)]">
         <div className="flex gap-4 items-center bg-[#040B16]/80 backdrop-blur-md px-5 py-2.5 border border-slate-800/80 max-w-fit shadow-[0_0_20px_rgba(0,0,0,0.5)] rounded-full">
            <span className="text-[10px] font-bold text-slate-300 uppercase tracking-[0.25em] border-r border-slate-700 pr-4 mr-2">Telemetry Legend</span>
            {[
              { label: 'Optical', color: 'bg-[#00D4FF] shadow-[0_0_8px_#00D4FF]' },
              { label: 'Thermal', color: 'bg-[#FF7A3D] shadow-[0_0_8px_#FF7A3D]' },
              { label: 'SAR (C-Band)', color: 'bg-[#70B1FF] shadow-[0_0_8px_#70B1FF]' },
              { label: 'AIS Tracks', color: 'bg-[#00FF9D] shadow-[0_0_8px_#00FF9D]' },
              { label: 'ADSB-Cargo', color: 'bg-[#C084FC] shadow-[0_0_8px_#C084FC]' }
            ].map(l => (
              <div key={l.label} className="flex items-center gap-2">
                 <div className={`w-2 h-2 rounded-full ${l.color}`}></div>
                 <span className="text-[9px] text-slate-400 font-bold tracking-[0.15em] uppercase font-mono">{l.label}</span>
              </div>
            ))}
         </div>
      </div>
      
      {/* FRAME ACCENTS */}
      <div className="absolute top-0 left-0 w-8 h-8 border-t border-l border-[#38bdf8]/40 pointer-events-none z-30"></div>
      <div className="absolute top-0 right-0 w-8 h-8 border-t border-r border-[#38bdf8]/40 pointer-events-none z-30"></div>
      <div className="absolute bottom-0 left-0 w-8 h-8 border-b border-l border-[#38bdf8]/40 pointer-events-none z-30"></div>
      <div className="absolute bottom-0 right-0 w-8 h-8 border-b border-r border-[#38bdf8]/40 pointer-events-none z-30"></div>
    </div>
  );
};

export default WorldView;
