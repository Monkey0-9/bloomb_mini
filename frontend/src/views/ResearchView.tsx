import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Sparkles, Send, FileText, Globe, Database, Cpu } from 'lucide-react';
import { useTerminalStore } from '../store';
import { executeCommand } from '../lib/commandEngine';

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

interface Citation {
  id: number;
  source: string;
  url?: string;
}

const ResearchView = () => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const { indices, currentTicker } = useTerminalStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: `SATTRADE AI COPILOT INITIALIZED. Currently tracking ${currentTicker}. Accessing institutional data streams, STAC telemetry, and global macro feeds. How can I assist your analysis today?`,
      timestamp: new Date()
    }
  ]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
     setMessages([{
        id: Date.now().toString(),
        role: 'ai',
        content: `SATTRADE AI COPILOT LINK ESTABLISHED. Now tracking ${currentTicker}. Analyzing orbital intel...`,
        timestamp: new Date()
     }]);
  }, [currentTicker]);

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

    // Command parsing logic
    const upperInput = input.trim().toUpperCase();
    if (upperInput.startsWith('/NAV ') || upperInput.endsWith(' <GO>')) {
        setTimeout(() => {
            setIsTyping(false);
            const cmd = upperInput.startsWith('/NAV ') ? upperInput.replace('/NAV ', '') : upperInput;
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'ai',
                content: `EXECUTING TERMINAL COMMAND: ${cmd}. Standby for transition.`,
                timestamp: new Date()
            }]);
            setTimeout(() => executeCommand(cmd), 1000);
        }, 1000);
        return;
    }

    // Perplexity style simulated response
    setTimeout(() => {
      setIsTyping(false);
      let responseContent = '';
      let citations: Citation[] = [];
      
      const cleanInput = input.trim().toUpperCase();
      // If it looks like a ticker, assume navigation intent
      if (cleanInput.length <= 5 && !cleanInput.includes(' ')) {
         useTerminalStore.getState().setCurrentTicker(`${cleanInput} US Equity`);
      }

      if (input.toLowerCase().includes('fertilizer') || input.toLowerCase().includes('maersk')) {
        responseContent = `Based on current AIS telemetry and Sentinel-2 optical data, the Maersk/ZIM fertilizer corridor is operating at 92% capacity. Recent berthing times at Shanghai Yangshan [1] suggest a slight backlog (+1.2 days). The ICIR score for the Asia-Pacific fertilizer route is currently 0.74 (Bullish) [2]. I recommend monitoring the MATX ticker for secondary impacts.`;
        citations = [
            { id: 1, source: 'Global Ports Tracker / AIS', url: '#' },
            { id: 2, source: 'SatTrade Internal Quant Model (Score 91)', url: '#' }
        ];
      } else if (input.toLowerCase().includes('market') || input.toLowerCase().includes('spy')) {
        const spy = indices.find(i => i.id === 'SPY');
        responseContent = `The broader market indices are showing mixed sentiment. The SPY is currently trading at ${spy?.value || 'N/A'} (${spy?.change || 'N/A'}). Institutional flow data suggests a rotation out of deep-water logistics into specialized freight. [1]`;
        citations = [{ id: 1, source: 'Alpaca Institutional Feed', url: '#' }];
      } else {
        responseContent = `I have analyzed your query against the current terminal state. While I don't have a specific pre-programmed intelligence brief for that exact phrasing, I am monitoring 75+ global assets and real-time market data. You can ask me about specific logistical corridors, commodity flows (like fertilizer), or ask me to navigate the terminal (e.g., /NAV MATRIX).`;
      }

      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'ai',
        content: responseContent,
        citations,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);
    }, 1500 + Math.random() * 1000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const formatContent = (content: string) => {
    // Replace [1], [2], etc. with styled citation pills
    const parts = content.split(/(\[\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        return (
          <sup key={index} className="inline-flex items-center justify-center w-4 h-4 ml-1 text-[9px] font-bold text-void bg-accent-primary rounded-full cursor-help hover:bg-white transition-colors align-top mt-1">
            {match[1]}
          </sup>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="flex-1 h-full bg-void flex flex-col pt-12"> {/* pt-12 to account for Masthead */}
      
      {/* HEADER */}
      <div className="h-14 border-b border-white/10 flex items-center px-6 shrink-0 bg-surface-1/50 backdrop-blur-sm z-10 relative">
        <Sparkles className="w-5 h-5 text-accent-primary mr-3" />
        <div>
            <h1 className="text-[14px] font-bold text-text-1 tracking-widest uppercase">SatTrade AI Copilot</h1>
            <p className="text-[10px] text-accent-primary/70 font-mono">STAC TELEMETRY • ALPACA MARKETS • OSINT</p>
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto p-6 md:p-12 scrollbar-hide space-y-8 max-w-5xl mx-auto w-full">
        {messages.map((msg) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={msg.id} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[85%] ${msg.role === 'user' ? 'ml-auto' : 'mr-auto'}`}>
                {msg.role === 'user' ? (
                    <div className="bg-surface-2 border border-white/5 rounded-2xl rounded-tr-sm px-6 py-4 text-[14px] text-text-1 font-sans leading-relaxed shadow-lg">
                        {msg.content}
                    </div>
                ) : (
                    <div className="flex gap-4">
                        <div className="w-8 h-8 rounded bg-accent-primary/10 border border-accent-primary/30 flex justify-center items-center shrink-0 mt-1">
                            <Cpu className="w-4 h-4 text-accent-primary" />
                        </div>
                        <div className="flex-1 space-y-4">
                            <div className="text-[15px] text-text-1 font-sans leading-relaxed">
                                {formatContent(msg.content)}
                            </div>
                            
                            {/* CITATIONS (Perplexity Style) */}
                            {msg.citations && msg.citations.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-white/10 flex gap-2 flex-wrap">
                                    {msg.citations.map(cit => (
                                        <div key={cit.id} className="flex items-center gap-2 bg-surface-1 border border-white/10 px-3 py-1.5 rounded-full hover:border-accent-primary/50 cursor-pointer transition-colors">
                                            <span className="w-4 h-4 rounded-full bg-surface-3 flex items-center justify-center text-[9px] font-bold text-text-3">
                                                {cit.id}
                                            </span>
                                            <span className="text-[11px] text-text-2 font-mono">{cit.source}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
          </motion.div>
        ))}
        
        {isTyping && (
             <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                  <div className="flex gap-4 max-w-[85%]">
                     <div className="w-8 h-8 rounded bg-accent-primary/10 border border-accent-primary/30 flex justify-center items-center shrink-0 mt-1">
                         <Cpu className="w-4 h-4 text-accent-primary animate-pulse" />
                     </div>
                     <div className="flex items-center gap-2 mt-2">
                         <div className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '0ms' }}></div>
                         <div className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '150ms' }}></div>
                         <div className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '300ms' }}></div>
                         <span className="text-[10px] text-accent-primary font-mono ml-2 uppercase">Synthesizing Data...</span>
                     </div>
                  </div>
             </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* INPUT AREA (Perplexity Style Search Bar) */}
      <div className="shrink-0 p-6 bg-gradient-to-t from-void via-void to-transparent relative z-10 w-full max-w-4xl mx-auto">
        <div className="relative group shadow-2xl">
            <div className="absolute inset-0 bg-accent-primary/5 blur-xl rounded-2xl transition-opacity opacity-0 group-focus-within:opacity-100"></div>
            <div className="relative bg-surface-2 border border-white/10 rounded-2xl flex items-center p-2 focus-within:border-accent-primary/50 transition-colors">
                <button className="p-3 text-text-4 hover:text-accent-primary transition-colors">
                    <Database className="w-5 h-5" />
                </button>
                <input 
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask anything or use /NAV to execute commands..."
                    className="flex-1 bg-transparent border-none outline-none text-[15px] text-text-1 placeholder:text-text-4 px-2 font-sans"
                />
                <button 
                    onClick={handleSend}
                    disabled={!input.trim() || isTyping}
                    className="p-3 bg-accent-primary text-void rounded-xl hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed mx-1"
                >
                    <Send className="w-4 h-4" />
                </button>
            </div>
        </div>
        
        <div className="flex justify-center gap-4 mt-4 text-[10px] text-text-4 font-mono font-bold uppercase tracking-widest">
            <span className="flex items-center gap-1"><Search className="w-3 h-3" /> Query OSINT</span>
            <span className="flex items-center gap-1"><Globe className="w-3 h-3" /> Analyze Routes</span>
            <span className="flex items-center gap-1"><FileText className="w-3 h-3" /> Generate Reports</span>
        </div>
      </div>

    </div>
  );
};

export default ResearchView;
