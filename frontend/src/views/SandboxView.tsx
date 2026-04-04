import React, { useState } from 'react';

const SandboxView = () => {
  const [location, setLocation] = useState('SUEZ');
  const [impact, setImpact] = useState('BLOCKADE');
  const [result, setResult] = useState<any>(null);

  const handleSimulate = async () => {
    const resp = await fetch('/api/sandbox/inject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location, impact })
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
                <span className="text-[10px]">PREDICTED GTFI IMPACT</span>
                <span className="text-bear font-bold">{result.predicted_gtfi_impact * 100}%</span>
              </div>
              <div className="flex justify-between items-center border-b border-border-1 pb-2">
                <span className="text-[10px]">CONFIDENCE</span>
                <span className="text-bull font-bold">{result.confidence}%</span>
              </div>
              <div className="pt-2">
                <p className="text-xs italic text-text-2">"{result.message}"</p>
              </div>
              <div className="pt-4">
                <span className="text-[10px] block mb-2">VULNERABLE TICKERS</span>
                <div className="flex gap-2">
                  {result.affected_tickers.map((t: string) => (
                    <span key={t} className="bg-surface-3 px-2 py-1 text-[10px] border border-border-1">{t}</span>
                  ))}
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
