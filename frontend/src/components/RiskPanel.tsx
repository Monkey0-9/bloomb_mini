import { useEffect, useState } from 'react';
import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

interface RiskGate {
  name: string;
  passed: boolean;
  value: string;
  threshold: string;
}

interface RiskStatus {
  status: string;
  portfolio: {
    equity: number;
    notional_exposure: number;
    gross_exposure_pct: number;
    net_exposure_pct: number;
    var_99_1d_pct: number;
    kill_switch_active: boolean;
  };
  gates: RiskGate[];
}

const RiskPanel = () => {
  const [risk, setRisk] = useState<RiskStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        const resp = await fetch('/api/risk');
        if (resp.ok) {
          const data = await resp.json();
          setRisk(data);
        }
      } catch (err) {
        console.error('Failed to fetch risk status:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRisk();
    const interval = setInterval(fetchRisk, 10000); // 10s refresh
    return () => clearInterval(interval);
  }, []);

  if (loading || !risk) return null;

  return (
    <div className="flex flex-col h-full bg-[var(--bg-base)] overflow-hidden">
      <div className="h-8 border-b border-[var(--border-subtle)] flex items-center justify-between px-3 shrink-0 bg-[var(--bg-surface)]">
        <div className="flex items-center gap-2">
           <Shield size={10} className={risk.status === 'GREEN' ? 'text-[var(--neon-bull)]' : 'text-[var(--neon-bear)]'} />
           <span className="text-[10px] tracking-widest text-[var(--text-primary)] font-bold uppercase">Risk Engine</span>
        </div>
        <span className={`text-[8px] px-1.5 py-0.5 font-bold tracking-widest border ${
          risk.status === 'GREEN' ? 'bg-[var(--neon-dim-bull)] text-[var(--neon-bull)] border-[var(--neon-bull)]/30' : 'bg-[var(--neon-dim-bear)] text-[var(--neon-bear)] border-[var(--neon-bear)]/30'
        }`}>
          {risk.status}
        </span>
      </div>

      <div className="p-3 flex flex-col gap-3 overflow-y-auto">
         {/* PORTFOLIO STATS */}
         <div className="grid grid-cols-2 gap-2">
            <div className="p-1.5 bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
               <span className="text-[8px] text-[var(--text-tertiary)] block mb-0.5 uppercase font-bold">Equity</span>
               <span className="text-[11px] text-[var(--text-primary)] font-bold font-mono">${(risk.portfolio.equity / 1e6).toFixed(1)}M</span>
            </div>
            <div className="p-1.5 bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
               <span className="text-[8px] text-[var(--text-tertiary)] block mb-0.5 uppercase font-bold">Gross Exp</span>
               <span className="text-[11px] text-[var(--text-primary)] font-bold font-mono">{(risk.portfolio.gross_exposure_pct * 100).toFixed(0)}%</span>
            </div>
         </div>

         {/* AUDIT GATES */}
         <div className="flex flex-col gap-1">
            <span className="text-[8px] text-[var(--text-tertiary)] uppercase tracking-widest font-bold mb-1">Pre-Trade Audit</span>
            {risk.gates.map((gate, i) => (
               <div key={i} className="flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0">
                  <div className="flex flex-col">
                     <span className="text-[9px] text-[var(--text-secondary)] font-bold uppercase">{gate.name}</span>
                     <span className="text-[8px] text-[var(--text-tertiary)] font-mono uppercase">Lim: {gate.threshold}</span>
                  </div>
                  <div className="flex flex-col items-end">
                     <div className="flex items-center gap-1.5">
                        <span className={`text-[10px] font-bold font-mono ${gate.passed ? 'text-[var(--neon-bull)]' : 'text-[var(--neon-bear)]'}`}>{gate.value}</span>
                        {gate.passed ? <ShieldCheck size={10} className="text-[var(--neon-bull)]" /> : <ShieldAlert size={10} className="text-[var(--neon-bear)]" />}
                     </div>
                  </div>
               </div>
            ))}
         </div>

         {/* ALERT CONFIGURATION (Bug 7 Fix) */}
         <button className="w-full mt-1 p-2 bg-[var(--bg-surface)] border border-[var(--border-subtle)] group hover:border-[var(--neon-signal)]/50 transition-all flex flex-col items-center justify-center gap-1">
            <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--text-tertiary)] group-hover:text-[var(--neon-signal)] transition-colors">Configure Alert Webhooks</span>
            <div className="w-12 h-[1px] bg-[var(--border-subtle)] group-hover:w-16 group-hover:bg-[var(--neon-signal)] transition-all duration-300"></div>
         </button>
      </div>
    </div>
  );
};

export default RiskPanel;
