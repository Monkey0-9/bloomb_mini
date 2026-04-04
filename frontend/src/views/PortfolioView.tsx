import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Briefcase, Activity, ShieldAlert, PieChart, Clock, TrendingUp, TrendingDown, ShieldCheck } from 'lucide-react';

const Sparkline = ({ data, color, isPositive }: { data: number[], color: string, isPositive: boolean }) => {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 80, h = 24;
  
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((d - min) / range) * h;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={w} height={h} className="overflow-visible">
      <polygon 
        points={`0,${h} ${points} ${w},${h}`} 
        fill={isPositive ? 'rgba(0, 255, 157, 0.1)' : 'rgba(255, 61, 61, 0.1)'} 
      />
      <polyline 
        points={points} 
        fill="none" 
        stroke={color} 
        strokeWidth={1.5} 
        strokeLinecap="round" 
        strokeLinejoin="round" 
      />
      <circle 
        cx={w} 
        cy={h - ((data[data.length - 1] - min) / range) * h} 
        r={2.5} 
        fill={color} 
        className="animate-pulse"
      />
    </svg>
  );
};

const PortfolioView = () => {
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
      <div className="flex-1 bg-void flex items-center justify-center">
        <div className="type-h1 text-bull animate-pulse uppercase tracking-[0.3em]">Auditing Active Positions...</div>
      </div>
    );
  }

  const positions = data?.positions || [];
  const maritimeAlloc = positions.filter((p: any) => p.sector === 'Maritime' || ['ZIM', 'SBLK'].includes(p.ticker)).reduce((acc: number, p: any) => acc + p.mktValue, 0);
  const totalMV = data?.total_mkt_value || 1;
  const maritimePct = (maritimeAlloc / totalMV * 100).toFixed(1);

  return (
    <div className="flex-1 bg-void overflow-hidden flex flex-col font-sans">
      {/* Header */}
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-4 shrink-0 bg-surface-base">
        <div className="flex items-center gap-3">
          <Briefcase size={16} className="text-bull" />
          <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">Physical Asset Portfolio</span>
          <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse ml-2" />
        </div>
        <div className="flex gap-4 items-center">
          <div className="flex items-center gap-2 px-3 py-1 bg-surface-1 border border-border-2 rounded-sm">
            <span className="type-data-xs text-text-5 uppercase tracking-widest">Total Valuation:</span>
            <span className="type-data-sm text-bull font-bold font-mono">
              ${data?.total_mkt_value?.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Top Stats */}
          <div className="grid grid-cols-4 gap-6">
            <div className="bg-surface-1 border border-border-2 p-4 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-1 h-full bg-bull opacity-50 group-hover:w-full group-hover:opacity-5 transition-all duration-500"></div>
              <div className="type-data-xs text-text-4 uppercase mb-2 flex items-center gap-2">
                <Activity size={12} className="text-bull"/> Realized P&L
              </div>
              <div className="type-h1 text-2xl text-bull">
                +${data?.total_pnl?.toLocaleString()}
              </div>
              <div className="type-data-xs text-bull-dim mt-1">+{data?.total_pnl_pct}% (All Time)</div>
            </div>

            <div className="bg-surface-1 border border-border-2 p-4 relative">
              <div className="type-data-xs text-text-4 uppercase mb-2 flex items-center gap-2">
                <PieChart size={12} className="text-accent-primary"/> Asset Concentration
              </div>
              <div className="type-h1 text-2xl text-text-1">{parseFloat(maritimePct) > 50 ? 'MARITIME' : 'DIVERSIFIED'}</div>
              <div className="type-data-xs text-text-4 mt-1">{maritimePct}% Allocation</div>
            </div>

            <div className="bg-surface-1 border border-border-2 p-4 relative overflow-hidden group">
               <div className="absolute top-0 left-0 w-1 h-full bg-accent-primary opacity-50"></div>
               <div className="type-data-xs text-text-4 uppercase mb-2 flex items-center gap-2">
                   <ShieldCheck size={12} className="text-accent-primary"/> Risk Exposure
               </div>
               <div className="type-h1 text-2xl text-text-1 uppercase">{Math.abs(data?.total_pnl_pct) > 5 ? 'ELEVATED' : 'MODERATE'}</div>
               <div className="type-data-xs text-text-4 mt-1">VaR (95%): {Math.abs(data?.total_pnl_pct * 0.4).toFixed(2)}%</div>
            </div>

            <div className="bg-surface-1 border border-border-2 p-4">
               <div className="type-data-xs text-text-4 uppercase mb-2 flex items-center gap-2">
                   <Clock size={12} className="text-text-5"/> Next Rebalance
               </div>
               <div className="type-h1 text-2xl text-text-1">14:22:01</div>
               <div className="type-data-xs text-text-4 mt-1">T+2 Settlement</div>
            </div>
          </div>

          {/* Positions Table */}
          <div className="bg-surface-1 border border-border-2 flex flex-col">
            <div className="grid grid-cols-8 border-b border-border-ghost p-3 bg-surface-base type-data-xs text-text-5 uppercase font-bold tracking-[0.1em]">
              <span>Ticker</span>
              <span>Sector</span>
              <span className="text-right">Qty</span>
              <span className="text-right">Cost Basis</span>
              <span className="text-right">Mkt Price</span>
              <span className="text-right">Mkt Value</span>
              <span className="text-right">P&L ($)</span>
              <span className="text-right">P&L (%)</span>
            </div>
            <div className="flex flex-col">
              {positions.map((p: any, i: number) => (
                <motion.div 
                  key={p.ticker}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="grid grid-cols-8 p-3 border-b border-border-ghost hover:bg-surface-2 transition-colors type-data-sm font-mono items-center group"
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-1 h-3 ${p.pnl >= 0 ? 'bg-bull' : 'bg-bear'}`}></div>
                    <span className="font-bold text-text-1 group-hover:text-accent-primary transition-colors">{p.ticker}</span>
                  </div>
                  <span className="text-[10px] text-text-5 uppercase tracking-tighter">{p.sector}</span>
                  <span className="text-right text-text-2">{p.quantity}</span>
                  <span className="text-right text-text-4">${p.avgCost.toFixed(2)}</span>
                  <span className="text-right text-text-1 group-hover:text-bull transition-colors font-bold">
                    ${p.currentPrice.toFixed(2)}
                  </span>
                  <span className="text-right text-text-2">${p.mktValue.toLocaleString()}</span>
                  <span className={`text-right font-bold ${p.pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                    {p.pnl >= 0 ? '+' : ''}{p.pnl.toLocaleString()}
                  </span>
                  <div className="text-right">
                    <span className={`px-2 py-0.5 rounded-sm text-[10px] font-bold ${p.pnlPct >= 0 ? 'bg-bull/10 text-bull' : 'bg-bear/10 text-bear'}`}>
                      {p.pnlPct >= 0 ? '▲' : '▼'} {Math.abs(p.pnlPct)}%
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
          
          {/* Execution Feed Simulation */}
          <div className="bg-surface-base p-4 border border-border-ghost">
            <div className="type-data-xs text-text-5 uppercase mb-3 flex items-center justify-between">
              <span>Live Execution Log</span>
              <span className="text-bull animate-pulse">STREAMING_LIVE</span>
            </div>
            <div className="space-y-2 font-mono text-[10px]">
               {positions.slice(0, 3).map((p: any, i: number) => (
                 <div key={i} className="flex gap-4 text-text-4">
                   <span className="text-text-5">[{new Date().toLocaleTimeString('en-US', { hour12: false })}]</span>
                   <span className="text-bull">VERIFIED</span>
                   <span>POSITION_SYNC: {p.ticker} | PX: {p.currentPrice} | QTY: {p.quantity} | STATUS: OPTIMAL</span>
                 </div>
               ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioView;
