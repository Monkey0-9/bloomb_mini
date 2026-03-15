import { useTerminalStore } from '../store';
import { 
  Globe2, 
  BarChart3, 
  LayoutGrid, 
  Satellite, 
  Briefcase, 
  BookOpen, 
  Terminal, 
  GraduationCap,
  Settings, 
  HelpCircle 
} from 'lucide-react';

const NavRail = () => {
  const { selectedView, setView } = useTerminalStore();
  
  const topItems = [
    { id: 'world', icon: <Globe2 size={20} strokeWidth={1.5} />, label: 'WORLD MAP' },
    { id: 'charts', icon: <BarChart3 size={20} strokeWidth={1.5} />, label: 'CHARTS & ANALYSIS' },
    { id: 'matrix', icon: <LayoutGrid size={20} strokeWidth={1.5} />, label: 'SIGNAL MATRIX' },
    { id: 'feed', icon: <Satellite size={20} strokeWidth={1.5} />, label: 'SATELLITE IMAGE FEED' },
    { id: 'portfolio', icon: <Briefcase size={20} strokeWidth={1.5} />, label: 'PORTFOLIO & POSITIONS' },
    { id: 'research', icon: <BookOpen size={20} strokeWidth={1.5} />, label: 'RESEARCH' },
  ];

  const secondaryItems = [
    { id: 'terminal', icon: <Terminal size={20} strokeWidth={1.5} />, label: 'RAW TERMINAL MODE' },
    { id: 'education', icon: <GraduationCap size={20} strokeWidth={1.5} />, label: 'EXPLAIN MODE' },
  ];

  const bottomItems = [
    { id: 'settings', icon: <Settings size={20} strokeWidth={1.5} />, label: 'SETTINGS' },
    { id: 'help', icon: <HelpCircle size={20} strokeWidth={1.5} />, label: 'HELP' },
  ];

  const NavButton = ({ item }: { item: typeof topItems[0] }) => {
    const isActive = selectedView === item.id;
    return (
      <button
        onClick={() => setView(item.id as any)}
        className={`w-10 h-10 flex items-center justify-center transition-all duration-150 relative group rounded-sm ${
          isActive ? 'bg-surface-3 text-accent-primary' : 'text-text-4 hover:bg-surface-2 hover:text-text-2'
        }`}
      >
        {isActive && (
          <div className="absolute left-[-12px] top-1 bottom-1 w-[2px] bg-accent-primary"></div>
        )}
        
        {item.icon}

        {/* TOOLTIP: Right of icon */}
        <div className="absolute left-14 px-3 py-1.5 bg-surface-3 border border-border-3 rounded-sm opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-overlay transition-all duration-150 translate-x-1 group-hover:translate-x-0 shadow-2">
          <span className="type-ui-sm text-text-1">{item.label}</span>
          {/* Arrow */}
          <div className="absolute left-[-4px] top-1/2 -translate-y-1/2 w-2 h-2 bg-surface-3 border-l border-b border-border-3 rotate-45"></div>
        </div>
      </button>
    );
  };

  return (
    <nav className="w-[52px] bg-void border-r border-border-1 flex flex-col items-center py-3 shrink-0 z-floating">
      <div className="flex-1 flex flex-col items-center gap-1">
        {topItems.map((item) => (
          <NavButton key={item.id} item={item} />
        ))}
        
        <div className="w-8 h-[1px] bg-border-1 my-4"></div>

        {secondaryItems.map((item) => (
          <NavButton key={item.id} item={item} />
        ))}
      </div>

      <div className="flex flex-col items-center gap-1 mt-auto">
        {bottomItems.map((item) => (
          <NavButton key={item.id} item={item as any} />
        ))}
      </div>
    </nav>
  );
};

export default NavRail;
