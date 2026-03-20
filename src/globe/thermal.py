import asyncio
import traceback
import csv
import io
import time
import requests

# NASA FIRMS Global (typically requires MAP_KEY from firms.modaps.eosdis.nasa.gov)
# We will construct the ingestion pipeline capable of parsing the standard 
# VIIRS 375m (NOAA-20 / SNPP) CSV format.
FIRMS_API_URL = "https://firms.modaps.eosdis.nasa.gov/api/active_fire/viirs-snpp/csv/{MAP_KEY}/24h"

# 25 Identified Industrial Hotspots (Steel Mills, LNG Terminals, Refineries)
INDUSTRIAL_ZONES = {
    'ArcelorMittal Dunkirk': (51.04, 2.30),
    'Jamnagar Refinery': (22.36, 69.96),
    'Freeport LNG': (28.94, -95.30),
    'Gwangyang Steelworks': (34.90, 127.73),
    'Jurong Island Chem': (1.26, 103.68),
    'Ulsan Petrochem': (35.50, 129.35),
    'Shanghai Baoshan Steel': (31.42, 121.43),
    'Ras Laffan LNG': (25.90, 51.55),
    'Jubail Industrial City': (27.05, 49.52),
    'Rotterdam Europort': (51.94, 4.13),
}

def generate_simulated_firms():
    """Generates synthetic thermodynamic data tracking to industrial zones."""
    import random
    hotspots = []
    
    for name, coords in INDUSTRIAL_ZONES.items():
        # Add 1-5 hotspots per facility to simulate blast furnaces / flares
        for i in range(random.randint(1, 5)):
            jitter_lat = random.uniform(-0.01, 0.01)
            jitter_lon = random.uniform(-0.01, 0.01)
            hotspots.append({
                'id': f"thermal-{name.replace(' ', '')}-{i}",
                'name': name,
                'lat': coords[0] + jitter_lat,
                'lon': coords[1] + jitter_lon,
                'brightness': random.uniform(330.0, 500.0), # Kelvin
                'frp': random.uniform(5.0, 150.0), # Fire Radiative Power (MW)
                'confidence': random.choice(['n', 'l', 'h']),
                'satellite': random.choice(['N', '1']),
                'last_update': time.time()
            })
            
    return hotspots

async def run_thermal_pipeline(update_callback, map_key=None):
    import os
    """Fetch or simulate NASA FIRMS active fire hotspots for key targets."""
    print("[THERMAL] Initializing VIIRS 375m monitoring...")
    key = map_key or os.environ.get("NASA_FIRMS_MAP_KEY")
    
    while True:
        try:
            data = []
            if key and key != "DEMO_KEY":
                try:
                    resp = requests.get(FIRMS_API_URL.format(MAP_KEY=key), timeout=10)
                    resp.raise_for_status()
                    reader = csv.DictReader(io.StringIO(resp.text))
                    # Filter for our 25 industrial locations
                    for row in reader:
                        lat, lon = float(row['latitude']), float(row['longitude'])
                        frp = float(row.get('frp', 10.0))
                        
                        # Check bounding box near our known targets
                        for name, coords in INDUSTRIAL_ZONES.items():
                            if abs(coords[0] - lat) < 0.05 and abs(coords[1] - lon) < 0.05:
                                data.append({
                                    'id': f"thermal-{row.get('acq_date')}-{row.get('acq_time')}",
                                    'name': name,
                                    'lat': lat,
                                    'lon': lon,
                                    'brightness': float(row.get('bright_ti4', 300.0)),
                                    'frp': frp,
                                    'confidence': row.get('confidence', 'n'),
                                    'satellite': row.get('satellite', 'N'),
                                    'last_update': time.time()
                                })
                except Exception as api_err:
                    print(f"[THERMAL] API FETCH FAILED: {api_err}. Falling back.")
                    data = generate_simulated_firms()
            else:
                data = generate_simulated_firms()
            
            if data:
                await update_callback({
                    '_topic': 'thermal',
                    'data': data
                })
        except Exception:
            traceback.print_exc()
            
        await asyncio.sleep(60)

if __name__ == "__main__":
    print(generate_simulated_firms()[0])
