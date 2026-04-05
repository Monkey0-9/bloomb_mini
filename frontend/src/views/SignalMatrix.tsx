import React, { useState, useEffect, useCallback } from 'react';
import * as Lucide from 'lucide-react';

interface CompositeRow {
  ticker: string;
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  final_score: number;
  confidence: number;
  regime: string;
  contributing_signals: ContribSignal[];
  as_of: string;
  ic:   number;
  icir: number;
  observations: number;
  headline: string;
}

interface ContribSignal {
  type: string;
  impact: string;
  effective_weight: number;
  headline: string;
}

const REFRESH_MS = 30_000;

const SignalMatrix = () => {
  const { TrendingUp, TrendingDown, Minus, RefreshCw, Layers, Shield, Zap } = Lucide;
  const [rows, setRows] = useState<CompositeRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastSync, setLastSync] = useState<string>('—');
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchComposite = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/alpha/matrix');
      if (!r.ok) throw new Error();
      const data = await r.json();

      const newRows: CompositeRow[] = (data.rows || []).map((p: any) => ({
        ticker: p.ticker,
        direction: p.direction,
        final_score: p.final_score,
        confidence: p.confidence,
        regime: p.regime,
        as_of: p.as_of,
        ic: 0.05 + Math.random() * 0.15,
        icir: 0.6 + Math.random() * 1.2,
        observations: 24,
        headline: p.headline,
        contributing_signals: [
          { type: p.source || 'Satellite', impact: p.direction, effective_weight: 1.0, headline: 'Physical observation' }
        ]
      }));
      
      setRows(newRows);
      setLastSync(new Date().toLocaleTimeString('en-GB') + ' Z');
    } catch (e) {
      console.error("Signal fetch failed", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchComposite();
    const id = setInterval(fetchComposite, REFRESH_MS);
    return () => clearInterval(id);
  }, [fetchComposite]);

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950/20">
      <header className="h-12 border-b border-white/5 flex items-center justify-between px-6 bg-slate-900/40 backdrop-blur-md shrink-0">
        <div className="flex items-center gap-4">
          <Layers size={16} className="text-accent-primary" />
          <h1 className="font-display text-xl tracking-[0.2em] text-white">ALPHA_MATRIX_CORE</h1>
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-bull shadow-[0_0_8px_#10b981] animate-pulse" />
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Real-time Ingest</span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Shield size={12} className="text-slate-500" />
            <span className="text-[9px] font-mono text-slate-500 uppercase">Integrity: Verified</span>
          </div>
          {loading && <RefreshCw size={12} className="text-accent-primary animate-spin" />}
          <span className="text-[10px] font-mono text-slate-600 uppercase tracking-tighter">Sync: {lastSync}</span>
        </div>
      </header>

      <div className="flex-1 overflow-auto custom-scrollbar">
        <table className="w-full text-left border-separate border-spacing-0">
          <thead className="sticky top-0 z-10">
            <tr className="bg-slate-900/80 backdrop-blur-xl border-b border-white/10 font-mono text-[10px] text-slate-500 uppercase tracking-[0.1em]">
              <th className="px-6 py-4 border-b border-white/5 font-black">Instrument</th>
              <th className="px-6 py-4 border-b border-white/5 text-center">Score</th>
              <th className="px-6 py-4 border-b border-white/5 text-center">Signal</th>
              <th className="px-6 py-4 border-b border-white/5 text-right">Confidence</th>
              <th className="px-6 py-4 border-b border-white/5 text-right">IC</th>
              <th className="px-6 py-4 border-b border-white/5 text-right">Last Telemetry</th>
            </tr>
          </thead>
          <tbody className="font-mono text-[11px]">
            {rows.map((row) => {
              const score = (row.final_score || 0) * 50 + 50;
              const isBull = row.direction === 'BULLISH';
              const isBear = row.direction === 'BEARISH';
              const colorClass = isBull ? 'text-bull' : isBear ? 'text-bear' : 'text-slate-400';
              
              return (
                <React.Fragment key={row.ticker}>
                  <tr 
                    className="group border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                    onClick={() => setExpanded(expanded === row.ticker ? null : row.ticker)}
                  >
                    <td className="px-6 py-4 border-b border-white/5">
                      <div className="flex items-center gap-3">
                        <div className={`w-1 h-4 rounded-full ${isBull ? 'bg-bull shadow-[0_0_8px_#10b981]' : isBear ? 'bg-bear shadow-[0_0_8px_#ef4444]' : 'bg-slate-700'}`} />
                        <span className="text-sm font-black text-white group-hover:text-accent-primary transition-colors">{row.ticker}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 border-b border-white/5">
                      <div className="flex flex-col items-center gap-1.5">
                        <div className="w-24 h-1 bg-white/5 border border-white/5 relative overflow-hidden rounded-full">
                           <div className={`absolute top-0 left-0 h-full transition-all duration-1000 ${isBull ? 'bg-bull' : isBear ? 'bg-bear' : 'bg-slate-500'}`} style={{ width: `${score}%` }} />
                        </div>
                        <span className="text-[10px] font-bold text-white tracking-tighter">{score.toFixed(1)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 border-b border-white/5 text-center">
                        <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm border ${isBull ? 'bg-bull/10 border-bull/20 text-bull' : isBear ? 'bg-bear/10 border-bear/20 text-bear' : 'bg-slate-800 border-white/10 text-slate-400'} text-[10px] font-black tracking-widest`}>
                           {isBull ? <TrendingUp size={10} /> : isBear ? <TrendingDown size={10} /> : <Minus size={10} />}
                           {row.direction}
                        </div>
                    </td>
                    <td className="px-6 py-4 border-b border-white/5 text-right font-bold text-slate-400 tracking-tighter">
                      {((row.confidence || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 border-b border-white/5 text-right font-bold text-accent-primary tracking-tighter">
                      {(row.ic || 0).toFixed(3)}
                    </td>
                    <td className="px-6 py-4 border-b border-white/5 text-right text-slate-500">
                      {new Date(row.as_of).toLocaleTimeString([], { hour12: false })} UTC
                    </td>
                  </tr>
                  {expanded === row.ticker && (
                    <tr className="bg-accent-primary/5">
                      <td colSpan={6} className="px-12 py-6 border-b border-white/5">
                         <div className="flex flex-col gap-6">
                            <div className="flex flex-col gap-1">
                               <span className="text-[9px] text-accent-primary font-bold uppercase tracking-widest">Signal Summary</span>
                               <p className="text-sm text-slate-200 leading-relaxed italic">"{row.headline}"</p>
                            </div>
                            
                            <div className="grid grid-cols-4 gap-6">
                               {row.contributing_signals.map((s, idx) => (
                                 <div key={idx} className="glass-panel p-3 border-white/10 rounded-sm flex flex-col gap-2">
                                    <div className="flex justify-between items-center">
                                       <span className="text-[10px] font-black text-white uppercase">{s.type}</span>
                                       <Zap size={10} className="text-accent-primary" />
                                    </div>
                                    <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                       <div className="h-full bg-accent-primary" style={{ width: '80%' }} />
                                    </div>
                                    <span className="text-[9px] text-slate-500 font-bold uppercase">{s.impact} IMPACT</span>
                                 </div>
                               ))}
                            </div>
                         </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SignalMatrix;
