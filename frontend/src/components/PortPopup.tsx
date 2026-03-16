/**
 * Component-based HTML generator for Port Popups.
 * Provides high-fidelity berth counts, signals, and ticker associations.
 */

export const getPortHTML = (p: any) => {
  // Mock berth intelligence for demo stability
  const throughput = p.throughput ?? 0.8;
  const signal = p.signal || 'NEUTRAL';
  const name = p.name || 'Global Port';
  
  const berthCount = Math.floor(Math.random() * 50) + 20;
  const activeBerths = Math.floor(berthCount * throughput);
  const waitTime = (1.0 - throughput) * 72;
  
  const tickerMap: any = {
    'ROTTERDAM': ['AMPBY', 'ZIM'],
    'SINGAPORE': ['MATX', 'AAPL'],
    'SHANGHAI': ['BHP', 'VALE'],
    'LONG BEACH': ['FDX', 'WMT'],
    'JEBEL ALI': ['AMZN', 'MPC']
  };

  const tickers = tickerMap[name.toUpperCase().replace(' PORT', '')] || ['GLOBAL'];

  return `
    <div class="glass-panel p-4 min-w-[280px] border-l-4 ${signal === 'BULLISH' ? 'border-bull' : 'border-bear'}">
      <div class="flex justify-between items-start mb-3">
        <div>
          <div class="type-h2 text-accent-primary uppercase tracking-widest">${name}</div>
          <div class="text-[9px] text-text-4 uppercase tracking-tighter">Strategic Logistics Hub</div>
        </div>
        <div class="px-2 py-0.5 bg-surface-2 rounded border border-white/10">
          <span class="type-data-xs font-bold ${signal === 'BULLISH' ? 'text-bull' : 'text-bear'}">${signal}</span>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4 mb-4">
        <div class="bg-surface-1/40 p-2 rounded-sm border border-white/5">
          <div class="type-data-xs text-text-4 uppercase mb-1">Berth Utilization</div>
          <div class="type-h3">${activeBerths}/${berthCount}</div>
        </div>
        <div class="bg-surface-1/40 p-2 rounded-sm border border-white/5">
          <div class="type-data-xs text-text-4 uppercase mb-1">Avg Anchor Wait</div>
          <div class="type-h3">${waitTime.toFixed(1)}h</div>
        </div>
      </div>

      <div class="mb-4">
        <div class="flex justify-between items-center mb-1">
          <span class="type-data-xs text-text-3 uppercase">Real-Time Throughput</span>
          <span class="type-data-xs font-bold text-text-1">${(throughput * 100).toFixed(1)}%</span>
        </div>
        <div class="segment-bar h-1.5">
           ${Array.from({length: 12}).map((_, i) => `
             <div class="segment ${i < (throughput * 12) ? (signal === 'BULLISH' ? 'active-bull' : 'active-bear') : ''}"></div>
           `).join('')}
        </div>
      </div>

      <div class="border-t border-white/5 pt-3">
        <div class="type-data-xs text-text-4 uppercase mb-2 tracking-widest">Inbound Tracked Vessel Alpha</div>
        <div class="flex flex-col gap-2">
          ${p.inboundVessels && p.inboundVessels.length > 0 ? p.inboundVessels.map((v: any) => `
            <div class="flex justify-between items-center bg-surface-2/40 p-1.5 rounded-sm border border-accent-primary/10">
              <div class="flex flex-col">
                <span class="type-data-xs text-text-1 font-bold">${v.name}</span>
                <span class="text-[8px] text-text-4 uppercase tracking-tighter">${v.cargo_type || 'Cargo'} | ETA: ${v.eta || 'TBD'}</span>
              </div>
              <span class="text-[9px] font-bold ${v.signal === 'BULLISH' ? 'text-bull' : 'text-bear'}">${v.signal}</span>
            </div>
          `).join('') : `
            <div class="type-data-xs text-text-5 italic text-center py-2">No tracked vessels in current window</div>
          `}
        </div>
      </div>
    </div>
  `;
};
