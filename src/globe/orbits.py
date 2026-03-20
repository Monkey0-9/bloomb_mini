import requests
import asyncio
import traceback
from sgp4.api import Satrec, WGS84
from sgp4.api import jday
from datetime import datetime, timezone

# Target Satellites
TARGET_SATS = {
    'SENTINEL-2A': 40697,
    'SENTINEL-2B': 42564,
    'LANDSAT 8': 39084,
    'LANDSAT 9': 49260,
    'WORLDVIEW-3': 40115
}

def get_tles_from_celestrak():
    """Download Active Earth Resource sat TLEs from Celestrak."""
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle"
    print("[ORBITS] Fetching latest TLEs from Celestrak...")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    
    lines = resp.text.strip().split('\n')
    sats = {}
    
    for i in range(0, len(lines), 3):
        if i + 2 >= len(lines):
            break
        name = lines[i].strip()
        line1 = lines[i+1].strip()
        line2 = lines[i+2].strip()
        
        # Check against targets
        for tgt_name, norad_id in TARGET_SATS.items():
            if str(norad_id) in line1 or tgt_name in name:
                sats[tgt_name] = {'line1': line1, 'line2': line2}
    
    return sats

def propagate_sats(sats):
    """Calculate current lat/lon/alt for each satellite."""
    now = datetime.now(timezone.utc)
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond / 1000000.0)
    
    # Calculate jday for +45 minutes
    jd_next, fr_next = jday(now.year, now.month, now.day, now.hour, now.minute + 45, now.second + now.microsecond / 1000000.0)

    positions = []
    import math

    def compute_geo(satellite, j_d, f_r):
        e, r, v = satellite.sgp4(j_d, f_r)
        if e != 0: return None
        x, y, z = r
        lon = math.atan2(y, x)
        lat = math.atan2(z, math.sqrt(x**2 + y**2))
        alt = math.sqrt(x**2 + y**2 + z**2) - 6371.0
        
        jd_int = int(j_d)
        jd_frac = j_d - jd_int + f_r
        t = (jd_int - 2451545.0 + jd_frac) / 36525.0
        gmst = 280.46061837 + 360.98564736629 * (jd_int - 2451545.0 + jd_frac) + \
               0.000387933 * t**2 - (t**3) / 38710000.0
        gmst = (gmst % 360.0) * math.pi / 180.0
        
        lon = lon - gmst
        lon = (lon + math.pi) % (2*math.pi) - math.pi
        return math.degrees(lat), math.degrees(lon), alt

    for name, tle in sats.items():
        satellite = Satrec.twoline2rv(tle['line1'], tle['line2'])
        curr = compute_geo(satellite, jd, fr)
        next_pos = compute_geo(satellite, jd_next, fr_next)
        
        if curr and next_pos:
            positions.append({
                'id': name,
                'name': name,
                'lat': curr[0],
                'lon': curr[1],
                'alt': curr[2],
                'next_lat': next_pos[0],
                'next_lon': next_pos[1],
                'line1': tle['line1'],
                'line2': tle['line2']
            })
            
    return positions

async def run_orbits_pipeline(update_callback):
    """Fetch TLEs and propagate positions to WS."""
    sats_tle = get_tles_from_celestrak()
    print(f"[ORBITS] Tracked {len(sats_tle)} mission critical satellites.")
    
    while True:
        try:
            positions = propagate_sats(sats_tle)
            if positions:
                await update_callback({
                    '_topic': 'orbits',
                    'data': positions
                })
        except Exception:
            traceback.print_exc()
        # Propagate every 30s as requested
        await asyncio.sleep(30)

if __name__ == "__main__":
    tles = get_tles_from_celestrak()
    pos = propagate_sats(tles)
    print(pos)
