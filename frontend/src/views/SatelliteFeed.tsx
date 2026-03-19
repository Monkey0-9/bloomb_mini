import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useSignalStore } from '../store';

const SatelliteFeed = () => {
  const [search, setSearch] = React.useState('');
  const { signals } = useSignalStore();
  
  const images = useMemo(() => {
    // Start with curated base imagery
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

    // Map live signals to high-fidelity feed items
    const liveItems = signals.slice(0, 10).map((s: any) => ({
      id: s.id,
      location: s.name,
      time: 'LIVE',
      cloud: '0%',
      res: '0.5m',
      type: 'WORLDVIEW-3',
      signal: s.status.toUpperCase(),
      detail: s.headline + '. ' + s.implication,
      url: s.status === 'bullish' 
        ? 'https://images.unsplash.com/photo-1570535560965-09559e4d4669?auto=format&fit=crop&w=800&q=80'
        : 'https://images.unsplash.com/photo-1541829070764-84a7d30dee6b?auto=format&fit=crop&w=800&q=80'
    }));

    return [...liveItems, ...baseImagery];
  }, [signals]);

  const filteredImages = useMemo(() => {
    if (!search) return images;
    const lowercasedSearch = search.toLowerCase();
    return images.filter((img: any) => 
      img.location.toLowerCase().includes(lowercasedSearch) ||
      img.detail.toLowerCase().includes(lowercasedSearch) ||
      img.type.toLowerCase().includes(lowercasedSearch)
    );
  }, [images, search]);

  return (
    <div className="flex-1 flex flex-col bg-[var(--bg-base)] overflow-hidden font-mono select-none">
      {/* FEED HEADER: OSINT STYLE */}
      <div className="h-10 border-b border-[var(--border-subtle)] flex items-center justify-between px-3 shrink-0 bg-[var(--bg-surface)]">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
               <span className="text-[12px] font-bold tracking-[0.2em] text-[var(--text-primary)] shadow-sm uppercase">Raw Intel Feed</span>
               <div className="w-1.5 h-1.5 rounded-none bg-[var(--neon-bull)] animate-pulse"></div>
            </div>
            
            {/* SEARCH FILTER */}
            <div className="flex items-center bg-[var(--bg-overlay)] border border-[var(--border-subtle)] px-2 py-0.5 group focus-within:border-[var(--neon-bull)] transition-all ml-2">
               <input 
                  type="text" 
                  placeholder="QUERY TARGET..." 
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-transparent outline-none text-[10px] uppercase text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] w-48 font-mono"
               />
            </div>
         </div>
         
         <div className="flex gap-2">
            <button className="text-[9px] font-bold px-2 py-1 bg-[var(--bg-overlay)] border border-[var(--border-subtle)] text-[var(--text-tertiary)] uppercase tracking-widest hover:border-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">DIFF MAP</button>
            <button className="text-[9px] font-bold px-2 py-1 bg-[var(--bg-overlay)] border border-[var(--border-subtle)] text-[var(--text-tertiary)] uppercase tracking-widest hover:border-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">DL RAW</button>
         </div>
      </div>

      <div className="flex-1 p-4 overflow-y-auto custom-scrollbar bg-transparent">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {filteredImages.map((img: any) => (
            <motion.div 
              key={img.id}
              className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-none overflow-hidden group cursor-pointer flex h-[160px]"
              whileHover={{ borderColor: 'var(--neon-bull)' }}
            >
              {/* IMAGE COLUMN */}
              <div className="w-[240px] shrink-0 relative overflow-hidden border-r border-[var(--border-subtle)]">
                <img src={img.url} alt={img.location} className="w-full h-full object-cover grayscale brightness-75 group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700" />
                <div className="absolute inset-0 bg-[var(--neon-bull)] opacity-10 group-hover:opacity-0 transition-opacity mix-blend-color"></div>
                
                <div className="absolute top-2 left-2 flex gap-1">
                   <div className="bg-[var(--bg-overlay)] backdrop-blur-md border border-[var(--border-subtle)] px-1.5 py-0.5 text-[8px] text-[var(--text-primary)] uppercase font-bold tracking-widest">{img.type}</div>
                </div>
              </div>
              
              {/* CONTENT COLUMN */}
              <div className="flex-1 flex flex-col p-3 min-w-0">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex flex-col">
                    <span className="text-[12px] font-bold text-[var(--text-primary)] group-hover:text-[var(--neon-bull)] transition-colors tracking-[0.1em] truncate">{img.location.toUpperCase()}</span>
                    <span className="text-[9px] text-[var(--text-tertiary)] uppercase mt-0.5 tracking-wider">{img.time} // COVERT: {img.cloud}</span>
                  </div>
                  <div className={`px-2 py-0.5 rounded-none border text-[9px] font-bold tracking-widest uppercase ${
                    img.signal === 'BULLISH' ? 'bg-[var(--neon-dim-bull)] border-[var(--neon-bull)]/50 text-[var(--neon-bull)]' : 
                    img.signal === 'BEARISH' ? 'bg-[var(--neon-dim-bear)] border-[var(--neon-bear)]/50 text-[var(--neon-bear)]' : 
                    'bg-[var(--bg-overlay)] border-[var(--border-subtle)] text-[var(--text-secondary)]'
                  }`}>
                    {img.signal}
                  </div>
                </div>

                <div className="bg-[var(--bg-overlay)] p-2 rounded-none border border-[var(--border-subtle)] flex-1 mb-2 overflow-hidden relative">
                   <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-[var(--text-tertiary)] opacity-30"></div>
                   <p className="text-[10px] text-[var(--text-secondary)] leading-snug line-clamp-3">
                     {img.detail}
                   </p>
                </div>

                <div className="flex justify-between items-center mt-auto border-t border-[var(--border-subtle)] pt-1.5">
                   <div className="flex gap-4">
                      <div className="flex flex-col">
                         <span className="text-[8px] text-[var(--text-tertiary)] uppercase tracking-widest">RES</span>
                         <span className="text-[10px] text-[var(--text-primary)] font-bold">{img.res}</span>
                      </div>
                   </div>
                   <span className="text-[9px] text-[var(--neon-bull)] font-bold tracking-[0.2em] group-hover:underline uppercase flex items-center gap-1">ANALYZE <span className="opacity-0 group-hover:opacity-100 transition-opacity">→</span></span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* FEED FOOTER */}
      <div className="h-8 border-t border-[var(--border-subtle)] flex items-center justify-between px-3 bg-[var(--bg-surface)] shrink-0">
         <span className="text-[9px] text-[var(--text-tertiary)] uppercase tracking-[0.2em] font-bold">L1 Stream: <span className="text-[var(--neon-bull)]">Encrypted / SECURE</span></span>
         <span className="text-[9px] text-[var(--text-tertiary)] uppercase tracking-[0.2em] font-bold">Next TX: <span className="text-[var(--text-primary)]">12:44:02 UTC</span></span>
      </div>
    </div>
  );
};

export default SatelliteFeed;
