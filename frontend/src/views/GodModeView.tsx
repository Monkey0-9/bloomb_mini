import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  Sword, 
  Scale, 
  Search, 
  Terminal, 
  Zap, 
  AlertTriangle, 
  Activity,
  Globe,
  Loader2,
  Cpu,
  ChevronRight,
  TrendingDown,
  TrendingUp,
  Minus
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const PersonaColumn = ({ 
  title, 
  persona, 
  icon: Icon, 
  color, 
  response, 
  isLoading 
}: { 
  title: string; 
  persona: string; 
  icon: any; 
  color: string; 
  response: any; 
  isLoading: boolean; 
}) => {
  return (
    <div className="flex-1 flex flex-col border-r border-white/5 bg-void/20 backdrop-blur-sm overflow-hidden">
      <div className={`p-4 border-b border-white/5 flex items-center justify-between bg-${color}/5`}>
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-${color}/10 border border-${color}/20`}>
            <Icon size={18} className={`text-${color}`} />
          </div>
          <div>
            <h3 className="text-[11px] font-bold text-white tracking-[0.2em] uppercase">{title}</h3>
            <p className="text-[8px] text-white/40 uppercase tracking-widest">{persona} PROFILE</p>
          </div>
        </div>
        {response && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-white/40">GTFI: {response.gtfi}</span>
            <div className={`w-1.5 h-1.5 rounded-full ${response.gtfi > 0.8 ? 'bg-bull' : 'bg-bear'} animate-pulse`} />
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-6">
        {isLoading ? (
          <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-50">
             <Loader2 size={32} className={`animate-spin text-${color}`} />
             <p className="text-[10px] font-mono uppercase tracking-[0.3em] animate-pulse text-white/40">Synthesizing {persona} Alpha...</p>
          </div>
        ) : response ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="prose prose-invert prose-xs max-w-none prose-p:text-[11px] prose-p:leading-relaxed prose-p:text-white/70 prose-headings:text-white prose-headings:tracking-tighter prose-headings:uppercase prose-headings:text-[13px] prose-strong:text-white prose-code:text-accent-primary"
          >
            <ReactMarkdown>{response.report}</ReactMarkdown>
          </motion.div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-20">
             <Terminal size={48} className="text-white/20" />
             <p className="text-[10px] font-mono uppercase tracking-[0.4em] text-center">Awaiting Tactical Requirement</p>
          </div>
        )}
      </div>

      {response && (
        <div className="p-4 border-t border-white/5 bg-white/2 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <div className="flex flex-col">
                    <span className="text-[8px] text-white/30 uppercase tracking-widest">Confidence</span>
                    <span className="text-[10px] font-bold text-white font-mono">{response.confidence}%</span>
                </div>
                <div className="w-[1px] h-6 bg-white/5" />
                <div className="flex flex-col">
                    <span className="text-[8px] text-white/30 uppercase tracking-widest">Status</span>
                    <span className="text-[10px] font-bold text-bull uppercase">Nominal</span>
                </div>
            </div>
            <button className={`p-2 hover:bg-${color}/10 border border-transparent hover:border-${color}/20 rounded-md transition-all text-white/40 hover:text-${color}`}>
               <ChevronRight size={16} />
            </button>
        </div>
      )}
    </div>
  );
};

const GodModeView = () => {
  const [query, setQuery] = useState('');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleSynthesize = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || isSynthesizing) return;

    setIsSynthesizing(true);
    try {
      const resp = await fetch('/api/intelligence/godmode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      if (resp.ok) {
        const data = await resp.json();
        setResults(data.responses);
      }
    } catch (err) {
      console.error("GodMode synthesis failed:", err);
    } finally {
      setIsSynthesizing(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden font-mono">
      {/* Header Bar */}
      <header className="h-16 border-b border-white/10 flex items-center justify-between px-8 bg-surface-1/40 backdrop-blur-xl z-20 shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
             <div className="p-2 rounded bg-accent-primary/20 border border-accent-primary/30">
                <Cpu size={20} className="text-accent-primary" />
             </div>
             <div className="flex flex-col">
               <h1 className="text-sm font-black text-white tracking-[0.4em] uppercase">GodMode Dashboard</h1>
               <span className="text-[9px] text-white/40 tracking-widest uppercase">Multi-Agent Strategic Divergence Discovery</span>
             </div>
          </div>
          <div className="h-8 w-[1px] bg-white/10" />
          <div className="flex items-center gap-8">
             {[
               { label: 'Swarm Nodes', val: '2,481', color: 'text-bull' },
               { label: 'Active Personas', val: '03', color: 'text-accent-primary' },
               { label: 'GTFI Consensus', val: results?.standard?.gtfi || '1.000', color: 'text-white' }
             ].map(stat => (
               <div key={stat.label} className="flex flex-col">
                 <span className="text-[8px] text-white/30 uppercase tracking-[0.2em]">{stat.label}</span>
                 <span className={`text-[11px] font-bold ${stat.color} font-mono uppercase tracking-tighter`}>{stat.val}</span>
               </div>
             ))}
          </div>
        </div>
        
        <div className="flex items-center gap-4">
           <div className="flex items-center gap-2 px-3 py-1 bg-bear/10 border border-bear/20 rounded-full">
              <div className="w-1.5 h-1.5 rounded-full bg-bear animate-pulse" />
              <span className="text-[9px] font-bold text-bear uppercase tracking-widest">Live Synthetic Intelligence</span>
           </div>
        </div>
      </header>

      {/* Main Comparison Area */}
      <div className="flex-1 flex overflow-hidden relative">
        <PersonaColumn 
          title="Tactical Reserve" 
          persona="Cautious" 
          icon={Shield} 
          color="bull" 
          isLoading={isSynthesizing}
          response={results?.cautious}
        />
        <PersonaColumn 
          title="Strategic Direct" 
          persona="Aggressive" 
          icon={Sword} 
          color="bear" 
          isLoading={isSynthesizing}
          response={results?.aggressive}
        />
        <PersonaColumn 
          title="Equilibrium Core" 
          persona="Standard" 
          icon={Scale} 
          color="accent-primary" 
          isLoading={isSynthesizing}
          response={results?.standard}
        />

        {/* Global UI Overlays */}
        <AnimatePresence>
          {!results && !isSynthesizing && (
            <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               exit={{ opacity: 0 }}
               className="absolute inset-0 pointer-events-none flex items-center justify-center z-10"
            >
               <div className="w-[800px] h-[800px] border border-white/5 rounded-full animate-spin-slow" />
               <div className="absolute w-[600px] h-[600px] border border-white/5 rounded-full animate-reverse-spin-slow" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Unified Input Bar (GodMode Pattern) */}
      <footer className="h-24 p-6 bg-surface-1/40 border-t border-white/10 flex items-center justify-center backdrop-blur-2xl z-30 shrink-0 shadow-2xl">
        <form 
          onSubmit={handleSynthesize}
          className="w-full max-w-4xl relative group"
        >
          <div className="absolute inset-y-0 left-5 flex items-center text-white/20 group-focus-within:text-accent-primary transition-colors">
            <Search size={20} />
          </div>
          <input 
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ENTER TACTICAL REQUIREMENT OR GEOPOLITICAL SCENARIO FOR MULTI-AGENT SYNTHESIS..."
            className="w-full h-14 bg-void/80 border border-white/10 rounded-lg pl-14 pr-40 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-accent-primary/50 focus:ring-1 focus:ring-accent-primary/20 transition-all shadow-inner tracking-wider font-mono uppercase"
          />
          <div className="absolute right-2 inset-y-2 flex items-center gap-2">
            <div className="px-3 h-full flex items-center gap-2 text-[9px] font-bold text-white/30 uppercase tracking-widest mr-2">
               CTRL + ENTER TO EXECUTE
            </div>
            <button 
              type="submit"
              disabled={isSynthesizing || !query.trim()}
              className={`h-full px-6 bg-accent-primary text-void font-black uppercase text-[10px] tracking-[0.2em] rounded-md transition-all flex items-center gap-2 ${
                isSynthesizing ? 'opacity-50 cursor-not-allowed' : 'hover:brightness-110 active:scale-95 shadow-lg shadow-accent-primary/20'
              }`}
            >
              {isSynthesizing ? <Loader2 className="animate-spin" size={14} /> : <Zap size={14} />}
              Synthesize Alpha
            </button>
          </div>
        </form>
      </footer>

      <style>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes reverse-spin-slow {
          from { transform: rotate(360deg); }
          to { transform: rotate(0deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 20s linear infinite;
        }
        .animate-reverse-spin-slow {
          animation: reverse-spin-slow 25s linear infinite;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 2px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.05);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.1);
        }
      `}</style>
    </div>
  );
};

export default GodModeView;
