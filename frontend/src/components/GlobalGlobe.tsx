import React, { useEffect, useRef, useMemo } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';

const GlobalGlobe: React.FC = () => {
  const globeEl = useRef<any>();

  // High-fidelity markers
  const places = useMemo(() => [
    { name: 'Rotterdam Port', lat: 51.9225, lng: 4.47917, size: 0.1, color: '#00FF9D', throughput: 0.9, signal: 'BULLISH' },
    { name: 'Singapore Port', lat: 1.28333, lng: 103.83333, size: 0.12, color: '#00FF9D', throughput: 0.85, signal: 'BULLISH' },
    { name: 'Shanghai Port', lat: 31.2304, lng: 121.4737, size: 0.15, color: '#FF3D3D', throughput: 0.45, signal: 'BEARISH' },
    { name: 'Los Angeles Port', lat: 33.7292, lng: -118.262, size: 0.08, color: '#6B7E99', throughput: 0.7, signal: 'NEUTRAL' },
    { name: 'Jebel Ali', lat: 25.0112, lng: 55.0611, size: 0.1, color: '#00FF9D', throughput: 0.92, signal: 'BULLISH' },
    { name: 'Busan', lat: 35.1796, lng: 129.0756, size: 0.09, color: '#00FF9D', throughput: 0.78, signal: 'BULLISH' }
  ], []);

  // Satellite orbit arcs
  const arcsData = useMemo(() => {
    return [
      { startLat: 51.9, startLng: 4.5, endLat: 1.3, endLng: 103.8, color: ['#00C8FF', '#00FF9D'] },
      { startLat: 31.2, startLng: 121.5, endLat: 33.7, endLng: -118.3, color: ['#00C8FF', '#FF3D3D'] }
    ];
  }, []);

  useEffect(() => {
    if (globeEl.current) {
      const globe = globeEl.current;
      globe.controls().autoRotate = true;
      globe.controls().autoRotateSpeed = 0.35;
      globe.pointOfView({ lat: 20, lng: 0, altitude: 2.2 });

      // Add atmospheric glow directly to the ThreeScene
      const scene = globe.scene();
      const light = new THREE.AmbientLight(0x404040, 2);
      scene.add(light);
    }
  }, []);

  return (
    <div className="w-full h-full relative group">
      <Globe
        ref={globeEl}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-dark.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        
        // Atmosphere
        showAtmosphere={true}
        atmosphereColor="#00C8FF"
        atmosphereAltitude={0.18}
        
        // Points (The Port Markers)
        pointsData={places}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointRadius="size"
        pointAltitude={0.01}
        pointLabel={(d: any) => `
          <div class="glass-panel p-3 min-w-[180px]">
            <div class="flex justify-between items-center mb-1">
               <span class="type-h2">${d.name}</span>
               <span class="type-data-xs px-1.5 py-0.5 bg-void rounded border border-white/10 ${d.signal === 'BULLISH' ? 'text-bull' : 'text-bear'}">${d.signal}</span>
            </div>
            <div class="type-data-md mb-2">Throughput: ${(d.throughput * 100).toFixed(1)}%</div>
            <div class="segment-bar">
               ${Array.from({length: 10}).map((_, i) => `
                 <div class="segment ${i < (d.throughput * 10) ? (d.signal === 'BULLISH' ? 'active-bull' : 'active-bear') : ''}"></div>
               `).join('')}
            </div>
          </div>
        `}
        
        // Pulsing Rings
        ringsData={places}
        ringLat="lat"
        ringLng="lng"
        ringColor={(d: any) => d.color}
        ringMaxRadius={2.5}
        ringPropagationSpeed={1.5}
        ringRepeatPeriod={1500}

        // Arcs (Satellite Orbits)
        arcsData={arcsData}
        arcColor="color"
        arcDashLength={0.4}
        arcDashGap={4}
        arcDashAnimateTime={2500}
        arcAltitudeAutoScale={0.5}
        arcStroke={0.2}
      />
      
      {/* HUD Labels */}
      <div className="absolute top-6 left-6 pointer-events-none">
        <div className="flex flex-col gap-0.5">
          <h2 className="type-h1 text-accent-primary glow-text-primary">Orbital Telemetry</h2>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-bull dot-live"></span>
            <p className="type-data-xs text-text-3 uppercase tracking-[0.2em]">6 Active Sentinel-2 Ingests</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlobalGlobe;
