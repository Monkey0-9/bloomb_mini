import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu } from 'lucide-react';

const DarkPoolView = () => {
  const [pools, setPools] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const resp = await fetch('/api/darkpool');
        const json = await resp.json();
        setPools(json.blocks);
        setSummary(json);
      } catch (err) {
        console.error("Failed to fetch dark pool data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && pools.length === 0) {
    return (
      <div className="flex-1 bg-void flex items-center justify-center">
        <div className="type-h1 text-[#C084FC] animate-pulse">SONAR DEPTH SEARCH: ACTIVE...</div>
      </div>
    );
  }

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
                <div className="type-h1 text-2xl text-[#C084FC]">{summary?.total_off_exchange_usd || '...'}</div>
             </div>
             <div className="bg-surface-1 border border-border-2 p-4">
                <div className="type-data-xs text-text-4 uppercase mb-2">Institutional Accumulation Bias</div>
                <div className="type-h1 text-2xl text-bull">{summary?.bias || '...'}</div>
             </div>
             <div className="bg-surface-1 border border-border-2 p-4 relative overflow-hidden">
                <div className="absolute inset-0 bg-accent-primary/5"></div>
                <div className="type-data-xs text-text-4 uppercase mb-2">AI Signal Confidence</div>
                <div className="type-h1 text-2xl text-accent-primary">{summary?.confidence || '0'}%</div>
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
