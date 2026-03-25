import React from 'react';
import { HelpCircle, Book, Code, Terminal, Zap, Shield, Globe, Search } from 'lucide-react';

const HelpCard = ({ title, icon: Icon, items }: any) => (
  <div className="bg-surface-1 border border-border-2 p-6 hover:border-accent-primary/40 transition-all group animate-in slide-in-from-right-4 duration-500">
    <div className="flex items-center gap-3 mb-4">
      <div className="p-2 bg-surface-2 border border-border-ghost group-hover:bg-accent-primary group-hover:text-void transition-colors">
        <Icon size={18} />
      </div>
      <h3 className="type-h3 text-xs uppercase tracking-widest text-text-0">{title}</h3>
    </div>
    <ul className="space-y-3">
      {items.map((item: string, i: number) => (
        <li key={i} className="flex items-start gap-2 group/item">
          <div className="w-1 h-1 rounded-full bg-accent-primary mt-1.5 shrink-0 opacity-40 group-hover/item:opacity-100 transition-opacity" />
          <span className="type-ui-xs text-text-3 font-mono leading-tight group-hover/item:text-text-1 transition-colors">{item}</span>
        </li>
      ))}
    </ul>
  </div>
);

const HelpView = () => {
  return (
    <div className="flex-1 h-full bg-void overflow-y-auto custom-scrollbar">
      <div className="max-w-6xl mx-auto px-8 py-12">
        
        {/* HERO SECTION */}
        <div className="mb-16 border-b border-border-ghost pb-10">
          <div className="flex items-center gap-4 mb-4">
             <HelpCircle size={28} className="text-accent-primary" />
             <h1 className="type-h1 text-3xl tracking-[0.2em] text-white uppercase">Intelligence Documentation</h1>
          </div>
          <p className="type-ui-lg text-text-3 max-w-3xl font-sans leading-relaxed">
            Welcome to the SatTrade Kernel. This terminal uses a hybrid-intelligence approach 
            fusing Earth Observation (EO) telemetry with quantitative risk engines. 
            Below is the command reference for institutional operation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          <HelpCard 
            title="Navigation Commands" 
            icon={Zap}
            items={[
              "/NAV charts — Price action visualization",
              "/NAV matrix — Multi-signal correlation",
              "/NAV world — Global orbital visualizer",
              "/NAV risk — Portfolio health check",
              "/NAV portfolio — Position management"
            ]}
          />

          <HelpCard 
            title="Intelligence Queries" 
            icon={Search}
            items={[
              "/SIGNAL [TICKER] — Unified alpha score",
              "/THERMAL [LAT,LON] — FIRMS anomaly fetch",
              "/VESSEL [MMSI] — AIS + SAR dark analysis",
              "CTRL+K — Interactive AI analyst (LLM)",
              "/ALERT CREATE [PARAMS] — Smart alerts"
            ]}
          />

          <HelpCard 
            title="Institutional Logic" 
            icon={Shield}
            items={[
              "P99 VaR — Value at Risk computation",
              "Spearman ρ — Macro lag analysis",
              "TFT Median — P50 probability forecast",
              "RS256 Signing — Secure kernel directive",
              "Kill-Switch — Emergency system halt"
            ]}
          />

          <HelpCard 
            title="Data Sources" 
            icon={Globe}
            items={[
              "Sentinel-1 SAR — Dark vessel detection",
              "Sentinel-2 MSI — High-res optical",
              "Landsat TIRS — Industrial thermal",
              "ADS-B / OpenSky — Aviation tracking",
              "AIS Hub — Maritime transponders"
            ]}
          />

          <HelpCard 
            title="System Architecture" 
            icon={Terminal}
            items={[
              "Node/React 18 — High-fidelity UI",
              "FastAPI — Async Python kernel",
              "Redis — Global message bus",
              "SQLite — Audit & metadata cache",
              "Claude 4.6 — Reasoning engine"
            ]}
          />

          <HelpCard 
            title="Getting Started" 
            icon={Book}
            items={[
              "Connect trading API keys in Settings",
              "Enable Top-Tier orbital layers on Globe",
              "Verify signal calibration in Matrix",
              "Review IC guidelines in Docs",
              "Join institutional Slack channel"
            ]}
          />

        </div>

        {/* FOOTER CALLOUT */}
        <div className="mt-16 p-8 bg-surface-1 border border-border-2 text-center relative overflow-hidden group">
            <div className="absolute inset-0 bg-accent-primary/5 -translate-x-full group-hover:translate-x-0 transition-transform duration-1000" />
            <h4 className="type-h3 text-white mb-2 relative z-10">NEED CUSTOM LOGIC?</h4>
            <p className="type-ui-sm text-text-4 max-w-xl mx-auto mb-6 relative z-10">
              Our engineering team can deploy custom SAR detection models or private data ingestors 
              within your dedicated instance.
            </p>
            <button className="px-8 py-2 bg-accent-primary text-void font-bold uppercase type-data-sm tracking-widest hover:scale-105 transition-transform relative z-10">
                CONTACT INSTITUTIONAL SUPPORT
            </button>
        </div>

      </div>
    </div>
  );
};

export default HelpView;
