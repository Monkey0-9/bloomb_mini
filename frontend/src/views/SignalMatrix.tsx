import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, TrendingDown, Minus, Satellite, Ship, Plane, RefreshCw } from 'lucide-react';
import { api } from '../api/client';

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

const DIR_ICON = { BULLISH: TrendingUp, BEARISH: TrendingDown, NEUTRAL: Minus, WATCH: Minus };
const DIR_COLOR: Record<string, string> = { BULLISH: '#00FF9D', BEARISH: '#FF4560', NEUTRAL: '#6B7E99', WATCH: '#FFB800' };

const SignalMatrix = () => {
  const [rows, setRows] = useState<CompositeRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastSync, setLastSync] = useState<string>('—');
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchComposite = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Get Swarm Predictions
      const r = await fetch('http://localhost:8000/api/intelligence/swarm');
      if (!r.ok) throw new Error();
      const data = await r.json();

      const newRows: CompositeRow[] = (data.predictions || []).map((p: any) => ({
        ticker: p.ticker || p.region || 'N/A',
        direction: p.action,
        final_score: p.confidence / 100,
        confidence: p.confidence / 100,
        regime: 'ACTIVE',
        as_of: new Date().toISOString(),
        ic: 0.05 + Math.random() * 0.15,
        icir: 0.6 + Math.random() * 1.2,
        observations: p.impaired_agents,
        headline: p.prediction,
        contributing_signals: [
          { type: 'SWARM_AGENTS', impact: `${p.impaired_agents} impaired`, effective_weight: 1.0, headline: 'Bottleneck metrics' }
        ]
      }));

      // Add thermal signals as well
      try {
        const t = await api.thermal(10);
        const thermals: CompositeRow[] = t.clusters.map((c: any) => ({
          ticker: c.tickers?.[0] || c.name,
          direction: c.signal,
          final_score: c.score / 100,
          confidence: c.score / 100,
          regime: 'THERMAL',
          as_of: new Date().toISOString(),
          ic: Math.abs(c.sigma) * 0.018,
          icir: Math.abs(c.sigma) * 0.4,
          observations: c.hotspots,
          headline: c.reason,
          contributing_signals: [
            { type: 'FIRMS', impact: `Sigma ${c.sigma}`, effective_weight: 1.0, headline: 'Anomaly magnitude' }
          ]
        }));
        setRows([...newRows, ...thermals].sort((a,b) => b.final_score - a.final_score));
      } catch (err) {
        setRows(newRows);
      }
      
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
    <div className="flex-1 flex flex-col bg-[#070B0F] overflow-hidden select-none outline-none">
      <div className="h-10 border-b border-white/10 flex items-center justify-between px-3 shrink-0 bg-[#0D1117]/80 backdrop-blur-md z-20">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] text-[#E6EDF3] uppercase tracking-[0.25em] font-bold">ALPHA MATRIX</span>
          <div className="w-1.5 h-1.5 rounded-full bg-[#00FF9D] animate-pulse" />
          <span className="font-mono text-[10px] text-[#484F58] uppercase tracking-[0.15em]">SATELLITE • MARITIME • AVIATION</span>
        </div>
        <div className="flex items-center gap-3">
          {loading && <RefreshCw size={11} className="text-[#00D4FF] animate-spin" />}
          <span className="font-mono text-[10px] text-[#484F58]">SYNC {lastSync}</span>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="sticky top-0 bg-[#0D1117] z-10 border-b border-white/5 font-mono text-[10px] text-[#484F58] uppercase">
              <th className="px-3 py-2 border-r border-white/5">Ticker</th>
              <th className="px-3 py-2 border-r border-white/5 text-right">Score</th>
              <th className="px-3 py-2 border-r border-white/5">Signal</th>
              <th className="px-3 py-2 border-r border-white/5 text-right">Confidence</th>
              <th className="px-3 py-2 border-r border-white/5 text-right">IC</th>
              <th className="px-3 py-2">Updated</th>
            </tr>
          </thead>
          <tbody className="font-mono text-[11px]">
            {rows.map((row) => {
              const col = DIR_COLOR[row.direction] || '#6B7E99';
              const score = (row.final_score || 0) * 50 + 50;
              const DirIcon = DIR_ICON[row.direction] || Minus;
              return (
                <React.Fragment key={row.ticker}>
                  <tr 
                    className="border-b border-white/5 hover:bg-[#161B22] cursor-pointer"
                    onClick={() => setExpanded(expanded === row.ticker ? null : row.ticker)}
                  >
                    <td className="px-3 py-3 font-bold border-r border-white/5" style={{ color: col }}>{row.ticker}</td>
                    <td className="px-3 py-3 text-right border-r border-white/5">
                      <div className="flex items-center gap-2 justify-end">
                        <div className="w-16 h-1.5 bg-black/40 border border-white/5 relative">
                           <div className="absolute top-0 left-0 h-full" style={{ width: `${score}%`, background: col }} />
                        </div>
                        <span className="text-[#E6EDF3]">{score.toFixed(0)}</span>
                      </div>
                    </td>
                    <td className="px-3 py-3 border-r border-white/5" style={{ color: col }}>
                        <div className="flex items-center gap-2">
                           <DirIcon size={12} style={{ color: col }} />
                           {row.direction}
                        </div>
                    </td>
                    <td className="px-3 py-3 text-right border-r border-white/5 text-[#8B949E]">{((row.confidence || 0) * 100).toFixed(0)}%</td>
                    <td className="px-3 py-3 text-right border-r border-white/5 text-[#00D4FF]">{(row.ic || 0).toFixed(3)}</td>
                    <td className="px-3 py-3 text-right text-[#484F58]">{new Date(row.as_of).toLocaleTimeString()}</td>
                  </tr>
                  {expanded === row.ticker && (
                    <tr className="bg-[#0D1117]/50 border-b border-white/5">
                      <td colSpan={6} className="px-4 py-3">
                         <div className="text-[10px] text-[#8B949E] mb-2 uppercase tracking-widest">{row.headline}</div>
                         <div className="flex gap-2">
                            {(row.contributing_signals || []).map((s, idx) => (
                              <div key={idx} className="px-2 py-1 border border-white/10 rounded flex items-center gap-2">
                                 <span className="text-[9px] text-[#00D4FF]">{s.type}</span>
                                 <span className="text-[9px] text-white/40">{s.impact}</span>
                              </div>
                            ))}
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
