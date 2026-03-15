import { useMemo } from 'react';
import { useTerminalStore } from '../store';
import { motion } from 'framer-motion';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';

const columnHelper = createColumnHelper<any>();

const SignalMatrix = () => {
  const { signals } = useTerminalStore();

  const data = useMemo(() => signals, [signals]);

  const columns = useMemo(() => [
    columnHelper.accessor('name', {
      header: 'MONITORED LOCATION',
      cell: info => (
        <div className="flex items-center gap-4">
          <div className="w-1.5 h-6 bg-accent-primary opacity-20 group-hover:opacity-100 transition-opacity rounded-[1px]"></div>
          <div className="flex flex-col">
            <span className="type-data-md text-accent-primary font-bold group-hover:text-text-0 transition-colors">
              {info.getValue().toUpperCase()}
            </span>
            <span className="type-data-xs text-text-4 tracking-tight uppercase">
              {info.row.original.headline}
            </span>
          </div>
        </div>
      ),
    }),
    columnHelper.accessor('score', {
      header: 'SIGNAL STRENGTH',
      cell: info => (
        <div className="flex items-center gap-3 w-full max-w-[200px]">
          <div className="flex-1 h-2 bg-surface-3 rounded-[1px] relative overflow-hidden border border-border-ghost">
            <motion.div 
              className={`h-full ${
                info.row.original.status === 'bullish' ? 'bg-bull' : 
                info.row.original.status === 'bearish' ? 'bg-bear' : 
                'bg-neutral'
              } shadow-[0_0_8px_currentColor]`}
              initial={{ width: 0 }}
              animate={{ width: `${info.getValue()}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
            ></motion.div>
          </div>
          <span className="type-data-md text-text-1 font-bold w-10 text-right">{info.getValue()}%</span>
        </div>
      ),
    }),
    columnHelper.accessor('status', {
      header: 'SENTIMENT',
      cell: info => (
        <div className="flex">
          <span className={`type-data-xs px-2.5 py-1 rounded-[1px] border font-bold tracking-[0.1em] ${
            info.getValue() === 'bullish' ? 'bg-bull-08 border-bull-60 text-bull' : 
            info.getValue() === 'bearish' ? 'bg-bear-08 border-bear-60 text-bear' : 
            'bg-neutral-08 border-neutral text-neutral'
          }`}>
            {info.getValue().toUpperCase()}
          </span>
        </div>
      ),
    }),
    columnHelper.accessor('ic', {
      header: 'IC (INF. COEFF)',
      cell: info => (
        <div className="flex flex-col items-center">
          <span className="type-data-md text-text-2 font-bold">{info.getValue().toFixed(3)}</span>
          <div className="h-[1px] w-8 bg-border-ghost mt-1"></div>
        </div>
      ),
    }),
    columnHelper.accessor('icir', {
      header: 'ICIR (RATIO)',
      cell: info => (
        <div className="flex flex-col items-center">
          <span className="type-data-md text-text-2 font-bold">{info.getValue().toFixed(2)}</span>
          <div className="h-[1px] w-8 bg-border-ghost mt-1"></div>
        </div>
      ),
    }),
    columnHelper.accessor('observations', {
      header: 'OBS (N)',
      cell: info => <span className="type-data-md text-text-4">{info.getValue() || '1,242'}</span>,
    }),
    columnHelper.accessor('lastUpdate', {
      header: 'LAST OVERPASS',
      cell: info => (
        <div className="flex flex-col items-end">
          <span className="type-data-xs text-text-1 font-bold">{info.getValue().toUpperCase()}</span>
          <span className="type-data-xs text-text-5 -mt-0.5">VIA SENTINEL-2B</span>
        </div>
      ),
    }),
  ], []);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="flex-1 flex flex-col bg-surface-0 overflow-hidden">
      {/* MATRIX HEADER: ALLX STYLE */}
      <div className="h-11 border-b border-border-1 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
               <span className="type-h1 text-sm tracking-[0.2em] text-text-0 shadow-sm uppercase">SIGNAL MATRIX</span>
               <div className="w-1.5 h-1.5 rounded-full bg-bull dot-live"></div>
            </div>
            <div className="h-6 w-[1px] bg-border-ghost"></div>
            <span className="type-data-xs text-text-4 uppercase tracking-widest leading-none">
              Monitoring <span className="text-text-1">{data.length} Global Intelligence Nodes</span>
            </span>
         </div>
         
         <div className="flex gap-2">
            <button className="type-data-xs px-3 py-1.5 bg-surface-2/60 border border-border-2 text-text-4 uppercase tracking-widest hover:border-accent-primary hover:text-text-1 transition-all">Filter</button>
            <button className="type-data-xs px-3 py-1.5 bg-surface-2/60 border border-border-2 text-text-4 uppercase tracking-widest hover:border-accent-primary hover:text-text-1 transition-all">Export (CSV)</button>
         </div>
      </div>

      {/* MATRIX GRID */}
      <div className="flex-1 overflow-auto custom-scrollbar">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 bg-surface-1 z-10 border-b border-border-3">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th key={header.id} className="px-6 py-3 text-left">
                    <div className="type-data-xs text-text-3 font-bold uppercase tracking-[0.15em] border-b border-dotted border-text-5 inline-block cursor-help">
                      {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-border-ghost">
            {table.getRowModel().rows.map(row => (
              <tr key={row.id} className="hover:bg-surface-3 transition-all duration-150 group cursor-crosshair">
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-6 py-4">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* MATRIX FOOTER STATUS */}
      <div className="h-8 border-t border-border-1 flex items-center justify-between px-4 bg-void shrink-0">
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Matrix Load: <span className="text-bull">Ideal</span></span>
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Last Sync: <span className="text-text-3">09:41:22 UTC</span></span>
      </div>
    </div>
  );
};

export default SignalMatrix;
