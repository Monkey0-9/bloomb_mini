import { 
  Globe, 
  Table, 
  Satellite, 
  BarChart3, 
  Briefcase, 
  Search, 
  Settings, 
  Terminal,
  TrendingUp,
  Layout,
  Newspaper,
  HelpCircle,
  Bell,
  Eye
} from 'lucide-react';
import { useTerminalStore } from '../store';

const NavButton = ({ item, isActive, onClick }: any) => (
  <button 
    onClick={onClick}
    className="w-12 h-12 group relative flex flex-col justify-center items-center shrink-0 transition-colors border-l-[2px] border-transparent"
    style={{
      backgroundColor: isActive ? 'var(--color-surface-2)' : 'transparent',
      borderLeftColor: isActive ? 'var(--color-accent-primary)' : 'transparent',
    }}
  >
    <div 
      className="transition-colors duration-200"
      style={{ color: isActive ? 'var(--color-accent-primary)' : 'var(--color-neutral)' }}
    >
      {item.icon}
    </div>
    
    {/* MACRO KEY TAG (Bloomberg Style shortcut) */}
    <div className="absolute top-1 left-1 opacity-0 group-hover:opacity-100 transition-opacity">
       <span 
         className="text-[8px] font-bold font-mono px-0.5 border"
         style={{ backgroundColor: 'var(--color-surface-1)', borderColor: 'var(--color-surface-4)', color: 'var(--color-neutral)' }}
       >{item.shortcut}</span>
    </div>

    {/* SEVERE TOOLTIP */}
    <div 
      className="absolute left-[56px] px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 text-[9px] uppercase font-bold tracking-[0.1em] border shadow-[0_4px_12px_rgba(0,0,0,0.8)]"
      style={{ 
        backgroundColor: 'var(--color-surface-1)', 
        borderColor: 'var(--color-accent-primary)',
        color: 'var(--color-accent-primary)'
      }}
    >
      <div className="flex items-center gap-2">
         {item.label} <span className="text-[8px] text-[var(--text-secondary)] px-1 bg-[var(--bg-card)]">CTRL + {item.shortcut}</span>
      </div>
    </div>
  </button>
);

const NavRail = () => {
  const { selectedView, setView } = useTerminalStore();

  const primaryNav = [
    { id: 'world',     icon: <Globe size={18} strokeWidth={1.5} />,        label: 'Orbital Visualizer', shortcut: 'W' },
    { id: 'matrix',    icon: <Table size={18} strokeWidth={1.5} />,        label: 'Signal Matrix',      shortcut: 'M' },
    { id: 'charts',    icon: <BarChart3 size={18} strokeWidth={1.5} />,    label: 'Price Action',       shortcut: 'C' },
    { id: 'portfolio', icon: <Briefcase size={18} strokeWidth={1.5} />,    label: 'Portfolio Engine',   shortcut: 'P' },
    { id: 'economics', icon: <TrendingUp size={18} strokeWidth={1.5} />,   label: 'Macro Surveillance', shortcut: 'E' },
    { id: 'launchpad', icon: <Layout size={18} strokeWidth={1.5} />,       label: 'Launchpad / LP',    shortcut: 'L' },
    { id: 'research',  icon: <Search size={18} strokeWidth={1.5} />,       label: 'AI Copilot / RAG',   shortcut: 'R' },
  ];

  const secondaryNav = [
    { id: 'news',      icon: <Newspaper size={16} strokeWidth={1.5} />,    label: 'Intelligence Hub',   shortcut: 'N' },
    { id: 'feed',      icon: <Satellite size={16} strokeWidth={1.5} />,    label: 'Raw STAC Feed',      shortcut: 'F' },
    { id: 'alerts',    icon: <Bell size={16} strokeWidth={1.5} />,         label: 'Alert Hub',          shortcut: 'A' },
    { id: 'workflow',  icon: <Layout size={16} strokeWidth={1.5} />,       label: 'Workflow Engine',    shortcut: 'W' },
    { id: 'dark_pools',icon: <Search size={16} strokeWidth={1.5} />,       label: 'Dark Pool Sonar',    shortcut: 'D' },
    { id: 'insider',   icon: <Eye size={16} strokeWidth={1.5} />,          label: 'Insider AI Tracker', shortcut: 'I' },
    { id: 'terminal',  icon: <Terminal size={16} strokeWidth={1.5} />,     label: 'Direct Kernel',      shortcut: 'K' },
  ];

  const bottomNav = [
    { id: 'help',      icon: <HelpCircle size={16} strokeWidth={1.5} />,     label: 'Documentation',      shortcut: 'H' },
    { id: 'settings',  icon: <Settings size={16} strokeWidth={1.5} />,     label: 'Core Settings',      shortcut: 'S' },
  ];

  return (
    <nav 
      className="w-12 h-full flex flex-col justify-between shrink-0 z-50 relative pb-2 bg-void"
      style={{ borderRight: '1px solid var(--color-surface-4)' }}
    >
        {/* LOGO MARK */}
        <div className="w-12 h-10 flex items-center justify-center shrink-0 border-b border-surface-4 bg-surface-1 cursor-pointer hover:bg-surface-2 transition-colors group">
            <span className="text-[14px] font-bold text-accent-primary font-mono">ST</span>
        </div>

      <div className="flex flex-col w-full flex-1 pt-2">
        {primaryNav.map((item) => (
          <NavButton
            key={item.id}
            item={item}
            isActive={selectedView === item.id}
            onClick={() => setView(item.id as any)}
          />
        ))}
        
        <div className="h-4 w-full flex items-center justify-center my-2">
            <div className="w-4 h-[1px] bg-[var(--border-subtle)]"></div>
        </div>

        {secondaryNav.map((item) => (
          <NavButton
            key={item.id}
            item={item}
            isActive={selectedView === item.id}
            onClick={() => setView(item.id as any)}
          />
        ))}
      </div>

      <div className="flex flex-col w-full pt-2 border-t border-surface-4">
        {bottomNav.map((item) => (
          <NavButton
            key={item.id}
            item={item}
            isActive={selectedView === item.id}
            onClick={() => setView(item.id as any)}
          />
        ))}
      </div>
    </nav>
  );
};

export default NavRail;
