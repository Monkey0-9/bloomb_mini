import React from 'react';
import { Layout, Plus, Search, GitBranch, Play, MoreHorizontal, Cpu, Database, Share2 } from 'lucide-react';

const WorkflowCard = ({ title, description, status, steps, author }: any) => (
  <div className="bg-surface-1 border border-border-2 p-5 hover:border-accent-primary/60 transition-all group animate-in zoom-in-95 duration-500">
    <div className="flex justify-between items-start mb-4">
      <div className="p-2 bg-surface-2 border border-border-ghost text-accent-primary group-hover:bg-accent-primary group-hover:text-void transition-all">
        <GitBranch size={16} />
      </div>
      <div className={`type-data-xs px-1.5 py-0.5 border ${status === 'ACTIVE' ? 'border-bull text-bull bg-bull/5' : 'border-text-4 text-text-4'} font-mono`}>
        {status}
      </div>
    </div>
    <h3 className="type-ui-md font-bold text-text-1 mb-2 group-hover:text-accent-primary transition-colors">{title}</h3>
    <p className="type-ui-xs text-text-4 line-clamp-2 mb-6 leading-relaxed">
      {description}
    </p>
    <div className="flex items-center justify-between mt-auto pt-4 border-t border-border-ghost">
      <div className="flex items-center gap-2 text-text-4 type-data-xs">
         <Cpu size={10} /> {steps} STEPS
      </div>
      <div className="flex items-center gap-3">
        <button className="text-text-4 hover:text-bull transition-colors"><Play size={14}/></button>
        <button className="text-text-4 hover:text-text-1 transition-colors"><Share2 size={14}/></button>
        <button className="text-text-4 hover:text-text-1 transition-colors"><MoreHorizontal size={14}/></button>
      </div>
    </div>
  </div>
);

const WorkflowView = () => {
  const workflows = [
    { title: 'Dark Fleet Sanctions Scan', description: 'Monthly audit cross-referencing Sentinel-1 SAR detections with OFAC SDN list for tanker MMSI matches.', status: 'ACTIVE', steps: 8, author: 'AlphaTeam' },
    { title: 'Port Congestion vs Retail', description: 'Correlation bridge between US West Coast dwell times and XRT Retail ETF price action.', status: 'ACTIVE', steps: 12, author: 'MacroDesk' },
    { title: 'Thermal Industrial Signal', description: 'Real-time alerting for NASA FIRMS hotspots at top 100 global manufacturing facilities.', status: 'INACTIVE', steps: 6, author: 'EnergyQuant' },
    { title: 'TFT Forecast Drift Monitor', description: 'Watchdog service comparing P50 forecasts with real-market realization over 5D horizons.', status: 'ACTIVE', steps: 15, author: 'System' },
    { title: 'Cargo Flight Volume Hub', description: 'Aggregating ADS-B cargo density into Memphis (FDX) and Louisville (UPS) for logistics alpha.', status: 'ACTIVE', steps: 11, author: 'Logistics' },
    { title: 'Spearman Macro Lead/Lag', description: 'Dynamic analysis of industrial production FRED data vs leading satellite optical signals.', status: 'ACTIVE', steps: 22, author: 'MacroDesk' },
  ];

  return (
    <div className="flex-1 h-full bg-void overflow-y-auto custom-scrollbar flex flex-col">
      <div className="h-14 border-b border-border-1 flex items-center px-8 justify-between shrink-0 bg-surface-base">
        <div className="flex items-center gap-3">
          <Layout size={18} className="text-accent-primary" />
          <h1 className="type-h1 text-sm tracking-[0.2em] text-white uppercase">Analytic Workflow Engine</h1>
        </div>
        <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 bg-accent-primary text-void px-4 py-1.5 type-data-xs font-bold uppercase tracking-widest hover:bg-white transition-all shadow-[0_0_15px_rgba(0,255,157,0.3)]">
                <Plus size={14} strokeWidth={3} /> NEW WORKFLOW
            </button>
        </div>
      </div>

      <div className="flex-1 p-8">
        <div className="max-w-6xl mx-auto">
          
          {/* STATS BAR */}
          <div className="grid grid-cols-4 gap-6 mb-10">
            {[
              { label: 'Active Automations', value: '42', icon: Play, color: 'text-bull' },
              { label: 'Cloud Ingest Rate', value: '1.2 GB/s', icon: Database, color: 'text-accent-blue' },
              { label: 'Compute Utilization', value: '68%', icon: Cpu, color: 'text-[#C084FC]' },
              { label: 'System Health', value: 'NOMINAL', icon: Shield, color: 'text-bull' },
            ].map((stat, i) => (
              <div key={i} className="bg-surface-1 border border-border-2 p-4 flex flex-col gap-1">
                <div className="flex justify-between items-center">
                  <span className="type-data-xs text-text-4 uppercase tracking-widest">{stat.label}</span>
                  <stat.icon size={12} className={stat.color} />
                </div>
                <span className={`text-xl font-bold font-mono ${stat.color}`}>{stat.value}</span>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-3 mb-6">
            <span className="type-h3 text-xs uppercase tracking-[0.3em] text-text-0">Market Workflows</span>
            <div className="flex-1 h-[1px] bg-border-ghost" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
             {workflows.map((w, i) => <WorkflowCard key={i} {...w} />)}
          </div>
        </div>
      </div>
    </div>
  );
};

const Shield = ({ size, className }: any) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

export default WorkflowView;
