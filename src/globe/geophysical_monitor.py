"""
Geophysical Events Monitor - USGS earthquakes + UCDP conflicts.

Monitors global earthquakes (M4.5+) and armed conflicts, checks proximity
to major chokepoints, and flags affected shipping/energy tickers.
"""

from __future__ import annotations

import logging
import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# Major shipping and energy chokepoints
CHOKEPOINTS = {
    "hormuz": {
        "name": "Strait of Hormuz",
        "coords": (26.5, 56.5),
        "tickers": ["XOM", "CVX", "LNG", "EURN", "STNG"],
        "description": "20% of global oil supply passes through daily"
    },
    "suez": {
        "name": "Suez Canal", 
        "coords": (30.0, 32.5),
        "tickers": ["AMKBY", "ZIM", "1919.HK", "HLAG.DE", "CCL"],
        "description": "12% of global trade, critical for Europe-Asia shipping"
    },
    "malacca": {
        "name": "Strait of Malacca",
        "coords": (1.5, 103.0),
        "tickers": ["AMKBY", "ZIM", "1919.HK", "XOM", "CVX"],
        "description": "80% of China's oil imports pass through"
    },
    "bosphorus": {
        "name": "Bosphorus Strait",
        "coords": (41.2, 29.0),
        "tickers": ["AMKBY", "1919.HK", "LNG", "GLNG"],
        "description": "Key Black Sea-Mediterranean route, Russian grain/oil exports"
    },
    "bab_mandeb": {
        "name": "Bab-el-Mandeb",
        "coords": (12.5, 43.5),
        "tickers": ["XOM", "CVX", "LNG", "AMKBY"],
        "description": "Southern Red Sea chokepoint, Yemen conflict zone"
    },
    "panama": {
        "name": "Panama Canal",
        "coords": (9.0, -79.5),
        "tickers": ["AMKBY", "ZIM", "CCL", "CUK", "NCLH"],
        "description": "Critical US-Asia container route, drought affecting capacity"
    }
}


@dataclass
class GeophysicalEvent:
    """A geophysical event with location and impact assessment."""
    event_id: str
    event_type: str  # 'earthquake' or 'conflict'
    lat: float
    lon: float
    magnitude: Optional[float]  # For earthquakes
    severity: str  # For conflicts
    location_description: str
    timestamp: datetime
    affected_chokepoints: List[str]
    affected_tickers: List[str]
    risk_assessment: str
    data_source: str


