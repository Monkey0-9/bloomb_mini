import React, { useState, useEffect } from 'react';
import { useSignalStore } from '../store';
import * as Lucide from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Activity = Lucide.Activity || Lucide.Zap;

const NewsHubView = () => {
  const { 
    Play, Newspaper, Search, Filter, Volume2, VolumeX, Maximize2, 
    Clock, TrendingUp, TrendingDown, Globe, X, Share2, Copy, Zap
  } = Lucide;
  const { events } = useSignalStore();
  const [newsArticles, setNewsArticles] = useState<any[]>([]);
  const [isMuted, setIsMuted] = useState(true);
  const [selectedArticle, setSelectedArticle] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const streams = [
    { id: 'iss', title: 'NASA Earth Live', url: 'https://www.youtube.com/embed/S_8S-P3K53k', category: 'Orbital Recon' },
    { id: 'bloomberg', title: 'Bloomberg Live', url: 'https://www.youtube.com/embed/SSTX8Xf0uDk', category: 'Market Alpha' },
    { id: 'cnbc', title: 'CNBC International', url: 'https://www.youtube.com/embed/_pD8l_6TidM', category: 'Macro Events' }
  ];
  const [selectedStream, setSelectedStream] = useState(streams[1]);

  const loadNews = async () => {
    if (isSearching) return;
    try {
      const response = await fetch('/api/news/live');
      const data = await response.json();
      setNewsArticles(data.articles || data.news || []);
    } catch (err) {
      console.error('Failed to fetch text news:', err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setIsSearching(false);
      loadNews();
      return;
    }
    
    setIsSearching(true);
    try {
      const response = await fetch(`/api/news/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      setNewsArticles(data.articles || []);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  useEffect(() => {
    loadNews();
    const interval = setInterval(() => {
        if (!isSearching) loadNews();
    }, 30000);
    return () => clearInterval(interval);
  }, [isSearching]);


  return (
    <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden font-mono selection:bg-accent-primary selection:text-void">
      {/* HEADER */}
      <header className="h-14 border-b border-white/5 flex items-center justify-between px-8 bg-slate-900/40 backdrop-blur-md shrink-0 z-20">
        <div className="flex items-center gap-4">
          <Zap size={18} className="text-accent-primary animate-pulse shadow-glow-sky" />
          <h1 className="font-display text-xl tracking-[0.3em] text-white leading-none uppercase">Intelligence_Induction_HUB</h1>
        </div>
        <div className="flex items-center gap-6">
           <div className="flex items-center gap-3 glass-panel px-4 py-1.5 border-white/10 rounded-full">
              <div className="w-1.5 h-1.5 rounded-full bg-bull animate-ping" />
              <span className="text-[10px] font-black text-bull uppercase tracking-[0.2em]">Signal: Synchronized</span>
           </div>
        </div>
      </header>

      {/* DASHBOARD CONTENT */}
      <div className="flex-1 flex overflow-hidden p-4 gap-4 bg-[#020617]">
        
        {/* LEFT: VISUAL THEATER + FAST FEED */}
        <div className="w-[45%] flex flex-col gap-4">
          <div className="h-[65%] glass-panel neo-border rounded-sm relative group overflow-hidden bg-black">
            <iframe 
              className="w-full h-full grayscale-[0.2] contrast-125 brightness-75 group-hover:brightness-100 transition-all pointer-events-auto"
              src={`${selectedStream.url}?autoplay=1&mute=${isMuted ? 1 : 0}&controls=0&showinfo=0&rel=0&loop=1`} 
              frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            />
            <div className="absolute inset-0 pointer-events-none border border-white/5 group-hover:border-accent-primary/10 transition-all" />
            
            <div className="absolute top-6 left-6 pointer-events-none">
               <div className="glass-panel px-3 py-1 border-white/10 text-[10px] font-black text-accent-primary uppercase tracking-[0.2em] shadow-2xl">
                  STREAM_01 // {selectedStream.title}
               </div>
            </div>

            <div className="absolute bottom-6 right-6 flex gap-3 opacity-0 group-hover:opacity-100 transition-all">
               <button onClick={() => setIsMuted(!isMuted)} className="w-10 h-10 glass-panel border-white/20 flex items-center justify-center hover:bg-white/10 text-white rounded-sm">
                  {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
               </button>
               <select 
                 value={selectedStream.id}
                 onChange={(e) => setSelectedStream(streams.find(s => s.id === e.target.value) || streams[1])}
                 className="glass-panel border-white/20 text-[10px] font-black text-white uppercase px-4 outline-none cursor-pointer hover:bg-white/10 rounded-sm"
               >
                 {streams.map(s => <option key={s.id} value={s.id} className="bg-slate-900">{s.id.toUpperCase()}_FEED</option>)}
               </select>
            </div>
          </div>

          <div className="flex-1 glass-panel neo-border rounded-sm flex flex-col overflow-hidden bg-slate-900/20">
            <header className="px-6 py-3 border-b border-white/5 flex items-center justify-between bg-white/2">
               <span className="text-[10px] font-black uppercase tracking-[0.3em] text-accent-primary flex items-center gap-2">
                 <Activity size={14} className="animate-pulse" /> Live_Event_Timeline
               </span>
               <div className="h-1.5 w-1.5 rounded-full bg-bull" />
            </header>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
               {events.map((e, i) => (
                 <div key={i} className="border-l-2 border-accent-primary/20 pl-4 py-1 hover:bg-white/[0.02] transition-colors cursor-default group">
                   <div className="text-[9px] text-slate-500 font-mono font-bold mb-1">[{e.timestamp.slice(11, 19)} Z]</div>
                   <div className="text-[11px] text-slate-300 group-hover:text-white transition-colors leading-relaxed uppercase tracking-tighter">{e.message}</div>
                 </div>
               ))}
            </div>
          </div>
        </div>

        {/* RIGHT: TEXTUAL NEWS FEED */}
        <div className="flex-1 glass-panel neo-border rounded-sm flex flex-col overflow-hidden bg-slate-900/20">
          <header className="px-8 py-4 border-b border-white/5 flex items-center justify-between bg-white/2">
            <span className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-300 flex items-center gap-3">
              <Newspaper size={16} className="text-accent-primary" /> Global_Surveillance_Feed
            </span>
            <form onSubmit={handleSearch} className="flex-1 max-w-md ml-8 mr-4 relative">
              <input 
                type="text" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="SEARCH_MARKET_INTELLIGENCE..."
                className="w-full bg-slate-900 border border-white/10 px-10 py-1.5 text-[10px] text-white uppercase font-mono tracking-widest outline-none focus:border-accent-primary/50"
              />
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            </form>
            <span className="text-[9px] font-mono text-slate-500 font-bold uppercase tracking-widest bg-white/5 px-2 py-0.5 border border-white/5">24H_Continuous_Scan</span>
          </header>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-3">
            {newsArticles.length > 0 ? newsArticles.map((a, i) => (
              <div 
                key={i} 
                onClick={() => setSelectedArticle(a)}
                className="p-5 bg-slate-900/40 border border-white/5 rounded-sm hover:bg-white/5 hover:border-accent-primary/20 transition-all cursor-pointer group"
              >
                <div className="flex justify-between items-start mb-3">
                   <span className="text-[10px] font-black text-accent-primary uppercase px-2 py-0.5 border border-accent-primary/20 bg-accent-primary/5">{a.source}</span>
                   <span className="text-[9px] text-slate-600 font-mono font-bold">{a.time} Z</span>
                </div>
                <h3 className="text-[13px] font-bold text-white group-hover:text-accent-primary transition-colors uppercase leading-snug tracking-tighter italic font-sans">{a.text}</h3>
              </div>
            )) : (
              <div className="h-full flex flex-col items-center justify-center opacity-20 space-y-6">
                <Globe size={80} className="animate-spin-slow text-white" />
                <p className="text-sm uppercase tracking-[0.5em] font-display text-white">Ingesting_Global_Signals</p>
              </div>
            )}
          </div>
        </div>

      </div>

      <AnimatePresence>
        {selectedArticle && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-24 bg-slate-950/90 backdrop-blur-md"
          >
            <article className="glass-panel neo-border w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl rounded-sm overflow-hidden animate-slide-up">
              <header className="p-6 border-b border-white/10 flex justify-between items-center bg-slate-900/40">
                 <div className="flex items-center gap-4">
                    <div className="px-3 py-1 bg-accent-primary text-slate-950 text-[10px] font-black uppercase tracking-widest">Report</div>
                    <span className="text-[11px] font-bold uppercase tracking-widest text-slate-400">{selectedArticle.source} // Intelligence Summary</span>
                 </div>
                 <button onClick={() => setSelectedArticle(null)} className="p-2 hover:bg-white/10 rounded-full transition-all text-slate-400 hover:text-white"><X size={20} /></button>
              </header>
              <div className="flex-1 overflow-y-auto p-16 custom-scrollbar bg-slate-900/20">
                <h1 className="font-display text-5xl text-white uppercase leading-none mb-12 tracking-tighter italic border-l-4 border-accent-primary pl-8">{selectedArticle.text}</h1>
                <div className="prose prose-invert max-w-none prose-p:text-lg prose-p:leading-relaxed prose-p:text-slate-300 font-sans italic opacity-90">
                  <p>
                    {selectedArticle.summary || selectedArticle.content || 
                    `REGULATORY FILING SUMMARY: ${selectedArticle.text}. 
                    Automated sentiment analysis indicates a ${selectedArticle.impact || 'neutral'} impact on the 
                    correlated physical assets. Satellite surveillance of associated manufacturing nodes 
                    shows no immediate disruption to throughput. Security cleared personnel should monitor 
                    downstream supply chain nodes for secondary friction.`}
                  </p>
                </div>
              </div>
              <footer className="p-8 border-t border-white/10 bg-slate-950 flex justify-between items-center text-[10px] font-mono text-slate-600 font-bold uppercase tracking-[0.4em]">
                 <span>Node: INTEL-SYNC-01</span>
                 <span className="text-accent-primary/40 animate-pulse">Uplink: Sentinel_Secure_T1</span>
              </footer>
            </article>
          </motion.div>
        )}
      </AnimatePresence>

      <footer className="h-8 border-t border-white/5 bg-slate-950 px-8 flex items-center justify-between shrink-0 box-border text-[9px] font-mono text-slate-700 uppercase tracking-[0.2em] font-bold">
         <div className="flex gap-10">
            <span>Terminal_ID: ST-HUB-X1</span>
            <span>Link: KA-BAND_ENCRYPTED</span>
         </div>
         <span>{new Date().toISOString()} Z</span>
      </footer>

      <style>{`
        @keyframes slide-up {
          from { transform: translateY(40px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-slide-up {
          animation: slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
      `}</style>
    </div>
  );
};

export default NewsHubView;
