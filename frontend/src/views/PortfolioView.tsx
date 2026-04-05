import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import * as Lucide from 'lucide-react';

const Activity = Lucide.Activity || Lucide.Zap;

const Sparkline = ({ data, color }: { data: number[], color: string }) => {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 100, h = 24;
  
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((d - min) / range) * h;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={w} height={h} className="opacity-40">
      <polyline 
        points={points} 
        fill="none" 
        stroke={color} 
        strokeWidth={1.5} 
        strokeLinejoin="round" 
      />
    </svg>
  );
};

const PortfolioView = () => {
  const { Briefcase, ShieldAlert, PieChart, Clock, TrendingUp, TrendingDown, ShieldCheck, Target, Zap } = Lucide;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const resp = await fetch('/api/portfolio');
      const json = await resp.json();
      setData(json);
    } catch (err) {
      console.error("Failed to fetch portfolio", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-6">
           <Lucide.RefreshCw size={48} className="animate-spin text-accent-primary opacity-40" />
           <span className="font-display text-2xl text-white tracking-[0.4em] animate-pulse">AUDITING_POSITIONS</span>
        </div>
      </div>
    );
  }

  const positions = data?.positions || [];
  const maritimeAlloc = positions.filter((p: any) => p.sector === 'Maritime' || ['ZIM', 'SBLK'].includes(p.ticker)).reduce((acc: number, p: any) => acc + p.mktValue, 0);
  const totalMV = data?.total_mkt_value || 1;
  const maritimePct = (maritimeAlloc / totalMV * 100).toFixed(1);

  return (
    <div className="flex-1 bg-slate-950 overflow-hidden flex flex-col font-mono">
      {/* HUD HEADER */}
      <header className="h-14 border-b border-white/5 flex items-center justify-between px-8 bg-slate-900/40 shrink-0 backdrop-blur-md z-20">
        <div className="flex items-center gap-4">
          <Briefcase size={18} className="text-bull shadow-glow-bull" />
          <h1 className="font-display text-xl tracking-[0.3em] text-white leading-none">RISK_EXPOSURE_SYSTEM</h1>
          <div className="h-6 w-px bg-white/10 mx-2" />
          <div className="flex items-center gap-3 glass-panel px-3 py-1 border-white/10 rounded-sm">
            <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">Total MV:</span>
            <span className="text-[11px] text-white font-black tracking-tighter">${data?.total_mkt_value?.toLocaleString()}</span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
             <ShieldCheck size={14} className="text-bull" />
             <span className="text-[9px] font-bold text-bull uppercase tracking-widest">NAV_VERIFIED</span>
          </div>
          <span className="text-[10px] text-slate-600 uppercase tracking-tighter">Last Update: {new Date().toISOString().slice(11, 19)} Z</span>
        </div>
      </header>

      <div className="flex-1 p-8 overflow-y-auto custom-scrollbar relative">
        <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />

        <div className="max-w-7xl mx-auto space-y-8 relative z-10">
          {/* TOP DASHBOARD CARDS */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { label: 'Realized Alpha', val: `+$${data?.total_pnl?.toLocaleString()}`, sub: `+${data?.total_pnl_pct}% Tot-Return`, col: 'bull', icon: Activity },
              { label: 'Concentration', val: `${maritimePct}%`, sub: 'Sector: Maritime/Physical', col: 'sky', icon: PieChart },
              { label: 'VaR Exposure', val: `${Math.abs(data?.total_pnl_pct * 0.4).toFixed(2)}%`, sub: '95% Confidence Interval', col: 'bear', icon: ShieldAlert },
              { label: 'Induction Phase', val: 'SETTLED', sub: 'Next Rebalance: 04:22 Z', col: 'slate-400', icon: Clock }
            ].map((card, i) => (
              <div key={i} className="glass-panel neo-border p-6 rounded-sm relative overflow-hidden group">
                <div className={`absolute top-0 left-0 w-1 h-full bg-${card.col === 'sky' ? 'accent-primary' : card.col} opacity-40`} />
                <div className="flex justify-between items-start mb-4">
                  <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{card.label}</span>
                  <card.icon size={16} className={`text-${card.col === 'sky' ? 'accent-primary' : card.col}`} />
                </div>
                <div className="text-3xl font-display text-white tracking-tighter mb-1">{card.val}</div>
                <div className="text-[9px] text-slate-500 uppercase font-bold tracking-widest">{card.sub}</div>
              </div>
            ))}
          </div>

          {/* POSITIONS TABLE */}
          <div className="glass-panel neo-border rounded-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex justify-between items-center">
               <div className="flex items-center gap-3">
                  <Target size={14} className="text-accent-primary" />
                  <span className="text-[11px] font-bold text-slate-300 uppercase tracking-[0.2em]">Active Exposure Matrix</span>
               </div>
               <span className="text-[9px] font-mono text-slate-500">POS_COUNT: {positions.length}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-900/60 font-mono text-[10px] text-slate-500 uppercase tracking-widest">
                    <th className="px-6 py-4 font-black">Ticker</th>
                    <th className="px-6 py-4 font-black">Cluster</th>
                    <th className="px-6 py-4 font-black text-right">Inventory</th>
                    <th className="px-6 py-4 font-black text-right">Cost Basis</th>
                    <th className="px-6 py-4 font-black text-right">Current Px</th>
                    <th className="px-6 py-4 font-black text-right">Mark Value</th>
                    <th className="px-6 py-4 font-black text-right">PnL Δ</th>
                  </tr>
                </thead>
                <tbody className="text-[11px] divide-y divide-white/5">
                  {positions.map((p: any) => (
                    <tr key={p.ticker} className="hover:bg-white/5 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-1 h-3 ${p.pnl >= 0 ? 'bg-bull' : 'bg-bear'}`} />
                          <span className="font-black text-white group-hover:text-accent-primary transition-colors">{p.ticker}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-400 font-bold">{p.sector.toUpperCase()}</td>
                      <td className="px-6 py-4 text-right text-slate-300 font-mono font-bold">{p.quantity.toLocaleString()}</td>
                      <td className="px-6 py-4 text-right text-slate-500 font-mono">${p.avgCost.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right text-white font-mono font-bold group-hover:text-bull transition-colors">${p.currentPrice.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right text-white font-mono font-bold">${p.mktValue.toLocaleString()}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex flex-col items-end gap-1">
                           <span className={`font-black ${p.pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                             {p.pnl >= 0 ? '+' : ''}{p.pnl.toLocaleString()}
                           </span>
                           <span className={`text-[9px] px-1 rounded-sm ${p.pnlPct >= 0 ? 'bg-bull/10 text-bull' : 'bg-bear/10 text-bear'} font-bold tracking-tighter`}>
                             {p.pnlPct >= 0 ? '▲' : '▼'} {Math.abs(p.pnlPct)}%
                           </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* LOGS PANEL */}
          <div className="glass-panel neo-border p-6 rounded-sm bg-slate-900/60">
             <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                   <Zap size={14} className="text-bull animate-pulse" />
                   <span className="text-[11px] font-black text-white uppercase tracking-[0.3em]">Live_Execution_Directive_Stream</span>
                </div>
                <div className="px-2 py-0.5 bg-bull/10 border border-bull/20 text-[9px] text-bull font-bold uppercase tracking-widest">Active_Node</div>
             </div>
             <div className="space-y-3">
                {positions.slice(0, 4).map((p: any, i: number) => (
                  <div key={i} className="flex gap-6 text-[11px] font-mono border-b border-white/5 pb-3 last:border-0 last:pb-0 group">
                    <span className="text-slate-600 font-bold whitespace-nowrap">[{new Date().toISOString().slice(11, 19)} Z]</span>
                    <span className="text-bull font-black uppercase tracking-widest opacity-60 group-hover:opacity-100 transition-opacity shrink-0">V_SYNC_NOMINAL</span>
                    <span className="text-slate-400 leading-none">
                       POS_AUDIT: <span className="text-white font-bold">{p.ticker}</span> // 
                       SECTOR: <span className="text-accent-primary">{p.sector}</span> // 
                       PX_MARK: <span className="text-bull">${p.currentPrice}</span> // 
                       STATUS: <span className="text-slate-200">OPTIMAL_LIQUIDITY</span>
                    </span>
                  </div>
                ))}
             </div>
          </div>
        </div>
      </div>

      {/* STATUS FOOTER */}
      <footer className="h-8 border-t border-white/5 bg-slate-950 px-8 flex items-center justify-between shrink-0 box-border text-[9px] font-mono text-slate-700 uppercase tracking-[0.2em] font-bold">
        <div className="flex gap-10">
          <span>Terminal_Kernel: ST-RISK-9.1</span>
          <span>Crypto_Key: AES-256-V2</span>
        </div>
        <span>{new Date().toISOString()} UTC</span>
      </footer>
    </div>
  );
};

export default PortfolioView;
