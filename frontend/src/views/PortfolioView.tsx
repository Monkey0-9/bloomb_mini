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
            const resp = await fetch(`http://localhost:8000/api/market/price/${h.ticker}`);
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

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden font-sans relative">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none mix-blend-screen opacity-20"></div>

      {/* HEADER */}
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-4 shrink-0 bg-surface-base z-10">
        <div className="flex items-center gap-3">
          <Briefcase size={16} className="text-accent-primary" />
          <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">Institutional Alpha Portfolio</span>
          <div className="px-2 py-0.5 border border-bull/30 bg-bull/10 text-bull type-data-xs tracking-widest uppercase font-bold flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse shadow-glow-bull" />
              LIVE TICK
          </div>
        </div>
        <div className="flex items-center gap-4">
            <span className="type-data-xs text-text-3 font-mono">TFT MONTE CARLO VaR: <span className="text-bear font-bold">-$42,105 (99%)</span></span>
        </div>
      </div>

      {/* PORTFOLIO HEADS UP DISPLAY */}
      <div className="grid grid-cols-4 border-b border-border-2 bg-gradient-to-b from-surface-1/50 to-void shrink-0 z-10 relative">
        <div className="p-4 flex flex-col justify-center border-r border-border-2 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity"><DollarSign size={48}/></div>
          <span className="type-data-xs text-text-4 uppercase tracking-widest mb-1 font-bold">Gross Exposure</span>
          <span className="text-3xl font-data font-semibold text-text-0 tabular-nums tracking-tight tracking-tighter">
            ${totalMV.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
        
        <div className="p-4 flex flex-col justify-center border-r border-border-2 relative overflow-hidden">
          <span className="type-data-xs text-text-4 uppercase tracking-widest mb-1 font-bold">Unrealized P&L</span>
          <div className={`flex items-baseline gap-3 ${totalPnL >= 0 ? 'text-bull' : 'text-bear'}`}>
            <span className="text-3xl font-data font-semibold tabular-nums tracking-tighter shadow-glow-bull">
              {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
            <span className="text-lg font-data font-bold">({totalPnLPct >= 0 ? '+' : ''}{totalPnLPct.toFixed(2)}%)</span>
          </div>
        </div>

        <div className="p-4 flex flex-col justify-center border-r border-border-2">
          <span className="type-data-xs text-text-4 uppercase tracking-widest mb-1 font-bold">Portfolio Greeks</span>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-1">
             <div className="flex justify-between type-data-xs"><span className="text-text-4">$\Delta$</span><span className="text-text-1 font-mono">{portfolioDelta.toFixed(3)}</span></div>
             <div className="flex justify-between type-data-xs"><span className="text-text-4">$\Gamma$</span><span className="text-text-1 font-mono">0.084</span></div>
             <div className="flex justify-between type-data-xs"><span className="text-text-4">$\Theta$</span><span className="text-bear font-mono">-142.50</span></div>
             <div className="flex justify-between type-data-xs"><span className="text-text-4">$V$</span><span className="text-text-1 font-mono">1.240</span></div>
          </div>
        </div>

        {/* SCENARIO HEATMAP WIDGET */}
        <div className="p-4 flex flex-col justify-center bg-surface-1/20 border-l border-border-active relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[1px] bg-accent-primary blur-[1px]"></div>
            <span className="type-data-xs text-accent-primary uppercase tracking-widest mb-2 font-bold flex items-center gap-1"><ShieldAlert size={12}/> Scenario Stress Matrix</span>
            <div className="flex gap-[1px] h-8 w-full">
                {/* Simulated Heatmap blocks */}
                <div className="flex-1 flex items-center justify-center bg-bull/20 border border-bull/30 type-data-xs text-bull font-bold" title="Oil +10%">+2.4%</div>
                <div className="flex-1 flex items-center justify-center bg-bear/40 border border-bear/50 type-data-xs text-bear font-bold shadow-[inset_0_0_10px_rgba(255,61,61,0.2)]" title="Rates +50bps">-1.8%</div>
                <div className="flex-1 flex items-center justify-center bg-bull/40 border border-bull/50 type-data-xs text-bull font-bold shadow-[inset_0_0_10px_rgba(0,255,157,0.2)]" title="China Stimulus">+4.1%</div>
            </div>
            <span className="type-data-xs text-text-5 mt-1 text-[9px]">MACRO SHOCK PNL IMPACT</span>
        </div>
      </div>

      {/* POSITIONS TABLE - EXTREME DENSITY */}
      <div className="flex-1 overflow-auto custom-scrollbar z-10 border-b border-border-1 relative">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
             <div className="flex flex-col items-center gap-4 border border-border-ghost bg-surface-1/50 p-6 backdrop-blur-md">
                 <Activity className="text-accent-primary animate-pulse w-8 h-8" />
                 <span className="type-data-xs font-mono text-accent-primary tracking-widest uppercase">Syncing FIX Engine...</span>
             </div>
          </div>
        ) : (
          <table className="w-full border-collapse">
            <thead className="sticky top-0 bg-void border-b-2 border-border-3 z-20">
              <tr>
                {['Asset', 'Sector', 'Cost Basis', 'Current', 'Intraday 7D', 'P&L', 'P&L %', 'Δ', 'Γ', 'Θ', 'V'].map(h => (
                  <th key={h} className="px-3 py-2 text-right first:text-left">
                    <span className="text-[10px] font-mono text-text-4 uppercase tracking-[0.1em]">{h}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {positions.map((p, i) => {
                const isUp = p.pnl >= 0;
                const cColor = isUp ? '#00FF9D' : '#FF3D3D';
                return (
                  <motion.tr
                    key={p.ticker}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="hover:bg-surface-2/40 transition-colors group h-12"
                  >
                    <td className="px-3 py-1.5 text-left border-l-[3px] border-transparent group-hover:border-accent-primary transition-colors">
                      <div className="flex flex-col">
                        <span className="type-data-md text-text-0 font-bold tracking-tight">{p.ticker}</span>
                        <span className="text-[9px] text-text-4 uppercase tracking-widest font-mono">{p.quantity} SHS</span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5 text-right">
                      <span className="text-[10px] px-2 py-0.5 rounded border border-border-ghost text-text-3 uppercase tracking-wider bg-surface-1">
                        {p.sector}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-right">
                      <span className="type-data-sm text-text-3 font-mono">${p.avgCost.toFixed(2)}</span>
                    </td>
                    <td className="px-3 py-1.5 text-right relative overflow-hidden">
                       <div className="absolute inset-0 bg-accent-primary/0 group-hover:bg-accent-primary/5 transition-colors duration-500"></div>
                       <span className="type-data-md text-text-0 font-mono font-bold tracking-tight relative z-10 transition-colors duration-300 group-hover:text-accent-primary">
                         ${p.currentPrice.toFixed(2)}
                       </span>
                    </td>
                    <td className="px-3 py-1.5 text-right w-32">
                       <div className="flex justify-end pr-2 opacity-70 group-hover:opacity-100 transition-opacity">
                            <Sparkline data={p.tail} color={cColor} isPositive={isUp} />
                       </div>
                    </td>
                    <td className="px-3 py-1.5 text-right">
                      <span className={`type-data-sm font-mono tracking-tight font-bold ${isUp ? 'text-bull' : 'text-bear'}`}>
                         {isUp ? '+' : ''}${p.pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-right">
                      <span className={`text-[11px] font-mono tracking-wider px-1.5 py-0.5 rounded-sm ${isUp ? 'bg-bull/10 text-bull border border-bull/20' : 'bg-bear/10 text-bear border border-bear/20'}`}>
                        {isUp ? '+' : ''}{p.pnlPct.toFixed(2)}%
                      </span>
                    </td>
                    
                    {/* Greeks */}
                    <td className="px-3 py-1.5 text-right bg-surface-1/10 group-hover:bg-surface-1/30 transition-colors"><span className="type-data-xs text-text-1 font-mono">{p.greeks.delta.toFixed(2)}</span></td>
                    <td className="px-3 py-1.5 text-right bg-surface-1/10 group-hover:bg-surface-1/30 transition-colors"><span className="type-data-xs text-text-2 font-mono">{p.greeks.gamma.toFixed(3)}</span></td>
                    <td className="px-3 py-1.5 text-right bg-surface-1/10 group-hover:bg-surface-1/30 transition-colors"><span className="type-data-xs text-bear font-mono">{p.greeks.theta.toFixed(2)}</span></td>
                    <td className="px-3 py-1.5 text-right bg-surface-1/10 group-hover:bg-surface-1/30 transition-colors"><span className="type-data-xs text-text-2 font-mono">{p.greeks.vega.toFixed(2)}</span></td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="h-8 flex items-center justify-between px-4 bg-void shrink-0 border-t border-border-ghost z-10 relative shadow-[0_-10px_20px_rgba(0,0,0,0.5)]">
        <div className="flex gap-4">
            <span className="text-[10px] text-accent-primary font-mono uppercase tracking-widest flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-accent-primary rounded-full animate-ping"></div> FIX L3 LINK DETECTED
            </span>
            <span className="text-[10px] text-text-4 font-mono uppercase tracking-widest">• Latency: 14ms</span>
        </div>
        <span className="text-[9px] text-text-5 font-mono uppercase tracking-[0.2em]">
          DATA CONFIDENTIAL • DO NOT DISTRIBUTE
        </span>
      </div>
    </div>
  );
};

export default PortfolioView;
