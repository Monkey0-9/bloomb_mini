import { motion } from 'framer-motion';

const PlaceholderView = ({ title }: { title: string }) => {
  return (
    <div className="flex-1 flex flex-col bg-surface-0 overflow-hidden select-none">
      {/* HEADER */}
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
        <div className="flex items-center gap-2">
           <span className="type-h1 text-sm tracking-[0.2em] text-text-0 uppercase">{title}</span>
        </div>
        <div className="flex gap-4 type-data-xs text-text-5 uppercase tracking-widest">
           <span>ST-ID: 8842-X</span>
           <span>SEC: LEVEL-4</span>
        </div>
      </div>

      {/* CONTENT */}
      <div className="flex-1 p-8 flex flex-col items-center justify-center text-center">
        <div className="max-w-md">
          <div className="w-16 h-16 rounded-full bg-accent-primary/5 border border-accent-primary/20 flex items-center justify-center mb-8 mx-auto">
            <div className="w-2 h-2 rounded-full bg-accent-primary dot-live"></div>
          </div>
          <h2 className="type-h1 text-xl mb-4 text-text-0 tracking-[0.3em] uppercase">ACCESS RESTRICTED</h2>
          <p className="type-data-md text-text-4 mb-10 uppercase tracking-widest leading-loose">
            The <span className="text-accent-primary">{title}</span> module is currently undergoing institutional validation. Access is limited to Platinum Tier satellite telemetry partners.
          </p>
          
          <div className="h-[1px] w-full bg-white/5 mb-8"></div>
          
          <div className="grid grid-cols-2 gap-8 text-left">
            <div className="flex flex-col">
              <span className="type-data-xs text-text-5 uppercase mb-1">Provisioning Status</span>
              <span className="type-data-md text-bull font-bold uppercase tracking-widest">Active Pulse</span>
            </div>
            <div className="flex flex-col">
              <span className="type-data-xs text-text-5 uppercase mb-1">Last Handshake</span>
              <span className="type-data-md text-text-2 font-bold uppercase tracking-widest">0.82ms ago</span>
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <div className="h-8 border-t border-border-ghost flex items-center px-4 bg-void shrink-0">
        <span className="type-data-xs text-text-5 uppercase tracking-[0.2em]">Institutional Core <span className="text-text-4">v2.1.4</span></span>
      </div>
    </div>
  );
};

export default PlaceholderView;
