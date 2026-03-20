import React, { useEffect, useState } from 'react';
import { X, Terminal as TerminalIcon } from 'lucide-react';

const TerminalOutput: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [output, setOutput] = useState<string[]>([]);

  useEffect(() => {
    const handleCommand = (e: any) => {
      const { command } = e.detail;
      setIsOpen(true);
      setOutput(prev => [...prev, `> ${command}`, `Executing...`, `Done.`].slice(-20));
    };

    window.addEventListener('terminal-command', handleCommand);
    return () => window.removeEventListener('terminal-command', handleCommand);
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-16 right-8 w-96 max-h-[400px] bg-surface-base border border-border-1 shadow-2xl z-50 flex flex-col font-mono">
      <div className="h-8 border-b border-border-1 flex items-center justify-between px-3 bg-surface-1">
        <div className="flex items-center gap-2">
          <TerminalIcon size={12} className="text-accent-primary" />
          <span className="text-[10px] font-bold text-text-3 uppercase tracking-widest">System Output</span>
        </div>
        <button onClick={() => setIsOpen(false)} className="text-text-4 hover:text-white">
          <X size={14} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar bg-void/80">
        {output.map((line, i) => (
          <div key={i} className={`text-[11px] mb-1 ${line.startsWith('>') ? 'text-accent-primary' : 'text-text-2'}`}>
            {line}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TerminalOutput;
