from apscheduler.schedulers.asyncio import AsyncIOScheduler
import structlog

log = structlog.get_logger()
scheduler = AsyncIOScheduler()

def start_scheduler():
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

    scheduler.start()
    log.info("scheduler_started", jobs=len(scheduler.get_jobs()))


async def refresh_aircraft():
    from src.globe.adsb import fetch_all_aircraft
    aircraft = fetch_all_aircraft()
    log.info("aircraft_refreshed", count=len(aircraft))


async def refresh_thermal():
    from src.globe.thermal import fetch_firms_thermal
    anomalies = fetch_firms_thermal()
    log.info("thermal_refreshed", count=len(anomalies))


async def refresh_prices():
    from src.data.market_data import get_bulk_prices
    prices = get_bulk_prices()
    log.info("prices_refreshed", count=len(prices))


async def refresh_news():
    from src.data.news import fetch_all_news
    news = fetch_all_news()
    log.info("news_refreshed", count=len(news))


async def refresh_orbits():
    from src.globe.orbits import get_ground_track
    for sat in ["Sentinel-2A", "Sentinel-2B", "Landsat-9"]:
        get_ground_track(sat)
    log.info("orbits_refreshed")


async def refresh_macro():
    from src.data.macro import get_macro_dashboard
    get_macro_dashboard()
    log.info("macro_refreshed")
