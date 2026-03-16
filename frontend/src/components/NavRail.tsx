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
  MapPin,
  Compass,
  Layout,
  Newspaper
} from 'lucide-react';
import { useTerminalStore } from '../store';

const NavButton = ({ item, isActive, onClick }: any) => (
  <button 
    onClick={onClick}
    className="w-14 h-14 group relative flex flex-col justify-center items-center shrink-0 transition-colors border-l-[3px] border-transparent"
    style={{
      backgroundColor: isActive ? 'var(--color-bg-surface-2)' : 'transparent',
      borderLeftColor: isActive ? 'var(--color-neon-bull)' : 'transparent',
    }}
  >
    <div 
      className="transition-colors duration-200"
      style={{ color: isActive ? 'var(--color-neon-bull)' : 'var(--color-text-dim)' }}
    >
      {item.icon}
    </div>
    
    {/* MACRO KEY TAG (Bloomberg Style shortcut) */}
    <div className="absolute top-1 left-1 opacity-0 group-hover:opacity-100 transition-opacity">
       <span 
         className="text-[8px] font-bold font-mono px-0.5 border"
         style={{ backgroundColor: 'var(--color-bg-surface)', borderColor: 'var(--color-text-dim)', color: 'var(--color-text-dim)' }}
       >{item.shortcut}</span>
    </div>

    {/* SEVERE TOOLTIP */}
    <div 
      className="absolute left-[64px] px-3 py-1.5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 text-[10px] uppercase font-bold tracking-[0.15em] border shadow-[0_4px_24px_rgba(0,0,0,0.8)]"
      style={{ 
        backgroundColor: 'var(--color-bg-surface)', 
        borderColor: 'var(--color-neon-bull)',
        color: 'var(--color-text-primary)'
      }}
    >
      <div className="flex items-center gap-2">
         {item.label} <span className="text-[8px] text-text-dim px-1 bg-surface-2">CMD + {item.shortcut}</span>
      </div>
    </div>
  </button>
);

const NavRail = () => {
  const { selectedView, setView } = useTerminalStore();

  const primaryNav = [
    { id: 'world',     icon: <Globe size={20} strokeWidth={1.5} />,        label: 'Orbital Visualizer', shortcut: 'W' },
    { id: 'matrix',    icon: <Table size={20} strokeWidth={1.5} />,        label: 'Signal Matrix',      shortcut: 'M' },
    { id: 'charts',    icon: <BarChart3 size={20} strokeWidth={1.5} />,    label: 'Price Action',       shortcut: 'C' },
    { id: 'portfolio', icon: <Briefcase size={20} strokeWidth={1.5} />,    label: 'Portfolio Engine',   shortcut: 'P' },
    { id: 'economics', icon: <TrendingUp size={20} strokeWidth={1.5} />,   label: 'Macro Surveillance', shortcut: 'E' },
    { id: 'launchpad', icon: <Layout size={20} strokeWidth={1.5} />,       label: 'Launchpad / LP',    shortcut: 'L' },
    { id: 'research',  icon: <Search size={20} strokeWidth={1.5} />,       label: 'AI Copilot / RAG',   shortcut: 'R' },
  ];

  const secondaryNav = [
    { id: 'news',      icon: <Newspaper size={18} strokeWidth={1.5} />,    label: 'Intelligence Hub',   shortcut: 'N' },
    { id: 'feed',      icon: <Satellite size={18} strokeWidth={1.5} />,    label: 'Raw STAC Feed',      shortcut: 'F' },
    { id: 'terminal',  icon: <Terminal size={18} strokeWidth={1.5} />,     label: 'Direct Kernel',      shortcut: 'K' },
  ];

  const bottomNav = [
    { id: 'settings',  icon: <Settings size={18} strokeWidth={1.5} />,     label: 'Core Settings',      shortcut: 'S' },
  ];

  return (
    <nav 
      className="w-14 h-full flex flex-col justify-between shrink-0 z-50 relative pb-2 bg-void"
      style={{ borderRight: '1px solid var(--border-terminal)' }}
    >
        {/* LOGO MARK */}
        <div className="w-14 h-12 flex items-center justify-center shrink-0 border-b border-white/10 bg-surface-base cursor-pointer hover:bg-surface-1 transition-colors group">
            <Compass size={22} className="text-text-2 group-hover:text-accent-primary transition-colors" strokeWidth={1.5} />
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
            <div className="w-6 h-[1px] bg-white/10"></div>
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

      <div className="flex flex-col w-full pt-2 border-t border-white/10">
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
