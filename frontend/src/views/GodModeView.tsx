import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as Lucide from 'lucide-react';
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
  const { ChevronRight, Loader2, Terminal, ShieldAlert } = Lucide;
  
  return (
    <div className="flex-1 flex flex-col border-r border-white/5 bg-slate-900/20 backdrop-blur-md overflow-hidden relative group">
      <header className={`p-6 border-b border-white/5 flex flex-col gap-4 bg-gradient-to-b from-${color}/5 to-transparent`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-sm bg-${color}/10 border border-${color}/20 shadow-glow-${color === 'bull' ? 'bull' : color === 'bear' ? 'bear' : 'sky'}`}>
              <Icon size={20} className={`text-${color}`} />
            </div>
            <div className="flex flex-col">
              <h3 className="font-display text-lg tracking-widest text-white leading-none">{title}</h3>
              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mt-1">{persona} AGENT PROFILE</span>
            </div>
          </div>
          {response && (
            <div className="flex flex-col items-end">
              <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Health Index</span>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-sm font-mono font-black ${response.gtfi > 0.8 ? 'text-bull' : 'text-bear'}`}>{response.gtfi}</span>
                <div className={`w-1.5 h-1.5 rounded-full ${response.gtfi > 0.8 ? 'bg-bull' : 'bg-bear'} animate-pulse shadow-[0_0_8px_currentColor]`} />
              </div>
            </div>
          )}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar space-y-8">
        {isLoading ? (
          <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-60">
             <div className="relative">
                <Loader2 size={48} className={`animate-spin text-${color}`} />
                <div className={`absolute inset-0 blur-xl animate-pulse text-${color}`}>
                   <Loader2 size={48} />
                </div>
             </div>
             <div className="flex flex-col items-center gap-2">
                <p className="text-[10px] font-mono font-bold uppercase tracking-[0.4em] text-white animate-pulse">Alpha Synthesis In_Progress</p>
                <div className="h-1 w-32 bg-white/5 rounded-full overflow-hidden">
                   <motion.div 
                     initial={{ width: 0 }}
                     animate={{ width: '100%' }}
                     transition={{ duration: 2, repeat: Infinity }}
                     className={`h-full bg-${color}`} 
                   />
                </div>
             </div>
          </div>
        ) : response ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="prose prose-invert prose-sm max-w-none prose-p:text-[13px] prose-p:leading-relaxed prose-p:text-slate-300 prose-headings:font-display prose-headings:tracking-widest prose-headings:uppercase prose-headings:text-white prose-strong:text-white prose-code:text-accent-primary"
          >
            <ReactMarkdown>{response.report}</ReactMarkdown>
          </motion.div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-20">
             <Terminal size={64} className="text-white" />
             <div className="text-center">
                <p className="font-display text-xl tracking-[0.3em] text-white mb-2 uppercase">Awaiting Directive</p>
                <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">Inject scenario into global swarm for parallel analysis</p>
             </div>
          </div>
        )}
      </div>

      {response && (
        <footer className="p-6 border-t border-white/5 bg-slate-900/40 flex items-center justify-between">
            <div className="flex items-center gap-8">
                <div className="flex flex-col">
                    <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Model Confidence</span>
                    <span className="text-[14px] font-mono font-black text-white tracking-tighter">{response.confidence}%</span>
                </div>
                <div className="flex flex-col">
                    <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Vector Logic</span>
                    <span className="text-[10px] font-bold text-bull uppercase tracking-widest">Validated</span>
                </div>
            </div>
            <button className={`w-10 h-10 rounded-sm bg-${color}/10 border border-${color}/20 flex items-center justify-center transition-all text-white/40 hover:text-${color} hover:bg-${color}/20 active:scale-95 shadow-glow-${color === 'bull' ? 'bull' : color === 'bear' ? 'bear' : 'sky'}`}>
               <ChevronRight size={20} />
            </button>
        </footer>
      )}
    </div>
  );
};

