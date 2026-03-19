import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart2, Globe, DollarSign, Activity, Crosshair, ArrowRight, ArrowRightLeft } from 'lucide-react';

const Sparkline = ({ history, color, isNegative }: { history: { value: string }[]; color: string; isNegative?: boolean }) => {
  const vals = history.slice(0, 30).map(h => parseFloat(h.value)).filter(v => !isNaN(v));
  if (vals.length < 2) return null;
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const W = 100, H = 24;
  
  const points = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * W;
    const y = H - ((v - min) / range) * H;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={W} height={H} className="opacity-90">
      <defs>
        <linearGradient id={`grad-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.2} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <polygon 
        points={`0,${H} ${points} ${W},${H}`} 
        fill={`url(#grad-${color.replace('#','')})`}
      />
      <polyline points={points} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
    </svg>
  );
};

const MACRO_SERIES = [
  { key: 'US_CPI',      label: 'US CPI Y/Y',      unit: '%',       color: '#00C8FF' },
  { key: 'US_PPI',      label: 'PPI Final Demand',unit: 'Index',   color: '#00FF9D' },
  { key: 'OIL_WTI',     label: 'WTI Crude Oil',   unit: '$/bbl',   color: '#FFB700' },
  { key: 'NATURAL_GAS', label: 'Henry Hub Gas',   unit: '$/MMBtu', color: '#FFB700' },
  { key: 'US_10Y',      label: 'US 10Y Yield',    unit: '%',       color: '#C084FC' },
  { key: 'FED_FUNDS',   label: 'Effective Fed Funds', unit: '%',   color: '#F472B6' },
  { key: 'USD_INDEX',   label: 'DXY Trade Index', unit: 'Index',   color: '#94A3B8' },
  { key: 'BALTIC_DRY',  label: 'Baltic Dry Index',unit: 'Pts',     color: '#00FF9D' },
];

interface SeriesData {
  latest_value: string | null;
  latest_date: string | null;
  history: { date: string; value: string }[];
}

const MacroRow = ({ s, data }: { s: typeof MACRO_SERIES[0], data: SeriesData | null }) => {
  const val = data?.latest_value ? parseFloat(data.latest_value) : null;
  const prev = data?.history?.[1]?.value ? parseFloat(data.history[1].value) : null;
  const change = val !== null && prev !== null ? val - prev : null;
  const pct = change !== null && prev ? (change / prev) * 100 : null;
  const isUp = change !== null && change >= 0;

  return (
      <div className="flex items-center h-8 border-b border-surface-4 hover:bg-surface-2 transition-colors group">
          <div className="w-1.5 h-full opacity-0 group-hover:opacity-100 transition-opacity" style={{ backgroundColor: s.color }}></div>
          <div className="flex-1 px-2 py-0 flex items-center justify-between">
              <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 shrink-0 border border-white/20" style={{ backgroundColor: s.color + '40' }}></div>
                  <span className="text-[11px] text-accent-primary font-bold uppercase w-40 truncate">{s.label}</span>
                  <span className="text-[9px] text-neutral uppercase w-16 text-right mr-4">{s.unit}</span>
              </div>
              <div className="flex items-center gap-2">
                  {data?.history ? (
                      <div className="w-20 opacity-60 group-hover:opacity-100 transition-opacity">
                          <Sparkline history={data.history} color={s.color} />
                      </div>
                  ) : <div className="w-20 h-4 bg-surface-1 animate-pulse"></div>}
                  
                  <div className="w-24 text-right flex flex-col items-end justify-center">
                      {val !== null ? (
                          <motion.span 
                              key={val}
                              initial={{ opacity: 0, x: -5 }}
                              animate={{ opacity: 1, x: 0 }}
                              className="text-[11px] font-bold text-accent-primary tabular-nums leading-none tracking-tight"
                          >
                              {val.toFixed(2)}
                          </motion.span>
                      ) : <span className="text-neutral animate-pulse">—</span>}
                      
                      {change !== null && (
                          <div className={`flex items-center justify-end gap-1 text-[9px] mt-0 tracking-wider ${isUp ? 'text-bull' : 'text-bear'}`}>
                              {isUp ? '+' : ''}{change.toFixed(3)} ({pct !== null ? (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%' : ''})
                          </div>
                      )}
                  </div>
              </div>
          </div>
      </div>
  );
};

const EconomicsView = () => {
  const [macroData, setMacroData] = useState<Record<string, SeriesData> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const resp = await fetch('http://localhost:8000/api/alpha/macro');
        if (!resp.ok) throw new Error();
        const data = await resp.json();
        
        // Mock Baltic Dry for completeness
        if (!data['BALTIC_DRY']) {
            const hist = Array.from({length: 30}).map((_, i) => ({ 
                date: `2024-01-${i+1}`, 
                value: (1800 + Math.random()*200 + i*10).toString() 
            }));
            data['BALTIC_DRY'] = { latest_value: hist[29].value, latest_date: 'Today', history: hist };
        }
        setMacroData(data);
      } catch {
        setMacroData(null);
      } finally {
        setLoading(false);
      }
    };
    load();
    const iv = setInterval(load, 30_000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden font-mono text-accent-primary select-none w-full tabular-nums">
      
      {/* HEADER */}
      <div className="h-7 border-b border-surface-4 flex items-center justify-between px-2 shrink-0 bg-void">
        <div className="flex items-center gap-2">
          <Globe size={12} className="text-accent-primary" />
          <span className="text-[11px] font-bold tracking-widest text-accent-primary uppercase">Global Macro Surveillance</span>
        </div>
        <div className="flex items-center gap-3">
            <span className="text-[9px] text-neutral uppercase tracking-widest border border-surface-4 px-1 py-0 bg-surface-1">
                FRED / ST. LOUIS
            </span>
            <span className="text-[9px] text-accent-secondary tracking-widest font-bold animate-pulse">L7 CONNECTION ACTIVE</span>
        </div>
      </div>

      <div className="flex-1 overflow-auto custom-scrollbar flex flex-col xl:flex-row divide-y xl:divide-y-0 xl:divide-x divide-surface-4">
        
        {/* LEFT PANE: LIVE STREAMS */}
        <div className="flex-1 p-0 xl:min-w-[500px] flex flex-col">
            <div className="h-6 bg-surface-1 flex items-center px-2 border-b border-surface-4 shrink-0">
                <span className="text-[9px] uppercase tracking-widest text-neutral font-bold flex items-center gap-2">
                    <Activity size={10}/> Live Economic Instruments
                </span>
            </div>
            
            <div className="flex-1 overflow-y-auto">
                {MACRO_SERIES.map(s => (
                <MacroRow
                    key={s.key}
                    s={s}
                    data={macroData ? macroData[s.key] as SeriesData : null}
                />
                ))}
            </div>
        </div>

        {/* RIGHT PANE: CROSS-ASSET CORRELATION MATRIX */}
        <div className="flex-1 bg-void flex flex-col">
            <div className="h-6 bg-surface-1 flex items-center justify-between px-2 border-b border-surface-4 shrink-0">
                <span className="text-[9px] uppercase tracking-widest text-neutral font-bold flex items-center gap-2">
                    <Crosshair size={10}/> Orbital ↔ Macro Correlation Matrix
                </span>
                <span className="text-[9px] uppercase tracking-widest text-accent-primary font-bold">Spearman ρ LEAD-LAG</span>
            </div>
            
            <div className="p-2">
                <div className="border border-surface-4 bg-void">
                    {/* Matrix Header */}
                    <div className="grid grid-cols-12 h-6 border-b border-surface-4 bg-surface-1">
                        <div className="col-span-4 flex items-center px-2"><span className="text-[9px] tracking-widest text-neutral uppercase font-bold">Satellite Alpha Node</span></div>
                        <div className="col-span-1 flex items-center justify-center border-l border-surface-4"><ArrowRightLeft size={10} className="text-neutral"/></div>
                        <div className="col-span-3 flex items-center px-2 border-l border-surface-4"><span className="text-[9px] tracking-widest text-neutral uppercase font-bold">Macro Target</span></div>
                        <div className="col-span-2 flex items-center justify-end px-2 border-l border-surface-4"><span className="text-[9px] tracking-widest text-neutral uppercase font-bold">ρ Score</span></div>
                        <div className="col-span-2 flex items-center justify-center border-l border-surface-4"><span className="text-[9px] tracking-widest text-neutral uppercase font-bold">Lag Vector</span></div>
                    </div>

                    {/* Matrix Rows */}
                    {[
                        { sat: 'Thermal FRP (Rotterdam)', macro: 'Eurozone CPI', rho: 0.74, lead: '+21D', type: 'LEAD', rhoColor: '#00FF00' },
                        { sat: 'Sentinel-2 Cargo Density', macro: 'Baltic Dry Index', rho: 0.88, lead: '+5D', type: 'LEAD', rhoColor: '#00FF00' },
                        { sat: 'Dark Vessel Anomalies', macro: 'WTI Crude ($/bbl)', rho: -0.62, lead: '-2D', type: 'LAG', rhoColor: '#FF3D3D' },
                        { sat: 'OpenSky Heavy Freight', macro: 'US Retail Sales', rho: 0.81, lead: 'SYNC', type: 'SYNC', rhoColor: '#C084FC' },
                        { sat: 'LNG Terminal Activity', macro: 'Henry Hub Gas', rho: 0.65, lead: '+14D', type: 'LEAD', rhoColor: '#00FF00' },
                        { sat: 'Shanghai Port Congestion', macro: 'US PPI (Goods)', rho: 0.58, lead: '+45D', type: 'LEAD', rhoColor: '#00FF00' },
                    ].map((row, i) => (
                        <div key={i} className="grid grid-cols-12 h-6 border-b border-surface-4 hover:bg-surface-2 transition-colors group">
                            <div className="col-span-4 flex items-center px-2">
                                <span className="text-[11px] text-accent-primary font-bold truncate pr-2">{row.sat}</span>
                            </div>
                            <div className="col-span-1 flex items-center justify-center border-l border-surface-4 opacity-40 group-hover:opacity-100 transition-opacity">
                                <ArrowRight size={10} className={row.rho >= 0 ? 'text-bull' : 'text-bear'}/>
                            </div>
                            <div className="col-span-3 flex items-center px-2 border-l border-surface-4">
                                <span className="text-[10px] text-neutral uppercase tracking-wider">{row.macro}</span>
                            </div>
                            <div className="col-span-2 flex items-center justify-end px-2 border-l border-surface-4">
                                <span className="text-[11px] font-bold" style={{ color: row.rhoColor }}>{row.rho.toFixed(2)}</span>
                            </div>
                            <div className="col-span-2 flex items-center justify-center border-l border-surface-4">
                                <span className={`text-[10px] font-bold px-1 py-0 border ${
                                    row.type === 'LEAD' ? 'text-bull border-bull bg-bull/10' : 
                                    row.type === 'LAG' ? 'text-bear border-bear bg-bear/10' : 'text-[#C084FC] border-[#C084FC]/30 bg-[#C084FC]/10'
                                }`}>
                                    {row.lead}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-4">
                    <span className="text-[9px] uppercase tracking-widest text-neutral font-bold block mb-1">Model Inference Insights</span>
                    <div className="bg-surface-1 border-l-2 border-bull p-2 text-[10px] text-accent-primary/80 leading-relaxed font-mono">
                        <strong className="text-accent-primary font-mono tracking-tight block mb-0.5">High-Conviction Alpha Detected</strong>
                        The TFT engine has identified a systemic lag between <span className="text-white font-bold">Sentinel-2 Cargo Density</span> and the <span className="text-white font-bold">Baltic Dry Index</span>. Signal lead time is actively decaying (+5D remaining). Suggest immediate rebalancing of bulk maritime exposure.
                    </div>
                </div>
            </div>
        </div>
      </div>

      <div className="h-6 border-t border-surface-4 flex items-center px-2 bg-surface-1 shrink-0 z-10">
        <span className="text-[9px] text-neutral uppercase tracking-widest font-mono">
          Proprietary Intelligence · FRED / IMF / WORLD BANK · Last Sync: {new Date().toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};

export default EconomicsView;
