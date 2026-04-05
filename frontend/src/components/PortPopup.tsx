/**
 * Static function to generate the HTML for the globe port popup.
 * Using a direct HTML template as required by pointLabel in react-globe.gl.
 */
export const getPortHTML = (p: any) => {
  const throughput = p.throughput ?? 0.82;
  const signal = p.signal || 'BULLISH';
  const name = p.name || 'GLOBAL_LOGISTICS_HUB';
  
  const berthCount = 42;
  const activeBerths = Math.floor(berthCount * throughput);
  const waitTime = (1.0 - throughput) * 48;
  const sigColor = signal === 'BULLISH' ? '#10b981' : '#ef4444';
  
  return `
  <div style="background: rgba(2, 6, 23, 0.95); backdrop-filter: blur(16px); border: 1px solid rgba(56, 189, 248, 0.2); min-width: 320px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); font-family: 'IBM Plex Mono', monospace; padding: 0;">
    <div style="padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center; background: rgba(56, 189, 248, 0.03);">
      <div style="display: flex; flex-direction: column; gap: 2px;">
        <span style="font-family: 'Bebas Neue', sans-serif; font-size: 22px; color: #fff; letter-spacing: 0.15em; line-height: 1;">${name.toUpperCase()}</span>
        <span style="font-size: 8px; color: #38bdf8; font-weight: 900; letter-spacing: 0.2em; text-transform: uppercase;">Strategic_Logistics_Node</span>
      </div>
      <div style="background: ${sigColor}22; border: 1px solid ${sigColor}44; color: ${sigColor}; padding: 4px 10px; font-size: 11px; font-weight: 900; letter-spacing: 0.1em; border-radius: 2px;">
        ${signal}
      </div>
    </div>

    <div style="padding: 20px; display: flex; flex-direction: column; gap: 20px;">
      <div style="display: grid; grid-template-cols: 1fr 1fr; gap: 12px;">
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: 2px;">
          <div style="font-size: 8px; color: #475569; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px;">Berth_Utilization</div>
          <div style="font-family: 'Bebas Neue', sans-serif; font-size: 20px; color: #fff;">${activeBerths}<span style="color: #475569; font-size: 14px;">/${berthCount}</span></div>
        </div>
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: 2px;">
          <div style="font-size: 8px; color: #475569; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px;">Avg_Anchor_Wait</div>
          <div style="font-family: 'Bebas Neue', sans-serif; font-size: 20px; color: #fff;">${waitTime.toFixed(1)}<span style="color: #475569; font-size: 14px;">H</span></div>
        </div>
      </div>

      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 9px; color: #475569; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em;">Real-Time Throughput</span>
          <span style="font-size: 11px; color: #fff; font-weight: bold;">${(throughput * 100).toFixed(1)}%</span>
        </div>
        <div style="height: 4px; width: 100%; background: rgba(255,255,255,0.05); border-radius: 2px; overflow: hidden; display: flex; gap: 2px;">
           ${Array.from({length: 10}).map((_, i) => `
             <div style="flex: 1; height: 100%; background: ${i < (throughput * 10) ? sigColor : 'transparent'}; opacity: ${i < (throughput * 10) ? '1' : '0'};"></div>
           `).join('')}
        </div>
      </div>

      <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 16px;">
        <div style="font-size: 9px; color: #38bdf8; font-weight: 900; text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 12px;">Inbound_Target_Alpha</div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <div style="background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.1); padding: 10px; border-radius: 2px; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; flex-direction: column; gap: 2px;">
              <span style="font-size: 11px; color: #fff; font-weight: bold;">COSCO_SHIPPING_HIMALAYAS</span>
              <span style="font-size: 8px; color: #64748b; text-transform: uppercase;">ULCC // ETA: 04:22 Z</span>
            </div>
            <span style="font-size: 9px; color: #10b981; font-weight: 900;">BULLISH</span>
          </div>
        </div>
      </div>
    </div>
    
    <div style="height: 2px; width: 100%; background: rgba(255,255,255,0.05);">
      <div style="height: 100%; width: 100%; background: ${sigColor}; box-shadow: 0 0 10px ${sigColor};"></div>
    </div>
  </div>
  `;
};
