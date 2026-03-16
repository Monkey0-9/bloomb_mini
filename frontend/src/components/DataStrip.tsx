import { useEquityStore } from '../store/equityStore';
import { useVesselStore } from '../store/vesselStore';
import { useFlightStore } from '../store/flightStore';

const DataStrip = () => {
  const { equities } = useEquityStore();
  const { vessels } = useVesselStore();
  const { flights } = useFlightStore();

  // Create dynamic events for the top row
  const activeVessels = vessels?.filter(v => v.voyage_progress_pct > 90).length || 0;
  const activeFlights = flights?.filter(f => f.progress_pct > 80).length || 0;

  return (
    <div className="h-8 bg-void border-t border-white/10 flex flex-col overflow-hidden shrink-0 z-raised relative">
      {/* Top Row: Intelligence Events */}
      <div className="h-1/2 flex items-center px-4 overflow-hidden relative group bg-surface-0/30 font-mono">
        <div className="flex gap-16 whitespace-nowrap items-center animate-ticker-slow">
           <div className="flex items-center gap-12 text-text-3 type-data-xs uppercase tracking-[0.15em]">
              <span className="flex items-center gap-2">
                <span className="text-accent-primary glow-text-primary">ROTTERDAM HUB</span> <span className="text-bull font-bold">+34%</span> <span className="text-text-5">·</span> Δ {activeVessels} VESSELS ARRIVING
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                 <span className="text-text-1">{activeFlights} CARGO TRANSITS</span> <span className="text-text-5">@</span> <span className="text-accent-primary">OPENSKY FEEDS</span>
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                <span className="text-accent-tertiary">SINGAPORE PSA</span> STATUS <span className="text-bull">OPTIMIZED</span>
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                <span className="text-white bg-accent-primary px-1 font-bold">SENTINEL-2A</span> INGEST COMPLETE: PANAMA CANAL
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                <span className="text-accent-quaternary">SUEZ CHOKEPOINT</span> TRANSIT DELAY <span className="text-bear">-4.2H</span>
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                <span className="text-accent-primary">SAR TASKING</span> <span className="text-bull">ENABLED</span> FOR BRTUB HUB
              </span>
           </div>
           {/* Loop */}
           <div className="flex items-center gap-12 text-text-3 type-data-xs uppercase tracking-[0.15em]">
              <span className="flex items-center gap-2">
                <span className="text-accent-primary glow-text-primary">ROTTERDAM HUB</span> <span className="text-bull font-bold">+34%</span> <span className="text-text-5">·</span> Δ {activeVessels} VESSELS ARRIVING
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                 <span className="text-text-1">{activeFlights} CARGO TRANSITS</span> <span className="text-text-5">@</span> <span className="text-accent-primary">OPENSKY FEEDS</span>
              </span>
           </div>
        </div>
      </div>

      <div className="absolute inset-x-0 top-1/2 h-[1px] bg-white/5" />

      {/* Bottom Row: Live Tickers */}
      <div className="h-1/2 flex items-center px-4 overflow-hidden relative group">
        <div className="flex gap-16 whitespace-nowrap items-center animate-ticker-medium ml-12">
           <div className="flex items-center gap-10 type-data-xs tabular-nums font-mono">
              {(equities && equities.length > 0 ? equities : [
                { ticker: "AMKBY", price: 128.40, change: 1.86 },
                { ticker: "ZIM", price: 14.22, change: 0.94 },
                { ticker: "FDX", price: 258.12, change: 1.40 },
                { ticker: "UPS", price: 152.33, change: 0.78 }
              ]).map((t, idx) => (
                <div key={idx} className="flex items-center gap-2">
                   <span className="text-accent-primary font-bold">{t.ticker}</span>
                   <span className="text-text-1">{(t.price || 0).toFixed(2)}</span>
                   <span className={(t.change || 0) >= 0 ? 'text-bull font-bold' : 'text-bear font-bold'}>
                     {(t.change || 0) >= 0 ? '+' : ''}{(t.change || 0).toFixed(2)}%
                   </span>
                </div>
              ))}
           </div>
           {/* Loop for seamless animation */}
           <div className="flex items-center gap-10 type-data-xs tabular-nums font-mono">
              {(equities && equities.length > 0 ? equities.slice(0, 10) : []).map((t, idx) => (
                <div key={`loop-${idx}`} className="flex items-center gap-2">
                   <span className="text-accent-primary font-bold">{t.ticker}</span>
                   <span className="text-text-1">{(t.price || 0).toFixed(2)}</span>
                   <span className={(t.change || 0) >= 0 ? 'text-bull font-bold' : 'text-bear font-bold'}>
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
