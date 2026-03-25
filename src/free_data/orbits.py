"""
Global Orbital Intelligence — Celestrak TLE tracking.
Propagates all Earth Resources satellites in real-time.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sgp4.api import Satrec, jday

logger = logging.getLogger(__name__)

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=earth-resources&FORMAT=tle"

@dataclass
class SatellitePosition:
    name: str
    lat: float
    lon: float
    alt_km: float
    timestamp: datetime

async def get_live_orbits() -> list[SatellitePosition]:
    """Fetch TLEs from Celestrak and propagate to current positions."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(CELESTRAK_URL)
            lines = resp.text.splitlines()
            
            positions = []
            now = datetime.now(timezone.utc)
            jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)
            
            for i in range(0, len(lines) - 2, 3):
                name = lines[i].strip()
                tle_l1 = lines[i+1]
                tle_l2 = lines[i+2]
                
                satellite = Satrec.twoline2rv(tle_l1, tle_l2)
                e, r, v = satellite.sgp4(jd, fr)
                
                if e == 0:
                    # Convert TEME (ECI) to Geodetic
                    # Simplified conversion for Phase 3 (needs skyfield for full precision)
                    import numpy as np
                    x, y, z = r
                    alt = np.sqrt(x**2 + y**2 + z**2) - 6371.0
                    lat = np.degrees(np.arcsin(z / (alt + 6371.0)))
                    lon = np.degrees(np.arctan2(y, x))
                    
                    # Correct for Earth rotation (GMST)
                    theta = (now.hour + now.minute/60.0 + now.second/3600.0) * 15.0
                    lon = (lon - theta + 180) % 360 - 180

                    positions.append(SatellitePosition(
                        name=name, lat=float(lat), lon=float(lon),
                        alt_km=float(alt), timestamp=now
                    ))
            
            return positions
    except Exception as e:
        logger.error(f"Orbital tracking error: {e}")
        return []
