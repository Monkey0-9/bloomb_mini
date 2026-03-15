import { useEffect, useRef, useState } from 'react';
import { useTerminalStore } from './store';
import { executeCommand } from './lib/commandEngine';

// Views
import WorldView from './views/WorldView';
import ChartView from './views/ChartView';
import SignalMatrix from './views/SignalMatrix';
import SatelliteFeed from './views/SatelliteFeed';
import GlobalEquitiesView from './views/GlobalEquitiesView';
import RawTerminalMode from './views/RawTerminalMode';

// Components
import Masthead from './components/Masthead';
import NavRail from './components/NavRail';
import SignalPanel from './components/SignalPanel';
import WatchlistPanel from './components/WatchlistPanel';
import DataStrip from './components/DataStrip';
import AlertHub from './components/AlertHub';
import ExplainMode from './components/ExplainMode';

const CommandLine = () => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleGlobalKeydown = (e: KeyboardEvent) => {
      if (e.key === '/' || e.key === ':') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleGlobalKeydown);
    return () => window.removeEventListener('keydown', handleGlobalKeydown);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      executeCommand(e.currentTarget.value);
      e.currentTarget.value = '';
    }
  };

  return (
    <div className="h-10 bg-surface-0 border-t border-border-3 flex items-center px-4 shrink-0 z-floating relative">
      <span className="type-data-md text-accent-primary font-bold mr-3 uppercase">SATTRADE&gt;</span>
      <input 
        ref={inputRef}
        type="text" 
        onKeyDown={handleKeyDown}
        className="flex-1 bg-transparent border-none outline-none type-data-md text-text-1 placeholder:text-text-4" 
        placeholder="Type any ticker, port name, or command — press / to focus"
      />
      <div className="flex gap-4 type-data-xs text-text-5 uppercase tracking-widest hidden md:flex">
        <span>↑↓ history</span>
        <span className="text-text-4">·</span>
        <span>TAB complete</span>
        <span className="text-text-4">·</span>
        <span>ESC clear</span>
      </div>
    </div>
  );
};

const App = () => {
  const { selectedView } = useTerminalStore();
  const [isExplainOpen, setIsExplainOpen] = useState(false);

  useEffect(() => {
    const handleExplain = (e: any) => {
        if (e.detail?.command === 'TEACH ME') setIsExplainOpen(true);
    };
    window.addEventListener('terminal-command', handleExplain as any);
    return () => window.removeEventListener('terminal-command', handleExplain as any);
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-void overflow-hidden selection:bg-accent-primary/30">
      {/* ZONE A: MASTHEAD */}
      <Masthead />
      
      <div className="flex flex-1 overflow-hidden relative">
        {/* ZONE B: NAV RAIL */}
        <NavRail />
        
        {/* ZONE C: MAIN VIEWPORT */}
        <div className="flex-1 flex flex-col min-w-0 relative">
           <div className="flex-1 relative flex overflow-hidden bg-surface-0">
              {selectedView === 'world' && <WorldView />}
              {selectedView === 'charts' && <ChartView />}
              {selectedView === 'matrix' && <SignalMatrix />}
              {selectedView === 'feed' && <SatelliteFeed />}
              {selectedView === 'portfolio' && <GlobalEquitiesView />}
              {selectedView === 'terminal' && <RawTerminalMode />}
              
              <ExplainMode 
                isOpen={isExplainOpen} 
                onClose={() => setIsExplainOpen(false)} 
                view={selectedView} 
              />
           </div>
           
           {/* ZONE F: DATA STRIP */}
           <DataStrip />

           {/* ZONE G: COMMAND LINE */}
           <CommandLine />
        </div>

        {/* INSTITUTIONAL SIDE PANELS */}
        <aside className="flex shrink-0">
           {/* ZONE D: SIGNAL PANEL */}
           <SignalPanel />
           {/* ZONE E: WATCHLIST PANEL */}
           <WatchlistPanel />
        </aside>
      </div>

      <AlertHub />
    </div>
  );
};

export default App;
