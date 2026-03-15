import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { useTerminalStore } from '../store';
import { executeCommand } from '../lib/commandEngine';

const RawTerminalMode = () => {
  const [history, setHistory] = useState<string[]>([
    "════════════════════════════════════════════════════════════",
    "SATTRADE TERMINAL  v2.1.4      15 MAR 2026  09:41:22 UTC",
    "Satellite Intelligence Platform      © SatTrade Inc.",
    "════════════════════════════════════════════════════════════",
    "",
    "3 SIGNALS LIVE    PIPELINE HEALTHY    94% COVERAGE",
    "",
    "PORT SIGNAL:    +34%  BULLISH   IC:0.047  ICIR:0.62",
    "RETAIL SIGNAL:  +12%  BULLISH   IC:0.044  ICIR:0.58",
    "THERMAL SIGNAL: +45%  BULLISH   IC:0.052  ICIR:0.68",
    "",
    "Type HELP for commands. Type any ticker for equity data.",
    "════════════════════════════════════════════════════════════",
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
      
      setHistory(prev => [...prev, `SATTRADE> ${cmd}`, `EXECUTING INSTITUTIONAL RELAY...`]);
      executeCommand(cmd);
      setInput("");
      
      if (cmd.toUpperCase() === 'HELP') {
        setHistory(prev => [...prev, "AVAILABLE COMMANDS:", "- <TICKER>: Equity lookup", "- W <GO>: Global world map", "- MX <GO>: Signal Matrix", "- FD <GO>: Satellite feed", "- TEACH ME: Explain mode", ""]);
      }
    }
  };

  return (
    <div className="flex-1 bg-void p-6 font-mono text-sm text-text-01 overflow-hidden flex flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto custom-scrollbar mb-4 whitespace-pre">
        {history.map((line, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, x: -10 }} 
            animate={{ opacity: 1, x: 0 }}
            className={line.includes('BULLISH') ? 'text-bull' : line.includes('BEARISH') ? 'text-bear' : ''}
          >
            {line}
          </motion.div>
        ))}
      </div>
      
      <div className="flex items-center gap-2">
         <span className="text-accent-1 font-bold">SATTRADE&gt;</span>
         <input 
           autoFocus
           className="bg-transparent border-none outline-none flex-1 text-text-01"
           value={input}
           title="Terminal Command Input"
           placeholder="Enter command..."
           onChange={(e) => setInput(e.target.value)}
           onKeyDown={handleCommand}
         />
         <motion.div 
           animate={{ opacity: [0, 1, 0] }}
           transition={{ duration: 0.8, repeat: Infinity }}
           className="w-2 h-4 bg-accent-1"
         />
      </div>
    </div>
  );
};

export default RawTerminalMode;
