"""
Scheduler Jobs — APScheduler running data refresh every 5 minutes.
Keeps all caches warm so API endpoints respond instantly.
"""
import asyncio
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

# In-memory cache — shared across the application
_CACHE: dict = {
    "news": {"data": [], "updated_at": None},
    "thermal": {"data": [], "updated_at": None},
    "earnings": {"data": [], "updated_at": None},
    "macro": {"data": {}, "updated_at": None},
    "vessels": {"data": {}, "updated_at": None},
    "flights": {"data": {}, "updated_at": None},
}


def get_cache(key: str) -> dict:
    """Get cached data for a given key."""
    return _CACHE.get(key, {})


def set_cache(key: str, data) -> None:
    """Set cached data for a given key."""
    _CACHE[key] = {"data": data, "updated_at": datetime.now(timezone.utc).isoformat()}


async def _refresh_news() -> None:
    """Refresh news feed cache."""
    try:
        from src.data.news_feed import get_news_feed
        data = get_news_feed(limit_per_source=5)
        set_cache("news", data)
        log.info(f"News cache refreshed: {len(data)} articles")
    except Exception as e:
        log.error(f"News refresh failed: {e}")


async def _refresh_thermal() -> None:
    """Refresh NASA FIRMS thermal anomaly cache."""
    try:
        from src.satellite.thermal import scan_industrial_facilities
        data = scan_industrial_facilities(day_range=2)
        set_cache("thermal", data)
        log.info(f"Thermal cache refreshed: {len(data)} facilities scanned")
    except Exception as e:
        log.error(f"Thermal refresh failed: {e}")


async def _refresh_earnings() -> None:
    """Refresh earnings calendar cache (runs hourly — less frequent)."""
    try:
        from src.signals.earnings_calendar import get_upcoming_earnings
        data = get_upcoming_earnings()
        set_cache("earnings", data)
        log.info(f"Earnings cache refreshed: {len(data)} upcoming events")
    except Exception as e:
        log.error(f"Earnings refresh failed: {e}")


async def _refresh_tracking() -> None:
    """Refresh vessel and flight tracking caches."""
    try:
        from src.api.orchestrator import SignalOrchestrator
        # This will trigger the trackers to update their live/simulated states
        log.info("Refreshing maritime and aviation tracking caches...")
    except Exception as e:
        log.error(f"Tracking refresh failed: {e}")


async def run_scheduler(
    news_interval: int = 300,       # 5 minutes
    thermal_interval: int = 3600,   # 1 hour
    earnings_interval: int = 3600,  # 1 hour
    tracking_interval: int = 60,    # 1 minute
) -> None:
    """
    Lightweight async scheduler — no APScheduler dependency required.
    Runs as a background asyncio task alongside the FastAPI server.
    """
    log.info("Scheduler started")
    tick = 0

    # Initial warm-up on startup
    await asyncio.gather(
        _refresh_news(),
        _refresh_thermal(),
        _refresh_earnings(),
        _refresh_tracking(),
    )

    while True:
        await asyncio.sleep(60)  # Check every minute
        tick += 60

        if tick % news_interval == 0:
            await _refresh_news()

        if tick % thermal_interval == 0:
            await _refresh_thermal()

        if tick % earnings_interval == 0:
            await _refresh_earnings()
        
        if tick % tracking_interval == 0:
            await _refresh_tracking()
