import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSignalStore } from '../store';
import * as Lucide from 'lucide-react';

const SatelliteFeed = () => {
  const { Search, Filter, Maximize2, Download, Info, Zap, Globe, Clock, Layers } = Lucide;
  const [search, setSearch] = useState('');
  const [brightness, setBrightness] = useState(85);
  const [filter, setFilter] = useState('ALL');
  const { satFeed } = useSignalStore();
  
  const images = useMemo(() => {
    const baseImagery = [
      { 
        id: 'b1', 
        location: 'Rotterdam Europort', 
        time: '5h 42m ago', 
        cloud: '8%', 
        res: '10m', 
        type: 'SENTINEL-2', 
        signal: 'BULLISH', 
        detail: 'Visual confirmation of 12 VLCC vessels at berthing sector 4. Significant gantry movement.',
        url: 'https://images.unsplash.com/photo-1590214840332-60cc328f645a?auto=format&fit=crop&w=800&q=80' 
      },
      { 
        id: 'b2', 
        location: 'Singapore Jurong Island', 
        time: '3h 12m ago', 
        cloud: '12%', 
        res: '10m', 
        type: 'SENTINEL-2', 
        signal: 'STABLE', 
        detail: 'Thermal storage tanks at 84% capacity. Consistent with seasonal export patterns.',
        url: 'https://images.unsplash.com/photo-1566847438217-76e82d383f84?auto=format&fit=crop&w=800&q=80' 
      },
    ];

    const liveItems = (satFeed || []).map((s: any) => ({
      id: s.id,
      location: s.location,
      time: s.time,
      cloud: s.cloud,
      res: s.res,
      type: s.type,
      signal: s.signal?.toUpperCase() || 'STABLE',
      detail: s.detail,
      url: s.url
    }));

    return [...liveItems, ...baseImagery];
  }, [satFeed]);

  const filteredImages = useMemo(() => {
    let result = images;
    if (search) {
      const lowercasedSearch = search.toLowerCase();
      result = result.filter((img: any) => 
        img.location.toLowerCase().includes(lowercasedSearch) ||
        img.detail.toLowerCase().includes(lowercasedSearch)
      );
    }
    if (filter !== 'ALL') {
      result = result.filter((img: any) => img.signal === filter);
    }
    return result;
  }, [images, search, filter]);

  return (
    <div className="flex-1 flex flex-col bg-slate-950 font-mono h-full overflow-hidden">
      {/* OSINT HEADER */}
      <header className="h-14 border-b border-white/5 flex items-center justify-between px-8 bg-slate-900/40 shrink-0 backdrop-blur-md z-20">
         <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
               <Layers size={18} className="text-accent-primary animate-pulse" />
               <h1 className="font-display text-xl tracking-[0.3em] text-white">RAW_STAC_INGEST_L2</h1>
            </div>
            
            <div className="h-6 w-px bg-white/10 mx-2" />

            <div className="flex items-center bg-slate-950 border border-white/10 px-3 py-1.5 rounded-sm focus-within:border-accent-primary transition-all group">
               <Search size={14} className="text-slate-600 group-focus-within:text-accent-primary" />
               <input 
                  type="text" 
                  placeholder="QUERY_GEO_NODE..." 
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-transparent outline-none text-[10px] uppercase text-white placeholder:text-slate-700 w-48 ml-3"
               />
            </div>

            <div className="flex gap-1">
              {['ALL', 'BULLISH', 'BEARISH'].map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`text-[9px] font-black px-3 py-1 border transition-all uppercase tracking-widest rounded-sm ${
                    filter === f ? 'bg-accent-primary text-slate-950 border-accent-primary' : 'bg-white/5 border-white/5 text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
         </div>
         
         <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <span className="text-[9px] text-slate-500 uppercase font-black tracking-widest">LUM:</span>
              <input 
                type="range" min="0" max="150" value={brightness} 
                onChange={(e) => setBrightness(parseInt(e.target.value))}
                className="w-24 h-1 bg-slate-800 appearance-none cursor-pointer accent-accent-primary"
              />
            </div>
            <div className="h-6 w-px bg-white/10" />
            <button className="flex items-center gap-2 text-[9px] font-black text-accent-primary uppercase tracking-widest hover:brightness-110">
               <Download size={14} /> DL_SITAR_RAW
            </button>
         </div>
      </header>

      <div className="flex-1 p-8 overflow-y-auto custom-scrollbar relative">
        <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

        <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-8">
          {filteredImages.map((img: any) => (
            <motion.div 
              key={img.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-panel neo-border rounded-sm overflow-hidden group cursor-pointer flex flex-col h-[380px] hover:bg-white/5 transition-all"
            >
              {/* IMAGE HUD */}
              <div className="h-[220px] shrink-0 relative overflow-hidden bg-black">
                <img 
                  src={img.url} 
                  alt={img.location} 
                  style={{ filter: `grayscale(1) brightness(${brightness}%) contrast(1.1)` }}
                  className="w-full h-full object-cover group-hover:grayscale-0 group-hover:scale-110 transition-all duration-1000 opacity-80 group-hover:opacity-100" 
                />
                
                {/* CROSSHAIR OVERLAY */}
                <div className="absolute inset-0 border border-white/5 pointer-events-none group-hover:border-accent-primary/20 transition-all" />
                <div className="absolute top-1/2 left-0 w-full h-px bg-white/5 pointer-events-none group-hover:bg-accent-primary/10" />
                <div className="absolute top-0 left-1/2 w-px h-full bg-white/5 pointer-events-none group-hover:bg-accent-primary/10" />

                <div className="absolute top-4 left-4 flex gap-2">
                   <div className="glass-panel px-2 py-1 border-white/10 text-[9px] text-white font-mono font-bold tracking-widest uppercase rounded-sm flex items-center gap-2">
                      <Zap size={10} className="text-accent-primary" /> {img.type}
                   </div>
                   <div className="glass-panel px-2 py-1 border-white/10 text-[9px] text-white font-mono font-bold tracking-widest uppercase rounded-sm">
                      {img.res} RES
                   </div>
                </div>

                <div className="absolute bottom-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                   <button className="p-2 bg-slate-950/80 border border-white/20 text-white rounded-sm hover:bg-accent-primary hover:text-slate-950 transition-all">
                      <Maximize2 size={14} />
                   </button>
                </div>
              </div>
              
              {/* CONTENT AREA */}
              <div className="flex-1 flex flex-col p-6 min-w-0 bg-slate-900/40">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-black text-white group-hover:text-accent-primary transition-colors tracking-tight uppercase truncate w-48">{img.location}</span>
                    <div className="flex items-center gap-2">
                       <Clock size={10} className="text-slate-500" />
                       <span className="text-[9px] text-slate-500 font-mono uppercase font-bold">{img.time} // COVERT: {img.cloud}</span>
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded-sm border text-[9px] font-black tracking-widest uppercase shadow-2xl ${
                    img.signal === 'BULLISH' ? 'bg-bull/10 border-bull/30 text-bull shadow-glow-bull' : 
                    img.signal === 'BEARISH' ? 'bg-bear/10 border-bear/30 text-bear shadow-glow-bear' : 
                    'bg-white/5 border-white/10 text-slate-400'
                  }`}>
                    {img.signal}
                  </div>
                </div>

                <div className="bg-void/60 p-3 border-l-2 border-accent-primary/40 rounded-sm flex-1 mb-4 relative overflow-hidden">
                   <p className="text-[11px] text-slate-300 leading-relaxed italic font-sans">
                     "{img.detail}"
                   </p>
                </div>

                <footer className="flex justify-between items-center pt-4 border-t border-white/5">
                   <div className="flex items-center gap-4 text-[8px] font-mono text-slate-600 font-bold uppercase tracking-widest">
                      <span>Ref: S2-T99</span>
                      <span>Auth: 0x99</span>
                   </div>
                   <button className="text-[10px] text-accent-primary font-black tracking-[0.2em] uppercase flex items-center gap-2 hover:underline group/btn">
                      Induce_Alpha <Lucide.ArrowRight size={12} className="group-hover/btn:translate-x-1 transition-transform" />
                   </button>
                </footer>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* OSINT FOOTER */}
      <footer className="h-10 border-t border-white/5 bg-slate-950 px-6 flex items-center justify-between shrink-0">
         <div className="flex gap-8 items-center">
            <span className="text-[9px] text-slate-600 font-bold uppercase tracking-widest flex items-center gap-2">
               <div className="w-1.5 h-1.5 rounded-full bg-bull" /> L1_STREAM: SECURE
            </span>
            <span className="text-[9px] text-slate-600 font-bold uppercase tracking-widest flex items-center gap-2">
               <div className="w-1.5 h-1.5 rounded-full bg-accent-primary" /> ORBIT_SYNC: NOMINAL
            </span>
         </div>
         <span className="text-[9px] font-mono text-slate-700 uppercase tracking-tighter">DATASET_REF_ID: SAT-OSINT-MASTER-2026</span>
      </footer>
    </div>
  );
};

export default SatelliteFeed;
