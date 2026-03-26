import { useEffect, useRef, useState, useCallback } from 'react';
import { 
  useTerminalStore, 
  useSignalStore, 
  useVesselStore, 
  useFlightStore,
  useSatelliteStore
} from './store';
import { executeCommand } from './lib/commandEngine';
import type { ViewType } from './store/uiStore';

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
import EconomicsView from './views/EconomicsView';
import EarningsView from './views/EarningsView';
import PortfolioView from './views/PortfolioView';
import LaunchpadView from './views/LaunchpadView';
import NewsHubView from './views/NewsHubView';
import SettingsView from './views/SettingsView';
import HelpView from './views/HelpView';
import AlertsView from './views/AlertsView';
import WorkflowView from './views/WorkflowView';
import DarkPoolView from './views/DarkPoolView';
import InsiderView from './views/InsiderView';
import { useEquityStore } from './store/equityStore';

// Components
import Masthead from './components/Masthead';
import NavRail from './components/NavRail';
import IntelligenceFeed from './components/IntelligenceFeed';
import WatchlistPanel from './components/WatchlistPanel';
import GlobalGlobe from './components/GlobalGlobe';
import TerminalOutput from './components/TerminalOutput';
import { ErrorBoundary } from './components/ErrorBoundary';

const UI_LAYOUT = {
  activeView: 'satellite_feed' as ViewType,
  sidebarExpanded: true,
};

export default function TerminalApp() {
  const { selectedView, sidebarExpanded, setView } = useTerminalStore();
  const [command, setCommand] = useState('');
  const terminalRef = useRef<HTMLDivElement>(null);

  const { fetchSignals } = useSignalStore();
  const { fetchFlights } = useFlightStore();
  const { fetchVessels } = useVesselStore();
  const { fetchSatellites } = useSatelliteStore();

  // Global Data Induction for Terminal Parity
  useEffect(() => {
    fetchSignals();
    fetchFlights();
    fetchVessels();
    fetchSatellites();
    
    const interval = setInterval(() => {
      fetchSignals();
      fetchFlights();
      fetchVessels();
      fetchSatellites();
    }, 30000); // 30s refresh cycle
    
    return () => clearInterval(interval);
  }, [fetchSignals, fetchFlights, fetchVessels, fetchSatellites]);

  // Keyboard layout for Terminal Parity
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        // Focus search/command bar
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;
    
    // Virtual Engine Execution
    await executeCommand(command);
    
    setCommand('');
  };

  const renderView = () => {
    switch (selectedView) {
      case 'world':
        return <WorldView />;
      case 'charts':
        return <ChartView />;
      case 'matrix':
        return <SignalMatrix />;
      case 'satellite_feed':
        return <SatelliteFeed />;
      case 'global_equities':
        return <GlobalEquitiesView />;
      case 'terminal':
        return <RawTerminalMode />;
      case 'research':
        return <ResearchView />;
      case 'education':
        return <EducationView />;
      case 'news':
        return <NewsHubView />;
      case 'feed':
        return <FeedView />;
      case 'economics':
        return <EconomicsView />;
      case 'earnings':
        return <EarningsView />;
      case 'portfolio':
        return <PortfolioView />;
      case 'launchpad':
        return <LaunchpadView />;
      case 'alerts':
        return <AlertsView />;
      case 'workflow':
        return <WorkflowView />;
      case 'settings':
        return <SettingsView />;
      case 'dark_pools':
        return <DarkPoolView />;
      case 'insider':
        return <InsiderView />;
      case 'help':
        return <HelpView />;
      default:
        return <SatelliteFeed />;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-void text-text-1 overflow-hidden font-inter selection:bg-accent-primary selection:text-black">
      {/* GLOBAL BACKGROUND GLOBE (GPU ACCELERATED) */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-40">
        <GlobalGlobe />
      </div>

      <NavRail />

      <main className="flex-1 flex flex-col min-w-0 z-10 relative">
        <Masthead />
        
        <div className="flex-1 flex min-h-0">
          <div className="flex-1 flex flex-col min-w-0 border-r border-border-1 bg-void/40 backdrop-blur-sm">
            <div className="flex-1 min-h-0 overflow-hidden relative">
              <ErrorBoundary widgetName="Main View">
                {renderView()}
              </ErrorBoundary>
            </div>

            {/* COMMAND BAR — Bloomberg Command Line Interface */}
            <div className="h-12 bg-surface-base border-t border-border-1 flex items-center px-4 gap-4 shrink-0 shadow-2xl">
              <div className="flex items-center gap-2 text-accent-primary animate-pulse">
                <span className="type-data-xs font-bold font-mono">SAT-OS {'>'}</span>
              </div>
              <form onSubmit={handleCommand} className="flex-1">
                <input
                  type="text"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  placeholder="EX: .SENTINEL BRASKEM | .VAR PORTFOLIO_1 | .AIS ZIM_QUICK"
                  className="w-full bg-transparent border-none outline-none text-accent-primary type-data-sm placeholder:text-text-4/30 font-mono tracking-wider no-ring"
                />
              </form>
              <div className="flex items-center gap-4 text-text-4 font-mono text-[10px]">
                <span className="opacity-40">RSID: {Math.random().toString(16).slice(2, 8).toUpperCase()}</span>
                <span className="text-bull font-bold">● SYSTEM NOMINAL</span>
              </div>
            </div>
          </div>

          <aside className="w-96 flex flex-col shrink-0 bg-surface-base/80 backdrop-blur-md hidden xl:flex">
             <div className="flex-1 min-h-0 flex flex-col border-b border-border-1">
                <ErrorBoundary widgetName="Watchlist">
                  <WatchlistPanel />
                </ErrorBoundary>
             </div>
             <div className="flex-1 flex flex-col min-h-0 border-t border-border-1">
                <ErrorBoundary widgetName="Intelligence Feed">
                  <IntelligenceFeed />
                </ErrorBoundary>
             </div>
          </aside>
        </div>
      </main>

      {/* GLOBAL OVERLAYS */}
      <TerminalOutput />
    </div>
  );
}
