import React from 'react';
import { useSignalStore } from '../store';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Globe, Zap, Shield, AlertTriangle } from 'lucide-react';

const FeedView = () => {
  const { events } = useSignalStore();

  return (
    <div className="flex-1 flex flex-col bg-surface-0 overflow-hidden">
      {/* FEED HEADER */}
      <div className="h-11 border-b border-white/5 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-accent-primary" />
          <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">TEMPORAL INTELLIGENCE FEED</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="type-data-xs text-text-4 uppercase flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse"></span>
            Live Stream Active
          </span>
        </div>
      </div>

      {/* FEED CONTENT */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 bg-void/20">
        <div className="max-w-3xl mx-auto space-y-4">
          <AnimatePresence initial={false}>
            {events.map((event, index) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  onClick={() => {
                    const url = event.url || `https://www.google.com/search?q=${encodeURIComponent(event.message)}&tbm=nws`;
                    window.open(url, '_blank');
                  }}
                  className="group relative flex gap-4 p-4 bg-surface-1/50 border border-white/5 hover:bg-surface-2 transition-all cursor-alias"
                >
                <div className="shrink-0 pt-1">
                   <EventIcon type={event.type} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between mb-1">
                    <span className="type-data-xs text-accent-primary font-bold uppercase tracking-widest">{event.type} update</span>
                    <span className="type-data-xs text-text-5 font-mono">{event.timestamp}</span>
                  </div>
                  <p className="type-ui-sm text-text-1 font-medium leading-relaxed uppercase tracking-tight">
                    {event.message}
                  </p>
                </div>
                {/* DECORATIVE LINE */}
                <div className="absolute left-[-1px] top-4 bottom-4 w-[2px] bg-accent-primary opacity-0 group-hover:opacity-100 transition-opacity"></div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* SKELETON LOADERS FOR ATMOSPHERE */}
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={`skel-${i}`} className="opacity-20 flex gap-4 p-4 border border-white/5 grayscale">
               <div className="w-10 h-10 bg-white/10 rounded-sm"></div>
               <div className="flex-1 space-y-2">
                  <div className="h-3 w-24 bg-white/10 rounded-sm"></div>
                  <div className="h-4 w-full bg-white/10 rounded-sm"></div>
               </div>
            </div>
          ))}
        </div>
      </div>

      {/* FEED FOOTER */}
      <div className="h-8 border-t border-white/5 flex items-center px-4 bg-surface-1 shrink-0">
        <span className="type-data-xs text-text-4 uppercase tracking-widest">Latency: <span className="text-bull">24ms</span></span>
        <div className="mx-4 h-3 w-[1px] bg-white/10"></div>
        <span className="type-data-xs text-text-4 uppercase tracking-widest">Source: <span className="text-text-2">Direct Orbital Downlink</span></span>
      </div>
    </div>
  );
};

const EventIcon = ({ type }: { type: string }) => {
  switch (type) {
    case 'satellite': return <Globe size={20} className="text-bull" />;
    case 'market': return <Zap size={20} className="text-accent-primary" />;
    case 'system': return <Shield size={20} className="text-text-3" />;
    default: return <Activity size={20} className="text-text-4" />;
  }
};

export default FeedView;
