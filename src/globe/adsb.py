import json
import time
import requests
import asyncio
import traceback
from typing import List, Dict

# Cargo airlines: FedEx, UPS, DHL (DHK), Cargolux, ABX
CARGO_CALLSIGNS = ('FDX', 'UPS', 'DHK', 'CLX', 'ABX', 'PAC', 'GTI')

# Known US/NATO Military Hex prefixes (approximate heuristics for OpenSky filtering if full ADSBx db missing)
MILITARY_HEX_PREFIXES = ('ae', 'af', 'ad', '43', '3e', '3f') 

def fetch_opensky_states() -> List[Dict]:
    """Retrieve all aircraft currently tracked by OpenSky."""
    try:
        response = requests.get('https://opensky-network.org/api/states/all', timeout=10)
        response.raise_for_status()
        data = response.json()
        
        vectors = data.get('states', [])
        results = []
        for v in vectors:
            if not v[5] or not v[6]: # Needs lat/lon
                continue
                
            icao24 = str(v[0]).strip().lower()
            callsign = str(v[1]).strip().upper() if v[1] else ""
            longitude = float(v[5])
            latitude = float(v[6])
            altitude = v[7] if v[7] else 0
            velocity = v[9] if v[9] else 0
            heading = v[10] if v[10] else 0
            squawk = str(v[14]).strip() if v[14] else ""
            
            # Cargo evaluation
            is_cargo = any(callsign.startswith(c) for c in CARGO_CALLSIGNS)
            
            # Military evaluation
            is_military = any(icao24.startswith(prefix) for prefix in MILITARY_HEX_PREFIXES)
            
            flight_type = None
            if is_cargo:
                flight_type = 'CARGO'
            elif is_military:
                flight_type = 'MILITARY'
                
            if flight_type:
                results.append({
                    'id': icao24,
                    'callsign': callsign,
                    'type': flight_type,
                    'lat': latitude,
                    'lon': longitude,
                    'alt': altitude,
                    'speed': velocity,
                    'heading': heading,
                    'squawk': squawk,
                    'timestamp': time.time()
                })
                
        return results
    except Exception as e:
        print(f"[ADSB] Error fetching Opensky Data: {e}")
        return []

async def run_adsb_pipeline(update_callback):
    """Async loop that polls Opensky every 10 seconds and pushes to websocket."""
    print("[ADSB] Starting OpenSky pipeline for Military + Cargo flights...")
    while True:
        try:
            flights = fetch_opensky_states()
            if flights:
                print(f"[ADSB] Found {len(flights)} priority aircraft (Military + Cargo).")
                # Push back to central socket via callback
                await update_callback({
                    '_topic': 'flight_update',
                    'count': len(flights),
                    'flights': flights
                })
        except Exception:
            traceback.print_exc()
            
        await asyncio.sleep(10)

if __name__ == '__main__':
    # Test script standalone execution
    res = fetch_opensky_states()
    mils = [f for f in res if f['type'] == 'MILITARY']
    cargs = [f for f in res if f['type'] == 'CARGO']
    print(f"Test poll completed: {len(mils)} Military, {len(cargs)} Cargo.")
    if res:
        print(json.dumps(res[0], indent=2))
