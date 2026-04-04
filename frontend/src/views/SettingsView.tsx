import React from 'react';
import { Settings, Shield, User, Bell, Cpu, Zap, Lock, Globe, Database } from 'lucide-react';

const SettingsSection = ({ title, icon: Icon, children }: any) => (
  <div className='mb-10 animate-in fade-in slide-in-from-bottom-2 duration-500'>
    <div className='flex items-center gap-2 mb-4 border-b border-border-ghost pb-2'>
      <Icon size={16} className='text-accent-primary' />
      <h3 className='type-h3 text-xs uppercase tracking-[0.2em] text-text-0'>{title}</h3>
    </div>
    <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
      {children}
    </div>
  </div>
);

const SettingItem = ({ label, description, action, value, children }: any) => (
  <div className='bg-surface-1 border border-border-2 p-4 hover:border-accent-primary/50 transition-colors group'>
    <div className='flex justify-between items-start mb-2'>
      <div className='flex flex-col flex-1'>
        <span className='type-ui-sm font-bold text-text-1 group-hover:text-accent-primary transition-colors'>{label}</span>
        <span className='type-ui-xs text-text-4 mt-1 leading-relaxed'>{description}</span>
      </div>
      <div className='type-data-xs px-2 py-0.5 border border-border-2 text-text-3 font-mono ml-4 shrink-0'>
        {value}
      </div>
    </div>
    {children}
    <button className='mt-2 w-full py-1.5 bg-surface-2 border border-border-2 hover:bg-accent-primary hover:text-void transition-all uppercase type-data-xs font-bold tracking-widest'>
      {action}
    </button>
  </div>
);

const SettingsView = () => {
  const [profile, setProfile] = React.useState<any>(null);
  const [sensitivity, setSensitivity] = React.useState(2.0);

  React.useEffect(() => {
    fetch('/api/profile')
      .then(r => r.json())
      .then(setProfile)
      .catch(console.error);
  }, []);

  return (
    <div className='flex-1 h-full bg-void overflow-y-auto custom-scrollbar'>
      <div className='max-w-5xl mx-auto px-8 py-12'>
        {/* PROFILE SECTION */}
        <div className='mb-12 bg-surface-1 border border-accent-primary/20 p-6 flex items-center justify-between'>
            <div className='flex items-center gap-6'>
                <div className='w-16 h-16 bg-accent-primary/10 border border-accent-primary flex items-center justify-center text-accent-primary'>
                    <User size={32} />
                </div>
                <div>
                    <h2 className='text-xl font-bold text-white mb-1 uppercase tracking-widest'>{profile?.username || 'LOADING...'}</h2>
                    <div className='flex gap-4 text-[10px] font-mono text-text-4 uppercase'>
                        <span>Role: <span className='text-accent-primary'>{profile?.role}</span></span>
                        <span>Tier: <span className='text-bull'>{profile?.tier}</span></span>
                        <span>Joined: {profile?.joined}</span>
                    </div>
                </div>
            </div>
            <div className='flex gap-8 text-right pr-4'>
                <div>
                    <div className='text-[9px] text-text-5 uppercase tracking-widest'>Queries</div>
                    <div className='text-lg font-bold text-white font-mono'>{profile?.stats?.queries_run || 0}</div>
                </div>
                <div>
                    <div className='text-[9px] text-text-5 uppercase tracking-widest'>Alpha BPS</div>
                    <div className='text-lg font-bold text-bull font-mono'>+{profile?.stats?.alpha_captured_bps || 0}</div>
                </div>
            </div>
        </div>

        {/* HEADER */}
        <div className='mb-12 border-l-4 border-accent-primary pl-6'>
          <div className='flex items-center gap-3 mb-2'>
             <Settings size={20} className='text-accent-primary animate-spin-slow' />
             <h1 className='type-h1 text-2xl tracking-[0.1em] text-white uppercase'>Terminal Configuration</h1>
          </div>
          <p className='type-ui-md text-text-3 max-w-2xl font-sans'>
            Manage your institutional connectivity, risk parameters, and AI-grounding preferences. 
            All changes are logged to the audit kernel.
          </p>
        </div>

        <SettingsSection title='Identity & Security' icon={Shield}>
          <SettingItem 
            label='API Credentialing' 
            description='Manage your RS256 private keys and OAuth2 tokens for data ingestors.'
            action='MANAGE KEYS'
            value='ACTIVE'
          />
          <SettingItem 
            label='Two-Person Rule' 
            description='Require dual approval for all high-notional trades and system halts.'
            action='CONFIGURE'
            value='ENFORCED'
          />
        </SettingsSection>

        <SettingsSection title='Intelligence Engine' icon={Cpu}>
          <SettingItem 
            label='LLM Grounding' 
            description='Toggle real-time grounding between Sentinel-2, AIS, and ADS-B datasets.'
            action='CALIBRATE'
            value='STAC+AIS'
          >
            <div className='flex gap-2 mt-1 mb-2'>
              {['STAC+AIS', 'SENTINEL-1', 'OSINT-ONLY'].map(v => (
                <button key={v} className='text-[8px] px-2 py-0.5 border border-border-2 hover:border-accent-primary transition-all uppercase font-mono'>
                  {v}
                </button>
              ))}
            </div>
          </SettingItem>
          <SettingItem 
            label='Signal Sensitivity' 
            description='Adjust the ICIR (Information Coefficient) threshold for automated alerts.'
            action='SAVE PARAMETERS'
            value={`σ > ${sensitivity.toFixed(1)}`}
          >
            <div className='mt-2 mb-4'>
              <input 
                type="range" 
                min="0.5" 
                max="5.0" 
                step="0.1" 
                value={sensitivity} 
                onChange={(e) => setSensitivity(parseFloat(e.target.value))}
                className="w-full h-1 bg-surface-2 appearance-none cursor-pointer accent-accent-primary"
              />
              <div className='flex justify-between text-[8px] font-mono text-text-5 mt-1 uppercase'>
                <span>Aggressive</span>
                <span>Balanced</span>
                <span>Conservative</span>
              </div>
            </div>
          </SettingItem>
        </SettingsSection>

        <SettingsSection title='Data Connectivity' icon={Globe}>
          <SettingItem 
            label='Sentinel Hub' 
            description='Sentinel-1 SAR and Sentinel-2 Multi-spectral imagery ingest status.'
            action='STATUS'
            value='CONNECTED'
          />
          <SettingItem 
            label='NASA FIRMS' 
            description='Thermal anomaly detection feed for global industrial monitoring.'
            action='REFRESH'
            value='LIVE'
          />
        </SettingsSection>

        <SettingsSection title='Risk Parameters' icon={Lock}>
          <SettingItem 
            label='Gross Exposure Limit' 
            description='Maximum portfolio notional relative to NAV (Investment Committee Policy).'
            action='EDIT'
            value='150%'
          />
          <SettingItem 
            label='Kill-Switch Logic' 
            description='Automatic system halt on VaR (Value at Risk) breach of 2.0%.'
            action='TEST'
            value='ENABLED'
          />
        </SettingsSection>

      </div>
    </div>
  );
};

export default SettingsView;