class GeophysicalMonitor:
    """
    Monitors USGS earthquakes and UCDP armed conflicts.
    
    Features:
    - Polls USGS for M4.5+ earthquakes globally
    - Polls UCDP for armed conflict events
    - Checks proximity to 6 major chokepoints
    - Flags affected shipping/energy tickers
    - Provides risk assessment
    """
    
    USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"
    UCDP_URL = "https://ucdpapi.pcr.uu.se/api/gedevents/23.1"
    
    def __init__(self, proximity_threshold_km: float = 300):
        self.proximity_threshold = proximity_threshold_km
        self._last_earthquakes: List[Dict[str, Any]] = []
        self._last_conflicts: List[Dict[str, Any]] = []
        
    def fetch_usgs_earthquakes(self) -> List[Dict[str, Any]]:
        """Fetch M4.5+ earthquakes from last 7 days from USGS."""
        try:
            response = requests.get(self.USGS_URL, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            earthquakes = []
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                geom = feature.get('geometry', {})
                coords = geom.get('coordinates', [0, 0])
                
                eq = {
                    'id': feature.get('id'),
                    'lat': coords[1],
                    'lon': coords[0],
                    'magnitude': props.get('mag'),
                    'place': props.get('place'),
                    'time': datetime.fromtimestamp(props.get('time', 0) / 1000, tz=timezone.utc),
                    'tsunami': props.get('tsunami', 0),
                    'depth': coords[2] if len(coords) > 2 else 0,
                }
                earthquakes.append(eq)
            
            logger.info(f"Fetched {len(earthquakes)} earthquakes from USGS")
            self._last_earthquakes = earthquakes
            return earthquakes
            
        except Exception as e:
            logger.error(f"USGS fetch failed: {e}")
            return self._last_earthquakes
    
    def fetch_ucdp_conflicts(self) -> List[Dict[str, Any]]:
        """Fetch armed conflict events from UCDP."""
        try:
            # UCDP API with date filter for recent events
            params = {
                'pagesize': 100,
                'StartDate': (datetime.now(timezone.utc) - 
                              __import__('datetime').timedelta(days=30)).strftime('%Y-%m-%d')
            }
            
            response = requests.get(self.UCDP_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            conflicts = []
            for event in data.get('Result', []):
                conflict = {
                    'id': event.get('id'),
                    'lat': float(event.get('latitude', 0)),
                    'lon': float(event.get('longitude', 0)),
                    'deaths': event.get('best', 0),  # Best estimate of deaths
                    'country': event.get('country', 'Unknown'),
                    'region': event.get('region', 'Unknown'),
                    'date': event.get('date_start', ''),
                    'type': event.get('type_of_violence', 'Unknown'),
                    'side_a': event.get('side_a', 'Unknown'),
                    'side_b': event.get('side_b', 'Unknown'),
                }
                conflicts.append(conflict)
            
            logger.info(f"Fetched {len(conflicts)} conflicts from UCDP")
            self._last_conflicts = conflicts
            return conflicts
            
        except Exception as e:
            logger.error(f"UCDP fetch failed: {e}")
            return self._last_conflicts
    
    def check_chokepoint_proximity(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        """
        Check if location is near any major chokepoints.
        
        Returns:
            List of nearby chokepoints with distances
        """
        nearby = []
        
        for choke_id, choke_data in CHOKEPOINTS.items():
            clat, clon = choke_data['coords']
            
            # Haversine distance calculation
            from math import radians, sin, cos, sqrt, atan2
            
            R = 6371  # Earth radius in km
            lat1, lon1 = radians(lat), radians(lon)
            lat2, lon2 = radians(clat), radians(clon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            if distance < self.proximity_threshold:
                nearby.append({
                    'id': choke_id,
                    'name': choke_data['name'],
                    'distance_km': round(distance, 1),
                    'tickers': choke_data['tickers'],
                    'description': choke_data['description']
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance_km'])
        return nearby
    
    def process_earthquake(self, eq: Dict[str, Any]) -> Optional[GeophysicalEvent]:
        """Process earthquake and create event if near chokepoints."""
        lat = eq.get('lat')
        lon = eq.get('lon')
        mag = eq.get('magnitude')
        
        nearby = self.check_chokepoint_proximity(lat, lon)
        
        if not nearby:
            return None
        
        # Collect all affected tickers
        all_tickers = []
        for choke in nearby:
            all_tickers.extend(choke['tickers'])
        all_tickers = list(set(all_tickers))
        
        # Risk assessment
        if mag and mag >= 7.0:
            risk = "CRITICAL"
        elif mag and mag >= 6.0:
            risk = "HIGH"
        else:
            risk = "MODERATE"
        
        return GeophysicalEvent(
            event_id=eq.get('id', 'unknown'),
            event_type='earthquake',
            lat=lat,
            lon=lon,
            magnitude=mag,
            severity=risk,
            location_description=eq.get('place', 'Unknown'),
            timestamp=eq.get('time', datetime.now(timezone.utc)),
            affected_chokepoints=[c['name'] for c in nearby],
            affected_tickers=all_tickers,
            risk_assessment=f"M{mag} earthquake within {nearby[0]['distance_km']}km of {nearby[0]['name']}",
            data_source='USGS'
        )
    
    def process_conflict(self, conflict: Dict[str, Any]) -> Optional[GeophysicalEvent]:
        """Process conflict and create event if near chokepoints."""
        lat = conflict.get('lat')
        lon = conflict.get('lon')
        deaths = conflict.get('deaths', 0)
        
        nearby = self.check_chokepoint_proximity(lat, lon)
        
        if not nearby:
            return None
        
        # Collect all affected tickers
        all_tickers = []
        for choke in nearby:
            all_tickers.extend(choke['tickers'])
        all_tickers = list(set(all_tickers))
        
        # Risk assessment based on death toll
        if deaths >= 100:
            risk = "CRITICAL"
        elif deaths >= 50:
            risk = "HIGH"
        else:
            risk = "MODERATE"
        
        return GeophysicalEvent(
            event_id=str(conflict.get('id', 'unknown')),
            event_type='conflict',
            lat=lat,
            lon=lon,
            magnitude=None,
            severity=risk,
            location_description=f"{conflict.get('country')} - {conflict.get('side_a')} vs {conflict.get('side_b')}",
            timestamp=datetime.strptime(conflict.get('date', ''), '%Y-%m-%d').replace(tzinfo=timezone.utc) if conflict.get('date') else datetime.now(timezone.utc),
            affected_chokepoints=[c['name'] for c in nearby],
            affected_tickers=all_tickers,
            risk_assessment=f"Armed conflict ({deaths} deaths) within {nearby[0]['distance_km']}km of {nearby[0]['name']}",
            data_source='UCDP'
        )
    
    def get_all_events(self) -> List[GeophysicalEvent]:
        """
        Main entry point: fetch all events and process for chokepoint impact.
        
        Returns:
            List of GeophysicalEvent objects that affect chokepoints
        """
        events = []
        
        # Process earthquakes
        earthquakes = self.fetch_usgs_earthquakes()
        for eq in earthquakes:
            event = self.process_earthquake(eq)
            if event:
                events.append(event)
                logger.warning(
                    f"GEOHAZARD: {event.risk_assessment} - "
                    f"Tickers: {event.affected_tickers}"
                )
        
        # Process conflicts
        conflicts = self.fetch_ucdp_conflicts()
        for conflict in conflicts:
            event = self.process_conflict(conflict)
            if event:
                events.append(event)
                logger.warning(
                    f"CONFLICT: {event.risk_assessment} - "
                    f"Tickers: {event.affected_tickers}"
                )
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2}
        events.sort(key=lambda e: severity_order.get(e.severity, 3))
        
        return events
    
    def to_geojson_collection(self, events: List[GeophysicalEvent]) -> Dict[str, Any]:
        """Convert events to GeoJSON FeatureCollection for frontend."""
        features = []
        for event in events:
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [event.lon, event.lat]
                },
                'properties': {
                    'event_type': event.event_type,
                    'magnitude': event.magnitude,
                    'severity': event.severity,
                    'location': event.location_description,
                    'chokepoints': event.affected_chokepoints,
                    'tickers': event.affected_tickers,
                    'risk_assessment': event.risk_assessment,
                    'timestamp': event.timestamp.isoformat(),
                    'source': event.data_source
                }
            })
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'meta': {
                'count': len(events),
                'critical': sum(1 for e in events if e.severity == 'CRITICAL'),
                'high': sum(1 for e in events if e.severity == 'HIGH'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }


# Singleton instance
_monitor: Optional[GeophysicalMonitor] = None

def get_geophysical_monitor() -> GeophysicalMonitor:
    """Get or create the geophysical monitor singleton."""
    global _monitor
    if _monitor is None:
        _monitor = GeophysicalMonitor()
    return _monitor


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    monitor = GeophysicalMonitor()
    events = monitor.get_all_events()
    
    print(f"\nFound {len(events)} geophysical events affecting chokepoints:\n")
    
    for event in events[:10]:
        print(f"  [{event.severity}] {event.event_type.upper()}")
        print(f"    Location: {event.location_description}")
        print(f"    Coords: {event.lat:.3f}, {event.lon:.3f}")
        if event.magnitude:
            print(f"    Magnitude: M{event.magnitude}")
        print(f"    Affected: {', '.join(event.affected_chokepoints)}")
        print(f"    Tickers: {', '.join(event.affected_tickers)}")
        print(f"    {event.risk_assessment}")
        print()
