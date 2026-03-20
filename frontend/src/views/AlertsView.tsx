import React from 'react';
import { Bell, AlertTriangle, Info, ShieldAlert, Zap, Filter, Search, MoreHorizontal } from 'lucide-react';

const AlertRow = ({ type, ticker, message, timestamp, severity }: any) => {
  const sevColors: any = {
    CRITICAL: 'text-bear border-bear bg-bear/10',
    WARNING: 'text-[#FFB800] border-[#FFB800] bg-[#FFB800]/10',
    INFO: 'text-accent-blue border-accent-blue bg-accent-blue/10',
    SIGNAL: 'text-accent-primary border-accent-primary bg-accent-primary/10',
  };

  const IconMapping: Record<string, any> = {
    CRITICAL: ShieldAlert,
    WARNING: AlertTriangle,
    INFO: Info,
    SIGNAL: Zap,
  };
  const Icon = IconMapping[severity] || Bell;

  return (
    <div className={`flex items-center gap-4 p-4 border rounded-sm transition-all hover:bg-surface-2 group mb-3 ${sevColors[severity] || 'border-border-2'}`}>
      <div className="p-2 border border-current shrink-0">
        <Icon size={16} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <span className="type-data-xs font-bold uppercase tracking-widest">{ticker}</span>
          <span className="type-data-xs opacity-60 font-mono">{timestamp}</span>
        </div>
        <p className="type-ui-sm font-medium text-text-1 truncate">{message}</p>
      </div>
      <div className="flex items-center gap-6 opacity-40 group-hover:opacity-100 transition-opacity">
        <button className="type-data-xs uppercase font-bold tracking-widest border border-current px-2 py-0.5 hover:bg-current hover:text-black transition-all">ANALYSIS</button>
        <button className="text-text-4 hover:text-text-1"><MoreHorizontal size={14}/></button>
      </div>
    </div>
  );
};

const AlertsView = () => {
  const alerts = [
    { type: 'SIGNAL', ticker: 'ZIM US Equity', message: 'Dark vessel density at Port of Rotterdam exceeded 3σ. Alpha Signal updated to STRONG BULLISH.', timestamp: '14:22:11 UTC', severity: 'SIGNAL' },
    { type: 'CRITICAL', ticker: 'PORTFOLIO_NAV', message: 'Parametric VaR 99% breach (2.12% > 2.0% Limit). Automated position reduction initiated.', timestamp: '14:15:05 UTC', severity: 'CRITICAL' },
    { type: 'WARNING', ticker: 'VALE US Equity', message: 'Landsat TIRS anomaly detected at Carajás processing plant. Capacity reduction suspected.', timestamp: '13:58:34 UTC', severity: 'WARNING' },
    { type: 'INFO', ticker: 'SYSTEM_KERNEL', message: 'Async Landsat Ingestor refactored to Aiohttp. Latency reduced by 440ms.', timestamp: '13:45:00 UTC', severity: 'INFO' },
    { type: 'SIGNAL', ticker: 'AMKBY US Equity', message: 'AIS/Fleet gap analysis shows 12 unidentified vessels in South China Sea. Monitoring.', timestamp: '13:12:11 UTC', severity: 'SIGNAL' },
    { type: 'WARNING', ticker: 'MAERSK-B DC', message: 'Satellite signal confluence (Maritime + Econ) dropped below +0.40 conviction threshold.', timestamp: '12:45:22 UTC', severity: 'WARNING' },
  ];

  return (
    <div className="flex-1 h-full bg-void overflow-y-auto custom-scrollbar flex flex-col">
      <div className="h-14 border-b border-border-1 flex items-center px-8 justify-between shrink-0 bg-surface-base">
        <div className="flex items-center gap-3">
          <Bell size={18} className="text-accent-primary" />
          <h1 className="type-h1 text-sm tracking-[0.2em] text-white uppercase">Institutional Alert Hub</h1>
        </div>
        <div className="flex items-center gap-4">
            <div className="relative">
                <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-4" />
                <input 
                    type="text" 
                    placeholder="FILTER ALERTS..." 
                    className="bg-surface-1 border border-border-2 pl-9 pr-4 py-1.5 type-data-xs text-text-1 outline-none focus:border-accent-primary transition-colors w-64"
                />
            </div>
            <button className="flex items-center gap-2 type-data-xs border border-border-2 px-3 py-1.5 text-text-3 hover:text-white hover:border-text-3 transition-all">
                <Filter size={12} /> CONFIG FILTERS
            </button>
        </div>
      </div>

      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-5xl mx-auto">
           <div className="mb-6 flex justify-between items-end border-b border-border-ghost pb-2">
              <span className="type-data-xs text-text-4 uppercase tracking-widest">Showing {alerts.length} live alerts from Kernel Stream</span>
              <button className="type-data-xs text-accent-blue hover:underline uppercase">Clear All Seen</button>
           </div>

           {alerts.map((a, i) => <AlertRow key={i} {...a} />)}

           <div className="mt-12 p-10 border-2 border-dashed border-border-ghost text-center grayscale opacity-50 hover:grayscale-0 hover:opacity-100 transition-all cursor-pointer">
              <Zap size={24} className="mx-auto text-accent-primary mb-3" />
              <h3 className="type-h3 text-text-1 uppercase mb-1">Create Webhook Relay</h3>
              <p className="type-ui-sm text-text-4">Bridge SatTrade alerts to Slack, Discord, or Bloomberg IB Chat.</p>
           </div>
        </div>
      </div>
    </div>
  );
};

export default AlertsView;
