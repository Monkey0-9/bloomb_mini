import logging
from pathlib import Path
from typing import Dict, Any
import numpy as np
import rasterio
import requests

logger = logging.getLogger(__name__)

def download_sentinel_tile(
    tile_id: str,
    band: str = "B04",
    date: str = "2024-01-01",
    output_dir: str = "./data/tiles",
) -> str:
    """Download Sentinel-2 COG tile from AWS public bucket."""
    base_url = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
    utm_zone = tile_id[:2]
    latitude_band = tile_id[2]
    grid_square = tile_id[3:]
    year, month, _ = date.split("-")
    
    # Construct URL for L2A COGs
    url = f"{base_url}/sentinel-s2-l2a-cogs/{utm_zone}/{latitude_band}/{grid_square}/{year}/{int(month)}/S2A_{tile_id}_{date.replace('-', '')}_0_L2A/{band}.tif"
    
    output_path = Path(output_dir) / f"{tile_id}_{date}_{band}.tif"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        output_path.write_bytes(response.content)
        return str(output_path)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed download: {e}")
        raise

def compute_ndvi(red_path: str, nir_path: str) -> np.ndarray:
    """Calculate NDVI: (NIR - Red) / (NIR + Red)"""
    with rasterio.open(red_path) as src:
        red = src.read(1).astype(np.float32) / 10000.0
    with rasterio.open(nir_path) as src:
        nir = src.read(1).astype(np.float32) / 10000.0
    
    denom = nir + red
    denom = np.where(denom == 0, 1e-6, denom)
    ndvi = (nir - red) / denom
    return np.clip(ndvi, -1.0, 1.0)

def process_tile(tile_id: str, date: str) -> Dict[str, Any]:
    """Process a single Sentinel-2 tile."""
    red_path = download_sentinel_tile(tile_id, "B04", date)
    nir_path = download_sentinel_tile(tile_id, "B08", date)
    
    ndvi = compute_ndvi(red_path, nir_path)
    
    return {
        "tile_id": tile_id,
        "date": date,
        "ndvi_mean": float(np.mean(ndvi)),
        "ndvi_std": float(np.std(ndvi))
    }
