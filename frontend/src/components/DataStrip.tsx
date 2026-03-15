const DataStrip = () => {
  return (
    <div className="h-8 bg-void border-t border-white/10 flex flex-col overflow-hidden shrink-0 z-raised relative">
      <div className="h-1/2 flex items-center px-4 overflow-hidden relative group bg-surface-0/30">
        <div className="flex gap-16 whitespace-nowrap items-center animate-ticker-slow">
           <div className="flex items-center gap-12 text-text-3 type-data-xs uppercase tracking-[0.15em]">
              <span className="flex items-center gap-2">
                <span className="text-accent-primary glow-text-primary">ROTTERDAM HUB</span> <span className="text-bull font-bold">+34%</span> <span className="text-text-5">·</span> Δ 12 VESSELS
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                 <span className="text-text-1">47 AT BERTH</span> <span className="text-text-5">@</span> <span className="text-accent-primary">SHANGHAI YANGSHAN</span>
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                <span className="text-accent-tertiary">SINGAPORE PSA</span> STATUS <span className="text-bull">OPTIMIZED</span>
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                <span className="text-white bg-accent-primary px-1 font-bold">SENTINEL-2A</span> INGEST COMPLETE: PORT OF ROTTERDAM
              </span>
           </div>
           {/* Loop */}
           <div className="flex items-center gap-12 text-text-3 type-data-xs uppercase tracking-[0.15em]">
              <span className="flex items-center gap-2">
                <span className="text-accent-primary glow-text-primary">ROTTERDAM HUB</span> <span className="text-bull font-bold">+34%</span> <span className="text-text-5">·</span> Δ 12 VESSELS
              </span>
              <span className="text-text-5">//</span>
              <span className="flex items-center gap-2">
                 <span className="text-text-1">47 AT BERTH</span> <span className="text-text-5">@</span> <span className="text-accent-primary">SHANGHAI YANGSHAN</span>
              </span>
           </div>
        </div>
      </div>

      <div className="absolute inset-x-0 top-1/2 h-[1px] bg-white/5" />

      <div className="h-1/2 flex items-center px-4 overflow-hidden relative group">
        <div className="flex gap-16 whitespace-nowrap items-center animate-ticker-medium ml-12">
           <div className="flex items-center gap-10 type-data-xs tabular-nums">
              <div className="flex items-center gap-2">
                 <span className="text-accent-primary font-bold">AMKBY</span>
                 <span className="text-text-1">128.40</span>
                 <span className="text-bull font-bold">+1.86%</span>
              </div>
              <div className="flex items-center gap-2">
                 <span className="text-accent-primary font-bold">ZIM</span>
                 <span className="text-text-1">14.22</span>
                 <span className="text-bull font-bold">+0.94%</span>
              </div>
              <div className="flex items-center gap-2">
                 <span className="text-accent-primary font-bold">TGT</span>
                 <span className="text-text-1">142.10</span>
                 <span className="text-bear font-bold">-0.33%</span>
              </div>
              <div className="flex items-center gap-2">
                 <span className="text-accent-primary font-bold">WMT</span>
                 <span className="text-text-1">158.30</span>
                 <span className="text-bull font-bold">+1.22%</span>
              </div>
              <div className="flex items-center gap-2">
                 <span className="text-accent-primary font-bold">COSCO</span>
                 <span className="text-text-1">42.15</span>
                 <span className="text-bear font-bold">-0.12%</span>
              </div>
           </div>
           {/* Loop */}
           <div className="flex items-center gap-10 type-data-xs tabular-nums">
              <div className="flex items-center gap-2">
                 <span className="text-accent-primary font-bold">AMKBY</span>
                 <span className="text-text-1">128.40</span>
                 <span className="text-bull font-bold">+1.86%</span>
              </div>
           </div>
        </div>
      </div>

      <style>{`
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-ticker-slow {
          animation: ticker 45s linear infinite;
        }
        .animate-ticker-medium {
          animation: ticker 30s linear infinite;
        }
        .animate-ticker-slow:hover, .animate-ticker-medium:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};


export default DataStrip;
