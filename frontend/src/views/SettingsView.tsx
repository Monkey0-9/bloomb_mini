import React from 'react';
import { Settings, Shield, User, Bell, Cpu, Zap, Lock, Globe, Database } from 'lucide-react';

const SettingsSection = ({ title, icon: Icon, children }: any) => (
  <div className="mb-10 animate-in fade-in slide-in-from-bottom-2 duration-500">
    <div className="flex items-center gap-2 mb-4 border-b border-border-ghost pb-2">
      <Icon size={16} className="text-accent-primary" />
      <h3 className="type-h3 text-xs uppercase tracking-[0.2em] text-text-0">{title}</h3>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {children}
    </div>
  </div>
);

const SettingItem = ({ label, description, action, value }: any) => (
  <div className="bg-surface-1 border border-border-2 p-4 hover:border-accent-primary/50 transition-colors group">
    <div className="flex justify-between items-start mb-2">
      <div className="flex flex-col">
        <span className="type-ui-sm font-bold text-text-1 group-hover:text-accent-primary transition-colors">{label}</span>
        <span className="type-ui-xs text-text-4 mt-1 leading-relaxed">{description}</span>
      </div>
      <div className="type-data-xs px-2 py-0.5 border border-border-2 text-text-3 font-mono">
        {value}
      </div>
    </div>
    <button className="mt-2 w-full py-1.5 bg-surface-2 border border-border-2 hover:bg-accent-primary hover:text-void transition-all uppercase type-data-xs font-bold tracking-widest">
      {action}
    </button>
  </div>
);

const SettingsView = () => {
  return (
    <div className="flex-1 h-full bg-void overflow-y-auto custom-scrollbar">
      <div className="max-w-5xl mx-auto px-8 py-12">
        {/* HEADER */}
        <div className="mb-12 border-l-4 border-accent-primary pl-6">
          <div className="flex items-center gap-3 mb-2">
             <Settings size={20} className="text-accent-primary animate-spin-slow" />
             <h1 className="type-h1 text-2xl tracking-[0.1em] text-white uppercase">Terminal Configuration</h1>
          </div>
          <p className="type-ui-md text-text-3 max-w-2xl font-sans">
            Manage your institutional connectivity, risk parameters, and AI-grounding preferences. 
            All changes are logged to the audit kernel.
          </p>
        </div>

        <SettingsSection title="Identity & Security" icon={Shield}>
          <SettingItem 
            label="API Credentialing" 
            description="Manage your RS256 private keys and OAuth2 tokens for data ingestors."
            action="MANAGE KEYS"
            value="ACTIVE"
          />
          <SettingItem 
            label="Two-Person Rule" 
            description="Require dual approval for all high-notional trades and system halts."
            action="CONFIGURE"
            value="ENFORCED"
          />
        </SettingsSection>

        <SettingsSection title="Intelligence Engine" icon={Cpu}>
          <SettingItem 
            label="LLM Grounding" 
            description="Toggle real-time grounding between Sentinel-2, AIS, and ADS-B datasets."
            action="CALIBRATE"
            value="STAC+AIS"
          />
          <SettingItem 
            label="Signal Sensitivity" 
            description="Adjust the ICIR (Information Coefficient) threshold for automated alerts."
            action="ADJUST ρ"
            value="σ > 2.0"
          />
        </SettingsSection>

        <SettingsSection title="Data Connectivity" icon={Globe}>
          <SettingItem 
            label="Sentinel Hub" 
            description="Sentinel-1 SAR and Sentinel-2 Multi-spectral imagery ingest status."
            action="STATUS"
            value="CONNECTED"
          />
          <SettingItem 
            label="NASA FIRMS" 
            description="Thermal anomaly detection feed for global industrial monitoring."
            action="REFRESH"
            value="LIVE"
          />
        </SettingsSection>

        <SettingsSection title="Risk Parameters" icon={Lock}>
          <SettingItem 
            label="Gross Exposure Limit" 
            description="Maximum portfolio notional relative to NAV (Investment Committee Policy)."
            action="EDIT"
            value="150%"
          />
          <SettingItem 
            label="Kill-Switch Logic" 
            description="Automatic system halt on VaR (Value at Risk) breach of 2.0%."
            action="TEST"
            value="ENABLED"
          />
        </SettingsSection>

      </div>
    </div>
  );
};

export default SettingsView;
