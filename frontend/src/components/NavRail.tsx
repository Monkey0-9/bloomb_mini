import { 
  Globe, 
  Table, 
  Satellite, 
  BarChart3, 
  Briefcase, 
  Search, 
  Settings, 
  Terminal,
  HelpCircle,
  GraduationCap
} from 'lucide-react';
import { useTerminalStore } from '../store';

const NavButton = ({ item, isActive, onClick }: any) => (
  <button 
    onClick={onClick}
    className={`w-full group relative flex flex-col items-center py-3 transition-all duration-200 border-l-2 ${
      isActive 
        ? 'bg-surface-2 border-accent-primary' 
        : 'border-transparent hover:bg-surface-1'
    }`}
  >
    <div className={`transition-colors duration-200 ${
        isActive ? 'text-accent-primary' : 'text-text-4 group-hover:text-text-2'
      }`}>
      {item.icon}
    </div>
    <span className={`text-[8px] uppercase mt-1 font-bold tracking-tighter text-center px-1 ${
      isActive ? 'text-accent-primary' : 'text-text-5 group-hover:text-text-4'
    }`}>
      {item.id.substring(0, 4)}
    </span>
    
    {/* Bloomberg Shortcut Tag */}
    <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
       <span className="text-[7px] text-text-5 bg-surface-3 px-0.5 rounded-sm">{item.shortcut}</span>
    </div>

    {/* TOOLTIP */}
    <div className="absolute left-full ml-2 px-2 py-1 bg-surface-3 border border-white/10 rounded-sm opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-floating text-[10px] text-text-1 uppercase tracking-widest shadow-xl">
      {item.label}
    </div>
  </button>
);

const NavRail = () => {
  const { selectedView, setView } = useTerminalStore();

  const navItems = [
    { id: 'world', icon: <Globe size={18} />, label: 'Global Map', shortcut: 'W' },
    { id: 'matrix', icon: <Table size={18} />, label: 'Signal Matrix', shortcut: 'MX' },
    { id: 'feed', icon: <Satellite size={18} />, label: 'Satellite Feed', shortcut: 'FD' },
    { id: 'charts', icon: <BarChart3 size={18} />, label: 'Price Charts', shortcut: 'CH' },
    { id: 'portfolio', icon: <Briefcase size={18} />, label: 'Portfolio', shortcut: 'PF' },
    { id: 'research', icon: <Search size={18} />, label: 'Research', shortcut: 'RS' },
    { id: 'education', icon: <GraduationCap size={18} />, label: 'SatTrade Academy', shortcut: 'ED' },
    { id: 'terminal', icon: <Terminal size={18} />, label: 'Terminal Mode', shortcut: 'TM' },
  ];

  const bottomItems = [
    { id: 'help', icon: <HelpCircle size={18} />, label: 'Help', shortcut: 'H' },
    { id: 'settings', icon: <Settings size={18} />, label: 'Settings', shortcut: 'ST' },
  ];

  return (
    <nav className="w-14 h-full bg-void border-r border-white/5 flex flex-col justify-between shrink-0 z-raised relative">
      <div className="flex flex-col w-full">
        {navItems.map((item) => (
          <NavButton
            key={item.id}
            item={item}
            isActive={selectedView === item.id}
            onClick={() => setView(item.id as any)}
          />
        ))}
      </div>

      <div className="flex flex-col w-full border-t border-white/5">
        {bottomItems.map((item) => (
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
