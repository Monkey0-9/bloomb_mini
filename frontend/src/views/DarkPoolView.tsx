import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu } from 'lucide-react';

const mockDarkPools = [
  { symbol: 'TSLA', volume: '14.2M', priceDiff: '+1.2%', time: '14:23:01', venue: 'SIGMA-X', intent: 'ACCUMULATION' },
  { symbol: 'AAPL', volume: '8.5M', priceDiff: '-0.4%', time: '14:22:45', venue: 'CROSSFINDER', intent: 'DISTRIBUTION' },
  { symbol: 'NVDA', volume: '22.1M', priceDiff: '+3.1%', time: '14:20:12', venue: 'LIQUIDNET', intent: 'ACCUMULATION' },
  { symbol: 'AMD', volume: '5.4M', priceDiff: '-1.1%', time: '14:18:55', venue: 'IEX', intent: 'NEUTRAL' },
  { symbol: 'MSFT', volume: '11.0M', priceDiff: '+0.8%', time: '14:15:33', venue: 'LX', intent: 'ACCUMULATION' },
  { symbol: 'PLTR', volume: '19.8M', priceDiff: '+5.4%', time: '14:10:21', venue: 'LEVEL_ATS', intent: 'STRONG_ACCUMULATION' },
];

const DarkPoolView = () => {
  const [pools, setPools] = useState(mockDarkPools);

  // Simulate real-time blocks
  useEffect(() => {
    const interval = setInterval(() => {
      setPools(prev => {
        const newPool = { ...prev[Math.floor(Math.random() * prev.length)] };
        newPool.time = new Date().toLocaleTimeString('en-US', { hour12: false });
        newPool.volume = (Math.random() * 10 + 1).toFixed(1) + 'M';
        return [newPool, ...prev.slice(0, 15)];
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex-1 bg-void overflow-hidden flex flex-col font-sans">
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-4 shrink-0 bg-surface-base">
        <div className="flex items-center gap-3">
          <Activity size={16} className="text-[#C084FC]" />
          <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">Dark Pool Sonar</span>
          <div className="w-1.5 h-1.5 rounded-full bg-[#C084FC] animate-pulse ml-2" />
        </div>
        <div className="flex gap-4">
          <span className="type-data-xs text-text-5 uppercase tracking-widest font-mono">Status: ACTIVE</span>
        </div>
      </div>

      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="grid grid-cols-3 gap-6">
             <div className="bg-surface-1 border border-border-2 p-4">
                <div className="type-data-xs text-text-4 uppercase mb-2">Total Off-Exchange Volume</div>
                <div className="type-h1 text-2xl text-[#C084FC]">$14.2B</div>
             </div>
             <div className="bg-surface-1 border border-border-2 p-4">
                <div className="type-data-xs text-text-4 uppercase mb-2">Institutional Accumulation Bias</div>
                <div className="type-h1 text-2xl text-bull">+68.4%</div>
             </div>
             <div className="bg-surface-1 border border-border-2 p-4 relative overflow-hidden">
                <div className="absolute inset-0 bg-accent-primary/5"></div>
                <div className="type-data-xs text-text-4 uppercase mb-2">AI Signal Confidence</div>
                <div className="type-h1 text-2xl text-accent-primary">94.2%</div>
             </div>
          </div>

          <div className="bg-surface-1 border border-border-2 flex flex-col">
             <div className="grid grid-cols-6 border-b border-border-ghost p-3 bg-surface-base type-data-xs text-text-5 uppercase font-bold">
                 <span>Time</span>
                 <span>Symbol</span>
                 <span>Venue</span>
                 <span>Block Size</span>
                 <span>Price Shift</span>
                 <span>AI Intent</span>
             </div>
             <div className="flex flex-col">
                {pools.map((p, i) => (
                    <div key={i} className={`grid grid-cols-6 p-3 border-b border-border-ghost hover:bg-surface-2 transition-colors type-data-sm font-mono ${i === 0 ? 'bg-[#C084FC]/10' : ''}`}>
                        <span className="text-text-4">{p.time}</span>
                        <span className="font-bold text-text-1">{p.symbol}</span>
                        <span className="text-[#C084FC]">{p.venue}</span>
                        <span className="text-text-2">{p.volume}</span>
                        <span className={p.priceDiff.includes('+') ? 'text-bull' : 'text-bear'}>{p.priceDiff}</span>
                        <span className="flex items-center gap-2">
                           {p.intent.includes('ACCUMULATION') ? <Cpu size={12} className="text-bull"/> : <ShieldAlert size={12} className={p.intent === 'NEUTRAL' ? 'text-text-5' : 'text-bear'}/>}
                           <span className={p.intent.includes('ACCUMULATION') ? 'text-bull font-bold' : p.intent === 'NEUTRAL' ? 'text-text-4' : 'text-bear font-bold'}>
                               {p.intent.replace('_', ' ')}
                           </span>
                        </span>
                    </div>
                ))}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default DarkPoolView;
