// @ts-nocheck
import React, { useMemo, useState, useCallback } from 'react';
import Map, { Marker, Popup } from 'react-map-gl/maplibre';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useTerminalStore, useVesselStore, useFlightStore } from '../store';
import { Ship, Plane, X, Anchor, Package, MapPin, Navigation, Gauge, Flag } from 'lucide-react';

// ── Vessel popup card ──────────────────────────────────────────────────────
const VesselCard = ({ vessel, onClose }: { vessel: any; onClose: () => void }) => {
  const typeColor: Record<string, string> = {
    Container: '#00ffcc',
    Tanker:    '#ff6b35',
    'Bulk Carrier': '#ffc107',
    Cargo:     '#82aaff',
  };
  const col = typeColor[vessel.vessel_type] || '#00ffcc';
  const statusColor = vessel.status === 'UNDERWAY' ? '#00ff9d' : vessel.status === 'AT ANCHOR' ? '#ffc107' : '#aaa';

  return (
    <div
      style={{ borderColor: col + '44', boxShadow: `0 0 30px ${col}22` }}
      className="relative bg-[#02060f]/95 border rounded-sm backdrop-blur-2xl font-mono w-[340px] pointer-events-auto"
    >
      {/* Header */}
      <div style={{ borderColor: col + '44', background: `linear-gradient(135deg, ${col}12, transparent)` }}
        className="flex items-center justify-between px-4 py-3 border-b"
      >
        <div className="flex items-center gap-2.5">
          <Ship size={16} style={{ color: col }} />
          <div>
            <div className="text-[11px] font-black tracking-[0.2em] uppercase" style={{ color: col }}>{vessel.name}</div>
            <div className="text-[9px] text-white/40 tracking-widest">{vessel.vessel_type?.toUpperCase()} · MMSI {vessel.mmsi}</div>
          </div>
        </div>
        <button onClick={onClose} className="text-white/30 hover:text-white/80 transition-colors">
          <X size={14} />
        </button>
      </div>

      {/* Status badge */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-white/5">
        <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: statusColor }} />
        <span className="text-[10px] tracking-widest font-bold" style={{ color: statusColor }}>{vessel.status}</span>
        {vessel.flag && <span className="ml-auto text-[10px] text-white/30 tracking-widest">{vessel.flag?.toUpperCase()}</span>}
      </div>

      {/* Route */}
      <div className="px-4 py-3 border-b border-white/5">
        <div className="text-[8px] text-white/30 uppercase tracking-widest mb-1.5">Voyage Route</div>
        <div className="flex items-center gap-2">
          <div className="flex-1 min-w-0">
            <div className="text-[9px] text-white/40 mb-0.5">ORIGIN</div>
            <div className="text-[11px] text-white font-semibold truncate">{vessel.origin || 'Unknown'}</div>
          </div>
          <div className="text-white/20 text-[18px] flex-shrink-0">→</div>
          <div className="flex-1 min-w-0 text-right">
            <div className="text-[9px] text-white/40 mb-0.5">DESTINATION</div>
            <div className="text-[11px] text-white font-semibold truncate">{vessel.destination || 'Unknown'}</div>
          </div>
        </div>
      </div>

      {/* Cargo */}
      <div className="px-4 py-3 border-b border-white/5">
        <div className="text-[8px] text-white/30 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
          <Package size={9} className="text-white/30" /> Cargo Manifest
        </div>
        <div className="text-[11px] font-semibold" style={{ color: col }}>{vessel.cargo || 'General Cargo'}</div>
      </div>

      {/* Telemetry grid */}
      <div className="grid grid-cols-3 gap-px bg-white/5 border-t border-white/5">
        {[
          { icon: <Gauge size={10} />, label: 'SPEED', value: `${vessel.speed_knots || vessel.velocity || 0} kts` },
          { icon: <Navigation size={10} />, label: 'HEADING', value: `${vessel.heading || 0}°` },
          { icon: <MapPin size={10} />, label: 'POSITION', value: `${vessel.lat}°, ${vessel.lon}°` },
        ].map(({ icon, label, value }) => (
          <div key={label} className="bg-[#02060f]/80 px-3 py-2.5">
            <div className="flex items-center gap-1 text-white/30 mb-1">{icon}<span className="text-[8px] tracking-widest">{label}</span></div>
            <div className="text-[10px] text-white font-semibold tabular-nums">{value}</div>
          </div>
        ))}
      </div>

      {/* Dark vessel warning */}
      {vessel.dark_vessel_confidence > 0.5 && (
        <div className="bg-red-950/60 border-t border-red-500/30 px-4 py-2 text-[9px] text-red-300 font-bold tracking-widest uppercase animate-pulse">
          ⚠ AIS DARK VESSEL — Transponder Anomaly Detected
        </div>
      )}
    </div>
  );
};

