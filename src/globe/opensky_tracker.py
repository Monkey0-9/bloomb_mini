"""
OpenSky Aircraft Tracking - Real-time global aircraft monitoring.

Fetches aircraft positions every 10 seconds, filters for military/cargo/government,
detects emergency squawks (7700/7600/7500), and pushes to frontend.
Zero API key required.
"""

from __future__ import annotations

import logging
import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Aircraft:
    """Aircraft state from OpenSky."""
    icao24: str  # ICAO 24-bit address
    callsign: Optional[str]  # Flight callsign
    origin_country: str
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]  # Meters
    velocity: Optional[float]  # m/s
    heading: Optional[float]  # Degrees
    vertical_rate: Optional[float]  # m/s
    squawk: Optional[str]  # Transponder code
    spi: bool  # Special position identification
    position_source: int
    last_contact: datetime
    
    @property
    def is_emergency(self) -> bool:
        """Check if aircraft is squawking emergency codes."""
        if not self.squawk:
            return False
        return self.squawk in ('7700', '7600', '7500')
    
    @property
    def emergency_type(self) -> Optional[str]:
        """Get emergency type from squawk code."""
        if self.squawk == '7700':
            return 'GENERAL_EMERGENCY'
        elif self.squawk == '7600':
            return 'RADIO_FAILURE'
        elif self.squawk == '7500':
            return 'HIJACK'
        return None
    
    @property
    def is_military(self) -> bool:
        """Check if aircraft is military based on ICAO24 prefix or callsign."""
        if not self.icao24:
            return False
        # Military ICAO24 prefixes (common ones)
        mil_prefixes = ('ae', 'ad', 'a', '3', '7', '0a')
        if self.icao24.lower().startswith(mil_prefixes):
            return True
        # Military callsign patterns
        if self.callsign:
            mil_callsigns = ('rfr', 'mmf', 'usaf', 'navy', 'af', 'cnv', 'rch')
            if any(self.callsign.lower().startswith(m) for m in mil_callsigns):
                return True
        return False
    
    @property
    def is_cargo(self) -> bool:
        """Check if aircraft is cargo based on callsign prefix."""
        if not self.callsign:
            return False
        cargo_prefixes = ('fdx', 'ups', 'clx', 'gcl', 'atlas', 'kalitta')
        return any(self.callsign.lower().startswith(p) for p in cargo_prefixes)
    
    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON feature for frontend."""
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [self.longitude, self.latitude]
            },
            'properties': {
                'icao24': self.icao24,
                'callsign': self.callsign,
                'country': self.origin_country,
                'altitude_m': self.altitude,
                'velocity_ms': self.velocity,
                'heading': self.heading,
                'squawk': self.squawk,
                'is_emergency': self.is_emergency,
                'emergency_type': self.emergency_type,
                'is_military': self.is_military,
                'is_cargo': self.is_cargo,
                'last_contact': self.last_contact.isoformat()
            }
        }


class OpenSkyTracker:
    """
    Real-time aircraft tracking using OpenSky Network.
    
    Features:
    - Polls all aircraft states every 10 seconds
    - Filters for interesting aircraft (military, cargo, emergency)
    - Detects emergency squawks immediately
    - Formats for WebSocket broadcast to frontend
    
    Zero API key required for public endpoint.
    """
    
    OPENSKY_URL = "https://opensky-network.org/api/states/all"
    
    def __init__(self):
        self._last_update: Optional[datetime] = None
        self._tracked_aircraft: Dict[str, Aircraft] = {}
        self._emergency_history: List[Dict[str, Any]] = []
        
    def fetch_all_aircraft(self) -> List[Aircraft]:
        """
        Fetch current state of all aircraft from OpenSky.
        
        Returns:
            List of Aircraft objects
        """
        try:
            response = requests.get(
                self.OPENSKY_URL,
                timeout=15,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            data = response.json()
            
            aircraft_list = []
            states = data.get('states', [])
            
            for state in states:
                # OpenSky state vector format:
                # [icao24, callsign, origin_country, time_position, last_contact,
                #  longitude, latitude, baro_altitude, on_ground, velocity,
                #  heading, vertical_rate, sensors, geo_altitude, squawk, spi,
                #  position_source]
                if len(state) < 17:
                    continue
                    
                aircraft = Aircraft(
                    icao24=state[0] or 'unknown',
                    callsign=state[1].strip() if state[1] else None,
                    origin_country=state[2] or 'Unknown',
                    longitude=state[5],
                    latitude=state[6],
                    altitude=state[7],
                    velocity=state[9],
                    heading=state[10],
                    vertical_rate=state[11],
                    squawk=state[14],
                    spi=bool(state[15]),
                    position_source=state[16] if state[16] else 0,
                    last_contact=datetime.now(timezone.utc)
                )
                aircraft_list.append(aircraft)
            
            logger.info(f"Fetched {len(aircraft_list)} aircraft from OpenSky")
            return aircraft_list
            
        except Exception as e:
            logger.error(f"OpenSky fetch failed: {e}")
            return []
    
    def get_interesting_aircraft(self, 
                                 include_military: bool = True,
                                 include_cargo: bool = True,
                                 include_emergency: bool = True) -> List[Aircraft]:
        """
        Get aircraft filtered for intelligence relevance.
        
        Args:
            include_military: Include military aircraft
            include_cargo: Include cargo aircraft
            include_emergency: Include emergency squawk aircraft
            
        Returns:
            Filtered list of Aircraft
        """
        all_aircraft = self.fetch_all_aircraft()
        interesting = []
        
        for ac in all_aircraft:
            # Skip if no position data
            if ac.latitude is None or ac.longitude is None:
                continue
                
            # Check emergency first (always include)
            if include_emergency and ac.is_emergency:
                interesting.append(ac)
                continue
            
            # Check military
            if include_military and ac.is_military:
                interesting.append(ac)
                continue
            
            # Check cargo
            if include_cargo and ac.is_cargo:
                interesting.append(ac)
                continue
        
        return interesting
    
    def check_emergencies(self) -> List[Dict[str, Any]]:
        """
        Check for new emergency squawks and return alerts.
        
        Returns:
            List of emergency alerts with aircraft info and recommended tickers
        """
        all_aircraft = self.fetch_all_aircraft()
        emergencies = []
        
        for ac in all_aircraft:
            if ac.is_emergency and ac.latitude and ac.longitude:
                # Determine affected tickers based on location
                tickers = self._get_tickers_for_location(ac.latitude, ac.longitude)
                
                alert = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'aircraft': asdict(ac),
                    'emergency_type': ac.emergency_type,
                    'location': {'lat': ac.latitude, 'lon': ac.longitude},
                    'affected_tickers': tickers,
                    'urgency': 'CRITICAL' if ac.squawk == '7500' else 'HIGH'
                }
                emergencies.append(alert)
                
                # Log critical alert
                logger.critical(
                    f"EMERGENCY SQUAWK {ac.squawk}: {ac.callsign or ac.icao24} "
                    f"at ({ac.latitude:.3f}, {ac.longitude:.3f}) "
                    f"- Tickers: {tickers}"
                )
        
        if emergencies:
            self._emergency_history.extend(emergencies)
            
        return emergencies
    
    def _get_tickers_for_location(self, lat: float, lon: float) -> List[str]:
        """Get relevant tickers for emergency location."""
        # Chokepoint proximity check
        chokepoints = {
            'hormuz': (26.5, 56.5, ['XOM', 'CVX', 'LNG', 'EURN']),
            'suez': (30.0, 32.5, ['AMKBY', 'ZIM', '1919.HK']),
            'malacca': (1.5, 103.0, ['AMKBY', 'ZIM', 'XOM']),
            'bab_mandeb': (12.5, 43.5, ['XOM', 'CVX', 'LNG']),
            'panama': (9.0, -79.5, ['AMKBY', 'ZIM', 'CCL']),
        }
        
        for name, (clat, clon, tickers) in chokepoints.items():
            dist = ((lat - clat)**2 + (lon - clon)**2) ** 0.5
            if dist < 2.0:  # Within ~200km
                return tickers
        
        return []
    
    def to_geojson_collection(self, aircraft_list: List[Aircraft]) -> Dict[str, Any]:
        """
        Convert aircraft list to GeoJSON FeatureCollection for frontend.
        
        Returns:
            GeoJSON FeatureCollection
        """
        return {
            'type': 'FeatureCollection',
            'features': [ac.to_geojson() for ac in aircraft_list if ac.latitude and ac.longitude],
            'meta': {
                'count': len(aircraft_list),
                'emergencies': sum(1 for ac in aircraft_list if ac.is_emergency),
                'military': sum(1 for ac in aircraft_list if ac.is_military),
                'cargo': sum(1 for ac in aircraft_list if ac.is_cargo),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }


# Singleton instance
_tracker: Optional[OpenSkyTracker] = None

def get_opensky_tracker() -> OpenSkyTracker:
    """Get or create the OpenSky tracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = OpenSkyTracker()
    return _tracker


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    tracker = OpenSkyTracker()
    
    # Fetch interesting aircraft
    aircraft = tracker.get_interesting_aircraft()
    
    print(f"\nFound {len(aircraft)} interesting aircraft:\n")
    
    for ac in aircraft[:20]:
        status = []
        if ac.is_emergency:
            status.append(f"EMERGENCY-{ac.emergency_type}")
        if ac.is_military:
            status.append("MILITARY")
        if ac.is_cargo:
            status.append("CARGO")
            
        print(f"  {ac.callsign or ac.icao24} ({ac.origin_country})")
        print(f"    Position: {ac.latitude:.3f}, {ac.longitude:.3f}")
        print(f"    Altitude: {ac.altitude:.0f}m | Speed: {ac.velocity:.0f}m/s | Heading: {ac.heading:.0f}°")
        print(f"    Status: {', '.join(status) if status else 'Normal'}")
        print()
