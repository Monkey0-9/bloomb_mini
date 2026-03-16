import { useEffect, useRef, useState } from 'react';
import { useTerminalStore, useSignalStore, useVesselStore, useFlightStore } from './store';
import { executeCommand } from './lib/commandEngine';

// Views
import WorldView from './views/WorldView';
import ChartView from './views/ChartView';
import SignalMatrix from './views/SignalMatrix';
import SatelliteFeed from './views/SatelliteFeed';
import GlobalEquitiesView from './views/GlobalEquitiesView';
import RawTerminalMode from './views/RawTerminalMode';
import ResearchView from './views/ResearchView';
import EducationView from './views/EducationView';
import FeedView from './views/FeedView';
import PlaceholderView from './views/PlaceholderView';
import EconomicsView from './views/EconomicsView';
import EarningsView from './views/EarningsView';
import PortfolioView from './views/PortfolioView';
import LaunchpadView from './views/LaunchpadView';
import NewsHubView from './views/NewsHubView';
import { useEquityStore } from './store/equityStore';

// Components
import Masthead from './components/Masthead';
import NavRail from './components/NavRail';
import SignalPanel from './components/SignalPanel';
import WatchlistPanel from './components/WatchlistPanel';
import RiskPanel from './components/RiskPanel';
import DataStrip from './components/DataStrip';
import AlertHub from './components/AlertHub';
import ExplainMode from './components/ExplainMode';
import NewsTicker from './components/NewsTicker';
import MissionControlPanel from './components/MissionControlPanel';

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
    <div 
      className="h-10 flex items-center px-4 shrink-0 z-floating relative"
      style={{ backgroundColor: 'var(--color-bg-surface)', borderTop: 'var(--border-terminal)' }}
    >
      <span 
        className="type-data-md font-bold mr-3 uppercase"
        style={{ color: 'var(--color-neon-bull)', fontFamily: 'var(--font-data)' }}
      >SATTRADE&gt;</span>
      <input 
        ref={inputRef}
        type="text" 
        onKeyDown={handleKeyDown}
        className="flex-1 bg-transparent border-none outline-none type-data-md" 
        style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-data)' }}
        placeholder="Type any ticker, port name, or command — press / to focus"
      />
      <div 
        className="flex gap-4 type-data-xs uppercase tracking-widest hidden md:flex"
        style={{ color: 'var(--color-text-dim)', fontFamily: 'var(--font-data)' }}
      >
        <span>↑↓ history</span>
        <span style={{ color: 'var(--color-text-dim)' }}>·</span>
        <span>TAB complete</span>
        <span style={{ color: 'var(--color-text-dim)' }}>·</span>
        <span>ESC clear</span>
      </div>
    </div>
  );
};

const App = () => {
  const { selectedView } = useTerminalStore();
  const { signals, fetchSignals } = useSignalStore();
  const { fetchVessels } = useVesselStore();
  const { fetchFlights } = useFlightStore();
  const { fetchEquities } = useEquityStore();
  const [isExplainOpen, setIsExplainOpen] = useState(false);

  useEffect(() => {
    fetchSignals();
    fetchVessels();
    fetchFlights();
    fetchEquities();
  }, [fetchSignals, fetchVessels, fetchFlights, fetchEquities]);

  useEffect(() => {
    const handleExplain = (e: any) => {
        if (e.detail?.command === 'TEACH ME') setIsExplainOpen(true);
    };
    window.addEventListener('terminal-command', handleExplain as any);
    return () => window.removeEventListener('terminal-command', handleExplain as any);
  }, []);

  return (
    <div 
      className="flex flex-col h-screen w-screen overflow-hidden selection:bg-accent-primary/30"
      style={{ backgroundColor: 'var(--color-bg-base)' }}
    >
      {/* ZONE A: MASTHEAD */}
      <Masthead />
      
      <div className="flex flex-1 overflow-hidden relative">
        {/* ZONE B: NAV RAIL */}
        <NavRail />
        
        {/* ZONE C: MAIN VIEWPORT */}
        <div className="flex-1 flex flex-col min-w-0 relative">
           <div 
             className="flex-1 relative flex overflow-hidden"
             style={{ backgroundColor: 'var(--color-bg-surface)' }}
           >
              {selectedView === 'world'     && <WorldView />}
              {selectedView === 'charts'    && <ChartView />}
              {selectedView === 'matrix'    && <SignalMatrix />}
              {selectedView === 'feed'      && <FeedView />}
              {selectedView === 'portfolio' && <PortfolioView />}
              {selectedView === 'economics' && <EconomicsView />}
              {selectedView === 'earnings'  && <EarningsView />}
              {selectedView === 'terminal'  && <RawTerminalMode />}
              {selectedView === 'research'  && <ResearchView />}
              {selectedView === 'settings'  && <PlaceholderView title="Terminal Settings" />}
              {selectedView === 'help'      && <PlaceholderView title="Documentation" />}
              {selectedView === 'education' && <EducationView />}
              {selectedView === 'launchpad' && <LaunchpadView />}
              {selectedView === 'news'      && <NewsHubView />}
              
              <ExplainMode 
                isOpen={isExplainOpen} 
                onClose={() => setIsExplainOpen(false)} 
                view={selectedView as any} 
              />
           </div>
           
           {/* ZONE F: DATA STRIP */}
           <DataStrip />

           {/* ZONE G: COMMAND LINE */}
           <CommandLine />
        </div>

        {/* INSTITUTIONAL SIDE PANELS */}
        <aside className="flex shrink-0">
           <div className="flex flex-col border-r w-[280px]" style={{ borderRight: 'var(--border-terminal)' }}>
              <MissionControlPanel />
              <SignalPanel />
           </div>
           
           {/* ZONE E: WATCHLIST & RISK PANEL */}
           <div 
             className="flex flex-col border-l"
             style={{ borderLeft: 'var(--border-terminal)' }}
           >
              <WatchlistPanel />
              <RiskPanel />
           </div>
        </aside>
      </div>

      <AlertHub />
    </div>
  );
};

export default App;
