import { useState, useRef, useEffect, useMemo } from 'react';
import { useSignalStore } from '../store';
import { motion } from 'framer-motion';

const SignalMatrix = () => {
  const { signals } = useSignalStore();
  const [focusedCell, setFocusedCell] = useState<{ row: number; col: number } | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  const data = useMemo(() => signals || [], [signals]);
  
  // Matrix Columns
  const columns = ['LOCATION', 'HEADLINE', 'STRENGTH', 'SENTIMENT', 'IC', 'ICIR', 'OBS', 'UPDATE'];

  // Keyboard Navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!focusedCell) return;
      
      let { row, col } = focusedCell;
      if (e.key === 'ArrowUp') row = Math.max(0, row - 1);
      if (e.key === 'ArrowDown') row = Math.min(data.length - 1, row + 1);
      if (e.key === 'ArrowLeft') col = Math.max(0, col - 1);
      if (e.key === 'ArrowRight') col = Math.min(columns.length - 1, col + 1);

      if (row !== focusedCell.row || col !== focusedCell.col) {
        e.preventDefault();
        setFocusedCell({ row, col });
        
        // Auto-scroll logic if needed could go here
        const el = document.getElementById(`cell-${row}-${col}`);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusedCell, data.length, columns.length]);

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden select-none outline-none" tabIndex={0} onFocus={() => setFocusedCell({ row: 0, col: 0 })}>
      {/* MATRIX HEADER */}
      <div className="h-10 border-b border-white/10 flex items-center justify-between px-3 shrink-0 bg-surface-1/60 backdrop-blur-md z-20">
         <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
               <span className="type-data-md text-text-0 uppercase tracking-widest shadow-sm">ALPHA MATRIX</span>
               <div className="w-1.5 h-1.5 rounded-full bg-bull dot-live"></div>
            </div>
            <div className="h-4 w-[1px] bg-white/10"></div>
            <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">
              Mode: <span className="text-accent-primary">High-Density Heatmap</span>
            </span>
         </div>
      </div>

      {/* HEATMAP GRID */}
      <div className="flex-1 overflow-auto custom-scrollbar bg-void" ref={gridRef}>
        <div className="min-w-max">
            {/* Headers */}
            <div className="grid grid-cols-[140px_200px_120px_100px_80px_80px_80px_110px] sticky top-0 bg-surface-1 z-10 border-b border-white/5">
                {columns.map((col, i) => (
                    <div key={col} className={`px-3 py-2 text-left type-data-xs text-text-3 font-bold uppercase tracking-[0.1em] ${i < columns.length - 1 ? 'border-r border-white/5' : ''}`}>
                        {col}
                    </div>
                ))}
            </div>

            {/* Rows */}
            <div className="flex flex-col">
                {data.map((row: any, rIdx: number) => (
                    <div key={rIdx} className="grid grid-cols-[140px_200px_120px_100px_80px_80px_80px_110px] border-b border-white/5 group">
                        
                        {/* Location */}
                        <div id={`cell-${rIdx}-0`} onClick={() => setFocusedCell({row: rIdx, col: 0})} className={`px-3 py-1.5 flex items-center border-r border-white/5 cursor-crosshair transition-all ${focusedCell?.row === rIdx && focusedCell?.col === 0 ? 'bg-surface-3 ring-1 ring-inset ring-accent-primary' : 'group-hover:bg-surface-2'}`}>
                            <span className="type-data-xs text-accent-primary font-bold truncate">{row.name.toUpperCase()}</span>
                        </div>

                        {/* Headline */}
                        <div id={`cell-${rIdx}-1`} onClick={() => setFocusedCell({row: rIdx, col: 1})} className={`px-3 py-1.5 flex items-center border-r border-white/5 cursor-crosshair transition-all ${focusedCell?.row === rIdx && focusedCell?.col === 1 ? 'bg-surface-3 ring-1 ring-inset ring-accent-primary' : 'group-hover:bg-surface-2'}`}>
                            <span className="type-data-xs text-text-2 truncate">{row.headline}</span>
                        </div>

                        {/* Strength Heatmap */}
                        <div id={`cell-${rIdx}-2`} onClick={() => setFocusedCell({row: rIdx, col: 2})} className={`px-3 py-1.5 flex items-center border-r border-white/5 cursor-crosshair transition-all ${focusedCell?.row === rIdx && focusedCell?.col === 2 ? 'bg-surface-3 ring-1 ring-inset ring-accent-primary' : 'group-hover:bg-surface-2'}`}>
                            <div className="w-full flex items-center gap-2">
                                <div className="flex-1 h-3 bg-surface-0 border border-white/10 relative overflow-hidden">
                                     <div 
                                        className={`absolute top-0 left-0 h-full ${row.status === 'bullish' ? 'bg-bull/80' : row.status === 'bearish' ? 'bg-bear/80' : 'bg-neutral/80'}`}
                                        style={{ width: `${row.score}%` }}
                                     />
                                </div>
                                <span className="type-data-xs tabular-nums text-text-0">{row.score}%</span>
                            </div>
                        </div>

                        {/* Sentiment */}
                        <div id={`cell-${rIdx}-3`} onClick={() => setFocusedCell({row: rIdx, col: 3})} className={`px-3 py-1.5 flex items-center border-r border-white/5 cursor-crosshair transition-all ${focusedCell?.row === rIdx && focusedCell?.col === 3 ? 'bg-surface-3 ring-1 ring-inset ring-accent-primary' : 'group-hover:bg-surface-2'} ${row.status === 'bullish' ? 'bg-bull/10' : row.status === 'bearish' ? 'bg-bear/10' : ''}`}>
                            <span className={`type-data-xs font-bold ${row.status === 'bullish' ? 'text-bull' : row.status === 'bearish' ? 'text-bear' : 'text-neutral'}`}>
                                {row.status.toUpperCase()}
                            </span>
                        </div>

                        {/* IC Heatmap */}
                        <div 
                            id={`cell-${rIdx}-4`} 
                            onClick={() => setFocusedCell({row: rIdx, col: 4})} 
                            className={`px-3 py-1.5 flex justify-end items-center border-r border-white/5 cursor-crosshair transition-all ${focusedCell?.row === rIdx && focusedCell?.col === 4 ? 'bg-surface-3 ring-1 ring-inset ring-accent-primary' : 'group-hover:bg-surface-2'}`}
                            style={{ backgroundColor: `rgba(0, 255, 157, ${Math.min(row.ic * 5, 0.4)})` }}
                        >
                            <span className="type-data-xs tabular-nums text-text-0 font-bold">{row.ic.toFixed(3)}</span>
                        </div>

                        {/* ICIR Heatmap */}
                        <div 
                            id={`cell-${rIdx}-5`} 
                            onClick={() => setFocusedCell({row: rIdx, col: 5})} 
                            className={`px-3 py-1.5 flex justify-end items-center border-r border-white/5 cursor-crosshair transition-all ${focusedCell?.row === rIdx && focusedCell?.col === 5 ? 'bg-surface-3 ring-1 ring-inset ring-accent-primary' : 'group-hover:bg-surface-2'}`}
                            style={{ backgroundColor: `rgba(0, 255, 157, ${Math.min((row.icir || 0) * 0.5, 0.4)})` }}
                        >
                             <span className="type-data-xs tabular-nums text-text-0 font-bold">{(row.icir || 0.65).toFixed(2)}</span>
                        </div>

                        {/* Observations */}
                        <div id={`cell-${rIdx}-6`} onClick={() => setFocusedCell({row: rIdx, col: 6})} className={`px-3 py-1.5 flex justify-end items-center border-r border-white/5 cursor-crosshair transition-all ${focusedCell?.row === rIdx && focusedCell?.col === 6 ? 'bg-surface-3 ring-1 ring-inset ring-accent-primary' : 'group-hover:bg-surface-2'}`}>
                             <span className="type-data-xs tabular-nums text-text-3">{row.observations?.toLocaleString() || '-'}</span>
                        </div>

                        {/* As of */}
                        <div id={`cell-${rIdx}-7`} onClick={() => setFocusedCell({row: rIdx, col: 7})} className={`px-3 py-1.5 flex justify-end items-center cursor-crosshair transition-all ${focusedCell?.row === rIdx && focusedCell?.col === 7 ? 'bg-surface-3 ring-1 ring-inset ring-accent-primary' : 'group-hover:bg-surface-2'}`}>
                             <span className="type-data-xs tabular-nums text-text-3">{row.as_of ? new Date(row.as_of).toISOString().substring(11, 16) : 'N/A'} z</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
      </div>

      {/* FOOTER */}
      <div className="h-8 border-t border-white/5 flex items-center justify-between px-3 bg-void shrink-0">
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em] flex items-center gap-2">
            Status: <span className="text-bull">Synched</span>
            {focusedCell && <span className="ml-4 text-text-5 border border-white/10 px-1 rounded-sm">ROW {focusedCell.row} COL {focusedCell.col}</span>}
         </span>
         <span className="type-data-xs text-text-5 uppercase tracking-[0.2em]">Nav: ↑↓←→ Focus</span>
      </div>
    </div>
  );
};

export default SignalMatrix;
