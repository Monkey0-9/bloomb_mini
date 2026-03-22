import React, { useEffect, useState, useRef } from 'react';
import { X, Terminal as TerminalIcon, Loader2 } from 'lucide-react';

const TerminalOutput: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [output]);

  useEffect(() => {
    const handleCommand = async (e: any) => {
      const { command } = e.detail;
      setIsOpen(true);
      setIsStreaming(true);
      setOutput(prev => [...prev, `> ${command}`]);

      try {
        const url = `${(import.meta.env.VITE_API_URL as string) || ''}/api/command/stream?query=${encodeURIComponent(command)}`;
        const eventSource = new EventSource(url);
        
        let currentSynthesisLine = "";

        eventSource.onmessage = (event) => {
          if (event.data === '[DONE]') {
            eventSource.close();
            setIsStreaming(false);
            return;
          }

          try {
            const data = JSON.parse(event.data);
            if (data.content) {
              currentSynthesisLine += data.content;
              setOutput(prev => {
                const newLines = [...prev];
                if (newLines.length > 0 && !newLines[newLines.length-1].startsWith('>')) {
                  newLines[newLines.length-1] = currentSynthesisLine;
                } else {
                  newLines.push(currentSynthesisLine);
                }
                return newLines.slice(-40);
              });
            }
          } catch (err) {
            console.error("Failed to parse stream chunk:", err);
          }
        };

        eventSource.onerror = (err) => {
          console.error("EventSource error:", err);
          eventSource.close();
          setIsStreaming(false);
          setOutput(prev => [...prev, "!! SIGNAL INTERRUPTED: CONNECTION LOST"]);
        };

      } catch (err) {
        setOutput(prev => [...prev, `!! ERROR: ${(err as Error).message}`]);
        setIsStreaming(false);
      }
    };

    window.addEventListener('terminal-command', handleCommand);
    return () => window.removeEventListener('terminal-command', handleCommand);
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-16 right-8 w-[500px] max-h-[600px] bg-void/90 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.8)] z-[200] flex flex-col font-mono backdrop-blur-2xl transition-all overflow-hidden rounded-sm ring-1 ring-white/10">
      <div className="h-10 border-b border-white/10 flex items-center justify-between px-4 bg-surface-1/60">
        <div className="flex items-center gap-3">
          <TerminalIcon size={14} className="text-accent-primary animate-pulse" />
          <span className="text-[10px] font-black text-white/80 uppercase tracking-[0.3em]">Institutional Synthesis Terminal // ST-CORE-V2</span>
        </div>
        <div className="flex items-center gap-3">
          {isStreaming && <Loader2 size={12} className="text-accent-primary animate-spin" />}
          <button onClick={() => setIsOpen(false)} className="text-white/40 hover:text-white transition-colors">
            <X size={16} />
          </button>
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-void/30 leading-relaxed"
      >
        {output.map((line, i) => (
          <div key={i} className={`text-[12px] mb-3 ${line.startsWith('>') ? 'text-accent-primary font-bold border-b border-white/5 pb-1' : line.startsWith('!!') ? 'text-bear font-bold animate-pulse' : 'text-text-1'}`}>
            {line}
          </div>
        ))}
        {isStreaming && (
            <div className="w-2 h-4 bg-accent-primary animate-pulse inline-block align-middle ml-1" />
        )}
      </div>
    </div>
  );
};

export default TerminalOutput;
