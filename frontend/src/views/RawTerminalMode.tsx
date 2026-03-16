import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { useTerminalStore, useSignalStore } from '../store';
import { executeCommand } from '../lib/commandEngine';

const RawTerminalMode = () => {
  const { signals } = useSignalStore();
  const [history, setHistory] = useState<string[]>([
    "EXECUTING INSTITUTIONAL RELAY...",
    "HANDSHAKE COMPLETE. SESSION SECURE.",
    "READY."
  ]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [history]);

  const handleCommand = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      const cmd = input.trim();
      if (!cmd) return;
      
      setHistory(prev => [...prev, `SATTRADE> ${cmd}`]);
      executeCommand(cmd);
      setInput("");
      
      if (cmd.toUpperCase() === 'HELP') {
        setHistory(prev => [...prev, 
          "AVAILABLE COMMANDS:", 
          "- <TICKER>: Equity lookup", 
          "- W <GO>: Global world map", 
          "- MX <GO>: Signal Matrix", 
          "- FD <GO>: Satellite feed", 
          "- ZOOM <LVL>: Set zoom (1-5)",
          "- FILTER <LAYER>: Toggle layer (PORTS, VESSELS, THERMAL, FLIGHTS)",
          "- SEARCH <TICKER>: Instant chart",
          "- TEACH ME: Explain mode", 
          ""]);
      }
    }
  };

  return (
    <div className="flex-1 bg-void p-6 font-mono text-sm text-text-1 overflow-hidden flex flex-col">
      {/* PERSISTENT HEADER (BLOOMBERG STYLE) */}
      <div className="mb-4 border-b border-white/10 pb-4">
        <div className="text-accent-primary font-bold mb-2">
          SATTRADE TERMINAL v2.1.4 | {new Date().toUTCString()}
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-surface-1 p-2 border border-white/5">
            <div className="text-[10px] text-text-4 uppercase">System Status</div>
            <div className="text-bull font-bold">LIVE / HEALTHY</div>
          </div>
          <div className="bg-surface-1 p-2 border border-white/5">
             <div className="text-[10px] text-text-4 uppercase">Signals Active</div>
             <div className="text-text-1 font-bold">{signals.length}</div>
          </div>
          <div className="bg-surface-1 p-2 border border-white/5">
             <div className="text-[10px] text-text-4 uppercase">Global Coverage</div>
             <div className="text-text-2 font-bold">100.0%</div>
          </div>
          <div className="bg-surface-1 p-2 border border-white/5">
             <div className="text-[10px] text-text-4 uppercase">Alpha Pipeline</div>
             <div className="text-bull font-bold italic">ENABLED</div>
          </div>
        </div>
        
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-2">
          {signals.map(s => (
            <div key={s.id} className="flex justify-between items-center text-[12px] bg-surface-2 px-2 py-1 border border-white/5">
              <span className="text-text-4 uppercase">{s.name}</span>
              <div className="flex gap-3">
                <span className={s.status === 'bullish' ? 'text-bull' : 'text-bear'}>{s.score}%</span>
                <span className="text-text-5 font-mono">IC:{s.ic.toFixed(3)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SCROLLABLE HISTORY */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto custom-scrollbar mb-4 whitespace-pre-wrap">
        {history.map((line, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, x: -10 }} 
            animate={{ opacity: 1, x: 0 }}
            className="mb-1"
          >
            {line}
          </motion.div>
        ))}
      </div>
      
      {/* INPUT LINE */}
      <div className="flex items-center gap-2 border-t border-white/10 pt-4">
         <span className="text-accent-primary font-bold shrink-0">SATTRADE&gt;</span>
         <input 
           autoFocus
           className="bg-transparent border-none outline-none flex-1 text-text-1"
           value={input}
           title="Full Terminal Input"
           placeholder="Type command (HELP for list)..."
           onChange={(e) => setInput(e.target.value)}
           onKeyDown={handleCommand}
         />
         <motion.div 
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="w-2 h-4 bg-accent-primary"
         />
      </div>
    </div>
  );
};

export default RawTerminalMode;
