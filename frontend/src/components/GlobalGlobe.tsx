import React, { useEffect, useRef, useMemo } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';
import { useTerminalStore } from '../store';
import { countryLabels } from '../data/countries';

const GlobalGlobe: React.FC = () => {
  const { activeLayers, zoomLevel } = useTerminalStore();
  const globeEl = useRef<any>(null);
  const [movements, setMovements] = React.useState<any>({ vessels: [], flights: [] });

  // Fetch movements from API
  useEffect(() => {
    const fetchMovements = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/geo/movements');
        const data = await res.json();
        setMovements(data);
      } catch (err) {
        console.error('Failed to fetch movements:', err);
      }
    };
    fetchMovements();
    const interval = setInterval(fetchMovements, 10000);
    return () => clearInterval(interval);
  }, []);

  // Update camera on zoom/view change
  useEffect(() => {
    if (globeEl.current) {
        const altitude = 4.0 / (zoomLevel || 1);
        globeEl.current.pointOfView({ lat: 20, lng: -20, altitude }, 1000);
    }
  }, [zoomLevel]);

  // High-fidelity markers
  const places = useMemo(() => [
    { name: 'Rotterdam Port', lat: 51.9225, lng: 4.47917, size: 0.1, color: '#00FF9D', throughput: 0.9, signal: 'BULLISH', type: 'PORTS' },
    { name: 'Singapore Port', lat: 1.28333, lng: 103.83333, size: 0.12, color: '#00FF9D', throughput: 0.85, signal: 'BULLISH', type: 'PORTS' },
    { name: 'Shanghai Port', lat: 31.2304, lng: 121.4737, size: 0.15, color: '#FF3D3D', throughput: 0.45, signal: 'BEARISH', type: 'PORTS' },
    { name: 'Los Angeles Port', lat: 33.7292, lng: -118.262, size: 0.08, color: '#6B7E99', throughput: 0.7, signal: 'NEUTRAL', type: 'PORTS' },
    { name: 'Jebel Ali', lat: 25.0112, lng: 55.0611, size: 0.1, color: '#00FF9D', throughput: 0.92, signal: 'BULLISH', type: 'PORTS' },
    { name: 'Busan', lat: 35.1796, lng: 129.0756, size: 0.09, color: '#00FF9D', throughput: 0.78, signal: 'BULLISH', type: 'PORTS' }
  ], []);

  const filteredPlaces = useMemo(() => 
    places.filter(p => activeLayers.includes(p.type || 'PORTS')), 
  [activeLayers, places]);

  const filteredVessels = useMemo(() => 
    (movements.vessels || []).filter(() => activeLayers.includes('VESSELS')), 
  [activeLayers, movements.vessels]);

  // Combined arcs (Satellite + Flights)
  const arcsData = useMemo(() => {
    const satelliteArcs = [
      { startLat: 51.9, startLng: 4.5, endLat: 1.3, endLng: 103.8, color: ['#00C8FF', '#00FF9D'], label: 'Sentinel-2A Orbit' },
      { startLat: 31.2, startLng: 121.5, endLat: 33.7, endLng: -118.3, color: ['#00C8FF', '#FF3D3D'], label: 'Sentinel-2B Orbit' }
    ];

    const flightArcs = activeLayers.includes('RETAIL') ? (movements.flights || []).map((f: any) => ({
      startLat: f.startLat,
      startLng: f.startLng,
      endLat: f.endLat,
      endLng: f.endLng,
      color: ['#FFFFFF', '#FFD700'],
      label: `${f.callsign} (${f.airline})`,
      country: f.country,
      eta: f.eta,
      origin_country: f.origin_country
    })) : [];

    return [...satelliteArcs, ...flightArcs];
  }, [movements.flights, activeLayers]);

  useEffect(() => {
    if (globeEl.current) {
      const globe = globeEl.current;
      globe.controls().autoRotate = true;
      globe.controls().autoRotateSpeed = 0.35;

      const scene = globe.scene();
      const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
      directionalLight.position.set(1, 1, 1);
      scene.add(directionalLight);
    }
  }, []);

  return (
    <div className={`w-full h-full relative group translate-x-[-22%] transition-transform duration-1000 scale-110 ${activeLayers.includes('CLOUDS') ? 'opacity-90' : 'opacity-100'}`}>
      <Globe
        ref={globeEl}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-dark.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        
        // Atmosphere
        showAtmosphere={true}
        atmosphereColor="#00C8FF"
        atmosphereAltitude={activeLayers.includes('CLOUDS') ? 0.25 : 0.18}
        
        // Points (Vessels and Ports)
        pointsData={[...filteredPlaces, ...filteredVessels.map((v: any) => ({ ...v, size: 0.05, color: '#00C8FF', isVessel: true }))]}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointRadius="size"
        pointAltitude={0.01}
        pointLabel={(d: any) => `
          <div class="glass-panel p-3 min-w-[220px]">
            <div class="flex justify-between items-center mb-1">
               <span class="type-h2">${d.name}</span>
               ${d.isVessel ? `<span class="type-data-xs px-1.5 py-0.5 bg-accent-primary/20 rounded border border-accent-primary/30 text-accent-primary">VESSEL</span>` : 
                `<span class="type-data-xs px-1.5 py-0.5 bg-void rounded border border-white/10 ${d.signal === 'BULLISH' ? 'text-bull' : 'text-bear'}">${d.signal}</span>`}
            </div>
            ${d.isVessel ? `
              <div class="flex flex-col gap-1 mt-2">
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>Origin</span><span class="text-bull font-bold">${d.origin_country || 'Unknown'}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>Flag State</span><span class="text-text-1 font-bold">${d.country}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>Destination</span><span class="text-accent-primary underline italic">${d.dest}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>ETA</span><span class="text-bull font-bold">${d.eta}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px] mt-2 border-t border-white/10 pt-1"><span>Cargo</span><span class="text-text-1 font-bold">${d.cargo || 'N/A'}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>Amount</span><span class="text-accent-primary font-bold">${d.amount || 'N/A'}</span></div>
              </div>
            ` : `
              <div class="type-data-md mb-2">Throughput: ${(d.throughput * 100).toFixed(1)}%</div>
              <div class="segment-bar">
                 ${Array.from({length: 10}).map((_, i) => `
                   <div class="segment ${i < (d.throughput * 10) ? (d.signal === 'BULLISH' ? 'active-bull' : 'active-bear') : ''}"></div>
                 `).join('')}
              </div>
            `}
          </div>
        `}
        
        // Pulsing Rings
        ringsData={[...places, ...(movements.vessels || []).filter((v:any) => v.cargo && v.cargo.includes('Fertilizer')).map((v: any) => ({ ...v, color: '#FFD700' }))]}
        ringLat="lat"
        ringLng="lng"
        ringColor={(d: any) => d.color}
        ringMaxRadius={3.5}
        ringPropagationSpeed={2}
        ringRepeatPeriod={2000}

        // Arcs (Satellite & Flights)
        arcsData={arcsData}
        arcColor="color"
        arcDashLength={0.6}
        arcDashGap={1.5}
        arcDashAnimateTime={3500}
        arcAltitudeAutoScale={0.7}
        arcStroke={0.8}
        arcLabel={(d: any) => `
          <div class="glass-panel p-3 min-w-[200px]">
            <div class="type-h2 mb-1">${d.label}</div>
            ${d.eta ? `
              <div class="flex flex-col gap-1 mt-1">
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>Origin</span><span class="text-text-2 font-bold">${d.origin_country || 'Unknown'}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>Dest Country</span><span class="text-bull font-bold">${d.country}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>Arrival</span><span class="text-bull font-bold">${d.eta}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px] mt-2 border-t border-white/10 pt-1"><span>Cargo</span><span class="text-text-1 font-bold">${d.cargo || 'N/A'}</span></div>
                <div class="flex justify-between text-text-4 uppercase text-[10px]"><span>Amount</span><span class="text-accent-primary font-bold">${d.amount || 'N/A'}</span></div>
              </div>
            ` : ''}
          </div>
        `}

        // Country Labels
        labelsData={countryLabels}
        labelLat="lat"
        labelLng="lng"
        labelText="name"
        labelSize={1.2}
        labelDotRadius={0.02}
        labelColor={() => 'rgba(255, 185, 0, 0.9)'} // Bloomberg Amber
        labelResolution={3}
      />
      
      {/* HUD Labels */}
      <div className="absolute top-6 left-[15%] pointer-events-none transition-all">
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
