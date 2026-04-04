import React, { useState, useEffect } from 'react';
import { ShieldAlert, Cpu, Eye, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

const InsiderView = () => {
  const [data, setData] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const resp = await fetch('http://localhost:9009/api/insider');
        const json = await resp.json();
        setData(json.trades);
        setSummary(json);
      } catch (err) {
        console.error("Failed to fetch insider trades", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && data.length === 0) {
    return (
      <div className="flex-1 bg-void flex items-center justify-center">
        <div className="type-h1 text-accent-primary animate-pulse">SYNCHRONIZING SEC EDGAR...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-void overflow-hidden flex flex-col font-sans">
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-4 shrink-0 bg-surface-base">
        <div className="flex items-center gap-3">
          <Eye size={16} className="text-[#FFB800]" />
          <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">Insider AI Tracker</span>
          <div className="w-1.5 h-1.5 rounded-full bg-[#FFB800] animate-pulse ml-2" />
        </div>
        <div className="flex gap-4">
          <span className="type-data-xs text-text-5 uppercase tracking-widest font-mono">Form 4 Parser: LIVE</span>
        </div>
      </div>

      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="grid grid-cols-3 gap-6">
             <div className="bg-surface-1 border border-border-2 p-4">
                <div className="type-data-xs text-text-4 uppercase mb-2">Net Insider Flow (30D)</div>
                <div className="type-h1 text-2xl text-bear">
                  {summary ? `$${(summary.net_flow_30d / 1e6).toFixed(1)}M` : '...'}
                </div>
             </div>
             <div className="bg-surface-1 border border-border-2 p-4">
                <div className="type-data-xs text-text-4 uppercase mb-2">Conviction Cluster Density</div>
                <div className="type-h1 text-2xl text-bull">{summary?.conviction_density || 'NORMAL'}</div>
             </div>
             <div className="bg-surface-1 border border-border-2 p-4 relative overflow-hidden">
                <div className="absolute inset-0 bg-[#FFB800]/5"></div>
                <div className="type-data-xs text-text-4 uppercase mb-2">Most Heavily Bought</div>
                <div className="type-h1 text-2xl text-[#FFB800]">{summary?.top_bought || 'N/A'}</div>
             </div>
          </div>

          <div className="bg-surface-1 flex flex-col border border-border-2">
             <div className="grid grid-cols-7 border-b border-border-ghost p-3 bg-surface-base type-data-xs text-text-5 uppercase font-bold tracking-widest">
                 <span>Date</span>
                 <span>Symbol</span>
                 <span className="col-span-2">Executive / Title</span>
                 <span>Transaction</span>
                 <span>Value</span>
                 <span>AI Assessment</span>
             </div>
             <div className="flex flex-col">
                {data.map((p, i) => (
                    <div key={i} className={`grid grid-cols-7 p-3 border-b border-border-ghost hover:bg-surface-2 transition-colors type-data-sm font-mono items-center`}>
                        <span className="text-text-4">{p.date}</span>
                        <span className="font-bold text-text-1">{p.symbol}</span>
                        <span className="col-span-2 text-text-2 flex flex-col">
                           <span className="text-text-1">{p.executive}</span>
                           <span className="text-[10px] text-text-5 tracking-widest">{p.title}</span>
                        </span>
                        <span className={`flex items-center gap-1 ${p.type === 'BUY' ? 'text-bull' : 'text-bear'}`}>
                           {p.type === 'BUY' ? <TrendingUp size={12}/> : <TrendingDown size={12}/>}
                           {p.shares.toLocaleString()}
                        </span>
                        <span className="text-[#FFB800]">${(p.value / 1e6).toFixed(1)}M</span>
                        <span className="flex items-center gap-2">
                           <Cpu size={12} className={p.intent.includes('CONVICTION') ? 'text-bull' : p.intent.includes('10B51') ? 'text-text-4' : 'text-bear'}/>
                           <span className={p.intent.includes('CONVICTION') ? 'text-bull font-bold' : p.intent.includes('10B51') ? 'text-text-4' : 'text-bear font-bold'}>
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
export default InsiderView;
