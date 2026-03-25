import time
import structlog
from src.free_data.vessels import get_global_ships

log = structlog.get_logger(__name__)

# Strategic Port Bounding Boxes (approx) [min_lon, min_lat, max_lon, max_lat]
STRATEGIC_PORTS = {
    'ROTTERDAM': [3.9, 51.8, 4.3, 52.0],
    'SINGAPORE': [103.5, 1.1, 104.1, 1.4],
    'SHANGHAI': [121.5, 30.5, 122.5, 31.5],
    'LOS_ANGELES': [-118.3, 33.6, -118.1, 33.8]
}

async def generate_fleet():
    """
    Returns real-time global vessel data from NOAA/Kystverket.
    Zero procedural simulation. Total real-world fidelity.
    """
    try:
        log.info("ais.fetching_real_ships")
        # Fetch real ships from the free_data engine
        ships = await get_global_ships(limit=500)
        
        fleet = []
        for v in ships:
            # Map common fields
            fleet.append({
                'mmsi': v.get('mmsi', ''),
                'name': v.get('name', 'UNKNOWN'),
                'lat': v.get('lat', 0),
                'lon': v.get('lon', 0),
                'heading': v.get('heading', 0),
                'speed_knots': v.get('speed_knots', 0),
                'type': v.get('vessel_type', 'CARGO'),
                'nav_status': v.get('status', 'UNDERWAY'),
                'last_update': v.get('last_updated', time.time())
            })
            
        if fleet:
            log.info("ais.real_ships_fetched", count=len(fleet))
            return fleet
    except Exception as e:
        log.error("ais.real_ships_fetch_failed", error=str(e))
        
    return []

fleet_state = {} # Use MMSI for deduplication

def update_fleet_from_live(live_data):
    """Callback to update fleet state from live AISstream data."""
    global fleet_state
    for v in live_data:
        mmsi = v.get("mmsi")
        if not mmsi: continue
        fleet_state[mmsi] = {
            'mmsi': mmsi,
            'name': v.get("vessel_name", "UNKNOWN"),
            'lat': v.get("lat"),
            'lon': v.get("lon"),
            'heading': v.get("heading", 0),
            'speed_knots': v.get("speed_knots", 0),
            'type': 'CARGO',
            'nav_status': v.get("status", "UNDERWAY"),
            'last_update': time.time()
        }

async def run_ais_pipeline(update_callback):
    """
    Start the AISStream.io pipeline and update the global fleet_state.
    """
    try:
        from src.globe.ais_live import run_aisstream_pipeline
        
        async def internal_callback(msg):
            if msg.get("_topic") == "vessel":
                update_fleet_from_live(msg.get("data", []))
                # Also propagate to the main update_callback (ticker)
                await update_callback(msg)

        log.info("ais_pipeline.starting")
        await run_aisstream_pipeline(internal_callback)
    except Exception as e:
        log.warning("ais_pipeline.failed", error=str(e))
