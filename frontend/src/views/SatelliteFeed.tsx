import React, { useMemo } from 'react';
import { motion } from 'framer-motion';

const SatelliteFeed = () => {
  const [search, setSearch] = React.useState('');
  
  const images = useMemo(() => [
    { 
      id: 1, 
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
      id: 2, 
      location: 'Singapore Jurong Island', 
      time: '3h 12m ago', 
      cloud: '12%', 
      res: '10m', 
      type: 'SENTINEL-2', 
      signal: 'STABLE', 
      detail: 'Thermal storage tanks at 84% capacity. Consistent with seasonal export patterns.',
      url: 'https://images.unsplash.com/photo-1566847438217-76e82d383f84?auto=format&fit=crop&w=800&q=80' 
    },
    { 
      id: 3, 
      location: 'Port of Long Beach', 
      time: '8h 22m ago', 
      cloud: '2%', 
      res: '0.5m', 
      type: 'WORLDVIEW-3', 
      signal: 'BEARISH', 
      detail: 'Empty container stacks increasing. Anchorage congestion at 48-month high.',
      url: 'https://images.unsplash.com/photo-1541829070764-84a7d30dee6b?auto=format&fit=crop&w=800&q=80' 
    },
    { 
      id: 4, 
      location: 'Shanghai Yangshan', 
      time: '2h 47m ago', 
      cloud: '15%', 
      res: '10m', 
      type: 'SENTINEL-2', 
      signal: 'BULLISH', 
      detail: 'Intense nighttime thermal activity in assembly zone 3. Production ramping ahead of schedule.',
      url: 'https://images.unsplash.com/photo-1570535560965-09559e4d4669?auto=format&fit=crop&w=800&q=80' 
    },
  ], []);

  const filteredImages = useMemo(() => {
    if (!search) {
      return images;
    }
    const lowercasedSearch = search.toLowerCase();
    return images.filter(img => 
      img.location.toLowerCase().includes(lowercasedSearch) ||
      img.detail.toLowerCase().includes(lowercasedSearch) ||
      img.type.toLowerCase().includes(lowercasedSearch)
    );
  }, [images, search]);

  return (
    <div className="flex-1 flex flex-col bg-surface-0 overflow-hidden">
      {/* FEED HEADER: ALLX STYLE */}
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
               <span className="type-h1 text-sm tracking-[0.2em] text-text-0 shadow-sm uppercase">SATELLITE IMAGE FEED</span>
               <div className="w-1.5 h-1.5 rounded-full bg-bull dot-live"></div>
            </div>
            <div className="h-6 w-[1px] bg-border-ghost"></div>
            
            {/* SEARCH FILTER */}
            <div className="flex items-center bg-surface-2/60 border border-white/5 px-3 py-1 rounded-sm group focus-within:border-accent-primary transition-all ml-4">
               <input 
                  type="text" 
                  placeholder="SEARCH LOCATIONS..." 
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-transparent outline-none type-data-xs text-text-1 placeholder:text-text-5 w-40"
               />
            </div>
         </div>
         
         <div className="flex gap-2">
            <button className="type-data-xs px-3 py-1.5 bg-surface-2/60 border border-border-2 text-text-4 uppercase tracking-widest hover:border-accent-primary hover:text-text-1 transition-all">Difference Map</button>
            <button className="type-data-xs px-3 py-1.5 bg-surface-2/60 border border-border-2 text-text-4 uppercase tracking-widest hover:border-accent-primary hover:text-text-1 transition-all">Download (Level 2A)</button>
         </div>
      </div>

      <div className="flex-1 p-sp-4 overflow-y-auto custom-scrollbar bg-void/20">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-sp-4">
          {filteredImages.map((img) => (
            <motion.div 
              key={img.id}
              className="bg-surface-1 border border-border-1 rounded-sm overflow-hidden group cursor-pointer flex h-[180px]"
              whileHover={{ borderColor: 'var(--accent-primary)', backgroundColor: 'var(--surface-2)' }}
            >
              {/* IMAGE COLUMN */}
              <div className="w-[280px] shrink-0 relative overflow-hidden">
                <img src={img.url} alt={img.location} className="w-full h-full object-cover grayscale brightness-75 group-hover:grayscale-0 group-hover:scale-110 transition-all duration-700" />
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-surface-1 group-hover:to-surface-2 transition-all"></div>
                
                <div className="absolute top-2 left-2 flex gap-1">
                   <div className="bg-void/80 backdrop-blur-md border border-border-normal px-2 py-0.5 text-[9px] mono text-text-1 uppercase font-bold">{img.type}</div>
                </div>
              </div>
              
              {/* CONTENT COLUMN */}
              <div className="flex-1 flex flex-col p-4 min-w-0">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex flex-col">
                    <span className="type-h1 text-[13px] text-text-0 group-hover:text-accent-primary transition-colors tracking-widest">{img.location.toUpperCase()}</span>
                    <span className="type-data-xs text-text-4 uppercase mt-0.5">{img.time} — CLOUD: {img.cloud}</span>
                  </div>
                  <div className={`px-2 py-0.5 rounded-sm border type-data-xs font-bold tracking-widest ${
                    img.signal === 'BULLISH' ? 'bg-bull-08 border-bull-60 text-bull' : 
                    img.signal === 'BEARISH' ? 'bg-bear-08 border-bear-60 text-bear' : 
                    'bg-neutral-08 border-neutral text-neutral'
                  }`}>
                    {img.signal}
                  </div>
                </div>

                <div className="bg-void/30 p-2.5 rounded-sm border border-border-ghost flex-1 mb-3">
                   <p className="type-ui-sm text-text-2 text-[11px] leading-snug line-clamp-3 italic">
                     "{img.detail}"
                   </p>
                </div>

                <div className="flex justify-between items-center mt-auto">
                   <div className="flex gap-4">
                      <div className="flex flex-col">
                         <span className="type-data-xs text-text-5 uppercase text-[8px]">Resolution</span>
                         <span className="type-data-md text-text-3 font-bold">{img.res}</span>
                      </div>
                   </div>
                   <button className="type-data-xs text-accent-primary font-bold tracking-widest hover:underline uppercase">Full Analysis →</button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* FEED FOOTER */}
      <div className="h-8 border-t border-border-1 flex items-center justify-between px-4 bg-void shrink-0">
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Imagery Stream: <span className="text-bull font-bold">Encrypted / SECURE</span></span>
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Next Refresh: <span className="text-text-1">12:44:02 UTC</span></span>
      </div>
    </div>
  );
};

export default SatelliteFeed;
