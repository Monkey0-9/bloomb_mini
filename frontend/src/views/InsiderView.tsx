import React, { useState, useEffect } from 'react';
import { ShieldAlert, Cpu, Eye, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

const mockInsider = [
  { company: 'PLTR', executive: 'Karp Alexander', title: 'CEO', type: 'SALE', shares: '2.5M', val: '$51.2M', date: 'TODAY', intent: 'SCHEDULED_10B51' },
  { company: 'NVDA', executive: 'Huang Jen-Hsun', title: 'CEO', type: 'SALE', shares: '1.2M', val: '$118.5M', date: 'TODAY', intent: 'TAX_LIABILITY' },
  { company: 'RIVN', executive: 'Scaringe RJ', title: 'CEO', type: 'BUY', shares: '150K', val: '$2.1M', date: 'YESTERDAY', intent: 'CONVICTION_BUY' },
  { company: 'COIN', executive: 'Armstrong Brian', title: 'CEO', type: 'SALE', shares: '75K', val: '$15.8M', date: 'YESTERDAY', intent: 'SCHEDULED_10B51' },
  { company: 'SOFI', executive: 'Noto Anthony', title: 'CEO', type: 'BUY', shares: '30K', val: '$240K', date: '-2 DAYS', intent: 'CONVICTION_BUY' },
  { company: 'INTC', executive: 'Gelsinger Pat', title: 'CEO', type: 'BUY', shares: '15K', val: '$320K', date: '-3 DAYS', intent: 'CONVICTION_BUY' },
  { company: 'SNOW', executive: 'Slootman Frank', title: 'DIR', type: 'SALE', shares: '500K', val: '$65.3M', date: '-3 DAYS', intent: 'OPPORTUNISTIC' },
];

const InsiderView = () => {
  const [data, setData] = useState(mockInsider);

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
                <div className="type-h1 text-2xl text-bear">-$1.4B</div>
             </div>
             <div className="bg-surface-1 border border-border-2 p-4">
                <div className="type-data-xs text-text-4 uppercase mb-2">Conviction Cluster Density</div>
                <div className="type-h1 text-2xl text-bull">HIGH</div>
             </div>
             <div className="bg-surface-1 border border-border-2 p-4 relative overflow-hidden">
                <div className="absolute inset-0 bg-[#FFB800]/5"></div>
                <div className="type-data-xs text-text-4 uppercase mb-2">Most Heavily Bought</div>
                <div className="type-h1 text-2xl text-[#FFB800]">RIVN</div>
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
                        <span className="font-bold text-text-1">{p.company}</span>
                        <span className="col-span-2 text-text-2 flex flex-col">
                           <span className="text-text-1">{p.executive}</span>
                           <span className="text-[10px] text-text-5 tracking-widest">{p.title}</span>
                        </span>
                        <span className={`flex items-center gap-1 ${p.type === 'BUY' ? 'text-bull' : 'text-bear'}`}>
                           {p.type === 'BUY' ? <TrendingUp size={12}/> : <TrendingDown size={12}/>}
                           {p.shares}
                        </span>
                        <span className="text-[#FFB800]">{p.val}</span>
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
