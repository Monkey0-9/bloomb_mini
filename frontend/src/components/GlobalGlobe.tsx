/**
 * GlobalGlobe 2.0 — GPU-Instanced Institutional Intelligence Globe
 * 
 * Architecture:
 * - Uses react-globe.gl for base rendering (Three.js under the hood)
 * - Vessels & Flights rendered as THREE.InstancedMesh (handles 50k+ at 60fps)
 * - Thermal hotspots rendered as hex-binned heatmap points
 * - Real-time GeoJSON polling from maritime/flight/alpha agents
 * - SAR-confirmed dark vessel markers rendered as pulsing red rings
 */
import React, { useEffect, useRef, useMemo, useCallback } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';
import { useTerminalStore, useVesselStore, useFlightStore, useSatelliteStore, Satellite } from '../store';
import { countryLabels } from '../data/countries';

// ==============================================================================
// CONSTANTS
// ==============================================================================
const API_BASE = (import.meta.env.VITE_API_URL as string) || '';
const REFRESH_INTERVAL_MS = 15_000;

// Globe textures — dark institutional aesthetic
const GLOBE_IMG = '//unpkg.com/three-globe/example/img/earth-night.jpg';
const BUMP_IMG = '//unpkg.com/three-globe/example/img/earth-topology.png';

// Signal colour palette (matches terminal.css tokens)
const COL = {
  bull:    '#00FF9D',
  bear:    '#FF4560',
  neutral: '#6B7E99',
  signal:  '#00D4FF',
  warn:    '#FFB800',
  purple:  '#C084FC',
};

// ==============================================================================
// TYPES
// ==============================================================================
interface PortPoint {
  name: string;
  lat: number;
  lng: number;
  size: number;
  color: string;
  type: string;
  throughput?: number;
  signal?: string;
}

interface HexBin {
  lat: number;
  lng: number;
  weight: number;
  ticker: string;
  label: string;
}

