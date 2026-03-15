import { useState, useEffect } from 'react';
import { Ship, ShoppingCart, Factory, Clock, Radio } from 'lucide-react';
import { motion } from 'framer-motion';

const Sparkline = ({ color }: { color: string }) => {
  const points = [10, 25, 15, 40, 30, 55, 45, 70, 60, 85].map((val, i) => `${i * 10},${100 - val}`).join(' ');
  return (
    <svg className="w-full h-8 overflow-visible" viewBox="0 0 90 100" preserveAspectRatio="none">
      <motion.polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        points={points}
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 1.5, ease: "easeInOut" }}
      />
    </svg>
  );
};

const SignalCard = ({ 
  icon: Icon, 
  title, 
  status, 
  score, 
  ic, 
  icir, 
  n, 
  equities,
  timestamp,
  persona 
}: any) => {
  const isBull = status === 'BULLISH';
  const statusColor = isBull ? 'text-bull' : status === 'BEARISH' ? 'text-bear' : 'text-neutral';
  const glowClass = isBull ? 'glow-bull' : status === 'BEARISH' ? 'glow-bear' : '';

  return (
    <div className="p-4 border-b border-white/5 group hover:bg-surface-2/40 transition-all duration-300 cursor-pointer overflow-hidden">
      {/* TOP ROW: SIGNAL IDENTITY */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-void border border-white/10 rounded-sm">
            <Icon size={14} className="text-accent-primary group-hover:glow-primary transition-all" />
          </div>
          <span className="type-h1 text-[13px] text-text-1 tracking-widest">{title}</span>
        </div>
        <div className={`px-2 py-0.5 rounded-sm border type-data-xs font-bold tracking-[0.1em] ${
          isBull ? 'bg-bull/10 border-bull/40 text-bull' : 
          status === 'BEARISH' ? 'bg-bear/10 border-bear/40 text-bear' : 
          'bg-white/5 border-white/10 text-text-4'
        }`}>
          {status}
        </div>
      </div>

      {/* HERO NUMBER + SPARKLINE */}
      <div className="flex items-end justify-between mb-4">
        <div>
          <div className={`type-data-hero text-[38px] ${statusColor} ${glowClass} leading-none tracking-tighter`}>
            {score}
          </div>
          <div className="type-data-xs text-text-4 uppercase tracking-widest mt-1">Sigma Δ (12m)</div>
        </div>
        <div className="w-24">
          <Sparkline color={isBull ? '#00FF9D' : '#FF3D3D'} />
        </div>
      </div>

      {/* SEGMENTED STRENGTH BAR */}
      <div className="mb-4 bg-void/50 p-2 border border-white/5 rounded-sm">
        <div className="flex justify-between text-[9px] uppercase tracking-widest text-text-4 mb-2">
          <span>Signal Strength</span>
          <span className={`type-data-xs ${statusColor}`}>Intensity 0.74</span>
        </div>
        <div className="segment-bar">
          {Array.from({ length: 20 }).map((_, i) => (
            <div 
              key={i} 
              className={`segment ${i < 14 ? (isBull ? 'active-bull' : 'active-bear') : ''}`}
            />
          ))}
        </div>
      </div>

      {/* THREE-COLUMN STATS */}
      <div className="grid grid-cols-3 gap-0.5 mb-4 bg-white/5 border border-white/5 rounded-sm overflow-hidden text-center">
        <div className="py-2 flex flex-col items-center">
          <span className="type-data-md text-text-1">{ic}</span>
          <span className="type-data-xs text-text-4 uppercase tracking-tighter">IC</span>
        </div>
        <div className="py-2 flex flex-col items-center border-x border-white/5">
          <span className="type-data-md text-text-1">{icir}</span>
          <span className="type-data-xs text-text-4 uppercase tracking-tighter">ICIR</span>
        </div>
        <div className="py-2 flex flex-col items-center">
          <span className="type-data-md text-text-1">{n}</span>
          <span className="type-data-xs text-text-4 uppercase tracking-tighter">Obs</span>
        </div>
      </div>

      {/* AFFECTED EQUITIES */}
      <div className="space-y-2">
        <span className="type-data-xs text-text-4 block tracking-widest uppercase mb-2">Top Proxy Equities</span>
        {equities.map((eq: any) => (
          <div key={eq.ticker} className="flex items-center justify-between group/row">
            <div className="flex items-center gap-2">
              <span className="type-data-md text-accent-primary font-bold w-12">{eq.ticker}</span>
              <span className="type-ui-sm text-text-3 truncate max-w-[110px] group-hover/row:text-text-1 transition-colors">{eq.name}</span>
            </div>
            <div className="flex items-center gap-2">
               <div className="w-12 h-1 bg-white/5 rounded-[1px] overflow-hidden">
                  <div className={`h-full ${eq.dir === 'up' ? 'bg-bull' : 'bg-bear'} w-[80%]`} />
               </div>
               <span className={`type-data-xs font-bold ${eq.dir === 'up' ? 'text-bull' : 'text-bear'}`}>{eq.dir === 'up' ? '↑' : '↓'}</span>
            </div>
          </div>
        ))}
      </div>

      {/* FOOTER */}
      <div className="mt-4 pt-3 border-t border-white/5 flex justify-between items-center type-data-xs">
        <div className="flex items-center gap-1.5 text-text-5">
          <Clock size={10} />
          <span>Ingested {timestamp} ago</span>
        </div>
        <div className="flex items-center gap-1.5 text-bull">
          <Radio size={10} className="dot-live" />
          <span>Active Ingest</span>
        </div>
      </div>
    </div>
  );
};

const SignalPanel = () => {
  const [signals, setSignals] = useState<any[]>([
    {
      id: 'S1',
      icon: Ship,
      title: 'MAERSK/ZIM CORRIDOR',
      status: 'BULLISH',
      score: 84,
      ic: 0.047,
      icir: 0.62,
      n: 1420,
      timestamp: '2m',
      equities: [
        { ticker: 'AMKBY', name: 'Maersk Adr', dir: 'up' },
        { ticker: 'ZIM', name: 'Zim Integrated', dir: 'up' },
        { ticker: 'COSCO', name: 'Cosco Shipping', dir: 'up' }
      ]
    },
    {
      id: 'S2',
      icon: ShoppingCart,
      title: 'US RETAIL VELOCITY',
      status: 'BEARISH',
      score: 12,
      ic: 0.038,
      icir: 0.45,
      n: 842,
      timestamp: '5m',
      equities: [
        { ticker: 'WMT', name: 'Walmart Inc', dir: 'down' },
        { ticker: 'TGT', name: 'Target Corp', dir: 'down' }
      ]
    }
  ]);

  return (
    <div className="w-[320px] h-full bg-surface-1 border-r border-white/5 flex flex-col overflow-hidden shrink-0 z-raised relative">
      <div className="p-4 border-b border-white/10 flex justify-between items-center bg-surface-0/30">
        <div className="flex flex-col">
          <span className="type-h1 text-sm tracking-widest text-accent-primary glow-text-primary">SIGNAL ALPHA</span>
          <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Live Telemetry</span>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-bull/10 border border-bull/20 rounded-sm">
           <Radio size={12} className="text-bull dot-live" />
           <span className="type-data-xs text-bull font-bold uppercase tracking-wider">HFT Active</span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {signals.map(s => (
          <SignalCard key={s.id} {...s} />
        ))}
      </div>

      <div className="p-4 bg-void/50 border-t border-white/5">
         <button className="w-full py-2 bg-accent-primary/10 border border-accent-primary/20 text-accent-primary type-data-xs font-bold uppercase tracking-[0.2em] rounded-sm hover:bg-accent-primary/20 transition-all">
            Open Score Matrix
         </button>
      </div>
    </div>
  );
};

export default SignalPanel;