// ── Flight popup card ──────────────────────────────────────────────────────
const FlightCard = ({ flight, onClose }: { flight: any; onClose: () => void }) => {
  const catColor: Record<string, string> = {
    MILITARY: '#ff4560',
    CARGO: '#ff9a00',
    GOVERNMENT: '#ffd700',
    COMMERCIAL: '#bd93f9',
    PRIVATE: '#82aaff',
  };
  const col = catColor[flight.category] || '#bd93f9';
  return (
    <div
      style={{ borderColor: col + '44', boxShadow: `0 0 30px ${col}22` }}
      className="relative bg-[#02060f]/95 border rounded-sm backdrop-blur-2xl font-mono w-[320px] pointer-events-auto"
    >
      <div style={{ borderColor: col + '44', background: `linear-gradient(135deg, ${col}12, transparent)` }}
        className="flex items-center justify-between px-4 py-3 border-b"
      >
        <div className="flex items-center gap-2.5">
          <Plane size={16} style={{ color: col }} />
          <div>
            <div className="text-[11px] font-black tracking-[0.2em] uppercase" style={{ color: col }}>{flight.callsign || 'UNKNOWN'}</div>
            <div className="text-[9px] text-white/40 tracking-widest">{(flight.category || 'AIRCRAFT').toUpperCase()} · {flight.icao24}</div>
          </div>
        </div>
        <button onClick={onClose} className="text-white/30 hover:text-white/80 transition-colors">
          <X size={14} />
        </button>
      </div>
      <div className="px-4 py-3 border-b border-white/5">
        <div className="text-[8px] text-white/30 uppercase tracking-widest mb-1">Operator</div>
        <div className="text-[11px] font-semibold text-white">{flight.operator || (flight.callsign ? `${flight.callsign.slice(0,3)} Airways` : 'Unknown Operator')}</div>
      </div>
      <div className="grid grid-cols-3 gap-px bg-white/5 border-t border-white/5">
        {[
          { label: 'ALTITUDE', value: `${(flight.position?.alt_ft || flight.alt_ft || 0).toLocaleString()} ft` },
          { label: 'HEADING',  value: `${flight.position?.heading || flight.heading || 0}°` },
          { label: 'SPEED',    value: `${flight.speed_kmh || flight.velocity || 0} kts` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-[#02060f]/80 px-3 py-2.5">
            <div className="text-[8px] text-white/30 tracking-widest mb-1">{label}</div>
            <div className="text-[10px] text-white font-semibold tabular-nums">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
};


// ── Main 2D Map ────────────────────────────────────────────────────────────
const GlobalMap2D: React.FC = () => {
  const { activeLayers } = useTerminalStore();
  const { vessels } = useVesselStore();
  const { flights } = useFlightStore();

  const [selectedVessel, setSelectedVessel] = useState<any>(null);
  const [selectedFlight, setSelectedFlight] = useState<any>(null);

  const filteredVessels = useMemo(() =>
    activeLayers.includes('VESSELS') ? vessels : [], [vessels, activeLayers]);

  const filteredFlights = useMemo(() =>
    activeLayers.includes('AIRCRAFT') ? flights : [], [flights, activeLayers]);

  const handleVesselClick = useCallback((v: any) => {
    setSelectedFlight(null);
    setSelectedVessel(v);
  }, []);

  const handleFlightClick = useCallback((f: any) => {
    setSelectedVessel(null);
    setSelectedFlight(f);
  }, []);

  const typeColor: Record<string, string> = {
    Container: '#00ffcc',
    Tanker:    '#ff6b35',
    'Bulk Carrier': '#ffc107',
    Cargo:     '#82aaff',
  };

  return (
    <div className="absolute inset-0 z-[5] bg-[#0a0f18]">
      <Map
        mapLib={maplibregl}
        initialViewState={{ longitude: 10, latitude: 20, zoom: 1.8 }}
        style={{ width: '100%', height: '100%' }}
        mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
      >
        {/* Vessels */}
        {filteredVessels.map((v: any, i: number) => {
          const lat = v.position?.lat ?? v.lat ?? 0;
          const lon = v.position?.lon ?? v.lon ?? 0;
          if (!lat && !lon) return null;
          const col = typeColor[v.vessel_type] || '#00ffcc';
          const isSelected = selectedVessel?.mmsi === v.mmsi;
          return (
            <Marker key={`vessel-${v.mmsi || i}`} longitude={lon} latitude={lat} anchor="center">
              <div
                onClick={() => handleVesselClick(v)}
                className="cursor-pointer transition-transform hover:scale-150"
                style={{ transform: `rotate(${v.position?.heading_degrees ?? v.heading ?? 0}deg)` }}
              >
                <div className="relative">
                  {isSelected && (
                    <div
                      className="absolute inset-[-8px] rounded-full animate-ping"
                      style={{ background: col + '33' }}
                    />
                  )}
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <polygon points="12,2 20,20 12,16 4,20" fill={col} opacity={isSelected ? 1 : 0.85} />
                  </svg>
                </div>
              </div>
            </Marker>
          );
        })}

        {/* Aircraft */}
        {filteredFlights.map((f: any, i: number) => {
          const lat = f.position?.lat ?? f.lat ?? 0;
          const lon = f.position?.lon ?? f.lon ?? 0;
          if (!lat && !lon) return null;
          const catColor: Record<string, string> = {
            MILITARY: '#ff4560', CARGO: '#ff9a00', GOVERNMENT: '#ffd700',
            COMMERCIAL: '#bd93f9', PRIVATE: '#82aaff',
          };
          const col = catColor[f.category] || '#bd93f9';
          const isSelected = selectedFlight?.icao24 === f.icao24;
          return (
            <Marker key={`flight-${f.icao24 || i}`} longitude={lon} latitude={lat} anchor="center">
              <div
                onClick={() => handleFlightClick(f)}
                className="cursor-pointer transition-transform hover:scale-150"
                style={{ transform: `rotate(${f.position?.heading ?? f.heading ?? 0}deg)` }}
              >
                <div className="relative">
                  {isSelected && (
                    <div className="absolute inset-[-8px] rounded-full animate-ping" style={{ background: col + '33' }} />
                  )}
                  <svg width="16" height="16" viewBox="0 0 24 24" fill={col} opacity={isSelected ? 1 : 0.8}>
                    <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
                  </svg>
                </div>
              </div>
            </Marker>
          );
        })}

        {/* Vessel popup */}
        {selectedVessel && (() => {
          const lat = selectedVessel.position?.lat ?? selectedVessel.lat ?? 0;
          const lon = selectedVessel.position?.lon ?? selectedVessel.lon ?? 0;
          return (
            <Popup
              longitude={lon}
              latitude={lat}
              anchor="left"
              closeButton={false}
              closeOnClick={false}
              offset={20}
              className="vessel-popup"
            >
              <VesselCard vessel={selectedVessel} onClose={() => setSelectedVessel(null)} />
            </Popup>
          );
        })()}

        {/* Flight popup */}
        {selectedFlight && (() => {
          const lat = selectedFlight.position?.lat ?? selectedFlight.lat ?? 0;
          const lon = selectedFlight.position?.lon ?? selectedFlight.lon ?? 0;
          return (
            <Popup
              longitude={lon}
              latitude={lat}
              anchor="left"
              closeButton={false}
              closeOnClick={false}
              offset={20}
              className="vessel-popup"
            >
              <FlightCard flight={selectedFlight} onClose={() => setSelectedFlight(null)} />
            </Popup>
          );
        })()}
      </Map>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 flex flex-col gap-1.5 pointer-events-none z-10">
        <div className="bg-black/70 backdrop-blur-sm border border-white/10 px-3 py-2 rounded-sm font-mono">
          <div className="text-[9px] text-white/30 uppercase tracking-widest mb-2">AIS LEGEND</div>
          {Object.entries({ Container: '#00ffcc', Tanker: '#ff6b35', 'Bulk Carrier': '#ffc107', Cargo: '#82aaff' }).map(([t, c]) => (
            <div key={t} className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-sm" style={{ background: c }} />
              <span className="text-[9px] text-white/50">{t}</span>
            </div>
          ))}
        </div>
        <div className="bg-black/70 backdrop-blur-sm border border-white/10 px-3 py-2 rounded-sm font-mono">
          <div className="text-[9px] text-white/50">
            <span className="text-white/80 font-bold">{filteredVessels.length}</span> vessels ·{' '}
            <span className="text-white/80 font-bold">{filteredFlights.length}</span> aircraft
          </div>
        </div>
      </div>

      {/* Click hint */}
      {filteredVessels.length > 0 && !selectedVessel && !selectedFlight && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 pointer-events-none z-10">
          <div className="bg-black/70 backdrop-blur-sm border border-white/10 px-4 py-2 rounded-sm font-mono text-[10px] text-white/40 tracking-widest uppercase">
            Click any vessel or aircraft for intelligence details
          </div>
        </div>
      )}
    </div>
  );
};

export default GlobalMap2D;