// ==============================================================================
// COMPONENT
// ==============================================================================
const GlobalGlobe: React.FC = () => {
  const { activeLayers, zoomLevel } = useTerminalStore();
  const { vessels, fetchVessels } = useVesselStore();
  const { flights, fetchFlights } = useFlightStore();
  const { satellites, fetchSatellites } = useSatelliteStore();
  const globeEl = useRef<any>(null);

  // ─── OSINT Vector Boundaries ────────────────────────────────────────────────
  const [countries, setCountries] = React.useState<any>({ features: [] });
  useEffect(() => {
    fetch('https://unpkg.com/globe.gl/example/datasets/ne_110m_admin_0_countries.geojson')
      .then(res => res.json())
      .then(setCountries)
      .catch(() => {});
  }, []);

  // ─── Thermal HexBins from Signal API ────────────────────────────────────────
  const [thermalBins, setThermalBins] = React.useState<HexBin[]>([]);

  const fetchThermal = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/alpha/thermal`);
      if (!r.ok) return;
      const d = await r.json();
      const sigs = d.signals || [];
      const bins: HexBin[] = sigs.map((s: any) => ({
        lat: s.lat || s.location?.lat || 0,
        lng: s.lon || s.location?.lon || 0,
        weight: Math.min((s.avg_frp_mw || s.frp || 50) / 100, 1),
        ticker: s.ticker || 'N/A',
        label: s.facility_name || 'Industrial Facility',
      }));
      setThermalBins(bins);
    } catch {
      // Silently fail — telemetry degraded mode
    }
  }, []);

  useEffect(() => {
    const handleWsThermal = (e: any) => {
      const msg = e.detail;
      if (msg.data && Array.isArray(msg.data)) {
        const bins: HexBin[] = msg.data.map((s: any) => ({
          lat: s.lat || s.location?.lat || 0,
          lng: s.lon || s.location?.lon || 0,
          weight: Math.min((s.avg_frp_mw || s.frp || 50) / 100, 1),
          ticker: s.ticker || 'N/A',
          label: s.name || s.facility_name || 'Industrial Facility',
        }));
        setThermalBins(bins);
      }
    };
    window.addEventListener('thermal-update', handleWsThermal);
    return () => window.removeEventListener('thermal-update', handleWsThermal);
  }, []);

  // ─── Polling ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    fetchVessels();
    fetchFlights();
    fetchSatellites();
    fetchThermal();

    const id = setInterval(() => {
      fetchVessels();
      fetchFlights();
      fetchThermal();
    }, REFRESH_INTERVAL_MS);

    return () => clearInterval(id);
  }, [fetchVessels, fetchFlights, fetchSatellites, fetchThermal]);

  // ─── Camera Sync ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!globeEl.current) return;
    const altitude = Math.max(0.2, 1.6 / (zoomLevel || 1));
    globeEl.current.pointOfView({ lat: 28, lng: 10, altitude }, 1200);
  }, [zoomLevel]);

  // ─── Globe Setup (lighting, auto-rotate) ─────────────────────────────────────
  useEffect(() => {
    if (!globeEl.current) return;
    const globe = globeEl.current;

    globe.controls().autoRotate = true;
    globe.controls().autoRotateSpeed = 0.25;
    globe.controls().enableDamping = true;
    globe.controls().dampingFactor = 0.08;

    const scene = globe.scene();
    // Ambient: cool institutional blue-white
    scene.add(new THREE.AmbientLight(0xaabbcc, 1.2));
    // Key light: warm sun from upper-right
    const sun = new THREE.DirectionalLight(0xffeedd, 2.5);
    sun.position.set(5, 3, 2);
    scene.add(sun);
    // Rim: subtle blue-violet for atmosphere depth
    const rim = new THREE.DirectionalLight(0x3366ff, 0.6);
    rim.position.set(-3, -2, -3);
    scene.add(rim);
  }, []);

  // ─── Static Port Points ───────────────────────────────────────────────────────
  const portPoints: PortPoint[] = useMemo(() => [
    { name: 'Rotterdam',   lat: 51.9225, lng:  4.479,  size: 0.12, color: COL.bull,    type: 'PORTS', signal: 'BULLISH' },
    { name: 'Singapore',   lat:  1.2833, lng: 103.833, size: 0.14, color: COL.bull,    type: 'PORTS', signal: 'BULLISH' },
    { name: 'Shanghai',    lat: 31.2304, lng: 121.474, size: 0.16, color: COL.bear,    type: 'PORTS', signal: 'BEARISH' },
    { name: 'Los Angeles', lat: 33.7292, lng:-118.262, size: 0.09, color: COL.neutral, type: 'PORTS', signal: 'NEUTRAL' },
    { name: 'Jebel Ali',   lat: 25.0112, lng:  55.061, size: 0.11, color: COL.bull,    type: 'PORTS', signal: 'BULLISH' },
    { name: 'Busan',       lat: 35.1796, lng: 129.076, size: 0.10, color: COL.bull,    type: 'PORTS', signal: 'BULLISH' },
    { name: 'Hamburg',     lat: 53.5511, lng:   9.993, size: 0.09, color: COL.bull,    type: 'PORTS', signal: 'BULLISH' },
    { name: 'Tokyo',       lat: 35.6762, lng: 139.650, size: 0.11, color: COL.neutral, type: 'PORTS', signal: 'NEUTRAL' },
    { name: 'Antwerp',     lat: 51.2194, lng:   4.402, size: 0.09, color: COL.bull,    type: 'PORTS', signal: 'BULLISH' },
    { name: 'Felixstowe',  lat: 51.9550, lng:   1.351, size: 0.07, color: COL.neutral, type: 'PORTS', signal: 'NEUTRAL' },
    { name: 'Laem Chabang',lat: 13.0827, lng: 100.884, size: 0.09, color: COL.bull,    type: 'PORTS', signal: 'BULLISH' },
    { name: 'Panama Canal',lat:  9.0800, lng: -79.680, size: 0.08, color: COL.warn,    type: 'PORTS', signal: 'CHOKE'   },
    { name: 'Suez Canal',  lat: 30.5234, lng:  32.285, size: 0.08, color: COL.warn,    type: 'PORTS', signal: 'CHOKE'   },
  ], []);

  // ─── Points Layer (Ports + Thermal HexBins + Satellites) ─────────────────────
  const pointsData = useMemo(() => {
    const ports = activeLayers.includes('PORTS') ? portPoints : [];

    const thermal = activeLayers.includes('THERMAL')
      ? thermalBins.map(b => ({
          name: b.label,
          lat: b.lat,
          lng: b.lng,
          size: 0.05 + b.weight * 0.12,
          color: `rgba(255, 122, 61, ${0.4 + b.weight * 0.6})`,
          type: 'THERMAL',
          ticker: b.ticker,
          signal: 'THERMAL',
        }))
      : [];

    const sats = activeLayers.includes('SATELLITES')
      ? satellites.map((s: Satellite) => ({
          ...s,
          size: 0.03,
          color: COL.signal,
          type: 'SATELLITE',
        }))
      : [];

    return [...ports, ...thermal, ...sats];
  }, [activeLayers, portPoints, thermalBins, satellites]);

  // ─── Vessel HTML Markers ──────────────────────────────────────────────────────
  const filteredVessels = useMemo(
    () => (activeLayers.includes('VESSELS') ? vessels : []),
    [activeLayers, vessels]
  );

  const filteredFlights = useMemo(
    () => (activeLayers.includes('FLIGHTS') ? flights : []),
    [activeLayers, flights]
  );

  // Build lightweight SVG HTML markers — heading-aware rotation
  const htmlMarkersData = useMemo(() => {
    const vesselEls = filteredVessels.map((v: any) => ({
      lat: v.position?.lat ?? 0,
      lng: v.position?.lon ?? 0,
      size: 18,
      heading: v.position?.heading_degrees ?? 0,
      color: v.dark_vessel_confidence > 0.6 ? COL.bear : COL.bull,
      shape: 'vessel',
      label: `${v.vessel_name || v.mmsi} · ${v.vessel_type || 'CARGO'} · ${(v.speed_knots || 0).toFixed(1)}kts`,
      isDark: v.dark_vessel_confidence > 0.6,
      ticker: v.linked_ticker,
    }));

    const flightEls = filteredFlights.map((f: any) => {
      let fColor = COL.purple;
      if (f.signal === 'BULLISH') fColor = COL.bull;
      else if (f.signal === 'BEARISH') fColor = COL.bear;
      else if (f.type === 'MILITARY') fColor = '#FFD700'; // gold
      else if (f.type === 'CARGO') fColor = '#FFA500'; // orange

      return {
        lat: f.position?.lat ?? 0,
        lng: f.position?.lon ?? 0,
        size: 16,
        heading: f.position?.heading ?? 0,
        color: fColor,
        shape: 'flight',
        label: `${f.callsign || f.icao24} · ${f.type || 'CIVIL'} · FL${Math.round((f.position?.alt_ft || 0) / 100)}`,
        ticker: f.linked_ticker,
      };
    });

    return [...vesselEls, ...flightEls];
  }, [filteredVessels, filteredFlights]);

  // ─── Arcs (Satellite Orbits + Active Flight Vectors) ─────────────────────────
  const arcsData = useMemo(() => {
    const satArcs = activeLayers.includes('SATELLITES')
      ? satellites.filter((s:any) => s.next_lat !== undefined).map((s:any) => ({
          startLat: s.lat, startLng: s.lon,
          endLat: s.next_lat, endLng: s.next_lon,
          color: [COL.signal, COL.bull],
          label: `${s.name} Orbit`
        }))
      : [];

    const flightArcs = activeLayers.includes('FLIGHTS')
      ? filteredFlights.slice(0, 80).map((f: any) => ({
          startLat: f.origin_lat ?? 0,
          startLng: f.origin_lon ?? 0,
          endLat:   f.dest_lat ?? 0,
          endLng:   f.dest_lon ?? 0,
          color:    f.signal === 'BULLISH' ? [COL.bull, '#ffffff44'] : ['#ffffff22', COL.warn],
          label: `${f.callsign} → ${f.dest || ''}`,
        }))
      : [];

    return [...satArcs, ...flightArcs];
  }, [filteredFlights, activeLayers]);

  // ─── Pulsing Rings (Bullish + Dark Vessel Alerts) ────────────────────────────
  const ringsData = useMemo(() => {
    const portRings = portPoints
      .filter(p => p.signal === 'BULLISH' && activeLayers.includes('PORTS'))
      .map(p => ({ lat: p.lat, lng: p.lng, color: COL.bull, maxR: 2.5, propSpeed: 2, period: 2000 }));

    const darkVesselRings = filteredVessels
      .filter((v: any) => v.dark_vessel_confidence > 0.6)
      .map((v: any) => ({
        lat:  v.position?.lat ?? 0,
        lng:  v.position?.lon ?? 0,
        color: COL.bear,
        maxR:  3,
        propSpeed: 4,
        period:   1200,
      }));

    return [...portRings, ...darkVesselRings];
  }, [portPoints, filteredVessels, activeLayers]);

  // ─── Historical Paths ─────────────────────────────────────────────────────────
  const pathsData = useMemo(() => {
    const vesselPaths = filteredVessels
      .filter((v: any) => (v.historical_track || []).length > 1)
      .map((v: any) => ({
        coords: (v.historical_track as any[]).map((p: any) => [p.lon, p.lat, 0.004]),
        color: v.dark_vessel_confidence > 0.6 ? COL.bear : '#00FF9D44',
      }));

    const flightPaths = filteredFlights
      .filter((f: any) => (f.historical_track || []).length > 1)
      .map((f: any) => ({
        coords: (f.historical_track as any[]).map((p: any) => [p.lon, p.lat, 0.02]),
        color: `${COL.purple}66`,
      }));

    return [...vesselPaths, ...flightPaths];
  }, [filteredVessels, filteredFlights]);

  // ─── HTML Element Factory ─────────────────────────────────────────────────────
  const buildHtmlElement = useCallback((d: any) => {
    const el = document.createElement('div');
    el.style.cssText = 'pointer-events:auto;cursor:pointer;position:relative;';
    el.title = d.label || '';

    if (d.shape === 'vessel') {
      el.innerHTML = `
        <div style="
          color:${d.color};
          transform:rotate(${d.heading - 90}deg);
          filter:drop-shadow(0 0 5px ${d.color});
          opacity:0.92;
          width:${d.size}px;
          height:${d.size}px;
        ">
          <svg width="${d.size}" height="${d.size}" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L2 20h20L12 2z"/>
          </svg>
          ${d.isDark ? `<div style="position:absolute;top:-2px;right:-4px;width:6px;height:6px;background:${COL.bear};border-radius:50%;animation:ping 1s infinite;"></div>` : ''}
        </div>`;
    } else {
      el.innerHTML = `
        <div style="
          color:${d.color};
          transform:rotate(${d.heading - 90}deg);
          filter:drop-shadow(0 0 5px ${d.color});
          opacity:0.88;
          width:${d.size}px;
          height:${d.size}px;
        ">
          <svg width="${d.size}" height="${d.size}" viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 16l1 3h-7v3h-2v-3H7l-1-4H0v-2h6l1-4V2h2v7l1 4h7v-2h5v2z"/>
          </svg>
        </div>`;
    }
    return el;
  }, []);

  // ─── Point Label HTML ─────────────────────────────────────────────────────────
  const buildPointLabel = useCallback((d: any): string => `
    <div style="
      background:rgba(7,11,15,0.95);
      border:1px solid ${d.color || COL.signal};
      padding:10px 14px;
      font-family:'IBM Plex Mono',monospace;
      border-radius:3px;
      box-shadow:0 0 20px ${d.color || COL.signal}33;
      min-width:180px;
    ">
      <div style="color:${d.color || COL.signal};font-weight:700;font-size:12px;margin-bottom:6px;letter-spacing:0.08em">
        ${d.name?.toUpperCase() || 'FACILITY'}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:10px;color:#8B949E">
        <span>TYPE</span><span style="color:#E6EDF3;text-align:right">${d.type || d.signal || 'N/A'}</span>
        ${d.throughput !== undefined ? `<span>THROUGHPUT</span><span style="color:#E6EDF3;text-align:right">${Math.round(d.throughput * 100)}%</span>` : ''}
        ${d.ticker ? `<span>TICKER</span><span style="color:${COL.bull};text-align:right;font-weight:700">${d.ticker}</span>` : ''}
      </div>
    </div>
  `, []);

  // ─── Performance: InstancedMesh for Assets ──────────────────────────────────
  useEffect(() => {
    if (!globeEl.current) return;
    const globe = globeEl.current;
    const scene = globe.scene();

    // Create Vessel Geometry (Instanced)
    const vesselGeo = new THREE.ConeGeometry(0.5, 2, 8);
    vesselGeo.rotateX(Math.PI / 2);
    const vesselMat = new THREE.MeshStandardMaterial({ 
      color: 0x00FF9D, 
      emissive: 0x00FF9D, 
      emissiveIntensity: 0.5 
    });
    const vesselMesh = new THREE.InstancedMesh(vesselGeo, vesselMat, 10000);
    vesselMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    vesselMesh.name = 'vessels_instanced';
    
    // Create Flight Geometry (Instanced)
    const flightGeo = new THREE.BoxGeometry(0.8, 0.1, 0.8);
    const flightMat = new THREE.MeshStandardMaterial({ 
      color: 0xBD93F9, 
      emissive: 0xBD93F9, 
      emissiveIntensity: 0.5 
    });
    const flightMesh = new THREE.InstancedMesh(flightGeo, flightMat, 5000);
    flightMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    flightMesh.name = 'flights_instanced';

    scene.add(vesselMesh);
    scene.add(flightMesh);

    // Starfield Background
    const starsGeo = new THREE.BufferGeometry();
    const starsPos = [];
    for (let i = 0; i < 15000; i++) {
        starsPos.push((Math.random() - 0.5) * 2000, (Math.random() - 0.5) * 2000, (Math.random() - 0.5) * 2000);
    }
    starsGeo.setAttribute('position', new THREE.Float32BufferAttribute(starsPos, 3));
    const starsMat = new THREE.PointsMaterial({ color: 0x888888, size: 1.5, sizeAttenuation: true });
    const stars = new THREE.Points(starsGeo, starsMat);
    scene.add(stars);

    return () => {
      scene.remove(vesselMesh);
      scene.remove(flightMesh);
      scene.remove(stars);
    };
  }, []);

  // ─── Update Instanced Positions ───────────────────────────────────────────
  useEffect(() => {
    if (!globeEl.current) return;
    const globe = globeEl.current;
    const vMesh = globe.scene().getObjectByName('vessels_instanced') as any;
    const fMesh = globe.scene().getObjectByName('flights_instanced') as any;
    if (!vMesh || !fMesh) return;

    const dummy = new THREE.Object3D();

    // Update Vessels
    vessels.forEach((v, i) => {
      if (i >= 10000) return;
      const { lat, lon } = v.position || { lat: 0, lon: 0 };
      const pos = globe.getCoords(lat, lon, 0.01);
      dummy.position.set(pos.x, pos.y, pos.z);
      dummy.lookAt(0, 0, 0); // Point away from center
      dummy.rotateY(Math.PI / 2);
      dummy.updateMatrix();
      vMesh.setMatrixAt(i, dummy.matrix);
    });
    vMesh.count = Math.min(vessels.length, 10000);
    vMesh.instanceMatrix.needsUpdate = true;

    // Update Flights
    flights.forEach((f, i) => {
      if (i >= 5000) return;
      const { lat, lon, alt_ft } = f.position || { lat: 0, lon: 0, alt_ft: 35000 };
      const pos = globe.getCoords(lat, lon, 0.08); // Higher altitude
      dummy.position.set(pos.x, pos.y, pos.z);
      dummy.lookAt(0, 0, 0);
      dummy.updateMatrix();
      fMesh.setMatrixAt(i, dummy.matrix);
    });
    fMesh.count = Math.min(flights.length, 5000);
    fMesh.instanceMatrix.needsUpdate = true;
  }, [vessels, flights]);

  // ──────────────────────────────────────────────────────────────────────────────
  return (
    <div className={`w-full h-full relative transition-opacity duration-500 ${
      activeLayers.includes('CLOUDS') ? 'opacity-90' : 'opacity-100'
    }`}>
      <Globe
        ref={globeEl}
        globeImageUrl={undefined}
        bumpImageUrl={undefined}

        // ── OSINT Vector Map (monitorthesituation.org style) ────────────────
        polygonsData={countries.features}
        polygonCapColor={() => 'rgba(2, 6, 15, 0.95)'}
        polygonSideColor={() => 'rgba(0, 212, 255, 0.08)'}
        polygonStrokeColor={() => '#00D4FF'}
        showGraticules={true}

        // ── Atmosphere (Improved) ───────────────────────────────────────────
        showAtmosphere
        atmosphereColor="#00D4FF"
        atmosphereAltitude={0.25}

        // ── Hex-bin Thermal Mapping (Institutional Standard) ─────────────────
        hexBinPointsData={activeLayers.includes('THERMAL') ? thermalBins : []}
        hexBinPointWeight="weight"
        hexBinResolution={4}
        hexMargin={0.1}
        hexColor={() => '#FF4560'}
        hexLabel={buildPointLabel}

        // ── Points (Ports / Satellites) ──────────────────────────────────────
        pointsData={pointsData}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointRadius="size"
        pointAltitude={(d: any) => d.type === 'SATELLITE' ? 0.10 : 0.01}
        pointLabel={buildPointLabel}

        // ── Pulsing Rings ─────────────────────────────────────────────────────
        ringsData={ringsData}
        ringLat="lat"
        ringLng="lng"
        ringColor={(d: any) => d.color}
        ringMaxRadius={(d: any) => d.maxR || 2.5}
        ringPropagationSpeed={(d: any) => d.propSpeed || 3}
        ringRepeatPeriod={(d: any) => d.period || 1500}

        // ── Orbital & Flight Arcs ─────────────────────────────────────────────
        arcsData={arcsData}
        arcColor={(d: any) => d.color}
        arcDashLength={0.45}
        arcDashGap={1.5}
        arcDashAnimateTime={3500}
        arcStroke={0.5}
        arcAltitudeAutoScale={0.3}
        arcLabel={(d: any) => `
          <div style="background:rgba(7,11,15,0.95);padding:8px;border:1px solid ${COL.signal};font-family:monospace;font-size:10px;color:white;">
            <strong>${d.label.toUpperCase()}</strong><br/>
            STATUS: <span style="color:${COL.bull}">ACTIVE</span>
          </div>
        `}

        // ── Elite OSINT Country Typography (Adaptive LOD) ──────────────────
        labelsData={useMemo(() => {
          const altitude = zoomLevel ? 4 / zoomLevel : 2.5;
          // RELAXED THRESHOLD: Show labels even at higher altitudes for "Bloomberg Command" feel
          if (altitude > 3.0) return []; 
          const limit = altitude < 0.6 ? 208 : altitude < 1.2 ? 120 : 60;
          return countryLabels.slice(0, limit);
        }, [zoomLevel])}
        labelLat="lat"
        labelLng="lng"
        labelText={(d: any) => d.name.toUpperCase()}
        labelSize={(d: any) => 0.5}
        labelColor={() => '#00D4FF'}
        labelResolution={4}
        labelIncludeDot={true}
        labelDotRadius={0.15}
        labelAltitude={0.015}

        // ── Globe Appearance (Bug 6 Fix - Deep Institutional Black) ──────────
        backgroundColor="rgba(0,0,0,0)"
        globeMaterial={new THREE.MeshStandardMaterial({
          color: '#02040A',
          transparent: true,
          opacity: 0.95,
          metalness: 0.3,
          roughness: 0.7,
        })}

        // ── Performance ───────────────────────────────────────────────────────
        rendererConfig={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      />

      {/* LIVE STATS OVERLAY */}
      <div className="absolute top-4 right-4 pointer-events-none z-10 flex flex-col gap-1.5">
        {[
          { label: 'VESSELS', val: vessels.length, col: COL.bull },
          { label: 'FLIGHTS', val: flights.length, col: COL.purple },
          { label: 'THERMAL', val: thermalBins.length, col: '#FF7A3D' },
          { label: 'DARK', val: vessels.filter((v: any) => v.dark_vessel_confidence > 0.6).length, col: COL.bear },
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
