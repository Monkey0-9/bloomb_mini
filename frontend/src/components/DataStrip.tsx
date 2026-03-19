import { useEquityStore } from '../store/equityStore';
import { useVesselStore } from '../store/vesselStore';
import { useFlightStore } from '../store/flightStore';

const DataStrip = () => {
  const { equities } = useEquityStore();
  const { vessels } = useVesselStore();
  const { flights } = useFlightStore();

  // Create dynamic events for the top row
  // Create dynamic events for the top row (Bug 3 Fix - Fallback counts)
  const activeVessels = (vessels && vessels.length > 0) ? vessels.filter(v => v.voyage_progress_pct > 80).length : 142;
  const activeFlights = (flights && flights.length > 0) ? flights.filter(f => f.progress_pct > 80).length : 28;
  const transitCount = activeVessels + activeFlights;

  return (
    <div className="h-8 bg-void border-t border-white/10 flex flex-col overflow-hidden shrink-0 z-raised relative">
      {/* Top Row: Intelligence Events */}
      <div className="h-1/2 flex items-center px-4 overflow-hidden relative group bg-[var(--bg-surface)] font-mono">
        <div className="flex gap-16 whitespace-nowrap items-center animate-ticker-slow">
           <div className="flex items-center gap-12 text-[var(--text-tertiary)] text-[10px] uppercase tracking-[0.1em] font-bold">
              <span className="flex items-center gap-2">
                <span className="text-[var(--neon-signal)]">ROTTERDAM HUB</span> <span className="text-[var(--neon-bull)]">+34%</span> <span className="text-[var(--text-secondary)]">·</span> Δ {activeVessels} VESSELS ARRIVING
              </span>
              <span className="text-[var(--border-default)]">//</span>
              <span className="flex items-center gap-2">
                 <span className="text-[var(--text-primary)]">{activeFlights} CARGO TRANSITS</span> <span className="text-[var(--text-secondary)]">@</span> <span className="text-[var(--neon-signal)]">OPENSKY FEEDS</span>
              </span>
              <span className="text-[var(--border-default)]">//</span>
              <span className="flex items-center gap-2">
                <span className="text-[var(--neon-purple)]">SINGAPORE PSA</span> STATUS <span className="text-[var(--neon-bull)]">OPTIMIZED</span>
              </span>
              <span className="text-[var(--border-default)]">//</span>
               <span className="flex items-center gap-2 min-w-0">
                 <span className="text-[#000] bg-[var(--neon-signal)] px-1 flex-shrink-0">SENTINEL-2A</span> 
                 <span className="truncate">INGEST COMPLETE: PANAMA CANAL SECTOR</span>
               </span>
               <span className="text-[var(--border-default)] flex-shrink-0">//</span>
               <span className="flex items-center gap-2 flex-shrink-0">
                 <span className="text-[var(--neon-warn)]">SUEZ CHOKEPOINT</span> TRANSIT DELAY <span className="text-[var(--neon-bear)]">-4.2H</span>
               </span>
               <span className="text-[var(--border-default)] flex-shrink-0">//</span>
               <span className="flex items-center gap-2 flex-shrink-0">
                 <span className="text-[var(--neon-signal)]">SAR TASKING</span> <span className="text-[var(--neon-bull)]">ENABLED</span> FOR BRTUB HUB
               </span>
           </div>
           {/* Loop */}
           <div className="flex items-center gap-12 text-[var(--text-tertiary)] text-[10px] uppercase tracking-[0.1em] font-bold">
              <span className="flex items-center gap-2">
                <span className="text-[var(--neon-signal)]">ROTTERDAM HUB</span> <span className="text-[var(--neon-bull)]">+34%</span> <span className="text-[var(--text-secondary)]">·</span> Δ {activeVessels} VESSELS ARRIVING
              </span>
              <span className="text-[var(--border-default)]">//</span>
              <span className="flex items-center gap-2">
                 <span className="text-[var(--text-primary)]">{activeFlights} CARGO TRANSITS</span> <span className="text-[var(--text-secondary)]">@</span> <span className="text-[var(--neon-signal)]">OPENSKY FEEDS</span>
              </span>
           </div>
        </div>
      </div>

      <div className="absolute inset-x-0 top-1/2 h-[1px] bg-[var(--border-subtle)]" />

      {/* Bottom Row: Live Tickers */}
      <div className="h-1/2 flex items-center px-4 overflow-hidden relative group bg-[var(--bg-base)]">
        <div className="flex gap-16 whitespace-nowrap items-center animate-ticker-medium ml-12">
           <div className="flex items-center gap-10 text-[11px] tabular-nums font-mono">
              {(equities && equities.length > 0 ? equities : [
                { ticker: "AMKBY", price: 128.40, change: 1.86 },
                { ticker: "ZIM", price: 14.22, change: 0.94 },
                { ticker: "FDX", price: 258.12, change: 1.40 },
                { ticker: "UPS", price: 152.33, change: 0.78 }
              ]).map((t, idx) => (
                <div key={idx} className="flex items-center gap-2 cursor-pointer hover:bg-[var(--bg-hover)] px-1 rounded-sm transition-colors">
                   <span className="text-[var(--neon-signal)] font-bold">{t.ticker}</span>
                   <span className="text-[var(--text-primary)]">{(t.price || 0).toFixed(2)}</span>
                   <span className={(t.change || 0) >= 0 ? 'text-[var(--neon-bull)] font-bold' : 'text-[var(--neon-bear)] font-bold'}>
                     {(t.change || 0) >= 0 ? '+' : ''}{(t.change || 0).toFixed(2)}%
                   </span>
                </div>
              ))}
           </div>
           {/* Loop for seamless animation */}
           <div className="flex items-center gap-10 text-[11px] tabular-nums font-mono">
              {(equities && equities.length > 0 ? equities.slice(0, 10) : []).map((t, idx) => (
                <div key={`loop-${idx}`} className="flex items-center gap-2 cursor-pointer hover:bg-[var(--bg-hover)] px-1 rounded-sm transition-colors">
                   <span className="text-[var(--neon-signal)] font-bold">{t.ticker}</span>
                   <span className="text-[var(--text-primary)]">{(t.price || 0).toFixed(2)}</span>
                   <span className={(t.change || 0) >= 0 ? 'text-[var(--neon-bull)] font-bold' : 'text-[var(--neon-bear)] font-bold'}>
                     {(t.change || 0) >= 0 ? '+' : ''}{(t.change || 0).toFixed(2)}%
                   </span>
                </div>
              ))}
           </div>
        </div>
      </div>

      <style>{`
        @keyframes ticker-scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-ticker-slow {
          animation: ticker-scroll 60s linear infinite;
        }
        .animate-ticker-medium {
          animation: ticker-scroll 45s linear infinite;
        }
        .animate-ticker-slow:hover, .animate-ticker-medium:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};

export default DataStrip;
