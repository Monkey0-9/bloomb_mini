import React, { useEffect, useState } from 'react';
import { useTerminalStore } from '../store';
import { motion, AnimatePresence } from 'framer-motion';
import * as Lucide from 'lucide-react';

const Activity = Lucide.Activity || Lucide.Zap;

const FeedView = () => {
  const { Globe, Zap, Shield, AlertTriangle, Search } = Lucide;
  const [finNews, setFinNews] = useState<any[]>([]);
  const [shipNews, setShipNews] = useState<any[]>([]);
  const [milNews, setMilNews] = useState<any[]>([]);
  const [squawks, setSquawks] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  useEffect(() => {
    let active = true;
    const fetchAll = async () => {
      try {
        const [fn, sn, mn, sq] = await Promise.all([
          api.news('financial'),
          api.news('shipping'),
          api.news('military'),
          api.squawkAlerts()
        ]);
        if (active) {
          if (fn.news) setFinNews(fn.news);
          if (sn.news) setShipNews(sn.news);
          if (mn.news) setMilNews(mn.news);
          if (sq.alerts) setSquawks(sq.alerts);
        }
      } catch (err) {}
    };
    fetchAll();
    const interval = setInterval(fetchAll, 60000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const handleSearch = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      try {
        const res = await api.newsSearch(searchQuery);
        setSearchResults(res.articles || []);
      } catch (err) {}
    }
  };

  const renderColumn = (title: string, items: any[], icon: any, colorClass: string) => (
    <div className="flex-1 flex flex-col min-w-0 border-r border-white/5 last:border-0">
      <div className={`h-8 flex items-center gap-2 px-4 border-b border-white/5 bg-surface-1/40 ${colorClass}`}>
        {icon}
        <span className="type-data-xs font-bold uppercase tracking-widest">{title}</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {items.map((n, i) => (
          <div key={i} className="group relative p-3 bg-surface-1/30 border border-white/5 hover:bg-surface-2 transition-all cursor-alias" onClick={() => window.open(n.url, '_blank')}>
             <div className="flex items-center justify-between mb-1.5">
               <span className={`text-[9px] font-mono px-1.5 py-0.5 bg-white/5 ${colorClass}`}>{n.source.toUpperCase()}</span>
               <span className="text-[9px] font-mono text-text-4">{new Date(n.published).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
             </div>
             <p className="text-[11px] font-medium leading-snug text-text-1 group-hover:text-white line-clamp-3">{n.title}</p>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="flex-1 flex flex-col bg-surface-0 overflow-hidden">
      {/* FEED HEADER */}
      <div className="h-11 border-b border-white/5 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-accent-primary" />
          <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">GLOBAL INTELLIGENCE FEED</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-surface-2/60 px-2 border border-white/10 rounded-sm">
             <Search size={12} className="text-text-4" />
             <input 
               type="text" 
               placeholder="Search GDELT..." 
               value={searchQuery}
               onChange={e => setSearchQuery(e.target.value)}
               onKeyDown={handleSearch}
               className="bg-transparent text-[10px] font-mono w-48 py-1 outline-none text-text-1 placeholder-text-5"
             />
          </div>
          <span className="type-data-xs text-text-4 uppercase flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse"></span>
            Live Stream Active
          </span>
        </div>
      </div>

      {/* FEED CONTENT */}
      {searchResults.length > 0 ? (
        <div className="flex-1 overflow-y-auto p-6 bg-void/20">
          <div className="flex items-center justify-between mb-4">
             <span className="type-data-xs text-accent-primary font-bold uppercase tracking-widest">Search Results for "{searchQuery}"</span>
             <button onClick={() => setSearchResults([])} className="text-[10px] font-mono text-text-4 hover:text-white">CLEAR</button>
          </div>
          <div className="grid grid-cols-2 gap-4">
             {searchResults.map((n, i) => (
                <div key={i} className="p-4 bg-surface-1/50 border border-white/5 hover:border-accent-primary/50 cursor-alias transition-all" onClick={() => window.open(n.url, '_blank')}>
                   <div className="flex items-center justify-between mb-2">
                     <span className="text-[10px] font-mono text-accent-primary">{n.source.toUpperCase()}</span>
                     <span className="text-[10px] font-mono text-text-4">{new Date(n.published).toLocaleDateString()}</span>
                   </div>
                   <p className="text-sm font-medium text-text-1 leading-snug">{n.title}</p>
                </div>
             ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden">
          {renderColumn('Financial', finNews, <Zap size={12}/>, 'text-accent-primary')}
          {renderColumn('Shipping & Maritime', shipNews, <Globe size={12}/>, 'text-[#00ccff]')}
          
          <div className="flex-1 flex flex-col min-w-0 border-r border-white/5 last:border-0">
            <div className="h-8 flex items-center gap-2 px-4 border-b border-white/5 bg-surface-1/40 text-bear">
              <Shield size={12}/>
              <span className="type-data-xs font-bold uppercase tracking-widest">Military & OSINT</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              {squawks.length > 0 && squawks.map((s, i) => (
                <div key={`sq-${i}`} className="group relative p-3 bg-bear/10 border border-bear/30 hover:bg-bear/20 transition-all cursor-alias">
                   <div className="flex items-center justify-between mb-1.5">
                     <span className="text-[9px] font-bold font-mono px-1.5 py-0.5 bg-bear/20 text-bear flex items-center gap-1"><AlertTriangle size={8}/> SQUAWK {s.squawk}</span>
                     <span className="text-[9px] font-mono text-text-4">{new Date(s.ts).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                   </div>
                   <p className="text-[11px] font-medium leading-snug text-bear">Callsign {s.callsign}: {s.desc} reported at {s.lat.toFixed(2)}°, {s.lon.toFixed(2)}°</p>
                </div>
              ))}
              {milNews.map((n, i) => (
                <div key={i} className="group relative p-3 bg-surface-1/30 border border-white/5 hover:bg-surface-2 transition-all cursor-alias" onClick={() => window.open(n.url, '_blank')}>
                   <div className="flex items-center justify-between mb-1.5">
                     <span className="text-[9px] font-mono px-1.5 py-0.5 bg-white/5 text-bear">{n.source.toUpperCase()}</span>
                     <span className="text-[9px] font-mono text-text-4">{new Date(n.published).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                   </div>
                   <p className="text-[11px] font-medium leading-snug text-text-1 group-hover:text-white line-clamp-3">{n.title}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* FEED FOOTER */}
      <div className="h-8 border-t border-white/5 flex items-center px-4 bg-surface-1 shrink-0">
        <span className="type-data-xs text-text-4 uppercase tracking-widest">Sources: <span className="text-text-2">Reuters | TradeWinds | GDELT | OpenSky</span></span>
      </div>
    </div>
  );
};

export default FeedView;
