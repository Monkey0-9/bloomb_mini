import React from 'react';
import { Flight } from '../types/aviation';

interface FlightPopupProps {
  flight: Flight;
}

export const getFlightHTML = (f: any) => {
  const signal = f.signal?.status || 'NEUTRAL';
  const cargo = f.cargo || {};
  return `
  <div class="glass-panel intelligence-popup transition-all duration-300 transform scale-100 min-w-[280px]">
    <div class="popup-header bg-surface-2/50 p-3 flex justify-between items-start border-b border-white/10">
      <div class="flex flex-col">
        <span class="type-h2 text-accent-secondary font-bold tracking-tight">${f.callsign || 'N/A'}</span>
        <span class="type-data-xs text-text-4 font-mono">${f.operator || 'Unknown Operator'}</span>
      </div>
      <span class="signal-badge ${signal === 'BULLISH' ? 'signal-bull' : signal === 'BEARISH' ? 'signal-bear' : 'signal-neutral'} shadow-lg py-1 px-2 rounded font-bold text-[10px]">
        ${signal}
      </span>
    </div>
    <div class="popup-body p-3">
      <div class="space-y-1.5 font-mono text-[11px]">
        <div class="data-row flex justify-between"><span class="data-label text-text-4 uppercase text-[9px]">Aircraft</span><span class="data-value">${f.type || 'Commercial'}</span></div>
        <div class="data-row flex justify-between pt-1 border-t border-white/5"><span class="data-label text-text-4 uppercase text-[9px]">Origin</span><span class="data-value">${f.origin || 'N/A'}</span></div>
        <div class="data-row flex justify-between"><span class="data-label text-text-4 uppercase text-[9px]">Dest</span><span class="data-value text-bull font-bold">${f.destination || 'N/A'}</span></div>
        <div class="data-row flex justify-between pt-1 border-t border-white/5"><span class="data-label text-text-4 uppercase text-[9px]">Altitude</span><span class="data-value text-accent-secondary">${(f.altitude_ft || 0).toLocaleString()} FT</span></div>
        <div class="data-row flex justify-between"><span class="data-label text-text-4 uppercase text-[9px]">Velocity</span><span class="data-value">${f.speed_knots || 0} KTS @ ${f.heading || 0}°</span></div>
      </div>

      <div class="mt-4 pt-3 border-t border-white/10">
        <div class="type-data-xs text-text-3 font-bold mb-1 uppercase tracking-widest text-[9px]">Payload Profile</div>
        <p class="type-data-xs text-text-4 leading-normal italic bg-surface-1/30 p-2 rounded border border-white/5">
          "${f.signal?.reason || 'Routine cargo monitoring...'}"
        </p>
      </div>

      <div class="mt-3 p-2 bg-bull/5 border border-bull/10 rounded-sm flex justify-between items-center">
        <div class="flex flex-col">
          <span class="text-[9px] uppercase text-bull font-bold opacity-70">CARGO LOAD</span>
          <span class="text-[11px] text-text-1 font-bold">${cargo.type || 'Standard Freight'}</span>
        </div>
        <div class="flex flex-col items-end">
            <span class="text-[10px] text-text-3">${cargo.weight || ''}</span>
            <span class="text-[12px] font-black text-bull">${cargo.value || ''}</span>
        </div>
      </div>

      <div class="mt-4 flex justify-between items-center bg-surface-2/40 p-2 rounded">
        <div class="flex flex-col">
          <span class="text-[9px] text-text-5 uppercase font-bold tracking-tighter">Market Signal</span>
          <span class="text-xs font-black ${signal === 'BULLISH' ? 'text-bull' : 'text-text-1'}">${signal}</span>
        </div>
        <div class="flex gap-1">
          ${f.tickers && Array.isArray(f.tickers) ? f.tickers.slice(0, 2).map((t: string) => `<span class="ticker-chip bg-accent-secondary/10 text-accent-secondary border border-accent-secondary/20 px-1 py-0.5 rounded text-[9px] font-bold">${t}</span>`).join('') : ''}
        </div>
      </div>
    </div>
  </div>
`;
};

const FlightPopup: React.FC<FlightPopupProps> = ({ flight }) => {
  return null;
};

export default FlightPopup;
