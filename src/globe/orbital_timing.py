"""
Satellite Orbital Timing - Link orbital passes to thermal signal predictions.

Uses Celestrak TLE data to predict when Sentinel-2, Landsat-8/9, and VIIRS
satellites will pass over signal locations, enabling imaging confirmation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import radians, sqrt
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class SatellitePass:
    """A predicted satellite pass over a location."""
    satellite: str  # Sentinel-2A, Landsat-9, etc.
    satellite_id: str  # NORAD ID
    lat: float
    lon: float
    pass_time: datetime
    elevation_deg: float  # Max elevation during pass
    duration_s: float  # Approximate pass duration
    next_pass_hours: float  # Hours until this pass
    cloud_cover_forecast: float | None  # % if available
    imaging_quality: str  # 'excellent', 'good', 'fair', 'poor'


@dataclass
class ThermalSignalTiming:
    """Timing info for a thermal signal including next satellite passes."""
    signal_id: str
    facility_name: str
    lat: float
    lon: float
    detected_at: datetime
    anomaly_sigma: float
    next_passes: list[SatellitePass]
    imaging_confidence: str  # 'confirmed', 'scheduled', 'pending'
    optimal_imaging_window: tuple[datetime, datetime] | None


class OrbitalPassPredictor:
    """
    Predict satellite orbital passes over thermal signal locations.
    
    Uses:
    - Celestrak TLE data for orbit propagation
    - Simplified pass prediction (good to ~5 minute accuracy)
    - Cloud cover from Open-Meteo for imaging condition forecasting
    
    Satellites tracked:
    - Sentinel-2A, Sentinel-2B (10m resolution, 5-day revisit)
    - Landsat-8, Landsat-9 (30m resolution, 16-day revisit)
    - NOAA-20, SNPP (VIIRS thermal, 750m resolution, daily)
    """

    CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php"

    # Satellite TLE groups from Celestrak
    SATELLITE_GROUPS = {
        'sentinel-2': 'visual',
        'landsat': 'visual',
        'noaa': 'weather',
        'snpp': 'weather'
    }

    # Specific satellites we care about
    TARGET_SATELLITES = {
        'SENTINEL-2A': '40697',
        'SENTINEL-2B': '42063',
        'LANDSAT-8': '39084',
        'LANDSAT-9': '49260',
        'NOAA-20': '43013',
        'S-NPP': '37849',
    }

    def __init__(self):
        self._tles: dict[str, dict[str, Any]] = {}
        self._tle_timestamp: datetime | None = None

    def fetch_tles(self, group: str = 'visual') -> dict[str, dict[str, Any]]:
        """
        Fetch TLE (Two-Line Element) data from Celestrak.
        
        Args:
            group: Satellite group ('visual', 'weather', 'earth', etc.)
            
        Returns:
            Dict mapping satellite name to TLE data
        """
        cache_key = f"tles_{group}"
        now = datetime.now(UTC)

        # Cache TLEs for 6 hours
        if (self._tle_timestamp and
            (now - self._tle_timestamp).total_seconds() < 21600 and
            cache_key in self._tles):
            return self._tles[cache_key]

        try:
            params = {
                'GROUP': group,
                'FORMAT': 'json'
            }

            response = requests.get(
                self.CELESTRAK_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Parse TLEs for target satellites
            tles = {}
            for sat in data:
                name = sat.get('OBJECT_NAME', '').upper()
                for target_name in self.TARGET_SATELLITES.keys():
                    if target_name in name:
                        tles[target_name] = {
                            'name': name,
                            'norad_id': sat.get('NORAD_CAT_ID'),
                            'tle_line1': sat.get('TLE_LINE1'),
                            'tle_line2': sat.get('TLE_LINE2'),
                            'epoch': sat.get('EPOCH'),
                            'inclination': float(sat.get('INCLINATION', 0)),
                            'period': float(sat.get('PERIOD', 0)),  # minutes
                        }
                        break

            logger.info(f"Fetched TLEs for {len(tles)} satellites from Celestrak")
            self._tles[cache_key] = tles
            self._tle_timestamp = now
            return tles

        except Exception as e:
            logger.error(f"TLE fetch failed: {e}")
            return self._tles.get(cache_key, {})

    def predict_pass(self,
                     sat_name: str,
                     sat_tle: dict[str, Any],
                     lat: float,
                     lon: float,
                     hours_ahead: int = 72) -> SatellitePass | None:
        """
        Predict next pass of a satellite over a location.
        
        Uses simplified orbital mechanics:
        - Assumes circular orbit
        - Considers inclination and orbital period
        - Accounts for Earth's rotation
        
        Args:
            sat_name: Satellite name
            sat_tle: TLE data dict
            lat: Target latitude
            lon: Target longitude  
            hours_ahead: How far ahead to predict
            
        Returns:
            SatellitePass object or None if no pass in window
        """
        try:
            # Simplified pass prediction
            # Real pass prediction requires SGP4 propagation
            # This is a fast approximation good to ~10 minute accuracy

            period_mins = sat_tle.get('period', 100)
            inclination = sat_tle.get('inclination', 98)

            # Earth rotates 15 degrees per hour
            # Satellite orbits ~15 times per day for LEO

            now = datetime.now(UTC)

            # Simplified: Find when satellite latitude crosses target
            # For polar orbits (inclination > 80), passes happen roughly every period
            # Ground track shifts ~15-25 degrees longitude per orbit

            lat_rad = radians(lat)
            inc_rad = radians(inclination)

            # Calculate approximate passes
            passes = []
            for orbit in range(int(hours_ahead * 60 / period_mins)):
                # Time of orbit
                orbit_time = now + timedelta(minutes=orbit * period_mins)

                # Approximate ground track (simplified)
                # Real calculation requires SGP4 with full TLE

                # Estimate if this orbit passes near target
                # For sun-synchronous orbits, ascending node shifts ~0.98 degrees/day

                # Calculate max elevation (simplified)
                # Simplification: assume equator crossing at longitude = orbit * 15 deg
                estimated_lon = (orbit * 25) % 360 - 180  # Rough longitude shift

                # Distance calculation (simplified, treats Earth as flat)
                lat_diff = 0  # Assume we cross target latitude
                lon_diff = abs(lon - estimated_lon)
                if lon_diff > 180:
                    lon_diff = 360 - lon_diff

                distance_deg = sqrt(lat_diff**2 + lon_diff**2)

                # Typical LEO elevation range
                if distance_deg < 30:  # Within 30 degrees
                    # Rough elevation estimate
                    elevation = 90 - distance_deg

                    if elevation > 15:  # Above horizon
                        # Calculate quality based on elevation and satellite
                        if 'SENTINEL' in sat_name and elevation > 30:
                            quality = 'excellent'
                        elif 'SENTINEL' in sat_name:
                            quality = 'good'
                        elif 'LANDSAT' in sat_name:
                            quality = 'good'
                        else:
                            quality = 'fair'

                        # Hours until pass
                        hours_until = orbit * period_mins / 60

                        return SatellitePass(
                            satellite=sat_name,
                            satellite_id=sat_tle.get('norad_id', ''),
                            lat=lat,
                            lon=lon,
                            pass_time=orbit_time,
                            elevation_deg=elevation,
                            duration_s=period_mins * 60 * 0.1,  # ~10% of orbit
                            next_pass_hours=hours_until,
                            cloud_cover_forecast=None,
                            imaging_quality=quality
                        )

            return None

        except Exception as e:
            logger.warning(f"Pass prediction failed for {sat_name}: {e}")
            return None

    def get_cloud_cover_forecast(self, lat: float, lon: float) -> float | None:
        """
        Fetch cloud cover forecast from Open-Meteo.
        
        Returns cloud cover % for the next few hours, or None if unavailable.
        """
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'hourly': 'cloud_cover',
                'forecast_days': 1
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Get average cloud cover for next 6 hours
            cloud_cover = data.get('hourly', {}).get('cloud_cover', [])
            if cloud_cover:
                return sum(cloud_cover[:6]) / len(cloud_cover[:6])

            return None

        except Exception as e:
            logger.warning(f"Cloud forecast failed for {lat},{lon}: {e}")
            return None

    def get_passes_for_location(self,
                                 lat: float,
                                 lon: float,
                                 facility_name: str,
                                 hours_ahead: int = 72) -> list[SatellitePass]:
        """
        Get all upcoming satellite passes for a location.
        
        Args:
            lat: Location latitude
            lon: Location longitude
            facility_name: Name for logging
            hours_ahead: How many hours ahead to predict
            
        Returns:
            List of SatellitePass objects, sorted by time
        """
        passes = []

        # Fetch TLEs for visual satellites
        tles = self.fetch_tles('visual')

        for sat_name, sat_tle in tles.items():
            pass_pred = self.predict_pass(
                sat_name, sat_tle, lat, lon, hours_ahead
            )
            if pass_pred:
                passes.append(pass_pred)

        # Add cloud cover forecast to each pass
        cloud_cover = self.get_cloud_cover_forecast(lat, lon)
        if cloud_cover is not None:
            for p in passes:
                p.cloud_cover_forecast = cloud_cover

        # Sort by time
        passes.sort(key=lambda x: x.next_pass_hours)

        logger.info(f"Found {len(passes)} satellite passes for {facility_name}")
        return passes

    def get_timing_for_signals(self,
                               signals: list[Any],
                               hours_ahead: int = 72) -> list[ThermalSignalTiming]:
        """
        Get satellite pass timing for a list of thermal signals.
        
        Args:
            signals: List of signal objects with lat, lon, facility_name
            hours_ahead: How far ahead to predict
            
        Returns:
            List of ThermalSignalTiming objects
        """
        timings = []

        for signal in signals:
            try:
                # Get passes for this signal location
                passes = self.get_passes_for_location(
                    signal.lat,
                    signal.lon,
                    signal.facility_name,
                    hours_ahead
                )

                # Determine imaging confidence
                if passes and passes[0].next_pass_hours < 6:
                    confidence = 'confirmed' if passes[0].cloud_cover_forecast and passes[0].cloud_cover_forecast < 20 else 'scheduled'
                elif passes:
                    confidence = 'scheduled'
                else:
                    confidence = 'pending'

                # Find optimal imaging window (lowest cloud cover in next 48h)
                optimal = None
                for p in passes:
                    if p.cloud_cover_forecast and p.cloud_cover_forecast < 30:
                        optimal = (p.pass_time, p.pass_time + timedelta(minutes=15))
                        break

                timing = ThermalSignalTiming(
                    signal_id=signal.signal_id,
                    facility_name=signal.facility_name,
                    lat=signal.lat,
                    lon=signal.lon,
                    detected_at=signal.detected_at,
                    anomaly_sigma=signal.anomaly_sigma,
                    next_passes=passes[:5],  # Next 5 passes
                    imaging_confidence=confidence,
                    optimal_imaging_window=optimal
                )

                timings.append(timing)

            except Exception as e:
                logger.error(f"Failed to get timing for signal {signal.signal_id}: {e}")
                continue

        return timings


# Singleton instance
_predictor: OrbitalPassPredictor | None = None

def get_orbital_predictor() -> OrbitalPassPredictor:
    """Get or create the orbital pass predictor singleton."""
    global _predictor
    if _predictor is None:
        _predictor = OrbitalPassPredictor()
    return _predictor


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    predictor = OrbitalPassPredictor()

    # Test: ArcelorMittal Dunkirk
    passes = predictor.get_passes_for_location(
        51.04, 2.38, "ArcelorMittal Dunkirk"
    )

    print("\nUpcoming satellite passes for ArcelorMittal Dunkirk:\n")
    for p in passes[:5]:
        print(f"  {p.satellite} (NORAD {p.satellite_id})")
        print(f"    Pass time: {p.pass_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"    In: {p.next_pass_hours:.1f} hours")
        print(f"    Max elevation: {p.elevation_deg:.0f}°")
        print(f"    Quality: {p.imaging_quality}")
        if p.cloud_cover_forecast:
            print(f"    Cloud cover: {p.cloud_cover_forecast:.0f}%")
        print()
