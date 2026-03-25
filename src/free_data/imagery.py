"""
Free satellite imagery adapter.
Sources: 
- AWS Public Dataset (Sentinel-2)
- Google Cloud Public Dataset
- ESA CopHub (Open Access Hub)
"""
from datetime import datetime, timedelta
import httpx
import structlog

log = structlog.get_logger(__name__)

# Sentinel-2 AWS S3 URL pattern (Public)
# Example: https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/T31UFU/2023/1/15/0/B04.tif
SENTINEL_S3_ROOT = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs"

def get_s2_tile_url(tile_id: str, date: datetime, band: str = "TCI") -> str:
    """Construct a public URL for a Sentinel-2 COG on AWS."""
    # tile_id format: T31UFU
    grid = tile_id[1:] if tile_id.startswith("T") else tile_id
    year = date.year
    month = date.month
    day = date.day
    return f"{SENTINEL_S3_ROOT}/{grid}/{year}/{month}/{day}/0/{band}.tif"

def check_tile_availability(tile_id: str, date: datetime) -> bool:
    """Check if a tile exists on the public COG bucket."""
    url = get_s2_tile_url(tile_id, date, "B02") # Blue band as proxy
    try:
        resp = httpx.head(url, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False

def get_latest_imagery_metadata(tile_id: str) -> dict:
    """Scan recent dates for available imagery."""
    now = datetime.now()
    for i in range(10): # Look back 10 days
        target_date = now - timedelta(days=i)
        if check_tile_availability(tile_id, target_date):
            return {
                "tile_id": tile_id,
                "date": target_date.strftime("%Y-%m-%d"),
                "tci_url": get_s2_tile_url(tile_id, target_date, "TCI"),
                "source": "AWS S2 COGS (Public)"
            }
    return {"error": "No imagery found in last 10 days"}
