import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, Send, FileText, Globe, Database, Cpu, Activity, Link2, BarChart2 } from 'lucide-react';
import { useTerminalStore, useSignalStore } from '../store';
import { executeCommand } from '../lib/commandEngine';

interface Citation {
  id: number;
  source: string;
  type: 'stac' | 'ais' | 'macro' | 'quant';
  confidence: number;
  url?: string;
}

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  citations?: Citation[];
  dataWidget?: 'vessel_density' | 'thermal_matrix' | 'macro_chart';
  timestamp: Date;
}

const SourcePill = ({ citation }: { citation: Citation }) => {
  const [hover, setHover] = useState(false);
  const colors = {
    stac: 'border-accent-primary text-accent-primary bg-accent-primary/10',
    ais: 'border-accent-blue text-accent-blue bg-accent-blue/10',
    macro: 'border-[#C084FC] text-[#C084FC] bg-[#C084FC]/10',
    quant: 'border-bull text-bull bg-bull/10',
  };
  
  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <span className={`inline-flex items-center justify-center min-w-[18px] h-[18px] ml-1 px-1 text-[10px] font-bold font-mono rounded-sm cursor-help transition-all border ${colors[citation.type]} align-top mt-1 hover:brightness-125`}>
        {citation.id}
      </span>
      <AnimatePresence>
        {hover && (
          <motion.div 
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-surface-2 border border-border-2 shadow-2xl z-50 p-3"
          >
            <div className="flex justify-between items-start mb-2 border-b border-border-ghost pb-2">
               <span className="type-data-xs text-text-3 uppercase tracking-widest">{citation.type} TELEMETRY</span>
               <span className="type-data-xs font-mono text-bull">CONF {citation.confidence}%</span>
            </div>
            <p className="type-ui-sm text-text-1 font-sans">{citation.source}</p>
            <div className="mt-2 flex items-center gap-1 text-accent-primary type-data-xs uppercase hover:underline cursor-pointer">
              <Link2 size={10} /> View Raw Stream
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const DataWidget = ({ type }: { type: 'vessel_density' | 'thermal_matrix' | 'macro_chart' }) => {
    if (type === 'vessel_density') {
        return (
            <div className="mt-4 p-4 border border-border-2 bg-surface-1/50 w-full max-w-sm">
                <div className="flex justify-between items-center mb-3">
                    <span className="type-data-xs text-text-3 uppercase tracking-widest">NLRTM PORT VEssEL DENSITY</span>
                    <Activity size={12} className="text-accent-blue" />
                </div>
                <div className="h-24 w-full flex items-end gap-[1px]">
                    {Array.from({length: 40}).map((_, i) => {
                        const h = 20 + Math.random() * 80;
                        const isHigh = h > 85;
                        return (
                            <div key={i} className={`flex-1 rounded-t-sm ${isHigh ? 'bg-bear shadow-[0_0_8px_rgba(255,61,61,0.5)]' : 'bg-accent-blue/50'}`} style={{ height: `${h}%` }} />
                        );
                    })}
                </div>
                <div className="mt-2 flex justify-between type-data-xs text-text-4">
                    <span>-30D</span>
                    <span className="text-bear font-bold">CURRENT CRITICAL</span>
                </div>
            </div>
        );
    }
    return null;
}

const ResearchView = () => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const { currentTicker } = useTerminalStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: `SATTRADE LLM CORE INITIALIZED. Integrating STAC orbital telemetry, AIS dark-fleet signatures, and real-time market microstructure.\n\nCurrently tracking [1]. Querying Alpha Streams...`,
      citations: [
         { id: 1, source: `${currentTicker} Live Equities Feed`, type: 'quant', confidence: 99 }
      ],
      timestamp: new Date()
    }
  ]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    const upperInput = input.trim().toUpperCase();
    if (upperInput.startsWith('/NAV ') || upperInput.endsWith(' <GO>')) {
        setTimeout(() => {
            setIsTyping(false);
            const cmd = upperInput.startsWith('/NAV ') ? upperInput.replace('/NAV ', '') : upperInput;
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'ai',
                content: `> EXECUTING KERNEL DIRECTIVE: ${cmd}\n> Initiating context switch.`,
                timestamp: new Date()
            }]);
            setTimeout(() => executeCommand(cmd), 1000);
        }, 1000);
        return;
    }

    // Institutional Perplexity Simulation
    setTimeout(() => {
      setIsTyping(false);
      let responseContent = '';
      let citations: Citation[] = [];
      let widget: any = undefined;

      if (input.toLowerCase().includes('fertilizer') || input.toLowerCase().includes('maersk') || input.toLowerCase().includes('port')) {
        responseContent = `Spatial anomaly detected at Port of Rotterdam (NLRTM) [1]. Dense dark-vessel clustering converging near major fertilizer terminals. SAR backscatter indicates deep draft (laden vessels). Conversely, Landsat TIRS [2] shows nominal industrial heat output at destination facilities.\n\n**Alpha Signal:** Lead-time discrepancy between vessel density and refining output suggests an upcoming supply bottleneck. ICIR Score +0.82 (High Conviction) [3].`;
        citations = [
            { id: 1, source: 'Copernicus Sentinel-1 SAR Backscatter (VV/VH)', type: 'stac', confidence: 94 },
            { id: 2, source: 'USGS Landsat-8 TIRS LST Retrieval', type: 'stac', confidence: 88 },
            { id: 3, source: 'SatTrade Alpha Risk Engine (TFT Model)', type: 'quant', confidence: 96 }
        ];
        widget = 'vessel_density';
      } else {
        responseContent = `I have parsed the global macro feed and orbital ingest cache. No statistically significant anomalies ($\sigma > 2$) found for this specific heuristic in the last 24H [1]. However, regional indices show elevated VIX [2]. I recommend constraining your query to specific logistical choke points (e.g., Hormuz, Panama) or industrial sectors (e.g., European Steel, LatAm Agri).`;
        citations = [
            { id: 1, source: 'Global Event Registry & GDELT', type: 'macro', confidence: 91 },
            { id: 2, source: 'CBOE VIX Spot Options', type: 'quant', confidence: 99 }
        ];
      }

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'ai',
        content: responseContent,
        citations,
        dataWidget: widget,
        timestamp: new Date()
      }]);
    }, 1800 + Math.random() * 1000);
  };

  const formatContent = (content: string, citations?: Citation[]) => {
    const parts = content.split(/(\[\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match && citations) {
        const citId = parseInt(match[1]);
        const cit = citations.find(c => c.id === citId);
        if (cit) {
            return <SourcePill key={index} citation={cit} />;
        }
      }
      // Process bolding for terminal look
      if (part.includes('**')) {
          const splitBold = part.split(/(\*\*.*?\*\*)/g);
          return (
              <span key={index}>
                  {splitBold.map((bp, i) => 
                      bp.startsWith('**') && bp.endsWith('**') 
                      ? <strong key={i} className="text-text-0 font-bold tracking-tight">{bp.slice(2, -2)}</strong> 
                      : bp
                  )}
              </span>
          )
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="flex-1 h-full bg-void flex flex-col font-sans">
      
      {/* HEADER - BLOOMBERG TERMINAL STYLE */}
      <div className="h-11 border-b border-border-1 flex items-center px-4 justify-between shrink-0 bg-surface-base">
        <div className="flex items-center gap-3">
          <Database size={16} className="text-accent-primary" />
          <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">Copilot Intelligence</span>
          <div className="w-1.5 h-1.5 rounded-full bg-bull dot-live shadow-glow-bull ml-2" />
        </div>
        <div className="flex items-center gap-4">
             <div className="flex items-center gap-2 type-data-xs text-text-4 uppercase tracking-widest border border-border-2 px-2 py-0.5">
                 <Cpu size={10} className="text-accent-blue" /> Claude 4.6 Sonnet
             </div>
             <span className="type-data-xs text-text-5 uppercase font-mono">Model: STAC-FIN-FINE-TUNED</span>
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto px-6 py-8 md:px-16 scrollbar-hide space-y-10 w-full xl:max-w-[75%] 2xl:max-w-6xl mx-auto custom-scrollbar">
        {messages.map((msg) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={msg.id} 
            className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`w-full ${msg.role === 'user' ? 'max-w-[70%]' : 'max-w-[90%]'}`}>
                {msg.role === 'user' ? (
                    <div className="bg-surface-1 border border-border-2 px-6 py-4 text-[15px] text-text-0 font-sans leading-relaxed shadow-[0_4px_24px_rgba(0,0,0,0.4)] relative">
                        {/* Terminal Corner accents */}
                        <div className="absolute top-0 left-0 w-1.5 h-1.5 border-t border-l border-accent-primary"></div>
                        <div className="absolute top-0 right-0 w-1.5 h-1.5 border-t border-r border-accent-primary"></div>
                        <div className="absolute bottom-0 left-0 w-1.5 h-1.5 border-b border-l border-accent-primary"></div>
                        <div className="absolute bottom-0 right-0 w-1.5 h-1.5 border-b border-r border-accent-primary"></div>
                        {msg.content}
                    </div>
                ) : (
                    <div className="flex gap-6">
                        <div className="w-8 h-8 flex justify-center items-center shrink-0 mt-1 border border-border-ghost bg-surface-2">
                            <Sparkles className="w-4 h-4 text-accent-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="text-[15px] text-text-1 font-sans leading-[1.8] tracking-tight whitespace-pre-wrap">
                                {formatContent(msg.content, msg.citations)}
                            </div>
                            
                            {msg.dataWidget && <DataWidget type={msg.dataWidget} />}

                            {msg.citations && msg.citations.length > 0 && (
                                <div className="mt-6 pt-4 border-t border-border-ghost">
                                    <div className="type-data-xs text-text-5 uppercase tracking-widest mb-3 flex items-center gap-2">
                                        <BarChart2 size={12}/> Verified Sources
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                        {msg.citations.map(cit => {
                                            const colors = {
                                                stac: 'border-accent-primary bg-accent-primary/5',
                                                ais: 'border-accent-blue bg-accent-blue/5',
                                                macro: 'border-[#C084FC] bg-[#C084FC]/5',
                                                quant: 'border-bull bg-bull/5',
                                              };
                                            return (
                                            <div key={cit.id} className={`flex items-start gap-3 border ${colors[cit.type]} p-3 hover:bg-surface-2 cursor-pointer transition-colors group`}>
                                                <span className="w-5 h-5 bg-surface-base border border-border-2 flex items-center justify-center text-[10px] font-bold text-text-2 shrink-0">
                                                    {cit.id}
                                                </span>
                                                <div className="flex flex-col min-w-0">
                                                    <span className="type-data-xs text-text-4 uppercase tracking-widest mb-0.5 group-hover:text-text-2 transition-colors">{cit.type}</span>
                                                    <span className="text-[12px] text-text-0 font-medium truncate">{cit.source}</span>
                                                </div>
                                            </div>
                                        )})}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
          </motion.div>
        ))}
        
        {isTyping && (
             <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start w-full">
                  <div className="flex gap-6 max-w-[90%] w-full">
                     <div className="w-8 h-8 flex justify-center items-center shrink-0 mt-1 border border-accent-primary/50 bg-accent-primary/10">
                         <Cpu className="w-4 h-4 text-accent-primary animate-pulse" />
                     </div>
                     <div className="flex-1 border border-border-ghost bg-surface-1/30 p-4 h-24 relative overflow-hidden">
                         <div className="absolute inset-0 bg-gradient-to-r from-transparent via-accent-primary/10 to-transparent animate-[shimmer_2s_infinite]"></div>
                         <div className="flex items-center gap-3 mb-2">
                             <div className="w-2 h-2 rounded-full bg-accent-primary shadow-[0_0_10px_#00FF9D] animate-pulse"></div>
                             <span className="type-data-xs text-accent-primary font-mono uppercase tracking-widest">Compiling Deep Search...</span>
                         </div>
                         <div className="space-y-2 mt-4 opacity-30">
                             <div className="h-2 bg-text-4 w-3/4"></div>
                             <div className="h-2 bg-text-4 w-1/2"></div>
                         </div>
                     </div>
                  </div>
             </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* COMMAND PALETTE - BLOOMBERG STYLE */}
      <div className="shrink-0 p-4 md:p-6 bg-surface-0 border-t border-border-1 relative z-10 w-full">
        <div className="w-full xl:max-w-[75%] 2xl:max-w-6xl mx-auto flex flex-col gap-2">
            <div className="relative group">
                <div className="absolute inset-0 bg-accent-primary/10 blur-md opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none"></div>
                <div className="relative bg-void border-2 border-border-active flex items-center p-1 focus-within:border-accent-primary/80 transition-colors shadow-inner">
                    <div className="px-4 text-accent-primary font-bold type-h1 border-r border-border-ghost mr-2 h-full flex items-center">
                        <span className="animate-pulse mr-2">_</span>CMD
                    </div>
                    <input 
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="ENTER QUERY / COMMAND (e.g. /NAV MATRIX)..."
                        className="flex-1 bg-transparent border-none outline-none text-[16px] text-accent-primary placeholder:text-text-4 font-data uppercase tracking-wider"
                    />
                    <button 
                        onClick={handleSend}
                        disabled={!input.trim() || isTyping}
                        className="h-10 px-6 bg-accent-primary text-void hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed mx-1 type-data-md font-bold uppercase tracking-widest"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
            
            <div className="flex justify-between items-center px-2">
                <div className="flex gap-4 text-[10px] text-text-4 font-mono uppercase tracking-widest">
                    <span className="flex items-center gap-1 hover:text-text-2 cursor-pointer transition-colors"><Search className="w-3 h-3" /> Deep Research</span>
                    <span className="flex items-center gap-1 hover:text-text-2 cursor-pointer transition-colors"><Globe className="w-3 h-3" /> Geopolitics</span>
                    <span className="flex items-center gap-1 hover:text-text-2 cursor-pointer transition-colors"><FileText className="w-3 h-3" /> SEC Filings</span>
                </div>
                <span className="type-data-xs text-text-5 font-mono">PRESS ↵ TO EXECUTE</span>
            </div>
        </div>
      </div>

    </div>
  );
};

export default ResearchView;
