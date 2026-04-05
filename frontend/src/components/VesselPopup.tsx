import React from 'react';
import { Vessel } from '../types/maritime';

interface VesselPopupProps {
  vessel: Vessel;
}

/**
 * Static function to generate the HTML for the globe popup.
 * Using a direct HTML template as required by pointLabel in react-globe.gl.
 */
export const getVesselHTML = (v: any) => {
  const signal = v.signal?.status || 'NEUTRAL';
  const cargo = v.cargo || {};
  const sigColor = signal === 'BULLISH' ? '#10b981' : signal === 'BEARISH' ? '#ef4444' : '#64748b';
  
  return `
  <div style="background: rgba(2, 6, 23, 0.9); backdrop-filter: blur(12px); border: 1px solid rgba(56, 189, 248, 0.2); min-width: 320px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); pointer-events: auto; font-family: 'IBM Plex Mono', monospace;">
    <div style="padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: flex-start; background: rgba(255,255,255,0.02);">
      <div style="display: flex; flex-direction: column; gap: 4px;">
        <span style="font-family: 'Bebas Neue', sans-serif; font-size: 20px; color: #fff; letter-spacing: 0.1em; line-height: 1;">${v.name || 'UNKNOWN_VESSEL'}</span>
        <span style="font-size: 9px; color: #64748b; font-weight: bold; letter-spacing: 0.1em; text-transform: uppercase;">${v.mmsi || 'MMSI_PENDING'} // ${v.operator || 'INDEPENDENT_OPS'}</span>
      </div>
      <div style="background: ${sigColor}22; border: 1px solid ${sigColor}44; color: ${sigColor}; padding: 4px 8px; font-size: 10px; font-weight: 900; letter-spacing: 0.1em; box-shadow: 0 0 10px ${sigColor}22;">
        ${signal}
      </div>
    </div>

    <div style="padding: 20px; display: flex; flex-direction: column; gap: 16px;">
      <div style="display: flex; flex-direction: column; gap: 6px;">
        <div style="display: flex; justify-content: space-between; font-size: 10px;">
          <span style="color: #475569; text-transform: uppercase; font-weight: bold;">Class</span>
          <span style="color: #38bdf8; font-weight: black;">${v.type || 'CARGO'}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 10px;">
          <span style="color: #475569; text-transform: uppercase; font-weight: bold;">Vector</span>
          <span style="color: #e2e8f0;">${v.origin || 'SEA_LANES'} → ${v.destination || 'UNKNOWN_DEST'}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 10px;">
          <span style="color: #475569; text-transform: uppercase; font-weight: bold;">Cargo_Manifest</span>
          <span style="color: #10b981; font-weight: black;">${cargo.type || 'GENERAL_FREIGHT'}</span>
        </div>
      </div>

      <div style="background: rgba(56, 189, 248, 0.05); border-left: 2px solid #38bdf8; padding: 12px;">
        <div style="font-size: 9px; color: #38bdf8; font-weight: 900; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 4px;">MIROFISH_INFERENCE</div>
        <div style="font-size: 11px; color: #cbd5e1; font-style: italic; line-height: 1.5;">"${v.signal?.reason || 'Initiating real-time signal induction...'}"</div>
      </div>
      
      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;">
        <div style="display: flex; flex-direction: column;">
          <span style="font-size: 8px; color: #475569; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em;">Est_Market_Impact</span>
          <span style="font-size: 16px; font-family: 'Bebas Neue', sans-serif; color: #10b981; letter-spacing: 0.05em;">$${(v.signal?.impact || 0).toFixed(1)}M USD</span>
        </div>
        <div style="display: flex; flex-direction: column; align-items: end;">
          <span style="font-size: 8px; color: #475569; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em;">Integrity</span>
          <span style="font-size: 10px; color: #10b981; font-weight: bold; display: flex; align-items: center; gap: 4px;">
            <span style="width: 6px; height: 6px; background: #10b981; border-radius: 50%; box-shadow: 0 0 5px #10b981;"></span>
            VERIFIED
          </span>
        </div>
      </div>
    </div>
    
    <div style="height: 2px; width: 100%; background: rgba(255,255,255,0.05);">
      <div style="height: 100%; width: ${v.progress_pct || 0}%; background: #10b981; box-shadow: 0 0 10px #10b981;"></div>
    </div>
  </div>
  `;
};

const VesselPopup: React.FC<VesselPopupProps> = ({ vessel }) => {
  return null;
};

export default VesselPopup;
