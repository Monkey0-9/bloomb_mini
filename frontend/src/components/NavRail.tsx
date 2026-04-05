import { 
  Globe, 
  Table, 
  BarChart3, 
  Briefcase, 
  Layout, 
  Search, 
  Newspaper, 
  Satellite, 
  Shield, 
  Zap, 
  Settings, 
  HelpCircle,
  Terminal,
  Activity
} from 'lucide-react';
import { useTerminalStore } from '../store';

const NavRail = () => {
  const { selectedView, setView } = useTerminalStore();

  const navItems = [
    { id: 'world', icon: Globe, label: 'World' },
    { id: 'matrix', icon: Table, label: 'Matrix' },
    { id: 'charts', icon: BarChart3, label: 'Charts' },
    { id: 'portfolio', icon: Briefcase, label: 'Risk' },
    { id: 'economics', icon: Layout, label: 'Macro' },
    { id: 'news', icon: Newspaper, label: 'Intel' },
    { id: 'feed', icon: Satellite, label: 'Raw' },
    { id: 'war_room', icon: Shield, label: 'Defcon' },
    { id: 'godmode', icon: Zap, label: 'GodMode' },
  ];

  return (
    <nav className="w-16 bg-slate-950 border-r border-white/5 flex flex-col items-center py-6 gap-8 z-50">
      <div className="w-10 h-10 bg-accent-primary/20 border border-accent-primary/40 rounded-lg flex items-center justify-center mb-4">
        <span className="font-display text-2xl text-accent-primary">ST</span>
      </div>

      <div className="flex-1 flex flex-col gap-4">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setView(item.id as any)}
            title={item.label}
            className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all group relative ${
              selectedView === item.id 
                ? 'bg-accent-primary text-slate-950 shadow-[0_0_15px_rgba(56,189,248,0.4)]' 
                : 'text-slate-500 hover:text-white hover:bg-white/5'
            }`}
          >
            <item.icon size={18} strokeWidth={selectedView === item.id ? 2.5 : 1.5} />
            
            {/* Tooltip */}
            <div className="absolute left-14 px-2 py-1 bg-slate-900 border border-white/10 rounded text-[10px] font-bold text-white uppercase tracking-widest opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap shadow-2xl z-[100]">
              {item.label}
            </div>

            {/* Active Indicator */}
            {selectedView === item.id && (
              <div className="absolute -left-3 w-1 h-6 bg-accent-primary rounded-r-full shadow-[0_0_10px_#38bdf8]" />
            )}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-4 mt-auto">
        <button 
          onClick={() => setView('terminal')}
          className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
            selectedView === 'terminal' ? 'text-accent-primary bg-white/5' : 'text-slate-500 hover:text-white'
          }`}
        >
          <Terminal size={18} />
        </button>
        <button 
          onClick={() => setView('settings')}
          className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
            selectedView === 'settings' ? 'text-accent-primary bg-white/5' : 'text-slate-500 hover:text-white'
          }`}
        >
          <Settings size={18} />
        </button>
      </div>
    </nav>
  );
};

export default NavRail;
