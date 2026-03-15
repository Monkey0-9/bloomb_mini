import { useTerminalStore } from '../store';
import GlobalGlobe from '../components/GlobalGlobe';

const WorldView = () => {
  const { activeLayers, toggleLayer, updateZoom } = useTerminalStore();

  return (
    <div className="w-full h-full relative bg-void overflow-hidden">
      {/* HUD OVERLAY: TOP CONTROLS */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-start z-overlay pointer-events-none">
        <div className="flex flex-col gap-1 pointer-events-auto">
           <div className="flex items-center gap-2">
              <span className="type-h1 text-sm tracking-[0.2em] text-accent-primary glow-text-primary">GLOBAL PHYSICAL REALITY</span>
              <div className="w-2 h-2 rounded-full bg-bull dot-live"></div>
           </div>
           <span className="type-data-xs text-text-3 uppercase tracking-widest">Orbit Status: <span className="text-text-1">Optimal</span> • Next Pass: <span className="text-accent-primary underline italic">04m 12s</span></span>
        </div>

        <div className="flex gap-2 pointer-events-auto">
           {['PORTS', 'RETAIL', 'THERMAL', 'VESSELS', 'CLOUDS'].map((l) => (
             <button 
                key={l}
                onClick={() => toggleLayer(l)}
                className={`type-data-xs px-3 py-1 border transition-all rounded-sm uppercase tracking-widest ${
                  activeLayers.includes(l) ? 'bg-accent-primary text-void border-accent-primary font-bold shadow-[0_0_10px_rgba(0,200,255,0.3)]' : 'bg-surface-1/40 border-white/10 text-text-3 hover:border-white/30'
               }`}
             >
               {l}
             </button>
           ))}
        </div>
      </div>

      {/* PORT INDEX PANEL */}
      <div className="absolute top-24 left-4 z-overlay pointer-events-auto w-48 bg-void/60 backdrop-blur-md border border-white/10 rounded-sm overflow-hidden flex flex-col max-h-[300px]">
         <div className="p-2 border-b border-white/10 bg-surface-1/40 text-[9px] text-text-4 uppercase tracking-widest font-bold">Port Registry</div>
         <div className="flex-1 overflow-y-auto custom-scrollbar p-1 space-y-0.5">
            {[
              { name: 'ROTTERDAM', lat: 51.9, lng: 4.5 },
              { name: 'SINGAPORE', lat: 1.3, lng: 103.8 },
              { name: 'SHANGHAI', lat: 31.2, lng: 121.5 },
              { name: 'LONG BEACH', lat: 33.7, lng: -118.3 },
              { name: 'JEBEL ALI', lat: 25.0, lng: 55.0 }
            ].map(p => (
              <button 
                key={p.name}
                onClick={() => updateZoom(3)} // Zoom in
                className="w-full text-left px-2 py-1.5 hover:bg-accent-primary hover:text-void transition-colors type-data-xs truncate"
              >
                {p.name}
              </button>
            ))}
         </div>
      </div>

      <GlobalGlobe />

      {/* BOTTOM HUD CONTROLS */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-1 z-overlay">
         <div className="bg-void/60 backdrop-blur-md border border-white/10 p-1 flex flex-col gap-1 rounded-sm">
            <button 
              onClick={() => updateZoom(-0.5)}
              className="w-7 h-7 flex items-center justify-center type-h1 text-text-2 hover:bg-surface-3 transition-colors"
            >＋</button>
            <div className="h-[1px] bg-white/5 mx-1"></div>
            <button 
              onClick={() => updateZoom(0.5)}
              className="w-7 h-7 flex items-center justify-center type-h1 text-text-2 hover:bg-surface-3 transition-colors"
            >－</button>
         </div>
         <button className="h-7 px-2 bg-void/60 backdrop-blur-md border border-white/10 type-data-xs text-text-2 hover:bg-surface-3 transition-colors uppercase">3D</button>
      </div>

      {/* FOOTER LEGEND */}
      <div className="absolute bottom-6 left-6 pointer-events-none z-overlay">
         <div className="flex gap-6 items-center bg-void/60 backdrop-blur-xl px-4 py-2 border border-white/5 rounded-sm shadow-2xl">
            {[
              { label: 'OPTICAL', color: 'bg-accent-primary' },
              { label: 'THERMAL', color: 'bg-[#FF7A3D]' },
              { label: 'SAR (RADAR)', color: 'bg-accent-secondary' },
              { label: 'AIS TRACKS', color: 'bg-bull' }
            ].map(l => (
              <div key={l.label} className="flex items-center gap-2">
                 <div className={`w-1.5 h-1.5 rounded-full ${l.color} shadow-[0_0_5px_currentColor]`}></div>
                 <span className="type-data-xs text-text-4 tracking-widest uppercase">{l.label}</span>
              </div>
            ))}
         </div>
      </div>
    </div>
  );
};

export default WorldView;

