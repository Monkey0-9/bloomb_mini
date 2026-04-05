import React, { useState } from 'react';

const SandboxView = () => {
  const [location, setLocation] = useState('SUEZ');
  const [impact, setImpact] = useState('BLOCKADE');
  const [result, setResult] = useState<any>(null);

  const handleSimulate = async () => {
    const resp = await fetch('/api/sandbox/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        title: `${impact} at ${location}`,
        location_id: location.toLowerCase(), 
        severity: impact === 'BLOCKADE' ? 0.9 : 0.4
      })
    });
    const data = await resp.json();
    setResult(data);
  };

  return (
    <div className="p-8 font-mono text-accent-primary bg-void h-full overflow-y-auto">
      <h1 className="text-2xl font-bold mb-4">MIROFISH DIGITAL SANDBOX</h1>
      <p className="text-xs text-text-4 mb-8">Inject variables into the parallel digital swarm to rehearse the future.</p>

      <div className="grid grid-cols-2 gap-8">
        <div className="bg-surface-base p-6 border border-border-1">
          <h2 className="text-sm font-bold mb-4 uppercase">Variable Injection</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] uppercase mb-1">Target Location</label>
              <select 
                value={location} 
                onChange={(e) => setLocation(e.target.value)}
                className="w-full bg-void border border-border-1 p-2 text-xs outline-none"
              >
                <option value="SUEZ">Suez Canal</option>
                <option value="HORMUZ">Strait of Hormuz</option>
                <option value="MALACCA">Malacca Strait</option>
                <option value="PANAMA">Panama Canal</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase mb-1">Impact Type</label>
              <select 
                value={impact} 
                onChange={(e) => setImpact(e.target.value)}
                className="w-full bg-void border border-border-1 p-2 text-xs outline-none"
              >
                <option value="BLOCKADE">Full Blockade</option>
                <option value="CONGESTION">Heavy Congestion</option>
                <option value="STRIKE">Military Strike</option>
                <option value="SEISMIC">Seismic Event</option>
              </select>
            </div>

            <button 
              onClick={handleSimulate}
              className="w-full bg-accent-primary text-void font-bold py-2 mt-4 hover:bg-white transition-colors"
            >
              RUN PARALLEL SIMULATION
            </button>
          </div>
        </div>

        <div className="bg-surface-base p-6 border border-border-1">
          <h2 className="text-sm font-bold mb-4 uppercase">Simulation Outcome</h2>
          
          {result ? (
            <div className="space-y-4 animate-in fade-in">
              <div className="flex justify-between items-center border-b border-border-1 pb-2">
                <span className="text-[10px]">PREDICTED GTFI SHIFT</span>
                <span className={result.predicted_gtfi_shift < 0 ? "text-bear font-bold" : "text-bull font-bold"}>
                    {(result.predicted_gtfi_shift * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center border-b border-border-1 pb-2">
                <span className="text-[10px]">SWARM CONSENSUS</span>
                <span className="text-white font-bold">{result.swarm_forecast.action}</span>
              </div>
              
              <div className="pt-2">
                <h3 className="text-[10px] uppercase mb-2 text-text-3">Graph Reasoning</h3>
                <p className="text-xs italic text-text-2">
                  {result.graph_impact?.reasoning || "No direct graph path identified for this location."}
                </p>
              </div>

              <div className="pt-4">
                <span className="text-[10px] block mb-2 uppercase text-text-3">Affected Tickers</span>
                <div className="flex flex-wrap gap-2">
                  {result.graph_impact?.affected_tickers?.map((t: any) => (
                    <div key={t.ticker} className="bg-slate-900 border border-border-1 px-2 py-1 flex flex-col min-w-[60px]">
                        <span className="text-[10px] font-bold text-accent-primary">{t.ticker}</span>
                        <span className={`text-[8px] ${t.impact_score < 0 ? "text-bear" : "text-bull"}`}>
                            {t.impact_score.toFixed(3)}
                        </span>
                    </div>
                  )) || <span className="text-[10px] text-text-4 italic">No high-confidence ticker impacts detected.</span>}
                </div>
              </div>

              <div className="pt-4 border-t border-border-1">
                 <h3 className="text-[10px] uppercase mb-2 text-text-3">Swarm Insight</h3>
                 <div className="bg-white/5 p-3 rounded-sm">
                    <p className="text-[11px] text-slate-300 leading-relaxed">
                        {result.swarm_forecast.prediction}
                    </p>
                 </div>
              </div>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center border border-dashed border-border-1">
              <span className="text-[10px] text-text-4">NO ACTIVE SIMULATION</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SandboxView;
