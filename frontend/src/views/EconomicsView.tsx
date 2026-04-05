import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import * as Lucide from 'lucide-react';

const Activity = Lucide.Activity || Lucide.Zap;

const Sparkline = ({ history, color }: { history: { value: string }[]; color: string }) => {
  const vals = history.slice(0, 20).map(h => parseFloat(h.value)).filter(v => !isNaN(v));
  if (vals.length < 2) return null;
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const W = 100, H = 24;
  const points = vals.map((v, i) => `${(i / (vals.length - 1)) * W},${H - ((v - min) / range) * H}`).join(' ');

  return (
    <svg width={W} height={H} className="opacity-60">
      <polyline points={points} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
    </svg>
  );
};

const MACRO_SERIES = [
  { key: 'US_CPI',      label: 'US CPI Y/Y',      unit: '%',       color: '#38bdf8' },
  { key: 'US_PPI',      label: 'PPI Industrial',  unit: 'Index',   color: '#10b981' },
  { key: 'OIL_WTI',     label: 'WTI Crude Oil',   unit: 'USD',     color: '#f59e0b' },
  { key: 'US_10Y',      label: 'US 10Y Yield',    unit: '%',       color: '#818cf8' },
  { key: 'USD_INDEX',   label: 'DXY Index',       unit: 'Index',   color: '#94a3b8' },
  { key: 'BALTIC_DRY',  label: 'Baltic Dry Index',unit: 'Pts',     color: '#10b981' },
];

