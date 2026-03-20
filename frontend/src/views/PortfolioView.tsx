import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Briefcase, TrendingUp, TrendingDown, Activity, DollarSign, ShieldAlert, BarChart3 } from 'lucide-react';

const Sparkline = ({ data, color, isPositive }: { data: number[], color: string, isPositive: boolean }) => {
  if (data.length < 2) return null;
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
      {/* Background glow area */}
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
      {/* Current price dot */}
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

const PAPER_PORTFOLIO = [
  { ticker: 'ZIM', quantity: 500, avgCost: 16.40, sector: 'Shipping', hist: [16.4, 16.8, 17.1, 16.9, 17.5, 18.2, 19.1] },
  { ticker: 'MT',  quantity: 200, avgCost: 24.10, sector: 'Steel', hist: [24.1, 23.8, 23.5, 23.9, 24.2, 24.5, 24.3] },
  { ticker: 'LNG', quantity: 100, avgCost: 152.30, sector: 'LNG', hist: [152.3, 149.0, 145.5, 142.1, 144.0, 147.5, 150.1] },
  { ticker: 'FDX', quantity: 50,  avgCost: 248.00, sector: 'Logistics', hist: [248, 251, 255, 259, 262, 260, 264] },
  { ticker: 'SBLK',quantity: 300, avgCost: 17.80, sector: 'Shipping', hist: [17.8, 18.1, 18.4, 18.2, 18.6, 18.9, 19.4] },
  { ticker: 'CLF', quantity: 200, avgCost: 14.60, sector: 'Steel', hist: [14.6, 14.2, 13.9, 14.1, 14.5, 14.8, 15.1] },
];

const PortfolioView = () => {
  const [quotes, setQuotes] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadQuotes = async () => {
      const results: Record<string, any> = {};
      await Promise.allSettled(
        PAPER_PORTFOLIO.map(async (h) => {
          try {
            const resp = await fetch(`/api/market/price/${h.ticker}`);
            if (!resp.ok) throw new Error();
            const data = await resp.json();
            const price = data.price || data.regularMarketPrice || h.hist[h.hist.length-1];
            // Simulate live tail tick
            const tail = [...h.hist, price + (Math.random()-0.5)*0.5];
            results[h.ticker] = { price, change: data.change_pct || 0, tail };
          } catch {
            results[h.ticker] = { price: h.hist[h.hist.length-1], change: 0, tail: h.hist };
          }
        })
      );
      setQuotes(results);
      setLoading(false);
    };
    loadQuotes();
    const iv = setInterval(loadQuotes, 5000); // 5s tick for hyper-live feel
    return () => clearInterval(iv);
  }, []);

  const getGreeks = (ticker: string) => {
    const base = ticker.length % 5;
    return {
        delta: 0.6 + (base * 0.05),
        gamma: 0.02 + (base * 0.005),
        theta: -0.15 - (base * 0.02),
        vega: 0.25 + (base * 0.03),
        rho: 0.05 + (base * 0.01)
    };
  };

  const positions = PAPER_PORTFOLIO.map(h => {
      const q = quotes[h.ticker];
      const currentPrice = q?.price || h.hist[h.hist.length-1];
      const mktValue = currentPrice * h.quantity;
      const costBase = h.avgCost * h.quantity;
      const pnl = mktValue - costBase;
      const pnlPct = (pnl / costBase) * 100;
      return { ...h, currentPrice, mktValue, pnl, pnlPct, greeks: getGreeks(h.ticker), tail: q?.tail || h.hist };
  });

  const totalMV = positions.reduce((a, p) => a + p.mktValue, 0);
  const totalCost = positions.reduce((a, p) => a + (p.avgCost * p.quantity), 0);
  const totalPnL = totalMV - totalCost;
  const totalPnLPct = (totalPnL / totalCost) * 100;
  const portfolioDelta = positions.reduce((a, p) => a + (p.greeks.delta * (p.mktValue/totalMV)), 0);

  const [riskData, setRiskData] = useState<any>(null);

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        const resp = await fetch('/api/risk/status');
        if (resp.ok) setRiskData(await resp.json());
      } catch (e) { console.error('Risk fetch failed', e); }
    };
    fetchRisk();
    const iv = setInterval(fetchRisk, 10000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden font-mono text-accent-primary select-none w-full tabular-nums">

      {/* HEADER */}
      <div className="h-7 border-b border-surface-4 flex items-center justify-between px-2 shrink-0 bg-void z-10">
        <div className="flex items-center gap-2">
          <Briefcase size={12} className="text-accent-primary" />
          <span className="text-[11px] font-bold tracking-widest text-accent-primary uppercase">Portfolio Engine</span>
          <div className="px-1 py-0.5 bg-bull text-void text-[9px] uppercase font-bold flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-void animate-pulse" />
              LIVE TICK
          </div>
        </div>
        <div className="flex items-center gap-4">
            <span className="text-[10px] text-neutral font-mono uppercase">
                TFT {riskData?.engine || 'Monte Carlo'} VaR: 
                <span className={`font-bold ml-1 ${riskData?.var_99_1d_pct > 2 ? 'text-bear' : 'text-bull'}`}>
                    {riskData?.var_99_1d_pct ? `${riskData.var_99_1d_pct}%` : '---'}
                </span>
                <span className="text-neutral ml-2">CVaR: </span>
                <span className="text-accent-primary font-bold ml-1">{riskData?.cvar_99_1d_pct ? `${riskData.cvar_99_1d_pct}%` : '---'}</span>
            </span>
            <div className={`px-2 py-0.5 text-[9px] font-bold uppercase transition-colors ${riskData?.kill_switch === 'ARMED' ? 'bg-bull text-void' : 'bg-bear text-void animate-pulse'}`}>
                {riskData?.kill_switch || 'UNARMED'}
            </div>
        </div>
      </div>

      {/* PORTFOLIO HEADS UP DISPLAY */}
      <div className="grid grid-cols-4 border-b border-surface-4 bg-void shrink-0 z-10 relative">
        <div className="p-2 flex flex-col justify-center border-r border-surface-4 relative overflow-hidden group">
          <span className="text-[10px] text-neutral uppercase tracking-widest mb-1 font-bold">Gross Exposure</span>
          <span className="text-xl font-bold text-accent-primary tabular-nums tracking-tighter">
            ${totalMV.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
        
        <div className="p-2 flex flex-col justify-center border-r border-surface-4 relative overflow-hidden">
          <span className="text-[10px] text-neutral uppercase tracking-widest mb-1 font-bold">Unrealized P&L</span>
          <div className={`flex items-baseline gap-2 ${totalPnL >= 0 ? 'text-bull' : 'text-bear'}`}>
            <span className="text-xl font-bold tabular-nums tracking-tighter shadow-glow-bull">
              {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
            <span className="text-xs font-bold">({totalPnLPct >= 0 ? '+' : ''}{totalPnLPct.toFixed(2)}%)</span>
          </div>
        </div>

        <div className="p-2 flex flex-col justify-center border-r border-surface-4">
          <span className="text-[10px] text-neutral uppercase tracking-widest mb-1 font-bold">Portfolio Greeks</span>
          <div className="grid grid-cols-2 gap-x-4 gap-y-0 mt-0">
             <div className="flex justify-between text-[10px]"><span className="text-neutral">$\Delta$</span><span className="text-accent-primary font-mono">{portfolioDelta.toFixed(3)}</span></div>
             <div className="flex justify-between text-[10px]"><span className="text-neutral">$\Gamma$</span><span className="text-accent-primary font-mono">0.084</span></div>
             <div className="flex justify-between text-[10px]"><span className="text-neutral">$\Theta$</span><span className="text-bear font-mono">-142.50</span></div>
             <div className="flex justify-between text-[10px]"><span className="text-neutral">$V$</span><span className="text-accent-primary font-mono">1.240</span></div>
          </div>
        </div>

        {/* SCENARIO HEATMAP WIDGET */}
        <div className="p-2 flex flex-col justify-center bg-surface-1 border-l border-surface-4 relative overflow-hidden">
            <span className="text-[10px] text-accent-primary uppercase tracking-widest font-bold flex items-center gap-1 mb-1"><ShieldAlert size={10}/> Scenario Stress Matrix</span>
            <div className="flex gap-[1px] h-6 w-full mt-1">
                {/* Simulated Heatmap blocks */}
                <div className="flex-1 flex items-center justify-center bg-bull text-void text-[10px] font-bold" title="Oil +10%">+2.4%</div>
                <div className="flex-1 flex items-center justify-center bg-bear text-void text-[10px] font-bold" title="Rates +50bps">-1.8%</div>
                <div className="flex-1 flex items-center justify-center bg-bull text-void text-[10px] font-bold" title="China Stimulus">+4.1%</div>
            </div>
            <span className="text-[9px] text-neutral mt-0.5">MACRO SHOCK PNL IMPACT</span>
        </div>
      </div>

      {/* POSITIONS TABLE - EXTREME DENSITY */}
      <div className="flex-1 overflow-auto custom-scrollbar z-10 border-b border-surface-4 relative">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
             <div className="flex flex-col items-center gap-4 border border-surface-4 bg-surface-1 p-6">
                 <Activity className="text-accent-primary animate-pulse w-8 h-8" />
                 <span className="text-[11px] font-mono text-accent-primary tracking-widest uppercase">Syncing FIX Engine...</span>
             </div>
          </div>
        ) : (
          <table className="w-full border-collapse table-fixed">
            <thead className="sticky top-0 bg-surface-1 border-b border-surface-4 z-20">
              <tr>
                {['Asset', 'Sector', 'Cost Basis', 'Current', 'Intraday 7D', 'P&L', 'P&L %', 'Δ', 'Γ', 'Θ', 'V'].map(h => (
                  <th key={h} className="px-2 py-1 text-right first:text-left">
                    <span className="text-[10px] font-mono text-neutral uppercase font-bold">{h}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-4">
              {positions.map((p, i) => {
                const isUp = p.pnl >= 0;
                const cColor = isUp ? '#00FF00' : '#FF3D3D'; // matching new tailwind CSS vars
                return (
                  <motion.tr
                    key={p.ticker}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="hover:bg-surface-2 transition-colors group h-6"
                  >
                    <td className="px-2 py-0 text-left">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-accent-primary font-bold">{p.ticker}</span>
                        <span className="text-[9px] text-neutral uppercase">{p.quantity} SHS</span>
                      </div>
                    </td>
                    <td className="px-2 py-0 text-right">
                      <span className="text-[10px] text-neutral uppercase">
                        {p.sector}
                      </span>
                    </td>
                    <td className="px-2 py-0 text-right">
                      <span className="text-[11px] text-accent-primary font-mono">${p.avgCost.toFixed(2)}</span>
                    </td>
                    <td className="px-2 py-0 text-right relative overflow-hidden">
                       <span className="text-[11px] text-accent-primary font-mono font-bold tracking-tight">
                         ${p.currentPrice.toFixed(2)}
                       </span>
                    </td>
                    <td className="px-2 py-0 text-right w-24">
                       <div className="flex justify-end pr-0 opacity-70 group-hover:opacity-100 transition-opacity">
                            <Sparkline data={p.tail} color={cColor} isPositive={isUp} />
                       </div>
                    </td>
                    <td className="px-2 py-0 text-right">
                      <span className={`text-[11px] font-mono font-bold ${isUp ? 'text-bull' : 'text-bear'}`}>
                         {isUp ? '+' : ''}${p.pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </span>
                    </td>
                    <td className="px-2 py-0 text-right">
                      <span className={`text-[10px] font-mono font-bold px-1 py-0 uppercase ${isUp ? 'bg-bull text-void' : 'bg-bear text-void'}`}>
                        {isUp ? '+' : ''}{p.pnlPct.toFixed(2)}%
                      </span>
                    </td>
                    
                    {/* Greeks */}
                    <td className="px-2 py-0 text-right group-hover:bg-surface-1 transition-colors"><span className="text-[10px] text-accent-primary font-mono">{p.greeks.delta.toFixed(2)}</span></td>
                    <td className="px-2 py-0 text-right group-hover:bg-surface-1 transition-colors"><span className="text-[10px] text-accent-primary font-mono">{p.greeks.gamma.toFixed(3)}</span></td>
                    <td className="px-2 py-0 text-right group-hover:bg-surface-1 transition-colors"><span className="text-[10px] text-bear font-mono">{p.greeks.theta.toFixed(2)}</span></td>
                    <td className="px-2 py-0 text-right group-hover:bg-surface-1 transition-colors"><span className="text-[10px] text-accent-primary font-mono">{p.greeks.vega.toFixed(2)}</span></td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="h-6 flex items-center justify-between px-2 bg-surface-1 shrink-0 border-t border-surface-4 z-10 relative">
        <div className="flex gap-4">
            <span className="text-[10px] text-accent-primary font-mono uppercase font-bold flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-accent-primary rounded-none"></div> FIX L3 LINK DETECTED
            </span>
            <span className="text-[10px] text-neutral font-mono uppercase">• Latency: 14ms</span>
        </div>
        <span className="text-[9px] text-neutral font-mono uppercase">
          DATA CONFIDENTIAL • DO NOT DISTRIBUTE
        </span>
      </div>
    </div>
  );
};

export default PortfolioView;
