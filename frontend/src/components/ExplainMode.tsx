import { motion, AnimatePresence } from 'framer-motion';

const ExplainMode = ({ isOpen, onClose, view }: any) => {
  const callouts: any = {
    'world': [
      { id: 1, x: '25%', y: '20%', title: 'Economic Hotspots', text: 'These markers indicate physical activity detected by satellites. Green rings show accelerating port throughput or retail footfall.' },
      { id: 2, x: '52%', y: '50%', title: 'The Global Alpha Engine', text: 'Our satellite network tracks the world’s supply chains in real-time. This is the raw data that institutional investors use to predict earnings before they are reported.' },
      { id: 3, x: '10%', y: '85%', title: 'Orbital Overpass', text: 'Shows the exact time our next satellite will pass over these locations to refresh the data.' },
    ],
    'charts': [
      { id: 1, x: '15%', y: '35%', title: 'The Satellite Lead', text: 'The green dotted line is the "Sat Signal". When it spikes before the blue price line, it means satellites saw economic activity (like more ships) that the market hasn’t priced in yet.' },
      { id: 2, x: '45%', y: '82%', title: 'Observation Evidence', text: 'Every arrow represents a physical image taken from space. Click them to see the primary evidence for the signal change.' },
    ],
    'matrix': [
      { id: 1, x: '20%', y: '40%', title: 'Institutional Ranking', text: 'We rank every monitored location by "Signal Strength". This tells you which global hubs are showing the most unusual activity right now.' },
      { id: 2, x: '70%', y: '40%', title: 'Predictive Metrics', text: 'IC (Information Coefficient) measures how reliable this signal has been at predicting stock prices in the past. 1.0 is a perfect prediction.' },
    ]
  };

  const activeCallouts = callouts[view] || callouts['world'];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-floating pointer-events-none">
          {/* SCRIM */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-void/60 backdrop-blur-[3px]"
          />
          
          {/* TEACHER CALLOUTS */}
          {activeCallouts.map((c: any) => (
            <motion.div
              key={c.id}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{ type: 'spring', damping: 15, stiffness: 200, delay: c.id * 0.1 }}
              style={{ left: c.x, top: c.y }}
              className="absolute pointer-events-auto"
            >
              <div className="relative group">
                <div className="w-9 h-9 bg-accent-primary text-void rounded-full flex items-center justify-center type-display text-[22px] font-bold cursor-help shadow-[0_0_20px_var(--accent-primary)] border-4 border-void">
                  {c.id}
                </div>
                
                <div className="absolute top-12 left-1/2 -translate-x-1/2 w-[280px] bg-surface-3 border border-accent-primary p-4 rounded-sm shadow-2xl opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none translate-y-2 group-hover:translate-y-0">
                  <div className="type-h1 text-[12px] text-accent-primary mb-2 tracking-widest">{c.title}</div>
                  <div className="type-ui-body text-text-1 text-[12px] leading-relaxed">{c.text}</div>
                  <div className="mt-3 pt-2 border-t border-border-ghost flex items-center gap-2">
                     <span className="type-data-xs text-text-4 uppercase">Persona:</span>
                     <span className="type-data-xs text-accent-secondary font-bold uppercase underline">Explain Everything</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}

          {/* TEACHER INTERFACE */}
          <div className="absolute bottom-12 left-12 w-[400px] pointer-events-auto">
             <div className="flex flex-col gap-4">
                <div className="flex flex-col">
                   <h1 className="type-display text-text-0 text-[48px] -mb-2">EXPLAIN MODE</h1>
                   <p className="type-editorial italic text-text-2 text-[18px] leading-snug">
                     "Economic data shouldn't be a secret handshake. We'll show you exactly what the satellites are seeing."
                   </p>
                </div>
                
                <div className="flex gap-4">
                   <button 
                     onClick={onClose}
                     className="bg-accent-primary text-void px-8 py-3 type-display text-[18px] font-bold shadow-2xl hover:bg-white hover:scale-105 active:scale-95 transition-all"
                   >
                     EXIT TUTORIAL
                   </button>
                   <button className="bg-void border border-border-3 text-text-2 px-8 py-3 type-display text-[18px] font-bold hover:border-accent-primary hover:text-text-1 transition-all">
                     NEXT LESSON
                   </button>
                </div>
             </div>
          </div>

          <div className="absolute top-20 right-12 w-64 pointer-events-none text-right">
             <div className="type-data-xs text-text-4 uppercase tracking-[0.3em] mb-1">Status:</div>
             <div className="type-h1 text-accent-secondary text-[14px]">Mentorship Session Active</div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ExplainMode;