const EconomicsView = () => {
  const { Globe, Crosshair, ArrowRightLeft, ArrowRight, TrendingUp } = Lucide;
  const [macroData, setMacroData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const resp = await fetch('/api/macro');
        if (!resp.ok) throw new Error();
        const json = await resp.json();
        const data = json.data;
        
        const mappedData: any = {};
        Object.keys(data).forEach(k => {
          mappedData[k] = {
            ...data[k],
            history: [
              { date: 'P', value: (data[k].prev || 0).toString() },
              { date: 'C', value: (data[k].value || 0).toString() }
            ]
          };
        });
        setMacroData(mappedData);
      } catch {
        setMacroData(null);
      } finally {
        setLoading(false);
      }
    };
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="flex-1 flex flex-col p-8 gap-8 overflow-hidden bg-slate-950/20 h-full">
      <header className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Globe size={20} className="text-accent-primary" />
          <h1 className="font-display text-2xl tracking-widest text-white">MACRO_SURVEILLANCE_L7</h1>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] font-mono text-slate-500 font-bold uppercase tracking-widest bg-white/5 px-2 py-1 border border-white/10">FRED // FED_RESERVE_ST_LOUIS</span>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse" />
            <span className="text-[10px] font-mono font-bold text-bull uppercase">Data Ingest Synchronized</span>
          </div>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-2 gap-8 min-h-0">
        {/* LEFT: INDICATORS LIST */}
        <div className="glass-panel neo-border rounded-sm flex flex-col min-h-0 overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex justify-between items-center">
            <span className="text-[11px] font-bold text-slate-300 uppercase tracking-[0.2em] flex items-center gap-2">
              <TrendingUp size={14} className="text-accent-primary" /> Live Economic Instruments
            </span>
            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">Update every 30s</span>
          </div>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <table className="w-full text-left">
              <thead className="sticky top-0 bg-slate-900/80 backdrop-blur-md z-10">
                <tr className="border-b border-white/5">
                  <th className="px-6 py-3 text-[10px] font-mono text-slate-500 uppercase tracking-widest">Instrument</th>
                  <th className="px-6 py-3 text-[10px] font-mono text-slate-500 uppercase tracking-widest">Trend</th>
                  <th className="px-6 py-3 text-[10px] font-mono text-slate-500 uppercase tracking-widest text-right">Last Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {MACRO_SERIES.map((s) => {
                  const d = macroData?.[s.key.replace('US_', '').replace('OIL_WTI', 'WTI_OIL').replace('USD_INDEX', 'DOLLAR_INDEX')];
                  const val = d?.value || 0;
                  const change = d?.change || 0;
                  return (
                    <tr key={s.key} className="hover:bg-white/5 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="text-[12px] font-bold text-white group-hover:text-accent-primary transition-colors">{s.label}</span>
                          <span className="text-[9px] text-slate-500 uppercase font-bold">{s.unit}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {d?.history && <Sparkline history={d.history} color={s.color} />}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex flex-col items-end">
                          <span className="text-[13px] font-mono font-bold text-white tracking-tighter">{Number(val).toFixed(2)}</span>
                          <span className={`text-[10px] font-mono font-bold ${change >= 0 ? 'text-bull' : 'text-bear'}`}>
                            {change >= 0 ? '+' : ''}{Number(change).toFixed(3)}
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT: CORRELATION MATRIX */}
        <div className="flex flex-col gap-8 min-h-0">
          <div className="glass-panel neo-border rounded-sm flex flex-col min-h-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex justify-between items-center">
              <span className="text-[11px] font-bold text-slate-300 uppercase tracking-[0.2em] flex items-center gap-2">
                <Crosshair size={14} className="text-accent-primary" /> Alpha Node Correlation
              </span>
              <span className="text-[10px] font-mono text-accent-primary font-bold uppercase underline tracking-widest">Spearman ρ Lead-Lag</span>
            </div>
            
            <div className="flex-1 p-4 overflow-y-auto custom-scrollbar">
              <div className="space-y-4">
                {[
                  { sat: 'Industrial Thermal', macro: 'US Industrial Prod', rho: 0.82, lead: '+12D' },
                  { sat: 'Maritime AIS Activity', macro: 'Global Trade Flow', rho: 0.91, lead: 'SYNC' },
                  { sat: 'Cargo flight Density', macro: 'Retail Logistics', rho: 0.77, lead: '+4D' },
                  { sat: 'MiroFish Consensus', macro: 'Market Volatility', rho: -0.68, lead: '+2D' },
                ].map((row, i) => (
                  <div key={i} className="bg-white/5 border border-white/5 p-4 rounded-sm hover:bg-white/10 transition-all flex items-center justify-between group">
                    <div className="flex items-center gap-4 flex-1">
                      <div className="flex flex-col">
                        <span className="text-[11px] font-bold text-white group-hover:text-accent-primary transition-colors uppercase">{row.sat}</span>
                        <div className="flex items-center gap-2 mt-1">
                           <ArrowRightLeft size={10} className="text-slate-500" />
                           <span className="text-[9px] text-slate-500 font-bold uppercase">{row.macro}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-8">
                       <div className="flex flex-col items-end">
                          <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">ρ Score</span>
                          <span className={`text-[12px] font-mono font-black ${row.rho > 0.8 ? 'text-bull' : row.rho < 0 ? 'text-bear' : 'text-accent-primary'}`}>
                            {row.rho.toFixed(2)}
                          </span>
                       </div>
                       <div className="w-16 flex flex-col items-center">
                          <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Vector</span>
                          <span className="text-[10px] font-mono font-bold bg-white/5 px-1.5 border border-white/10 text-slate-300 rounded-sm mt-1">{row.lead}</span>
                       </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* INSIGHTS PANEL */}
          <div className="glass-panel neo-border rounded-sm p-6 bg-accent-primary/5 flex flex-col gap-4 border-accent-primary/20 shadow-glow-sky">
            <div className="flex items-center gap-3">
              <Lucide.Lightbulb size={18} className="text-accent-primary" />
              <span className="text-[11px] font-bold text-accent-primary uppercase tracking-[0.3em]">AI Model Inference</span>
            </div>
            <p className="text-[13px] text-slate-200 leading-relaxed font-sans italic">
              "Systemic divergence detected between <span className="text-white font-bold underline">WTI Crude Oil</span> and 
              regional thermal activity in the Permian Basin. Historical rho-decay suggests a pricing correction 
              within the next 72-96 hours. Risk-weighted adjustment recommended."
            </p>
            <div className="mt-2 flex justify-between items-center">
              <div className="flex -space-x-2">
                 {[1,2,3].map(n => (
                   <div key={n} className="w-6 h-6 rounded-full bg-slate-800 border border-slate-900 flex items-center justify-center text-[8px] font-bold text-accent-primary">A{n}</div>
                 ))}
              </div>
              <span className="text-[10px] font-mono font-bold text-accent-primary/60 uppercase">Divergence Confidence: 94.2%</span>
            </div>
          </div>
        </div>
      </div>

      <footer className="h-6 flex items-center justify-between text-[9px] font-mono text-slate-600 uppercase tracking-widest border-t border-white/5 pt-4">
        <span>Terminal ID: ST-MACRO-99</span>
        <span>KA-BAND UPLINK: SECURE</span>
        <span>{new Date().toISOString()}</span>
      </footer>
    </div>
  );
};

export default EconomicsView;
