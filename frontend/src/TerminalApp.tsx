import { useEffect, useRef, useState, useCallback } from 'react';
import { useTerminalStore, useSignalStore, useVesselStore, useFlightStore } from './store';
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
import CommandPalette from './components/CommandPalette';
import MissionControlPanel from './components/MissionControlPanel';

const CommandLine = () => {
  const { setSelectedView } = useTerminalStore();
  const inputRef = useRef<HTMLInputElement>(null);
  const [cmdHistory, setCmdHistory] = useState<string[]>([]);
  const [histPos, setHistPos]       = useState(-1);

  useEffect(() => {
    const focus = (e: KeyboardEvent) => {
      if (e.key === '/' || e.key === ':') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', focus);
    return () => window.removeEventListener('keydown', focus);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const val = e.currentTarget.value.trim();
    if (e.key === 'Enter' && val) {
      // Slash NAV commands
      if (val.startsWith('/NAV ')) {
        setSelectedView(val.replace('/NAV ', '').trim().toLowerCase() as ViewType);
      } else {
        executeCommand(val);
      }
      setCmdHistory(prev => [val, ...prev.slice(0, 49)]);
      setHistPos(-1);
      e.currentTarget.value = '';
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const next = Math.min(histPos + 1, cmdHistory.length - 1);
      setHistPos(next);
      if (inputRef.current) inputRef.current.value = cmdHistory[next] ?? '';
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const next = Math.max(histPos - 1, -1);
      setHistPos(next);
      if (inputRef.current) inputRef.current.value = next === -1 ? '' : cmdHistory[next];
    } else if (e.key === 'Escape') {
      if (inputRef.current) inputRef.current.value = '';
      inputRef.current?.blur();
    }
  };

  return (
    <div
      className="h-8 flex items-center px-4 shrink-0 z-50 relative bg-[var(--bg-card)] border-t border-[var(--border-subtle)]"
    >
      <span
        className="font-mono text-[11px] font-bold mr-3 uppercase text-[var(--neon-bull)]"
      >SATTRADE&gt;</span>
      <input
        ref={inputRef}
        type="text"
        onKeyDown={handleKeyDown}
        className="flex-1 bg-transparent border-none outline-none font-mono text-[11px] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)]"
        placeholder="Ticker · /NAV charts · /SIGNAL VALE · Cmd+K for AI"
      />
      <div
        className="flex gap-4 font-mono text-[9px] uppercase tracking-widest hidden md:flex text-[var(--text-secondary)]"
      >
        <span>↑↓ history</span>
        <span>·</span>
        <span>Cmd+K AI</span>
        <span>·</span>
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
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // ─── WebSocket Hub ────────────────────────────────────────────────────────
  const connectWS = useCallback(() => {
    const token = localStorage.getItem('token');
    const wsUrl = `ws://localhost:8000/ws${token ? `?token=${token}` : ''}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WS: Connected to Institutional Hub');
      // Subscribe to all topics immediately
      ws.send(JSON.stringify({
        action: 'subscribe',
        topics: ['vessel', 'flight', 'signal', 'alerts']
      }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        // Route to appropriate store
        switch (msg._topic) {
          case 'vessel':
            useVesselStore.getState().handleWSUpdate(msg);
            break;
          case 'flight':
            useFlightStore.getState().handleWSUpdate(msg);
            break;
          case 'signal':
            useSignalStore.getState().handleWSUpdate(msg);
            break;
          case 'alerts':
            // AlertHub will capture this via custom event if needed
            window.dispatchEvent(new CustomEvent('terminal-alert', { detail: msg }));
            break;
        }
      } catch (e) {
        console.error('WS: Parse Error', e);
      }
    };

    ws.onclose = () => {
      console.warn('WS: Disconnected. Reconnecting in 3s...');
      setTimeout(connectWS, 3000);
    };

    ws.onerror = (err) => console.error('WS: Socket Error', err);
  }, []);

  useEffect(() => {
    connectWS();
    return () => {
      wsRef.current?.close();
    };
  }, [connectWS]);

  // ─── Initial Load ─────────────────────────────────────────────────────────
  useEffect(() => {
    fetchSignals();
    fetchVessels();
    fetchFlights();
    fetchEquities();
  }, [fetchSignals, fetchVessels, fetchFlights, fetchEquities]);

  // Cmd+K → CommandPalette
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  useEffect(() => {
    const handleExplain = (e: any) => {
        if (e.detail?.command === 'TEACH ME') setIsExplainOpen(true);
    };
    window.addEventListener('terminal-command', handleExplain as any);
    return () => window.removeEventListener('terminal-command', handleExplain as any);
  }, []);

  return (
    <div 
      className="flex flex-col h-screen w-screen overflow-hidden selection:bg-[var(--neon-signal)]/20"
      style={{ backgroundColor: 'var(--bg-base)' }}
    >
      {/* ZONE A: MASTHEAD */}
      <Masthead />
      
      <div className="flex flex-1 overflow-hidden relative">
        {/* ZONE B: NAV RAIL */}
        <NavRail />
        
        {/* ZONE C: MAIN VIEWPORT */}
        <div className="flex-1 flex flex-col min-w-0 relative">
           <div 
             className={`flex-1 relative flex overflow-hidden border-b border-[var(--border-subtle)] ${['world', 'feed'].includes(selectedView) ? 'osint-theme' : ''}`}
             style={{ backgroundColor: 'var(--bg-base)' }}
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
           <div className="flex flex-col border-r border-[var(--border-subtle)] w-[260px]">
              <MissionControlPanel />
              <SignalPanel />
           </div>
           
           {/* ZONE E: WATCHLIST & RISK PANEL */}
           <div 
             className="flex flex-col border-l border-[var(--border-subtle)] w-[280px]"
           >
              <WatchlistPanel />
              <RiskPanel />
           </div>
        </aside>
      </div>

      <AlertHub />
      <CommandPalette isOpen={isPaletteOpen} onClose={() => setIsPaletteOpen(false)} />
    </div>
  );
};

export default App;
