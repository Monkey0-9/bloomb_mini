import asyncio
import structlog
from datetime import datetime, timezone
from src.globe.adsb import fetch_all_aircraft, get_squawk_alerts
from src.common.trackers import vessel_tracker, flight_tracker
from src.api.broadcast import broadcast_manager

log = structlog.get_logger()

async def run_ticker():
    """
    Electronic Live Broadcast Ticker: Aggregates Global Feeds and Publishes to Clients.
    One Producer -> Many Consumers.
    """
    log.info("ticker.started")
    while True:
        try:
            # 1. Fetch aircraft from adsb.py (now uses adsb.fi fallback)
            aircraft = await asyncio.to_thread(fetch_all_aircraft)
            squawk_alerts = get_squawk_alerts(aircraft)
            
            # 2. Update trackers
            try:
                for a in aircraft:
                    # Map adsb.py Aircraft object to FlightTracker
                    flight_tracker.update_flight(
                        a.callsign, a.lat, a.lon, 
                        a.altitude_ft, a.speed_knots
                    )
            except Exception as e:
                log.error("ticker.flight_sync_error", error=str(e))

            # 3. Fetch Vessels (vessel_tracker now uses AISStream via ais.py)
            try:
                vessels_list = await vessel_tracker.get_all_vessels()
                vessels = [
                    {
                        "mmsi": v.mmsi,
                        "vessel_name": v.vessel_name,
                        "vessel_type": v.vessel_type,
                        "lat": v.lat,
                        "lon": v.lon,
                        "speed_knots": v.speed,
                        "heading": v.heading,
                        "dark_vessel_confidence": v.dark_vessel_confidence,
                        "flag": v.flag
                    }
                    for v in vessels_list
                ]

                payload = {
                    "type": "TICKER_UPDATE",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": {
                        "aircraft": [a.__dict__ for a in aircraft],
                        "squawks": squawk_alerts,
                        "vessels": vessels
                    }
                }
                
                await broadcast_manager.broadcast(payload)
                log.info("ticker.broadcast_success", aircraft=len(aircraft), vessels=len(vessels))
            except Exception as e:
                log.error("ticker.vessel_sync_error", error=str(e))

        except Exception as e:
            log.error("ticker.loop_error", error=str(e))
        
        await asyncio.sleep(3.0) # Balanced frequency