const GodModeView = () => {
  const { Cpu, Search, Zap, Loader2, Target, Info } = Lucide;
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
    <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden relative">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#38bdf8 1px, transparent 1px)', backgroundSize: '32px 32px' }} />

      <header className="h-16 border-b border-white/5 flex items-center justify-between px-10 glass-panel z-20 shrink-0">
        <div className="flex items-center gap-10">
          <div className="flex items-center gap-4">
             <div className="p-3 rounded-sm bg-accent-primary/20 border border-accent-primary/30 shadow-glow-sky">
                <Cpu size={22} className="text-accent-primary" />
             </div>
             <div className="flex flex-col">
               <h1 className="font-display text-2xl tracking-[0.3em] text-white leading-none">GODMODE_OVERRIDE</h1>
               <span className="text-[9px] font-mono text-slate-500 font-bold tracking-widest uppercase mt-1">Multi-Agent Strategic Divergence Engine</span>
             </div>
          </div>
          
          <div className="h-8 w-px bg-white/10" />
          
          <div className="flex items-center gap-12">
             {[
               { label: 'Global Swarm Nodes', val: '2,481', color: 'text-bull' },
               { label: 'Inductive Agents', val: '05', color: 'text-accent-primary' },
               { label: 'Consensus Delta', val: results?.standard?.gtfi || '1.000', color: 'text-white' }
             ].map(stat => (
               <div key={stat.label} className="flex flex-col">
                 <span className="text-[8px] text-slate-500 font-bold uppercase tracking-[0.2em]">{stat.label}</span>
                 <span className={`text-[13px] font-mono font-black ${stat.color} uppercase tracking-tighter mt-0.5`}>{stat.val}</span>
               </div>
             ))}
          </div>
        </div>
        
        <div className="flex items-center gap-3 glass-panel px-4 py-1.5 border-white/10 rounded-full">
           <div className="w-2 h-2 rounded-full bg-bear animate-pulse shadow-[0_0_8px_#ef4444]" />
           <span className="text-[10px] font-mono font-black text-bear uppercase tracking-[0.2em]">Live Simulation Mode</span>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden relative">
        <PersonaColumn 
          title="Tactical Reserve" 
          persona="Cautious" 
          icon={Lucide.Shield} 
          color="bull" 
          isLoading={isSynthesizing}
          response={results?.Cautious}
        />
        <PersonaColumn 
          title="Strategic Direct" 
          persona="Aggressive" 
          icon={Lucide.Sword} 
          color="bear" 
          isLoading={isSynthesizing}
          response={results?.Aggressive}
        />
        <PersonaColumn 
          title="Equilibrium Core" 
          persona="Standard" 
          icon={Lucide.Scale} 
          color="accent-primary" 
          isLoading={isSynthesizing}
          response={results?.Standard}
        />

        <AnimatePresence>
          {!results && !isSynthesizing && (
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center z-10 overflow-hidden">
               <div className="w-[120%] h-[120%] border border-accent-primary/5 rounded-full animate-spin-slow opacity-20" />
               <div className="absolute w-[80%] h-[80%] border border-accent-primary/5 rounded-full animate-reverse-spin-slow opacity-10" />
               <div className="absolute inset-0 bg-gradient-radial from-transparent via-transparent to-slate-950/80" />
            </div>
          )}
        </AnimatePresence>
      </div>

      <footer className="h-28 p-8 glass-panel border-t border-white/5 flex items-center justify-center z-30 shrink-0 shadow-2xl relative">
        <form 
          onSubmit={handleSynthesize}
          className="w-full max-w-5xl relative group"
        >
          <div className="absolute inset-y-0 left-6 flex items-center text-slate-600 group-focus-within:text-accent-primary transition-colors">
            <Search size={22} />
          </div>
          <input 
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="INJECT TACTICAL REQUIREMENT OR GEOPOLITICAL SCENARIO FOR MULTI-AGENT SYNTHESIS..."
            className="w-full h-16 bg-slate-900/60 border border-white/10 rounded-sm pl-16 pr-48 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-accent-primary/50 focus:bg-slate-900/80 transition-all shadow-inner tracking-widest font-mono uppercase"
          />
          <div className="absolute right-3 inset-y-3 flex items-center gap-4">
            <div className="px-4 h-full flex items-center border-l border-white/10 text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em]">
               EXECUTE_DIRECTIVE [ENTER]
            </div>
            <button 
              type="submit"
              disabled={isSynthesizing || !query.trim()}
              className={`h-full px-8 bg-accent-primary text-slate-950 font-display text-lg tracking-[0.2em] rounded-sm transition-all flex items-center gap-3 ${
                isSynthesizing ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white active:scale-95 shadow-glow-sky'
              }`}
            >
              {isSynthesizing ? <Loader2 className="animate-spin" size={16} /> : <Zap size={16} />}
              SYNTHESIZE
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
          animation: spin-slow 40s linear infinite;
        }
        .animate-reverse-spin-slow {
          animation: reverse-spin-slow 50s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default GodModeView;
