import { useState } from 'react';
import GlobalGlobe from '../components/GlobalGlobe';

const WorldView = () => {
  const [activeLayers, setActiveLayers] = useState<string[]>(['PORTS', 'VESSELS', 'THERMAL']);

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
               onClick={() => setActiveLayers(prev => prev.includes(l) ? prev.filter(x => x !== l) : [...prev, l])}
               className={`type-data-xs px-3 py-1 border transition-all rounded-sm uppercase tracking-widest ${
                 activeLayers.includes(l) ? 'bg-accent-primary text-void border-accent-primary font-bold shadow-[0_0_10px_rgba(0,200,255,0.3)]' : 'bg-surface-1/40 border-white/10 text-text-3 hover:border-white/30'
               }`}
             >
               {l}
             </button>
           ))}
        </div>
      </div>

      <GlobalGlobe />

      {/* BOTTOM HUD CONTROLS */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-1 z-overlay">
         <div className="bg-void/60 backdrop-blur-md border border-white/10 p-1 flex flex-col gap-1 rounded-sm">
            <button className="w-7 h-7 flex items-center justify-center type-h1 text-text-2 hover:bg-surface-3 transition-colors">＋</button>
            <div className="h-[1px] bg-white/5 mx-1"></div>
            <button className="w-7 h-7 flex items-center justify-center type-h1 text-text-2 hover:bg-surface-3 transition-colors">－</button>
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

