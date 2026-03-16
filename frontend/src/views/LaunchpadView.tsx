import React from 'react';
import { motion } from 'framer-motion';
import WorldView from './WorldView';
import SignalMatrix from './SignalMatrix';
import EconomicsView from './EconomicsView';
import PortfolioView from './PortfolioView';

const WidgetFrame = ({ title, children, className = "" }: { title: string, children: React.ReactNode, className?: string }) => (
  <div 
    className={`flex flex-col border overflow-hidden bg-bg-surface ${className}`}
    style={{ borderColor: 'var(--color-border-subtle)', borderStyle: 'solid', borderWidth: '1px' }}
  >
    <div 
      className="h-8 flex items-center px-3 shrink-0 border-b flex justify-between"
      style={{ backgroundColor: 'var(--color-bg-muted)', borderColor: 'var(--color-border-subtle)' }}
    >
      <span className="type-data-xs font-bold uppercase tracking-widest">{title}</span>
      <div className="flex gap-2">
        <div className="w-2 h-2 rounded-full bg-neon-bull opacity-50" />
        <div className="w-2 h-2 rounded-full bg-text-dim opacity-30" />
      </div>
    </div>
    <div className="flex-1 relative overflow-hidden">
      {children}
    </div>
  </div>
);

const LaunchpadView = () => {
  return (
    <div className="flex-1 grid grid-cols-12 grid-rows-12 gap-1 p-1 bg-bg-base overflow-hidden">
      {/* Top Left: Alpha Surveillance */}
      <WidgetFrame title="Alpha Surveillance" className="col-span-8 row-span-7">
        <SignalMatrix />
      </WidgetFrame>

      {/* Top Right: Global Telemetry */}
      <WidgetFrame title="Global Telemetry" className="col-span-4 row-span-5">
        <WorldView />
      </WidgetFrame>

      {/* Middle Right: Macro Correlation */}
      <WidgetFrame title="Macro Correlation" className="col-span-4 row-span-7">
        <EconomicsView />
      </WidgetFrame>

      {/* Bottom Left: Portfolio Risk */}
      <WidgetFrame title="Portfolio Risk" className="col-span-8 row-span-5">
        <PortfolioView />
      </WidgetFrame>
    </div>
  );
};

export default LaunchpadView;
