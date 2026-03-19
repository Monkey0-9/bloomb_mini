import { useTerminalStore } from '../store';
import GlobalGlobe from '../components/GlobalGlobe';
import { Crosshair, Target, Zap, Layers, ZoomIn, ZoomOut } from 'lucide-react';

const WorldView = () => {
  const { activeLayers, toggleLayer, updateZoom } = useTerminalStore();

  return (
    <div className="w-full h-full relative bg-[var(--bg-base)] overflow-hidden select-none">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_40%,rgba(0,0,0,0.9)_100%)] pointer-events-none z-10"></div>
      
      {/* HUD OVERLAY: TOP CONTROLS */}
      <div className="absolute top-0 left-0 right-0 p-3 flex justify-between items-start z-[20] pointer-events-none">
        
        {/* TOP LEFT: SYSTEM STATUS */}
        <div className="flex flex-col gap-1 pointer-events-auto">
           <div className="flex items-center gap-2 mb-1">
              <Crosshair size={12} className="text-[var(--neon-bull)] animate-pulse" />
              <span className="text-[10px] tracking-[0.2em] text-[var(--neon-bull)] font-bold uppercase">Orbital Synthesis Kernel</span>
              <div className="px-1.5 py-0.5 bg-[var(--neon-dim-bull)] border border-[var(--neon-bull)]/30 flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 bg-[var(--neon-bull)] shadow-[0_0_4px_var(--neon-bull)] animate-pulse"></div>
                  <span className="text-[8px] text-[var(--neon-bull)] font-bold tracking-widest uppercase">Live Telemetry</span>
              </div>
           </div>
           
           <div className="flex gap-4 text-[9px] text-[var(--text-tertiary)] font-mono uppercase tracking-[0.1em]">
               <span className="border-r border-[var(--border-subtle)] pr-4">
                   Const: <span className="text-[var(--text-primary)] font-bold">S2A/S2B/L8/L9</span>
               </span>
               <span className="border-r border-[var(--border-subtle)] pr-4">
                   Alt: <span className="text-[var(--text-primary)] font-bold">786 KM (SSO)</span>
               </span>
               <span>
                   Next: <span className="text-[var(--neon-bull)] font-bold">T- 04m 12s</span>
               </span>
           </div>
        </div>

        {/* TOP RIGHT: LAYER TOGGLES */}
        <div className="flex flex-col items-end gap-1.5 pointer-events-auto">
           <div className="flex items-center gap-2">
               <Layers size={10} className="text-[var(--text-tertiary)]" />
               <span className="text-[8px] text-[var(--text-tertiary)] uppercase tracking-[0.2em] font-bold">Data Planes</span>
           </div>
           <div className="flex gap-1">
             {['PORTS', 'THERMAL', 'VESSELS', 'CLOUDS', 'MACRO'].map((l) => {
                 const isActive = activeLayers.includes(l);
                 return (
                 <button 
                    key={l}
                    onClick={() => toggleLayer(l)}
                    className={`text-[9px] px-3 py-1 border transition-all uppercase tracking-[0.1em] font-bold ${
                      isActive 
                      ? 'bg-[var(--neon-dim-signal)] text-[var(--neon-signal)] border-[var(--neon-signal)]/50 shadow-[0_0_10px_rgba(0,212,255,0.1)]' 
                      : 'bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:border-[var(--text-secondary)] hover:text-[var(--text-secondary)]'
                    }`}
                 >
                   {l}
                 </button>
             )})}
           </div>
        </div>
      </div>

      {/* LEFT PANEL: ACTIVE SURVEILLANCE TARGETS */}
      <div className="absolute top-24 left-3 z-[20] pointer-events-none w-60 flex flex-col gap-2">
         <div className="bg-[var(--bg-overlay)] backdrop-blur-md border border-[var(--border-subtle)] overflow-hidden flex flex-col max-h-[360px] pointer-events-auto">
             <div className="px-2.5 py-1.5 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)] flex items-center justify-between">
                 <span className="text-[9px] text-[var(--text-secondary)] uppercase tracking-widest font-bold flex items-center gap-1.5">
                     <Target size={10} /> Priority Targets
                 </span>
                 <span className="text-[8px] font-mono text-[var(--neon-bull)] bg-[var(--neon-dim-bull)] px-1 border border-[var(--neon-bull)]/20">TRACKING 5</span>
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

      <GlobalGlobe />

      {/* BOTTOM RIGHT: CAMERA CONTROLS */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-2 z-[20] pointer-events-auto">
         <div className="bg-[var(--bg-overlay)] backdrop-blur-sm border border-[var(--border-subtle)] flex flex-col shadow-2xl">
            <button 
              onClick={() => updateZoom(-0.5)}
              className="w-8 h-8 flex items-center justify-center text-[var(--text-tertiary)] hover:text-[var(--neon-signal)] hover:bg-[var(--bg-hover)] transition-colors border-b border-[var(--border-subtle)]"
              title="Zoom In"
            >
                <ZoomIn size={14} />
            </button>
            <button 
              onClick={() => updateZoom(0.5)}
              className="w-8 h-8 flex items-center justify-center text-[var(--text-tertiary)] hover:text-[var(--neon-signal)] hover:bg-[var(--bg-hover)] transition-colors"
              title="Zoom Out"
            >
                <ZoomOut size={14} />
            </button>
         </div>
         <button className="h-8 px-2 flex items-center justify-center bg-[var(--bg-overlay)] backdrop-blur-sm border border-[var(--border-subtle)] text-[9px] font-bold text-[var(--text-tertiary)] hover:text-[var(--neon-signal)] hover:bg-[var(--bg-hover)] transition-colors uppercase tracking-[0.2em]">
             Reset
         </button>
      </div>

      {/* FOOTER LEGEND */}
      <div className="absolute bottom-6 left-6 z-[20] pointer-events-none w-[calc(100%-100px)]">
         <div className="flex gap-4 items-center bg-[var(--bg-overlay)] backdrop-blur-md px-4 py-2 border border-[var(--border-subtle)] max-w-fit shadow-2xl">
            <span className="text-[9px] font-bold text-[var(--text-tertiary)] uppercase tracking-[0.2em] border-r border-[var(--border-subtle)] pr-4 mr-2">Telemetry Legend</span>
            {[
              { label: 'Optical', color: 'bg-[var(--neon-signal)]' },
              { label: 'Thermal', color: 'bg-[#FF7A3D]' },
              { label: 'SAR (C-Band)', color: 'bg-[#70B1FF]' },
              { label: 'AIS Tracks', color: 'bg-[var(--neon-bull)]' },
              { label: 'ADSB-Cargo', color: 'bg-[#C084FC]' }
            ].map(l => (
              <div key={l.label} className="flex items-center gap-1.5">
                 <div className={`w-1.5 h-1.5 ${l.color} shadow-[0_0_4px_currentColor]`}></div>
                 <span className="text-[8px] text-[var(--text-secondary)] tracking-widest uppercase font-mono">{l.label}</span>
              </div>
            ))}
         </div>
      </div>
      
      {/* FRAME ACCENTS */}
      <div className="absolute top-0 left-0 w-6 h-6 border-t border-l border-[var(--neon-bull)]/30 pointer-events-none z-[30]"></div>
      <div className="absolute top-0 right-0 w-6 h-6 border-t border-r border-[var(--neon-bull)]/30 pointer-events-none z-[30]"></div>
      <div className="absolute bottom-0 left-0 w-6 h-6 border-b border-l border-[var(--neon-bull)]/30 pointer-events-none z-[30]"></div>
      <div className="absolute bottom-0 right-0 w-6 h-6 border-b border-r border-[var(--neon-bull)]/30 pointer-events-none z-[30]"></div>
    </div>
  );
};

export default WorldView;
