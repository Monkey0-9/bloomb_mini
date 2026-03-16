import React, { useState, useEffect } from 'react';
import { useSignalStore } from '../store';
import { 
  Play, Newspaper, Activity, Search, Filter, Volume2, VolumeX, Maximize2, 
  Clock, TrendingUp, TrendingDown, Globe, X, Share2, Copy, Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const NewsHubView = () => {
  const { events } = useSignalStore();
  const [newsArticles, setNewsArticles] = useState<any[]>([]);
  const [isMuted, setIsMuted] = useState(true);
  const [selectedArticle, setSelectedArticle] = useState<any>(null);

  const streams = [
    { id: 'iss', title: 'NASA Earth Live', url: 'https://www.youtube.com/embed/P9C25Un7xaM', category: 'Orbital Recon' },
    { id: 'bloomberg', title: 'Bloomberg TV', url: 'https://www.youtube.com/embed/dp8PhLsUcFE', category: 'Market Alpha' },
    { id: 'cnbc', title: 'CNBC International', url: 'https://www.youtube.com/embed/_pD8l_6TidM', category: 'Macro Events' }
  ];
  const [selectedStream, setSelectedStream] = useState(streams[1]);

  useEffect(() => {
    const loadNews = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/alpha/news');
        const data = await response.json();
        setNewsArticles(data.news || []);
      } catch (err) {
        console.error('Failed to fetch text news:', err);
      }
    };
    loadNews();
    const interval = setInterval(loadNews, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden font-sans border-l border-white/5">
      {/* HEADER */}
      <div className="h-14 border-b border-white/10 flex items-center justify-between px-6 bg-surface-1/40 backdrop-blur-xl z-20">
        <div className="flex items-center gap-3">
          <Zap size={18} className="text-accent-primary animate-pulse" />
          <h1 className="type-h1 text-sm tracking-[0.3em] text-text-0 uppercase font-black">Global Intelligence HUB</h1>
        </div>
        <div className="flex items-center gap-6">
           <div className="flex items-center gap-2 px-3 py-1.5 border border-white/5 bg-void/60 text-[10px] uppercase tracking-widest text-text-3 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-bull animate-ping"></span>
              Surveillance: <span className="text-text-1">Active</span>
           </div>
        </div>
      </div>

      {/* INTEGRATED DASHBOARD LAYOUT */}
      <div className="flex-1 flex overflow-hidden p-1 gap-1">
        
        {/* LEFT COMPONENT: LIVE VIDEO THEATER + SIGNAL STREAM */}
        <div className="w-[40%] flex flex-col gap-1">
          {/* THEATER */}
          <div className="h-[60%] bg-black border border-white/5 relative group overflow-hidden">
            <iframe 
              className="w-full h-full contrast-125 brightness-90 group-hover:brightness-100 transition-all pointer-events-auto"
              src={`${selectedStream.url}?autoplay=1&mute=${isMuted ? 1 : 0}&controls=0&showinfo=0&rel=0&loop=1`} 
              frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            />
            <div className="absolute top-4 left-4 pointer-events-none">
               <div className="px-2 py-1 bg-void/80 border border-white/10 text-[10px] font-bold text-accent-primary uppercase tracking-widest backdrop-blur-md">
                  LIVE // {selectedStream.title}
               </div>
            </div>
            <div className="absolute bottom-4 right-4 flex gap-2">
               <button onClick={() => setIsMuted(!isMuted)} className="p-2 bg-void/80 border border-white/10 hover:bg-surface-2 transition-colors text-text-2">
                  {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
               </button>
               <select 
                 onChange={(e) => setSelectedStream(streams.find(s => s.id === e.target.value) || streams[1])}
                 className="bg-void/80 border border-white/10 text-[10px] text-text-1 uppercase px-2 outline-none cursor-pointer"
               >
                 {streams.map(s => <option key={s.id} value={s.id}>{s.id.toUpperCase()}</option>)}
               </select>
            </div>
          </div>

          {/* SIGNAL STREAM (TICKER STYLE) */}
          <div className="flex-1 bg-surface-1/40 border border-white/5 flex flex-col overflow-hidden">
            <div className="px-4 py-2 border-b border-white/5 flex items-center justify-between bg-void/20">
               <span className="text-[10px] font-black uppercase tracking-[0.2em] text-accent-primary flex items-center gap-2">
                 <Activity size={12} /> Conviction Feed
               </span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
               {events.map((e, i) => (
                 <div key={i} className="border-l-2 border-accent-primary/30 pl-3">
                   <div className="text-[8px] text-text-4 uppercase mb-1">{e.timestamp}</div>
                   <div className="text-[10px] text-text-1 font-bold leading-tight uppercase">{e.message}</div>
                 </div>
               ))}
            </div>
          </div>
        </div>

        {/* RIGHT COMPONENT: ELECTRONIC NEWS FEED (AKSHARE/YFINANCE) */}
        <div className="flex-1 flex flex-col bg-surface-1/20 border border-white/5 overflow-hidden">
          <div className="px-6 py-3 border-b border-white/5 flex items-center justify-between bg-void/40">
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-text-2 flex items-center gap-2">
              <Newspaper size={12} /> Electronic Surveillance Feed
            </span>
            <span className="text-[9px] text-text-4 font-mono uppercase">24H Global Ingest Active</span>
          </div>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-3">
            {newsArticles.length > 0 ? newsArticles.map((a, i) => (
              <div 
                key={i} 
                onClick={() => setSelectedArticle(a)}
                className="p-4 bg-void/40 border border-white/5 hover:border-accent-primary/40 transition-all cursor-pointer group"
              >
                <div className="flex justify-between items-start mb-2">
                   <span className="text-[9px] font-bold text-accent-primary uppercase px-1.5 py-0.5 border border-accent-primary/20">{a.source}</span>
                   <span className="text-[9px] text-text-4 font-mono">{a.time}</span>
                </div>
                <h3 className="text-xs font-bold text-text-1 group-hover:text-accent-primary transition-colors uppercase leading-tight">{a.text}</h3>
              </div>
            )) : (
              <div className="h-full flex flex-col items-center justify-center opacity-40">
                <Globe size={48} className="animate-spin-slow mb-4" />
                <p className="text-[10px] uppercase tracking-widest">Ingesting Global Signals...</p>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* ARTICLE MODAL */}
      <AnimatePresence>
        {selectedArticle && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-12 bg-void/90 backdrop-blur-md"
          >
            <div className="bg-surface-1 border border-white/10 w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden">
              <div className="p-4 border-b border-white/10 flex justify-between items-center">
                 <span className="text-[10px] font-black uppercase tracking-widest text-accent-primary">{selectedArticle.source} // Intelligence Report</span>
                 <button onClick={() => setSelectedArticle(null)} className="p-2 hover:bg-white/10 rounded-full"><X size={18} /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-12 custom-scrollbar">
                <h1 className="text-2xl font-black text-text-0 uppercase leading-tight mb-8">{selectedArticle.text}</h1>
                <p className="text-text-2 text-lg leading-relaxed">
                  {selectedArticle.content || "Satellite telemetry confirmation pending. Initial analysis of terrestrial signals indicates a significant shift in market structural dynamics. Data ingested via local surveillance agents suggests that current trading volumes are influenced by high-frequency orbital throughput."}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* STATUS BAR */}
      <div className="h-8 border-t border-white/10 bg-surface-1 flex items-center px-6 justify-between shrink-0 box-border text-[9px] font-mono text-text-4 uppercase tracking-widest">
         <div className="flex gap-8">
            <span>Terminal: <span className="text-text-1 font-bold">ST-HUB-01</span></span>
            <span>Link: <span className="text-bull font-bold">KA-BAND OPTIMIZED</span></span>
         </div>
         <div>{new Date().toISOString()}</div>
      </div>
    </div>
  );
};

export default NewsHubView;
