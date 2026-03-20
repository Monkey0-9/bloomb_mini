import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Zap, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';

interface EarningsItem {
  ticker: string;
  earnings_date: string;
  eps_estimate: number | null;
  eps_low: number | null;
  eps_high: number | null;
  satellite_signal: string;
  satellite_reason: string;
  alpha_opportunity: boolean;
}

const SignalBadge = ({ signal }: { signal: string }) => {
  const color =
    signal === 'BULLISH' ? 'text-bull bg-bull-08 border-bull-60' :
    signal === 'BEARISH' ? 'text-bear bg-bear-08 border-bear-60' :
    signal === 'NO_SIGNAL' ? 'text-text-5 bg-surface-2 border-border-2' :
    'text-neutral bg-surface-2 border-border-2';
  return (
    <span className={`type-data-xs px-2 py-0.5 border font-bold tracking-widest uppercase ${color}`}>
      {signal === 'NO_SIGNAL' ? 'NO SAT DATA' : signal}
    </span>
  );
};

const daysUntil = (dateStr: string) => {
  const diff = new Date(dateStr).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
};

const EarningsView = () => {
  const [earnings, setEarnings] = useState<EarningsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const resp = await fetch('/api/alpha/earnings');
        if (!resp.ok) throw new Error();
        const data = await resp.json();
        setEarnings(data.earnings || []);
      } catch {
        setEarnings([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const alphaOpportunities = earnings.filter(e => e.alpha_opportunity);

  return (
    <div className="flex-1 flex flex-col bg-surface-0 overflow-hidden">
      {/* HEADER */}
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
        <div className="flex items-center gap-2">
          <Calendar size={16} className="text-accent-primary" />
          <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">Earnings + Satellite Signal</span>
          <div className="w-1.5 h-1.5 rounded-full bg-bull dot-live" />
        </div>
        <div className="flex items-center gap-4">
          <span className="type-data-xs text-text-4 uppercase tracking-widest">
            Alpha Opportunities: <span className="text-bull font-bold">{alphaOpportunities.length}</span>
          </span>
        </div>
      </div>

      {/* ALPHA ALERT STRIP */}
      {alphaOpportunities.length > 0 && (
        <div className="border-b border-bull/20 bg-bull/5 px-4 py-2 flex items-center gap-4 overflow-x-auto shrink-0">
          <div className="flex items-center gap-1.5 shrink-0">
            <Zap size={12} className="text-bull" />
            <span className="type-data-xs text-bull font-bold uppercase tracking-widest">Satellite Alpha:</span>
          </div>
          {alphaOpportunities.slice(0, 6).map(e => (
            <div key={e.ticker} className="shrink-0 flex items-center gap-2 bg-surface-2 border border-bull/20 px-2 py-1">
              <span className="type-data-xs text-text-0 font-bold">{e.ticker}</span>
              <SignalBadge signal={e.satellite_signal} />
            </div>
          ))}
        </div>
      )}

      {/* CALENDAR TABLE */}
      <div className="flex-1 overflow-auto custom-scrollbar">
        {loading ? (
          <div className="flex flex-col gap-1 p-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="h-14 bg-surface-1/30 border border-border-ghost animate-pulse" />
            ))}
          </div>
        ) : earnings.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="type-data-xs text-text-4 uppercase tracking-widest">No upcoming earnings data available</span>
          </div>
        ) : (
          <table className="w-full border-collapse">
            <thead className="sticky top-0 bg-surface-1 z-10 border-b border-border-3">
              <tr>
                {['Ticker', 'Earnings Date', 'Days Away', 'EPS Est.', 'Satellite Signal', 'Signal Reason'].map(h => (
                  <th key={h} className="px-4 py-3 text-left">
                    <span className="type-data-xs text-text-3 font-bold uppercase tracking-[0.15em]">{h}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border-ghost">
              {earnings.map((e, i) => {
                const days = daysUntil(e.earnings_date);
                const urgent = days >= 0 && days <= 14;
                return (
                  <motion.tr
                    key={`${e.ticker}-${i}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.02 }}
                    className={`hover:bg-surface-2 transition-all group ${e.alpha_opportunity ? 'bg-bull/3' : ''}`}
                  >
                    <td className="px-4 py-3">
                      <span className="type-data-md text-accent-primary font-bold">{e.ticker}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="type-data-xs text-text-2">{e.earnings_date?.split('T')[0] || '—'}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`type-data-xs font-bold ${days < 0 ? 'text-text-5' : urgent ? 'text-bull' : 'text-text-2'}`}>
                        {days < 0 ? 'Passed' : days === 0 ? 'TODAY' : `${days}d`}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="type-data-xs text-text-3 tabular-nums">
                        {e.eps_estimate != null ? `$${e.eps_estimate.toFixed(2)}` : '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <SignalBadge signal={e.satellite_signal} />
                    </td>
                    <td className="px-4 py-3 max-w-xs">
                      <span className="type-data-xs text-text-4 line-clamp-2">{e.satellite_reason}</span>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="h-8 border-t border-border-1 flex items-center justify-between px-4 bg-void shrink-0">
        <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">
          Source: <span className="text-text-2">yfinance + Satellite Signal Overlay</span>
        </span>
        <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">
          {earnings.length} upcoming events tracked
        </span>
      </div>
    </div>
  );
};

export default EarningsView;
