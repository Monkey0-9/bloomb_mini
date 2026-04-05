import { useEffect, useRef, useState } from 'react';
import { 
  useTerminalStore, 
  useSignalStore, 
  useVesselStore, 
  useFlightStore,
  useSatelliteStore
} from './store';
import { useEquityStore } from './store/equityStore';
import { ErrorBoundary } from './components/ErrorBoundary';
import { connectLive } from './api/client';

// Views
import WorldView from './views/WorldView';
import ChartView from './views/ChartView';
import SignalMatrix from './views/SignalMatrix';
import SatelliteFeed from './views/SatelliteFeed';
import GlobalEquitiesView from './views/GlobalEquitiesView';
import RawTerminalMode from './views/RawTerminalMode';
import ResearchView from './views/ResearchView';
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
import WarRoomView from './views/WarRoomView';
import SandboxView from './views/SandboxView';
import GodModeView from './views/GodModeView';

// Components
import Masthead from './components/Masthead';
import NavRail from './components/NavRail';
import IntelligenceFeed from './components/IntelligenceFeed';
import WatchlistPanel from './components/WatchlistPanel';
import GlobalGlobe from './components/GlobalGlobe';
import TerminalOutput from './components/TerminalOutput';
import IntelligenceDetails from './components/IntelligenceDetails';
import AlertHub from './components/AlertHub';

export default function TerminalApp() {
  const { selectedView, setView } = useTerminalStore();
  const { fetchSignals, fetchSatFeed, fetchWorkflows } = useSignalStore();
  const { fetchEquities } = useEquityStore();
  const { fetchFlights } = useFlightStore();
  const { fetchVessels } = useVesselStore();
  const { fetchSatellites } = useSatelliteStore();
  const { handleWSUpdate: handleSignalWS } = useSignalStore();
  const { handleWSUpdate: handleVesselWS } = useVesselStore();

  useEffect(() => {
    // Initial induction
    const fetchData = () => {
      fetchSignals();
      fetchSatFeed();
      fetchWorkflows();
      fetchEquities();
      fetchFlights();
      fetchVessels();
      fetchSatellites();
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    
    // Connect live WebSocket
    const unsub = connectLive((data) => {
        handleSignalWS(data);
        handleVesselWS(data);
    });

    return () => {
        clearInterval(interval);
        unsub();
    };
  }, [fetchSignals, fetchSatFeed, fetchWorkflows, fetchEquities, fetchFlights, fetchVessels, fetchSatellites]);


  const renderView = () => {
    switch (selectedView) {
      case 'world':           return <WorldView />;
      case 'charts':          return <ChartView />;
      case 'matrix':          return <SignalMatrix />;
      case 'satellite_feed':  return <SatelliteFeed />;
      case 'global_equities': return <GlobalEquitiesView />;
      case 'terminal':        return <RawTerminalMode />;
      case 'research':        return <ResearchView />;
      case 'news':            return <NewsHubView />;
      case 'feed':            return <FeedView />;
      case 'economics':       return <EconomicsView />;
      case 'earnings':        return <EarningsView />;
      case 'portfolio':       return <PortfolioView />;
      case 'launchpad':       return <LaunchpadView />;
      case 'alerts':          return <AlertsView />;
      case 'workflow':        return <WorkflowView />;
      case 'settings':        return <SettingsView />;
      case 'dark_pools':      return <DarkPoolView />;
      case 'insider':         return <InsiderView />;
      case 'war_room':        return <WarRoomView />;
      case 'sandbox':         return <SandboxView />;
      case 'godmode':         return <GodModeView />;
      case 'help':            return <HelpView />;
      default:                return <WorldView />;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-void text-slate-200 overflow-hidden font-sans selection:bg-accent-primary selection:text-void">
      {/* Background Globe Ambience */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-20">
        <GlobalGlobe />
      </div>

      <NavRail />

      <main className="flex-1 flex flex-col min-w-0 z-10 relative">
        <Masthead />
        
        <div className="flex-1 flex min-h-0">
          {/* Main Viewport */}
          <div className="flex-1 flex flex-col min-w-0 border-r border-white/5">
            <div className="flex-1 min-h-0 overflow-hidden relative bg-slate-900/20 backdrop-blur-sm">
              <ErrorBoundary widgetName="Main Viewport">
                {renderView()}
              </ErrorBoundary>
            </div>

            {/* Command Interface Strip */}
            <div className="h-10 bg-slate-950 border-t border-white/5 flex items-center px-4 gap-4 shrink-0">
              <div className="flex items-center gap-2 text-accent-primary">
                <span className="text-[10px] font-black font-mono tracking-tighter">CMD{'>'}</span>
              </div>
              <input 
                type="text" 
                placeholder="EXECUTE KERNEL DIRECTIVE..."
                className="flex-1 bg-transparent border-none outline-none text-[11px] text-accent-primary font-mono placeholder:text-slate-700"
              />
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                   <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse shadow-[0_0_8px_#10b981]" />
                   <span className="text-[9px] font-mono font-bold text-bull uppercase">System Nominal</span>
                </div>
                <div className="h-4 w-px bg-white/10" />
                <span className="text-[9px] font-mono text-slate-600 uppercase tracking-widest">Auth: LEVEL_4_CLEARANCE</span>
              </div>
            </div>
          </div>

          {/* Right Sidebar Panels */}
          <aside className="w-80 flex flex-col shrink-0 bg-slate-950/80 backdrop-blur-md hidden 2xl:flex">
             <div className="flex-1 min-h-0 flex flex-col border-b border-white/5">
                <div className="h-8 bg-white/5 flex items-center px-4 shrink-0">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Watchlist</span>
                </div>
                <div className="flex-1 overflow-hidden">
                  <ErrorBoundary widgetName="Watchlist">
                    <WatchlistPanel />
                  </ErrorBoundary>
                </div>
             </div>
             <div className="flex-1 min-h-0 flex flex-col">
                <div className="h-8 bg-white/5 flex items-center px-4 shrink-0">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Signal Intelligence</span>
                </div>
                <div className="flex-1 overflow-hidden">
                  <ErrorBoundary widgetName="Intelligence Feed">
                    <IntelligenceFeed />
                  </ErrorBoundary>
                </div>
             </div>
          </aside>
        </div>
      </main>

      {/* Global Modals & Overlays */}
      <TerminalOutput />
      <IntelligenceDetails />
      <AlertHub />
    </div>
  );
}
