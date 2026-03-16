import React, { useEffect, useRef, useMemo } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';
import { useTerminalStore, useVesselStore, useFlightStore } from '../store';
import { countryLabels } from '../data/countries';
import { getVesselHTML } from './VesselPopup';
import { getFlightHTML } from './FlightPopup';
import { getPortHTML } from './PortPopup';

const GlobalGlobe: React.FC = () => {
  const { activeLayers, zoomLevel } = useTerminalStore();
  const { vessels, fetchVessels } = useVesselStore();
  const { flights, fetchFlights } = useFlightStore();
  const globeEl = useRef<any>(null);

  // Initial fetch and polling
  useEffect(() => {
    fetchVessels();
    fetchFlights();
    const interval = setInterval(() => {
      fetchVessels();
      fetchFlights();
    }, 15000);
    return () => clearInterval(interval);
  }, [fetchVessels, fetchFlights]);

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
      size: 20,
      isVessel: true,
      html: `
        <div class="asset-marker" style="color: ${v.color || '#6B7E99'}; transform: rotate(${v.heading_deg || 0}deg);">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="filter: drop-shadow(0 0 4px currentColor);">
            <path d="M4,15C4,15 5,19 12,19C19,19 20,15 20,15V13L12,14L4,13V15M12,2L5,5V11C5,11 5,14 12,14C19,14 19,11 19,11V5L12,2Z" />
          </svg>
        </div>
      `
    }));

    const flightEls = filteredFlights.map((f: any) => ({
      ...f,
      lat: f.position.lat,
      lng: f.position.lon,
      size: 20,
      isFlight: true,
      html: `
        <div class="asset-marker" style="color: ${f.color || '#6B7E99'}; transform: rotate(${f.heading || 0}deg);">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="filter: drop-shadow(0 0 4px currentColor);">
            <path d="M21,16L22,19H15V22H13V19H10L9,15H2V13H9L10,9V2H12V9L13,13H20V15H13L15,18H21V16Z" />
          </svg>
        </div>
      `
    }));

    return [...vesselEls, ...flightEls];
  }, [filteredVessels, filteredFlights]);

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
        
        // Custom HTML Markers (Vessels & Flights)
        htmlElementsData={htmlElements}
        htmlElement={(d: any) => {
          const el = document.createElement('div');
          el.innerHTML = d.html;
          el.style.width = `${d.size}px`;
          el.style.pointerEvents = 'auto';
          el.style.cursor = 'pointer';
          return el;
        }}
        htmlLat="lat"
        htmlLng="lng"

        // Points (Ports and Satellites)
        pointsData={[
          ...filteredPlaces, 
          { lat: 51.9, lng: 4.5, name: 'Sentinel-2A', color: '#00C8FF', size: 0.15, isSatellite: true },
          { lat: 31.2, lng: 121.5, name: 'Sentinel-2B', color: '#00C8FF', size: 0.15, isSatellite: true }
        ]}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointRadius="size"
        pointAltitude={0.01}
        pointLabel={(d: any) => d.isSatellite ? `Satellite: ${d.name}` : getPortHTML(d)}
        
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

        // Arcs (Satellite & Flight Paths)
        arcsData={arcsData}
        arcColor="color"
        arcDashLength={0.5}
        arcDashGap={1.2}
        arcDashAnimateTime={2500}
        arcAltitudeAutoScale={0.4}
        arcStroke={0.6}
        arcLabel={(d: any) => d.callsign ? getFlightHTML(d) : d.mmsi ? getVesselHTML(d) : `Path: ${d.label}`}

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
            <p className="type-data-xs text-text-3 uppercase tracking-[0.2em]">Live Vessel & Flight Intelligence Feed</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlobalGlobe;
