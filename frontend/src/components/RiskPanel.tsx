import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
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
        const resp = await fetch('http://localhost:8000/api/risk');
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
    <div className="w-[280px] bg-surface-0 border-l border-border-1 flex flex-col shrink-0">
      <div className="h-11 border-b border-border-subtle flex items-center justify-between px-4 shrink-0 bg-surface-0/80 backdrop-blur-sm">
        <div className="flex items-center gap-2">
           <Shield size={14} className={risk.status === 'GREEN' ? 'text-bull' : 'text-bear'} />
           <span className="type-h1 text-sm tracking-widest text-text-1 uppercase">RISK ENGINE</span>
        </div>
        <span className={`type-data-xs px-2 py-0.5 rounded-sm font-bold tracking-widest ${
          risk.status === 'GREEN' ? 'bg-bull/10 text-bull' : 'bg-bear/10 text-bear'
        }`}>
          {risk.status}
        </span>
      </div>

      <div className="p-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar">
         {/* PORTFOLIO STATS */}
         <div className="grid grid-cols-2 gap-3">
            <div className="p-2 bg-surface-1 border border-border-subtle rounded-sm">
               <span className="type-data-xs text-text-4 block mb-1">EQUITY</span>
               <span className="type-data-md text-text-1 font-bold">${(risk.portfolio.equity / 1e6).toFixed(1)}M</span>
            </div>
            <div className="p-2 bg-surface-1 border border-border-subtle rounded-sm">
               <span className="type-data-xs text-text-4 block mb-1">GROSS EXP</span>
               <span className="type-data-md text-text-1 font-bold">{(risk.portfolio.gross_exposure_pct * 100).toFixed(0)}%</span>
            </div>
         </div>

         {/* AUDIT GATES */}
         <div className="flex flex-col gap-1">
            <span className="type-data-xs text-text-4 uppercase tracking-widest font-bold mb-1">Pre-Trade Audit</span>
            {risk.gates.map((gate, i) => (
               <div key={i} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                  <div className="flex flex-col">
                     <span className="type-data-xs text-text-2 font-bold">{gate.name}</span>
                     <span className="text-[10px] text-text-5 uppercase tracking-tighter">Lim: {gate.threshold}</span>
                  </div>
                  <div className="flex flex-col items-end">
                     <div className="flex items-center gap-1.5">
                        <span className={`type-data-xs font-bold ${gate.passed ? 'text-bull' : 'text-bear'}`}>{gate.value}</span>
                        {gate.passed ? <ShieldCheck size={12} className="text-bull" /> : <ShieldAlert size={12} className="text-bear" />}
                     </div>
                  </div>
               </div>
            ))}
         </div>

         {/* KILL SWITCH STATUS */}
         <div className={`p-3 rounded-sm border ${risk.portfolio.kill_switch_active ? 'bg-bear/10 border-bear/50' : 'bg-bull/10 border-bull/50'} transition-all`}>
            <div className="flex items-center justify-between mb-1">
               <span className="type-data-xs font-bold uppercase tracking-wider">Kill Switch</span>
               <div className={`w-2 h-2 rounded-full ${risk.portfolio.kill_switch_active ? 'bg-bear animate-pulse' : 'bg-bull'}`}></div>
            </div>
            <p className="text-[10px] text-text-4 leading-tight">
               {risk.portfolio.kill_switch_active ? 'Emergency stop active. Manual reset required.' : 'Circuit breakers armed. Monitoring all gates.'}
            </p>
         </div>
      </div>
    </div>
  );
};

export default RiskPanel;
