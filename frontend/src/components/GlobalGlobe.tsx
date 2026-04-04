import React, { useEffect, useRef, useMemo, useCallback } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';
import { useTerminalStore, useEquityStore } from '../store';
import { countryLabels } from '../data/countries';
import { api, connectLive } from '../api/client';

const COL = {
  bull:    '#00FF9D',
  bear:    '#FF4560',
  neutral: '#6B7E99',
  signal:  '#00D4FF',
  warn:    '#FFB800',
  purple:  '#C084FC',
};

interface HexBin {
  lat: number;
  lng: number;
  weight: number;
  ticker: string;
  label: string;
  signal?: string;
  score?: number;
}

interface Satellite {
  name: string;
  lat: number;
  lon: number;
  alt_km: number;
  next_lat?: number;
  next_lon?: number;
}

const GlobalGlobe: React.FC = () => {
  const { activeLayers, zoomLevel, setView, setCurrentTicker } = useTerminalStore();
  const { addToWatchlist } = useEquityStore();
  const globeEl = useRef<any>(null);

  const [countries, setCountries] = React.useState<any>({ features: [] });
  useEffect(() => {
    fetch('/countries.json')
      .then(res => res.json())
      .then(setCountries)
      .catch((e) => console.error("GeoJSON load fail:", e));
  }, []);

  const [thermalBins, setThermalBins] = React.useState<HexBin[]>([]);
  const [quakes, setQuakes] = React.useState<any[]>([]);
  const [conflicts, setConflicts] = React.useState<any[]>([]);
  const [strategic, setStrategic] = React.useState<any>({
    chokepoints: [],
  });
  
  const [vessels, setVessels] = React.useState<any[]>([]);
  const [flights, setFlights] = React.useState<any[]>([]);
  const [satellites, setSatellites] = React.useState<any[]>([]);

  const fetchStrategic = useCallback(async () => {
    try {
      const data = await api.chokepoints();
      setStrategic({ chokepoints: data.chokepoints || [] });
    } catch {}
  }, []);

  const fetchThermal = useCallback(async () => {
    try {
      const d = await api.thermal();
      const sigs = d.clusters || [];
      const bins: HexBin[] = sigs.map((s: any) => ({
        lat: s.lat || 0,
        lng: s.lon || 0,
        weight: Math.min((s.frp_avg || 50) / 100, 1),
        ticker: s.tickers?.[0] || 'N/A',
        label: s.name || 'Industrial Facility',
        signal: s.signal,
        score: s.score
      }));
      setThermalBins(bins);
    } catch {}
  }, []);

  const fetchConflicts = useCallback(async () => {
    try {
      const d = await api.conflicts();
      setConflicts(d.events || []);
    } catch {}
  }, []);
  
  const fetchVesselsData = useCallback(async () => {
    try {
      const d = await api.vessels();
      setVessels(d.vessels || []);
    } catch {}
  }, []);
  
  const fetchSatellitesData = useCallback(async () => {
    try {
      const d = await api.satellites();
      setSatellites(d.satellites || []);
    } catch {}
  }, []);

  useEffect(() => {
    fetchVesselsData();
    fetchSatellitesData();
    fetchThermal();
    fetchConflicts();
    fetchStrategic();  // Load real OSINT intelligence layers
    
    api.aircraft().then(d => setFlights(d.features || []));

    const unsub = connectLive(data => {
      if(data.type==="LIVE_UPDATE") {
        setFlights(data.aircraft?.features || []);
        // if(data.squawks.length > 0) showSquawkAlert(data.squawks[0])
      }
    });

    return () => unsub();
  }, [fetchVesselsData, fetchSatellitesData, fetchThermal, fetchConflicts, fetchStrategic]);

  useEffect(() => {
    if (!globeEl.current) return;
    const altitude = Math.max(0.2, 1.6 / (zoomLevel || 1));
    globeEl.current.pointOfView({ lat: 28, lng: 10, altitude }, 1200);
  }, [zoomLevel]);

  useEffect(() => {
    if (!globeEl.current) return;
    const globe = globeEl.current;
    globe.controls().autoRotate = true;
    globe.controls().autoRotateSpeed = 0.25;
    globe.controls().enableDamping = true;
    globe.controls().dampingFactor = 0.08;

    const scene = globe.scene();
    scene.add(new THREE.AmbientLight(0xaabbcc, 1.2));
    const sun = new THREE.DirectionalLight(0xffeedd, 2.5);
    sun.position.set(5, 3, 2);
    scene.add(sun);
    const rim = new THREE.DirectionalLight(0x3366ff, 0.6);
    rim.position.set(-3, -2, -3);
    scene.add(rim);
  }, []);

  const pointsData = useMemo(() => {
    const thermal = activeLayers.includes('THERMAL')
      ? thermalBins.map(b => ({
          name: b.label, lat: b.lat, lng: b.lng,
          size: 0.05 + b.weight * 0.12,
          color: `rgba(255, 122, 61, ${0.4 + b.weight * 0.6})`,
          type: 'THERMAL', ticker: b.ticker, signal: b.signal,
        }))
      : [];

    const sats = activeLayers.includes('SATELLITES')
      ? satellites.map((s: Satellite) => ({
          ...s, size: 0.03, color: COL.signal, type: 'SATELLITE',
        }))
      : [];
      
    const eq: any[] = []; // No longer needed
    return [...thermal, ...sats, ...eq];
  }, [activeLayers, thermalBins, satellites, quakes]);

  const filteredVessels = useMemo(() => (activeLayers.includes('VESSELS') ? vessels : []), [activeLayers, vessels]);
  const filteredFlights = useMemo(() => (activeLayers.includes('AIRCRAFT') ? flights : []), [activeLayers, flights]);

  const arcsData = useMemo(() => {
    const satArcs = activeLayers.includes('SATELLITES')
      ? satellites.filter((s:any) => s.next_lat !== undefined).map((s:any) => ({
          startLat: s.lat, startLng: s.lon, endLat: s.next_lat, endLng: s.next_lon,
          color: [COL.signal, COL.bull], label: `${s.name} Orbit`
        }))
      : [];
    return [...satArcs];
  }, [satellites, activeLayers]);

  const handleGlobeClick = useCallback((d: any) => {
    if (!d) return;
    const ticker = d.ticker;
    if (ticker && ticker !== 'N/A') {
      addToWatchlist(ticker);
      setCurrentTicker(ticker);
      setView('charts');
    }
  }, [addToWatchlist, setCurrentTicker, setView]);

  const handleHexClick = useCallback((hex: any) => {
    if (hex && hex.points && hex.points.length > 0) {
      handleGlobeClick(hex.points[0]);
    }
  }, [handleGlobeClick]);

  const ringsData = useMemo(() => {
    const darkVesselRings = filteredVessels
      .filter((v: any) => v.dark)
      .map((v: any) => ({
        lat: v.lat ?? 0, lng: v.lon ?? 0,
        color: COL.bear, maxR: 3, propSpeed: 4, period: 1200,
      }));
    const quakeRings: any[] = [];
    return [...darkVesselRings, ...quakeRings];
  }, [filteredVessels, quakes, activeLayers]);

  const htmlElementsData = useMemo(() => {
    const data: any[] = [];

    // ── Active War Zones & Conflicts (OSINT, real GDELT) ──
    if (activeLayers.includes('CONFLICTS')) {
      conflicts.forEach(c => data.push({
        lat: c.lat, lng: c.lon, size: c.severity === 'CRITICAL' ? 32 : 24, color: COL.bear,
        label: `CONFLICT: ${c.type}`, shape: 'conflict',
        risk: c.severity, ticker: c.tickers?.[0]
      }));
    }

    if (activeLayers.includes('HOTSPOTS') || activeLayers.includes('WATERWAYS') || activeLayers.includes('CHOKEPOINTS')) {
      (strategic.chokepoints || []).forEach((c: any) => data.push({
        lat: c.lat, lng: c.lon, size: 30, color: '#00ccff',
        label: `🚢 ${c.name}\nRisk: ${c.threat_level}`,
        name: c.name, type: 'CHOKEPOINT', shape: 'hotspot',
        risk: c.threat_level, alt_route: c.alt_route,
      }));
    }

    if (activeLayers.includes('VESSELS') && zoomLevel > 3) {
      filteredVessels.forEach(v => data.push({
        lat: v.lat, lng: v.lon, size: 8, color: COL.signal,
        label: `${v.name || 'VESSEL'}\n${v.type || ''}`, shape: 'vessel',
        type: 'VESSEL'
      }));
    }

    if (activeLayers.includes('AIRCRAFT') && zoomLevel > 5) {
      filteredFlights.forEach(f => {
        const props = f.properties || f;
        data.push({
          lat: props.lat || f.geometry?.coordinates[1],
          lng: props.lon || f.geometry?.coordinates[0],
          size: 6, color: COL.purple,
          label: `${props.callsign || 'FLIGHT'}\n${props.origin_country || ''}`, shape: 'flight',
          type: 'AIRCRAFT'
        });
      });
    }

    return data;
  }, [conflicts, strategic, activeLayers]);

  const buildHtmlElement = useCallback((d: any) => {
    const el = document.createElement('div');
    el.style.cssText = `pointer-events:auto;cursor:pointer;position:relative;display:flex;align-items:center;justify-content:center;transform:translate(-50%,-50%);`;
    el.title = d.label || d.name || '';

    const pulseAnim = d.shape === 'nuclear' ? '2.5s' : '1.5s';
    const badge = d.name ? d.name.toUpperCase().slice(0, 20) : (d.risk ? d.risk.toUpperCase() : '');
    const badgeColor = d.color || '#ff0033';

    let iconSvg = '';
    if (d.shape === 'conflict' || d.shape === 'hotspot') {
      iconSvg = `<polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" fill="none" stroke="${d.color}" stroke-width="1.5"/><circle cx="12" cy="12" r="3" fill="${d.color}" />`;
    } else if (d.shape === 'base') {
      iconSvg = `<rect x="4" y="4" width="16" height="16" fill="none" stroke="${d.color}" stroke-width="1.5"/><path d="M4 12h16 M12 4v16" stroke="${d.color}" stroke-width="1.5"/>`;
    } else if (d.shape === 'nuclear') {
      iconSvg = `<circle cx="12" cy="12" r="10" fill="none" stroke="${d.color}" stroke-width="1.5"/><path d="M12 12l5.5-3 M12 12l-5.5-3 M12 12v6" stroke="${d.color}" stroke-width="2"/>`;
    } else if (d.shape === 'outage') {
      iconSvg = `<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="${d.color}"/>`;
    }

    const showBadge = d.type === 'WAR' || d.type === 'GEOPOLITICAL' || d.shape === 'nuclear' || (d.risk && d.risk !== 'LOW');

    el.innerHTML = `
      <div style="position:relative;width:${d.size}px;height:${d.size}px;display:flex;align-items:center;justify-content:center;">
        <div style="position:absolute;inset:-12px;background:radial-gradient(circle, ${d.color} 0%, transparent 70%);opacity:0.35;border-radius:50%;animation:pulseRing ${pulseAnim} ease-out infinite;"></div>
        <div style="position:absolute;inset:-4px;border:1px solid ${d.color};opacity:0.5;border-radius:50%;animation:spinRing 4s linear infinite;"></div>
        <svg style="position:relative;z-index:2;filter:drop-shadow(0 0 10px ${d.color});" width="${d.size}" height="${d.size}" viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
          ${iconSvg}
        </svg>
        ${showBadge ? `<div style="position:absolute;top:-22px;left:50%;transform:translateX(-50%);background:rgba(2,6,15,0.95);border:1px solid ${badgeColor};color:${badgeColor};font-size:8px;padding:2px 5px;border-radius:2px;white-space:nowrap;font-family:'IBM Plex Mono',monospace;font-weight:bold;letter-spacing:0.08em;max-width:120px;overflow:hidden;text-overflow:ellipsis;">${badge}</div>` : ''}
      </div>
      <style>
        @keyframes pulseRing { 0% { transform: scale(0.3); opacity: 0.8; } 100% { transform: scale(2.0); opacity: 0; } }
        @keyframes spinRing { 100% { transform: rotate(360deg); } }
      </style>
    `;
    return el;
  }, []);

  const buildPointLabel = useCallback((d: any): string => `
    <div style="
      background:rgba(7,11,15,0.95);border:1px solid ${d.color || COL.signal};
      padding:10px 14px;font-family:'IBM Plex Mono',monospace;border-radius:3px;
      box-shadow:0 0 20px ${d.color || COL.signal}33;min-width:180px;
    ">
      <div style="color:${d.color || COL.signal};font-weight:700;font-size:12px;margin-bottom:6px;letter-spacing:0.08em">
        ${d.name?.toUpperCase() || 'FACILITY'}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:10px;color:#8B949E">
        <span>TYPE</span><span style="color:#E6EDF3;text-align:right">${d.type || d.signal || 'N/A'}</span>
        ${d.ticker ? `<span>TICKER</span><span style="color:${COL.bull};text-align:right;font-weight:700">${d.ticker}</span>` : ''}
      </div>
    </div>
  `, []);

  useEffect(() => {
    if (!globeEl.current) return;
    const scene = globeEl.current.scene();

    const vesselGeo = new THREE.ConeGeometry(0.5, 2, 8);
    vesselGeo.rotateX(Math.PI / 2);
    const vesselMat = new THREE.MeshPhysicalMaterial({ color: 0x00FF9D, emissive: 0x00FF9D, emissiveIntensity: 2.0, clearcoat: 1.0, roughness: 0.1 });
    const vesselMesh = new THREE.InstancedMesh(vesselGeo, vesselMat, 10000);
    vesselMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    vesselMesh.name = 'vessels_instanced';
    
    const flightGeo = new THREE.BoxGeometry(0.8, 0.1, 0.8);
    const flightMat = new THREE.MeshPhysicalMaterial({ color: 0xBD93F9, emissive: 0xBD93F9, emissiveIntensity: 1.8, clearcoat: 1.0, roughness: 0.1 });
    const flightMesh = new THREE.InstancedMesh(flightGeo, flightMat, 25000);
    flightMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    flightMesh.name = 'flights_instanced';

    scene.add(vesselMesh);
    scene.add(flightMesh);

    const starsGeo = new THREE.BufferGeometry();
    const starsPos = [];
    for (let i = 0; i < 15000; i++) starsPos.push((Math.random() - 0.5) * 2000, (Math.random() - 0.5) * 2000, (Math.random() - 0.5) * 2000);
    starsGeo.setAttribute('position', new THREE.Float32BufferAttribute(starsPos, 3));
    const starsMat = new THREE.PointsMaterial({ color: 0x888888, size: 1.5, sizeAttenuation: true });
    const stars = new THREE.Points(starsGeo, starsMat);
    scene.add(stars);

    return () => { scene.remove(vesselMesh); scene.remove(flightMesh); scene.remove(stars); };
  }, []);

  useEffect(() => {
    if (!globeEl.current) return;
    const globe = globeEl.current;
    const vMesh = globe.scene().getObjectByName('vessels_instanced') as any;
    const fMesh = globe.scene().getObjectByName('flights_instanced') as any;
    if (!vMesh || !fMesh) return;

    const dummy = new THREE.Object3D();

    filteredVessels.forEach((v: any, i: number) => {
      if (i >= 10000) return;
      const lat = v.lat || 0;
      const lon = v.lon || 0;
      const pos = globe.getCoords(lat, lon, 0.01);
      dummy.position.set(pos.x, pos.y, pos.z);
      dummy.lookAt(0, 0, 0); dummy.rotateY(Math.PI / 2); dummy.updateMatrix();
      vMesh.setMatrixAt(i, dummy.matrix);
    });
    vMesh.count = Math.min(filteredVessels.length, 10000);
    vMesh.instanceMatrix.needsUpdate = true;

    filteredFlights.forEach((feature: any, i: number) => {
      if (i >= 25000) return;
      const f = feature.properties || feature;
      const lat = f.lat || feature.geometry?.coordinates[1] || 0;
      const lon = f.lon || feature.geometry?.coordinates[0] || 0;
      const heading = f.heading || 0;
      const pos = globe.getCoords(lat, lon, 0.08); 
      dummy.position.set(pos.x, pos.y, pos.z);
      dummy.lookAt(0, 0, 0);
      dummy.rotateY((heading - 90) * (Math.PI/180));
      dummy.updateMatrix();
      
      let c = new THREE.Color(0xBD93F9); // default purple (commercial)
      if (f.category === 'MILITARY') c.setHex(0xFF4560);
      else if (f.category === 'CARGO') c.setHex(0xFFA500);
      else if (f.category === 'GOVERNMENT') c.setHex(0xFFD700);
      fMesh.setColorAt(i, c);
      fMesh.setMatrixAt(i, dummy.matrix);
    });
    fMesh.count = Math.min(filteredFlights.length, 25000);
    if(fMesh.count > 0) fMesh.instanceColor.needsUpdate = true;
    fMesh.instanceMatrix.needsUpdate = true;
  }, [filteredVessels, filteredFlights]);

  const pathsData = useMemo(() => {
    if (!activeLayers.includes('SATELLITES')) return [];
    return satellites.map((s: any) => ({
      coords: s.ground_track.map((p: any) => [p.lat, p.lon]),
      color: COL.signal,
      name: s.name
    }));
  }, [satellites, activeLayers]);

  return (
    <div className={`w-full h-full relative transition-opacity duration-500`}>
      <Globe
        ref={globeEl}
        globeImageUrl={undefined} bumpImageUrl={undefined}
        polygonsData={countries.features}
        polygonCapColor={() => '#040b16'}
        polygonSideColor={() => 'rgba(0, 212, 255, 0.15)'}
        polygonStrokeColor={() => '#38bdf8'}
        showGraticules={true} showAtmosphere atmosphereColor="#38bdf8" atmosphereAltitude={0.25}
        
        pathsData={pathsData}
        pathColor={(d: any) => d.color}
        pathDashLength={0.1}
        pathDashGap={0.008}
        pathDashAnimateTime={12000}
        pathStroke={0.4}
        
        hexBinPointsData={activeLayers.includes('THERMAL') ? thermalBins : []}
        hexBinPointWeight="weight" hexBinResolution={4} hexMargin={0.1}
        hexColor={() => '#FF4560'} hexLabel={buildPointLabel}
        onHexPolygonClick={handleHexClick}
        
        pointsData={pointsData} pointLat="lat" pointLng="lng" pointColor="color" pointRadius="size"
        pointAltitude={(d: any) => d.type === 'SATELLITE' ? 0.10 : 0.01} pointLabel={buildPointLabel}
        onPointClick={handleGlobeClick}
        
        htmlElementsData={htmlElementsData} htmlElement={buildHtmlElement}
        
        ringsData={ringsData} ringLat="lat" ringLng="lng" ringColor={(d: any) => d.color}
        ringMaxRadius={(d: any) => d.maxR || 2.5} ringPropagationSpeed={(d: any) => d.propSpeed || 3}
        ringRepeatPeriod={(d: any) => d.period || 1500}
        
        arcsData={arcsData} arcColor={(d: any) => d.color} arcDashLength={0.45} arcDashGap={1.5}
        arcDashAnimateTime={3500} arcStroke={0.5} arcAltitudeAutoScale={0.3}
        arcLabel={(d: any) => `<div style="background:rgba(7,11,15,0.95);padding:8px;border:1px solid ${COL.signal};font-family:monospace;font-size:10px;color:white;box-shadow: 0 0 10px ${COL.signal}40;"><strong>${d.label.toUpperCase()}</strong></div>`}
        
        labelsData={useMemo(() => {
          const altitude = zoomLevel ? 4 / zoomLevel : 2.5;
          const limit = altitude < 0.6 ? 500 : altitude < 1.2 ? 300 : 150;
          return countryLabels.slice(0, limit);
        }, [zoomLevel])}
        labelLat="lat" labelLng="lng" labelText={(d: any) => d.name.toUpperCase()}
        labelSize={(d: any) => 0.5} labelColor={() => '#38bdf8'} labelResolution={4}
        labelIncludeDot={true} labelDotRadius={0.15} labelAltitude={0.015}
        
        backgroundColor="rgba(0,0,0,0)"
        globeMaterial={new THREE.MeshPhysicalMaterial({
          color: '#000000',
          metalness: 0.8,
          roughness: 0.2,
          transparent: true,
          opacity: 0.9,
          emissive: '#020617',
          emissiveIntensity: 0.5,
          clearcoat: 1.0,
          clearcoatRoughness: 0.2,
        })}
        rendererConfig={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      />
      
      <div className="absolute top-4 right-4 pointer-events-none z-10 flex flex-col gap-1.5">
        {[
          { label: 'VESSELS', val: filteredVessels.length, col: COL.signal },
          { label: 'AIRCRAFT', val: filteredFlights.length, col: COL.purple },
          { label: 'THERMAL', val: thermalBins.length, col: '#FF7A3D' },
          { label: 'QUAKES', val: quakes.length, col: COL.warn },
          { label: 'CONFLICTS', val: conflicts.length, col: COL.bear },
        ].map(({ label, val, col }) => (
          <div key={label} style={{ borderColor: `${col}40` }} className="flex items-center gap-2 bg-black/70 backdrop-blur-sm border px-2.5 py-1 rounded-sm shadow-2xl">
            <span className="font-mono text-[10px] tracking-widest uppercase" style={{ color: col }}>{label}</span>
            <span className="font-mono text-[11px] font-bold text-white tabular-nums">{val.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GlobalGlobe;
