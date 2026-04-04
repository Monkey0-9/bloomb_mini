import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

log = structlog.get_logger()
scheduler = AsyncIOScheduler()

def start_scheduler():
    if scheduler.running:
        log.info("scheduler_already_running")
        return

    # Aircraft: every 10 seconds (OpenSky rate limit safe)
    scheduler.add_job(refresh_aircraft, "interval", seconds=10, id="aircraft")

    # Thermal: every 3 hours (FIRMS updates every few hours)
    scheduler.add_job(refresh_thermal, "interval", hours=3, id="thermal")

    # Market prices: every 30 seconds
    scheduler.add_job(refresh_prices, "interval", seconds=30, id="prices")

    # News: every 5 minutes
    scheduler.add_job(refresh_news, "interval", minutes=5, id="news")

    # Orbital elements: every 24 hours (TLE updates daily)
    scheduler.add_job(refresh_orbits, "interval", hours=24, id="orbits")

    # Macro data: every 1 hour
    scheduler.add_job(refresh_macro, "interval", hours=1, id="macro")

    # Vessels: every 15 seconds
    scheduler.add_job(refresh_vessels, "interval", seconds=15, id="vessels")

    scheduler.start()
    log.info("scheduler_started", jobs=len(scheduler.get_jobs()))


async def refresh_aircraft():
    from src.common.trackers import flight_tracker
    await flight_tracker.populate_global_fleet()
    log.info("aircraft_refreshed", count=len(flight_tracker.get_all_flights()))


async def refresh_vessels():
    from src.common.trackers import vessel_tracker
    vessels = await vessel_tracker.get_all_vessels()
    log.info("vessels_refreshed", count=len(vessels))


async def refresh_thermal():
    import asyncio

    from src.globe.thermal import fetch_firms_thermal
    anomalies = await asyncio.to_thread(fetch_firms_thermal)
    log.info("thermal_refreshed", count=len(anomalies))


async def refresh_prices():
    import asyncio

    from src.data.market_data import get_bulk_prices
    prices = await asyncio.to_thread(get_bulk_prices)
    log.info("prices_refreshed", count=len(prices))


async def refresh_news():
    import asyncio

    from src.data.news import fetch_all_news
    news = await asyncio.to_thread(fetch_all_news)
    log.info("news_refreshed", count=len(news))


async def refresh_orbits():
    import asyncio

    from src.globe.orbits import get_ground_track
    for sat in ["Sentinel-2A", "Sentinel-2B", "Landsat-9"]:
        await asyncio.to_thread(get_ground_track, sat)
    log.info("orbits_refreshed")


async def refresh_macro():
    import asyncio

    from src.data.macro import get_macro_dashboard
    await asyncio.to_thread(get_macro_dashboard)
    log.info("macro_refreshed")
