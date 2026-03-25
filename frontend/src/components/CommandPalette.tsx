/**
 * CommandPalette — Satellite-Grounded AI Intelligence Hub
 *
 * Architecture:
 * - Triggered by Ctrl+K or the `>` command line
 * - Sends natural-language queries to /api/command via POST (AnalystAgent)
 * - AnalystAgent routes intent → correct agent → view navigation
 * - Streaming response via SSE (EventSource) for live token output
 * - Supports slash commands: /NAV charts, /ALERT ZIM, /SIGNAL VALE, etc.
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, Satellite, Ship, Plane, TrendingUp, X, ArrowRight, Loader2, Command } from 'lucide-react';
import { useTerminalStore } from '../store';
import type { ViewType } from '../store/uiStore';
import { terminalCli } from '../lib/bloomberg-cli';

// ─── Types ────────────────────────────────────────────────────────────────────
interface IntentResult {
  intent: string;
  synthesis: string;
  view_suggestion: string;
  timestamp: string;
}

interface SuggestionGroup {
  label: string;
  icon: React.FC<any>;
  color: string;
  items: string[];
}

// ─── Constants ────────────────────────────────────────────────────────────────
const API_BASE = (import.meta.env.VITE_API_URL as string) || '';

const SUGGESTIONS: SuggestionGroup[] = [
  {
    label: 'Maritime Intelligence',
    icon: Ship,
    color: '#00FF9D',
    items: [
      'Show dark vessel activity near Suez Canal',
      'Port of Shanghai congestion vs ZIM stock signal',
      'AIS gap analysis for tankers in Strait of Hormuz',
    ],
  },
  {
    label: 'Satellite Signals',
    icon: Satellite,
    color: '#00D4FF',
    items: [
      'Industrial output signals for VALE in Brazil',
      'Thermal hotspot at Rio Tinto facilities',
      'Sentinel-2 optical analysis of Freeport LNG',
    ],
  },
  {
    label: 'Aviation Intelligence',
    icon: Plane,
    color: '#C084FC',
    items: [
      'Cargo flight density into Memphis hub — FDX signal',
      'UPS vs FedEx volume asymmetry this week',
      'Airline supply chain bottleneck scan',
    ],
  },
  {
    label: 'Alpha Signals',
    icon: TrendingUp,
    color: '#FFB800',
    items: [
      'Show composite alpha scores for all tickers',
      'Top 5 highest conviction BULLISH signals',
      'Macro regime vs satellite signal performance',
    ],
  },
];

// ─── Component ────────────────────────────────────────────────────────────────
interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const { setSelectedView } = useTerminalStore();
  const inputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [output, setOutput] = useState<string>('');
  const [result, setResult] = useState<IntentResult | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [histPos, setHistPos] = useState(-1);

  // Focus when opened
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setOutput('');
      setResult(null);
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [isOpen]);

  // ESC to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const submit = useCallback(async (q: string) => {
    if (!q.trim()) return;

    // 1. Try Institutional Typed CLI first (Stricli pattern)
    const cliOutput = await terminalCli.execute(q);
    if (!cliOutput.startsWith("Unknown command")) {
      setOutput(cliOutput);
      setStreaming(false);
      // If it suggested a view (e.g. RESEARCH), handle it
      if (cliOutput.includes("Research View")) {
        const ticker = q.split(/\s+/)[1]?.toUpperCase();
        if (ticker) {
          setSelectedView('signals' as ViewType);
          setTimeout(onClose, 800);
        }
      }
      return;
    }

    // 2. Fallback to Natural Language Synthesis (SSE)
    setStreaming(true);
    setOutput('');
    setResult(null);
    setHistory(prev => [q, ...prev.slice(0, 49)]);
    setHistPos(-1);

    const token = localStorage.getItem('token');
    const url = `${API_BASE}/api/command/stream?query=${encodeURIComponent(q)}&token=${token}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.token) {
          setOutput(prev => prev + data.token);
        }
        if (data.intent) {
          setResult(data);
          setStreaming(false);
          eventSource.close();
          
          if (data.view_suggestion) {
            setTimeout(() => {
              setSelectedView(data.view_suggestion as ViewType);
              onClose();
            }, 1200);
          }
        }
      } catch (err) {
        console.error('SSE Error', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Connection failed', err);
      eventSource.close();
      setStreaming(false);
      if (!output) setOutput('⚠ AI Connection Failed. Verify Satellite Uplink.');
    };
  }, [setSelectedView, onClose, output]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      submit(query);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const next = Math.min(histPos + 1, history.length - 1);
      setHistPos(next);
      setQuery(history[next] ?? '');
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const next = Math.max(histPos - 1, -1);
      setHistPos(next);
      setQuery(next === -1 ? '' : history[next]);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-start justify-center pt-[10vh]"
      style={{ background: 'rgba(7,11,15,0.88)', backdropFilter: 'blur(8px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="w-full max-w-2xl mx-4 overflow-hidden shadow-2xl"
        style={{
          background: '#0D1117',
          border: '1px solid #2D3748',
          borderRadius: '6px',
          boxShadow: '0 0 60px rgba(0,212,255,0.10), 0 20px 60px rgba(0,0,0,0.8)',
        }}
      >
        {/* ── Input Bar ─────────────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10">
          {streaming
            ? <Loader2 size={16} className="text-[#00D4FF] animate-spin shrink-0" />
            : <Search size={16} className="text-[#484F58] shrink-0" />
          }
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask satellite intelligence, type a ticker, or /NAV charts…"
            className="flex-1 bg-transparent border-none outline-none text-[13px] text-[#E6EDF3] placeholder-[#484F58]"
            style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          />
          <div className="flex items-center gap-1 shrink-0">
            <div className="border border-white/10 rounded px-1.5 py-0.5 font-mono text-[10px] text-[#484F58]">ESC</div>
          </div>
          <button onClick={onClose} className="text-[#484F58] hover:text-[#8B949E] transition-colors">
            <X size={14} />
          </button>
        </div>

        {/* ── Output Panel ──────────────────────────────────────────────────── */}
        {(streaming || output) && (
          <div className="px-5 py-4 border-b border-white/10 min-h-[80px]">
            <div className="flex items-center gap-2 mb-2">
              <Satellite size={11} className="text-[#00D4FF]" />
              <span className="font-mono text-[9px] text-[#00D4FF] uppercase tracking-widest">Satellite Intelligence Engine</span>
              {result && (
                <span className="ml-auto font-mono text-[9px] text-[#484F58] border border-white/10 px-1.5 py-0.5 rounded-sm uppercase">
                  {result.intent}
                </span>
              )}
            </div>
            <p className="font-mono text-[12px] text-[#CDD9E5] leading-relaxed">
              {output}
              {streaming && <span className="inline-block w-1.5 h-3.5 bg-[#00D4FF] ml-0.5 animate-pulse align-text-bottom" />}
            </p>
            {result?.view_suggestion && (
              <div className="mt-3 flex items-center gap-2 font-mono text-[10px] text-[#00FF9D]">
                <ArrowRight size={11} />
                Navigating to <span className="font-bold uppercase">{result.view_suggestion}</span>…
              </div>
            )}
          </div>
        )}

        {/* ── Suggestions ───────────────────────────────────────────────────── */}
        {!streaming && !output && (
          <div className="py-2 max-h-[400px] overflow-y-auto" style={{ scrollbarWidth: 'thin', scrollbarColor: '#1A2332 #0D1117' }}>
            {SUGGESTIONS.map(group => (
              <div key={group.label} className="mb-1">
                <div className="flex items-center gap-2 px-4 py-1.5">
                  <group.icon size={11} style={{ color: group.color }} />
                  <span className="font-mono text-[10px] uppercase tracking-widest" style={{ color: group.color }}>
                    {group.label}
                  </span>
                </div>
                {group.items.map(item => (
                  <button
                    key={item}
                    onClick={() => { setQuery(item); submit(item); }}
                    className="w-full text-left px-4 pl-8 py-2 font-mono text-[12px] text-[#8B949E] hover:text-[#E6EDF3] hover:bg-white/5 transition-all flex items-center justify-between group"
                  >
                    <span>{item}</span>
                    <ArrowRight size={11} className="opacity-0 group-hover:opacity-100 transition-opacity text-[#484F58]" />
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* ── Footer ────────────────────────────────────────────────────────── */}
        <div className="px-4 py-2 border-t border-white/5 flex items-center justify-between">
          <span className="font-mono text-[10px] text-[#1A2332] flex items-center gap-2">
            <Command size={9} /> Grounded in Sentinel-2 + AIS + ADS-B telemetry
          </span>
          <span className="font-mono text-[10px] text-[#1A2332]">↑↓ History · Enter Submit</span>
        </div>
      </div>
    </div>
  );
};

export default CommandPalette;
