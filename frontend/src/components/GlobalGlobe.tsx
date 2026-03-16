import React, { useEffect, useRef, useMemo } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';
import { useTerminalStore, useVesselStore, useFlightStore, useSatelliteStore, Satellite } from '../store';
import { countryLabels } from '../data/countries';
import { getVesselHTML } from './VesselPopup';
import { getFlightHTML } from './FlightPopup';
import { getPortHTML } from './PortPopup';

const GlobalGlobe: React.FC = () => {
  const { activeLayers, zoomLevel } = useTerminalStore();
  const { vessels, fetchVessels } = useVesselStore();
  const { flights, fetchFlights } = useFlightStore();
  const { satellites, fetchSatellites } = useSatelliteStore();
  const globeEl = useRef<any>(null);

  interface GlobeMarker {
    lat: number;
    lng: number;
    size: number;
    html: string;
    isVessel?: boolean;
    isFlight?: boolean;
    color?: string;
  }

  // Initial fetch and polling
  useEffect(() => {
    fetchVessels();
    fetchFlights();
    fetchSatellites();
    const interval = setInterval(() => {
      fetchVessels();
      fetchFlights();
      fetchSatellites();
    }, 15000);
    return () => clearInterval(interval);
  }, [fetchVessels, fetchFlights, fetchSatellites]);

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
    places.filter(p => activeLayers.includes(p.type || 'PORTS')).map(port => {
      const portCode = port.name.toUpperCase().replace(' PORT', '');
      const inboundVessels = vessels.filter((v: any) => 
        v.destination?.toUpperCase().includes(portCode) || 
        v.dest_locode === portCode
      );
      return { ...port, inboundVessels };
    }), 
  [activeLayers, places, vessels]);

  const filteredVessels = useMemo(() => 
    vessels.filter(() => activeLayers.includes('VESSELS')), 
  [activeLayers, vessels]);

  const filteredFlights = useMemo(() => 
    flights.filter(() => activeLayers.includes('FLIGHTS')), 
  [activeLayers, flights]);

  // Combined arcs (Satellite + Flights)
  const arcsData = useMemo(() => {
    const satelliteArcs = [
      { startLat: 51.9, startLng: 4.5, endLat: 1.3, endLng: 103.8, color: ['#00C8FF', '#00FF9D'], label: 'Sentinel-2A Orbit' },
      { startLat: 31.2, startLng: 121.5, endLat: 33.7, endLng: -118.3, color: ['#00C8FF', '#FF3D3D'], label: 'Sentinel-2B Orbit' }
    ];

    const flightArcs = activeLayers.includes('FLIGHTS') ? filteredFlights.map((f: any) => ({
      startLat: f.origin_lat || 0,
      startLng: f.origin_lon || 0,
      endLat: f.dest_lat || 0,
      endLng: f.dest_lon || 0,
      color: f.signal === 'BULLISH' ? ['#00FF9D', '#FFFFFF'] : ['#FFFFFF', '#FFB900'],
      label: `${f.callsign} (${f.operator})`,
      ...f
    })) : [];

    return [...satelliteArcs, ...flightArcs];
  }, [filteredFlights, activeLayers]);

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

  const htmlElements = useMemo(() => {
    const vesselEls = filteredVessels.map((v: any) => ({
      ...v,
      lat: v.position.lat,
      lng: v.position.lon,
      size: 24,
      isVessel: true,
      html: `
        <div class="asset-marker" style="color: ${v.color || '#00FF9D'}; transform: rotate(${(v.position.heading_degrees || 0) - 90}deg);">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" style="filter: drop-shadow(0 0 6px ${v.color || '#00FF9D'}); opacity: 0.9;">
            <path d="M21,16.5C21,16.88 20.79,17.21 20.47,17.38L12.57,21.82C12.41,21.94 12.21,22 12,22C11.79,22 11.59,21.94 11.43,21.82L3.53,17.38C3.21,17.21 3,16.88 3,16.5V7.5C3,7.12 3.21,6.79 3.53,6.62L11.43,2.18C11.59,2.06 11.79,2 12,2C12.21,2 12.41,2.06 12.57,2.18L20.47,6.62C20.79,6.79 21,7.12 21,7.5V16.5Z" />
          </svg>
        </div>
      `
    }));

    const flightEls = filteredFlights.map((f: any) => ({
      ...f,
      lat: f.current_position.lat,
      lng: f.current_position.lon,
      size: 24,
      isFlight: true,
      html: `
        <div class="asset-marker" style="color: ${f.color || '#C084FC'}; transform: rotate(${(f.current_position.heading_degrees || 0) - 90}deg);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" style="filter: drop-shadow(0 0 6px ${f.color || '#C084FC'});">
            <path d="M21,16L22,19H15V22H13V19H10L9,15H2V13H9L10,9V2H12V9L13,13H20V15H13L15,18H21V16Z" />
          </svg>
        </div>
      `
    }));

    return [...vesselEls, ...flightEls] as GlobeMarker[];
  }, [filteredVessels, filteredFlights]);

  const pathsData = useMemo(() => {
    const vesselPaths = filteredVessels.map((v: any) => ({
      coords: (v.historical_track || []).map((p: any) => [p.lon, p.lat, 0.005]),
      color: v.color || '#00FF9D'
    }));

    const flightPaths = filteredFlights.map((f: any) => ({
      coords: (f.historical_track || []).map((p: any) => [p.lon, p.lat, 0.02]),
      color: f.color || '#C084FC'
    }));

    return [...vesselPaths, ...flightPaths];
  }, [filteredVessels, filteredFlights]);

  return (
    <div className={`w-full h-full relative group translate-x-[-35%] transition-transform duration-1000 scale-110 ${activeLayers.includes('CLOUDS') ? 'opacity-90' : 'opacity-100'}`}>
      <Globe
        ref={globeEl}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-dark.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        
        // Atmosphere
        showAtmosphere={true}
        atmosphereColor="#00C8FF"
        atmosphereAltitude={activeLayers.includes('CLOUDS') ? 0.25 : 0.18}
        
        // Custom HTML Markers (Vessels & Flights)
        htmlElementsData={htmlElements}
        htmlElement={(d: object) => {
          const marker = d as GlobeMarker;
          const el = document.createElement('div');
          el.innerHTML = marker.html;
          el.style.width = `${marker.size}px`;
          el.style.pointerEvents = 'auto';
          el.style.cursor = 'pointer';
          return el;
        }}
        htmlLat="lat"
        htmlLng="lng"

        // Points (Ports and High-Density Satellites)
        pointsData={[
          ...filteredPlaces, 
          ...(activeLayers.includes('SATELLITES') ? satellites.map((s: Satellite) => ({ ...s, size: 0.03, color: s.color || '#00C8FF', type: 'SATELLITE' })) : [])
        ]}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointRadius="size"
        pointAltitude={(d: any) => d.type === 'SATELLITE' ? 0.08 : 0.01}
        pointLabel={(d: any) => `
            <div style="background: rgba(0,0,0,0.85); padding: 10px; border: 1px solid ${d.color}; font-family: 'JetBrains Mono', monospace; border-radius: 4px; box-shadow: 0 0 15px ${d.color}44;">
                <div style="color: ${d.color}; font-weight: bold; font-size: 12px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span style="width: 8px; h-8px; border-radius: 50%; background: ${d.color}; display: inline-block;"></span>
                    ${d.name || 'SATELLITE TRK'}
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 10px;">
                    <span style="color: #6B7E99;">CATEGORY</span><span style="color: #fff; text-align: right;">${d.category || 'SIGNAL'}</span>
                    <span style="color: #6B7E99;">ALTITUDE</span><span style="color: #fff; text-align: right;">${d.altitude || '350km'}</span>
                    <span style="color: #6B7E99;">OWNER</span><span style="color: #fff; text-align: right;">${d.owner || 'Copernicus'}</span>
                </div>
            </div>
        `}
        
        // Pulsing Rings (Signal Intensity)
        ringsData={[
          ...places.filter(p => p.signal === 'BULLISH'), 
          ...filteredVessels.filter((v:any) => v.signal === 'BULLISH' && v.position).map((v: any) => ({ 
            lat: v.position.lat, 
            lng: v.position.lon, 
            color: '#00FF9D' 
          })),
          ...filteredFlights.filter((f:any) => f.signal === 'BULLISH' && f.position).map((f: any) => ({
            lat: f.position.lat,
            lng: f.position.lon,
            color: '#00C8FF'
          }))
        ]}
        ringLat="lat"
        ringLng="lng"
        ringColor={(d: any) => d.color}
        ringMaxRadius={2.5}
        ringPropagationSpeed={3}
        ringRepeatPeriod={1500}

        // Historical Paths (24h Track)
        pathsData={pathsData}
        pathPoints="coords"
        pathPointLat={(p: any) => p[1]}
        pathPointLng={(p: any) => p[0]}
        pathPointAlt={(p: any) => p[2]}
        pathColor={(d: any) => d.color}
        pathDashLength={0.1}
        pathDashGap={0.05}
        pathDashAnimateTime={10000}
        pathStroke={1.5}

        // Arcs (Satellite & Active Flight Vectors)
        arcsData={arcsData}
        arcColor={(d: any) => d.color}
        arcDashLength={0.5}
        arcDashGap={1.2}
        arcDashAnimateTime={3000}
        arcStroke={0.5}
        arcAltitudeAutoScale={0.3}

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
            <p className="type-data-xs text-text-3 uppercase tracking-[0.2em]">Institutional Engine Active</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlobalGlobe;
