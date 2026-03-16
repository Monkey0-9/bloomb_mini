import { useTerminalStore } from '../store';
import GlobalGlobe from '../components/GlobalGlobe';
import { Crosshair, Navigation, Target, Activity, Satellite, Layers, ZoomIn, ZoomOut } from 'lucide-react';

const WorldView = () => {
  const { activeLayers, toggleLayer, updateZoom } = useTerminalStore();

  return (
    <div className="w-full h-full relative bg-void overflow-hidden font-sans select-none">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_50%,rgba(0,0,0,0.8)_100%)] pointer-events-none z-10"></div>
      
      {/* HUD OVERLAY: TOP CONTROLS */}
      <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-start z-overlay pointer-events-none bg-gradient-to-b from-void/90 via-void/40 to-transparent pb-12">
        
        {/* TOP LEFT: SYSTEM STATUS */}
        <div className="flex flex-col gap-1 pointer-events-auto">
           <div className="flex items-center gap-3 mb-1">
              <Crosshair size={14} className="text-accent-primary animate-[spin_10s_linear_infinite]" />
              <span className="type-h1 text-sm tracking-[0.25em] text-accent-primary glow-text-primary uppercase font-bold">ORBITAL SYNTHESIS KERNEL</span>
              <div className="px-2 py-0.5 bg-bull/10 border border-bull/30 flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-bull animate-ping"></div>
                  <span className="type-data-xs text-bull font-bold tracking-widest uppercase">Live Telemetry</span>
              </div>
           </div>
           
           <div className="flex gap-4 type-data-xs text-text-4 font-mono uppercase tracking-[0.1em] mt-1">
               <span className="flex items-center gap-1 border-r border-white/10 pr-4">
                   CONST: <span className="text-text-1 font-bold">S2A/S2B/L8/L9</span>
               </span>
               <span className="flex items-center gap-1 border-r border-white/10 pr-4">
                   ALT: <span className="text-text-1 font-bold">786 KM (SSO)</span>
               </span>
               <span className="flex items-center gap-1">
                   NEXT PASS: <span className="text-accent-primary font-bold shadow-glow-primary">T- 04m 12s</span>
               </span>
           </div>
        </div>

        {/* TOP RIGHT: LAYER TOGGLES */}
        <div className="flex flex-col items-end gap-2 pointer-events-auto">
           <div className="flex items-center gap-2 mb-1">
               <Layers size={12} className="text-text-4" />
               <span className="type-data-xs text-text-4 uppercase tracking-[0.2em] font-bold">Active Data Planes</span>
           </div>
           <div className="flex gap-1">
             {['PORTS', 'THERMAL', 'VESSELS', 'CLOUDS', 'MACRO'].map((l) => {
                 const isActive = activeLayers.includes(l);
                 return (
                 <button 
                    key={l}
                    onClick={() => toggleLayer(l)}
                    className={`type-data-xs px-4 py-1.5 border transition-all uppercase tracking-[0.15em] font-bold ${
                      isActive 
                      ? 'bg-accent-primary/10 text-accent-primary border-accent-primary/50 shadow-[0_0_15px_rgba(0,255,157,0.2)]' 
                      : 'bg-surface-1/40 border-border-ghost text-text-4 hover:border-text-4 hover:text-text-2'
                   }`}
                 >
                   {l}
                 </button>
             )})}
           </div>
        </div>
      </div>

      {/* LEFT PANEL: ACTIVE SURVEILLANCE TARGETS */}
      <div className="absolute top-28 left-4 z-overlay pointer-events-none w-64 flex flex-col gap-2">
         <div className="bg-void/80 backdrop-blur-md border border-border-ghost rounded-sm overflow-hidden flex flex-col max-h-[400px] pointer-events-auto shadow-[0_10px_30px_rgba(0,0,0,0.8)]">
             <div className="px-3 py-2 border-b border-border-ghost bg-surface-1/60 flex items-center justify-between">
                 <span className="text-[10px] text-text-3 uppercase tracking-widest font-bold flex items-center gap-1">
                     <Target size={10} /> Priority Targets
                 </span>
                 <span className="text-[9px] font-mono text-accent-blue bg-accent-blue/10 px-1">TRACKING 5</span>
             </div>
             
             <div className="flex-1 overflow-y-auto custom-scrollbar p-1">
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
                    className="w-full text-left px-2 py-2 hover:bg-surface-2 transition-colors flex flex-col gap-1 border-b border-white/5 last:border-0 group"
                  >
                    <div className="flex justify-between items-center">
                        <span className="type-data-sm text-text-1 font-bold tracking-tight group-hover:text-accent-primary transition-colors">{p.name}</span>
                        <span className={`text-[9px] font-bold tracking-widest px-1 ${
                            p.type === 'PORT' ? 'text-accent-blue bg-accent-blue/10' :
                            p.type === 'CHOKE' ? 'text-bear bg-bear/10' : 'text-bull bg-bull/10'
                        }`}>{p.type}</span>
                    </div>
                    <div className="flex justify-between items-center type-data-xs font-mono text-text-4 group-hover:text-text-3">
                        <span>{p.lat.toFixed(2)}°N {Math.abs(p.lng).toFixed(2)}°{p.lng < 0 ? 'W':'E'}</span>
                        <span className="font-bold text-text-2">{p.metric}</span>
                    </div>
                  </button>
                ))}
             </div>
         </div>
      </div>

      <GlobalGlobe />


      {/* BOTTOM RIGHT: CAMERA CONTROLS */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-2 z-overlay pointer-events-auto">
         <div className="bg-void/80 backdrop-blur-md border border-border-ghost flex flex-col rounded-sm shadow-xl">
            <button 
              onClick={() => updateZoom(-0.5)}
              className="w-10 h-10 flex items-center justify-center text-text-3 hover:text-accent-primary hover:bg-surface-2 transition-colors border-b border-border-ghost"
              title="Zoom In"
            >
                <ZoomIn size={16} />
            </button>
            <button 
              onClick={() => updateZoom(0.5)}
              className="w-10 h-10 flex items-center justify-center text-text-3 hover:text-accent-primary hover:bg-surface-2 transition-colors"
              title="Zoom Out"
            >
                <ZoomOut size={16} />
            </button>
         </div>
         <button className="h-10 px-3 flex items-center justify-center bg-void/80 backdrop-blur-md border border-border-ghost type-data-xs font-bold text-text-3 hover:text-accent-primary hover:bg-surface-2 transition-colors uppercase tracking-[0.2em]">
             RESET
         </button>
      </div>

      {/* FOOTER LEGEND */}
      <div className="absolute bottom-6 left-6 z-overlay pointer-events-none w-[calc(100%-100px)]">
         <div className="flex gap-6 items-center bg-void/90 backdrop-blur-xl px-6 py-3 border border-border-ghost rounded-sm shadow-2xl max-w-fit">
            <span className="text-[10px] font-bold text-text-5 uppercase tracking-[0.2em] border-r border-border-ghost pr-4 mr-2">Telemetry Legend</span>
            {[
              { label: 'OPTICAL (S2A/B)', color: 'bg-accent-primary' },
              { label: 'THERMAL (TIRS)', color: 'bg-[#FF7A3D]' },
              { label: 'SAR (C-BAND)', color: 'bg-accent-blue' },
              { label: 'AIS TRACKS', color: 'bg-bull' },
              { label: 'ADS-B CARGO', color: 'bg-[#C084FC]' }
            ].map(l => (
              <div key={l.label} className="flex items-center gap-2">
                 <div className={`w-2 h-2 ${l.color} shadow-[0_0_8px_currentColor]`}></div>
                 <span className="type-data-xs text-text-2 tracking-widest uppercase font-mono">{l.label}</span>
              </div>
            ))}
         </div>
      </div>
      
      {/* FRAME ACCENTS */}
      <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-accent-primary/50 pointer-events-none z-overlay"></div>
      <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-accent-primary/50 pointer-events-none z-overlay"></div>
      <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-accent-primary/50 pointer-events-none z-overlay"></div>
      <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-accent-primary/50 pointer-events-none z-overlay"></div>
    </div>
  );
};

export default WorldView;
