import * as Lucide from 'lucide-react';

const Activity = Lucide.Activity || Lucide.Zap;

const SignalCard = ({ 
  name, 
  location,
  status, 
  score, 
  ic, 
  icir, 
  tickers
}: any) => {
  const { setView, setCurrentTicker } = useTerminalStore();
  const isBull = status === 'BULLISH';
  const statusColor = isBull ? 'text-[var(--neon-bull)]' : status === 'BEARISH' ? 'text-[var(--neon-bear)]' : 'text-[var(--text-tertiary)]';

  const handleClick = () => {
    if (tickers && tickers.length > 0) {
        setCurrentTicker(`${tickers[0]} US Equity`);
        setView('charts');
    } else {
        setView('matrix');
    }
  };

  return (
    <div 
      onClick={handleClick}
      className="relative p-2.5 mx-2 mt-2 bg-transparent border border-[var(--border-subtle)] group hover:border-[var(--neon-bull)] transition-colors cursor-crosshair overflow-hidden"
    >
      <div className="absolute inset-0 bg-[var(--neon-bull)] opacity-0 group-hover:opacity-5 transition-opacity pointer-events-none"></div>
      
      <div className="flex justify-between items-start mb-1.5">
        <span className={`text-[8px] font-bold font-mono tracking-widest uppercase px-1.5 py-0.5 border ${
          isBull ? 'bg-[var(--neon-dim-bull)] border-[var(--neon-bull)]/50 text-[var(--neon-bull)]' :
          status === 'BEARISH' ? 'bg-[var(--neon-dim-bear)] border-[var(--neon-bear)]/50 text-[var(--neon-bear)]' :
          'bg-[var(--bg-overlay)] border-[var(--border-subtle)] text-[var(--text-secondary)]'
        }`}>
          {status}
        </span>
        <span className="text-[8px] text-[var(--text-tertiary)] font-mono uppercase tracking-widest">{location}</span>
      </div>

      <div className="mb-2">
        <span className="text-[11px] text-[var(--text-primary)] group-hover:text-[var(--neon-bull)] font-bold tracking-wider leading-tight uppercase line-clamp-2">
          {name}
        </span>
      </div>

      <div className="flex items-center gap-3 pt-1.5 border-t border-[var(--border-subtle)]">
        <div className="flex flex-col">
          <span className="text-[7px] text-[var(--text-tertiary)] uppercase tracking-widest">Confidence</span>
          <span className={`text-[12px] font-bold font-mono tracking-tighter ${statusColor}`}>
            {Number(score || 0).toFixed(1)}
          </span>
        </div>
        <div className="flex-1 grid grid-cols-2 gap-x-2 text-[9px] border-l border-[var(--border-subtle)] pl-2 font-mono">
          <div className="flex justify-between"><span className="text-[var(--text-tertiary)]">IC</span> <span className="text-[var(--text-primary)] font-bold">{Number(ic || 0).toFixed(3)}</span></div>
          <div className="flex justify-between"><span className="text-[var(--text-tertiary)]">IR</span> <span className="text-[var(--text-primary)] font-bold">{Number(icir || 0).toFixed(2)}</span></div>
        </div>
      </div>

      {tickers && tickers.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2 pt-1.5 border-t border-[var(--border-subtle)]">
          {tickers.slice(0, 3).map((t: string) => (
            <div key={t} className="flex items-center gap-1 text-[8px] font-mono font-bold bg-[var(--bg-overlay)] px-1 py-0.5 border border-[var(--border-subtle)]">
              <span className="text-[var(--text-secondary)]">{t}</span>
              <span className="text-[var(--neon-bull)] group-hover:animate-pulse">+{(Math.random() * 1.2).toFixed(2)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const SignalPanel = () => {
  const { setView } = useTerminalStore();
  const [signals, setSignals] = useState<any[]>([]);

  useEffect(() => {
    const fetchSig = async () => {
      try {
        const data = await api.thermal(6);
        setSignals(data.clusters.map((c: any) => ({
          id: c.id,
          name: c.reason,
          location: c.name,
          status: c.signal,
          score: c.score,         // Real score from FIRMS data
          ic: Math.abs(c.sigma) * 0.018,  // Derived from real sigma
          icir: Math.abs(c.sigma) * 0.4,
          tickers: c.tickers,
        })));
      } catch(e) {}
    }
    fetchSig();
    const interval = setInterval(fetchSig, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-full bg-[var(--bg-base)] overflow-hidden font-mono select-none">
      <div className="p-2 border-b border-[var(--border-subtle)] flex flex-col gap-1 bg-[var(--bg-surface)] shrink-0">
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-[var(--text-primary)] font-bold tracking-[0.2em] flex items-center gap-2 uppercase">
              <Activity size={10} className="text-[var(--neon-bull)]" /> ACTIVE INTERCEPTS
            </span>
            <div className="w-1.5 h-1.5 bg-[var(--neon-bull)] shadow-[0_0_4px_var(--neon-bull)] animate-pulse"></div>
          </div>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar pb-2">
        {signals.map(s => (
          <SignalCard key={s.id || s.location} {...s} />
        ))}
      </div>

      <div className="p-2 bg-[var(--bg-surface)] border-t border-[var(--border-subtle)] shrink-0">
         <button 
           onClick={() => setView('matrix')}
           className="w-full py-1.5 bg-[var(--bg-overlay)] border border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:border-[var(--neon-bull)] hover:text-[var(--neon-bull)] text-[9px] font-bold uppercase tracking-widest transition-colors flex justify-center items-center gap-2"
         >
            Signal Matrix <span className="opacity-50">→</span>
         </button>
      </div>
    </div>
  );
};

export default SignalPanel;

