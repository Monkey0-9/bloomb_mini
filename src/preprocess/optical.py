"""
Optical Preprocessing Pipeline (Sentinel-2 / Landsat).

Steps:
1. Download Sentinel-2 COG tile from AWS public bucket
2. Compute surface reflectance using simple scaling
3. Calculate indices (NDVI)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

import numpy as np
import rasterio

logger = logging.getLogger(__name__)


def download_sentinel_tile(
    tile_id: str,
    band: str = "B04",
    date: str = "2024-01-01",
    output_dir: str = "./data/tiles",
) -> str:
    """
    Download Sentinel-2 COG tile from AWS public bucket.
    
    Args:
        tile_id: MGRS tile ID (e.g., "31UET")
        band: Band name (B02=blue, B03=green, B04=red, B08=nir)
        date: Date string YYYY-MM-DD
        output_dir: Local directory to save tiles
        
    Returns:
        Path to downloaded tile
    """
    import requests
    
    # AWS S3 public bucket URL structure
    base_url = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
    
    # Parse tile ID
    utm_zone = tile_id[:2]
    latitude_band = tile_id[2]
    grid_square = tile_id[3:]
    
    # Parse date
    year, month, day = date.split("-")
    
    # Construct URL
    url = f"{base_url}/sentinel-s2-l2a-cogs/{utm_zone}/{latitude_band}/{grid_square}/{year}/{int(month)}/S2A_{tile_id}_{date.replace('-', '')}_0_L2A/{band}.tif"
    
    output_path = Path(output_dir) / f"{tile_id}_{date}_{band}.tif"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {output_path}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        output_path.write_bytes(response.content)
        return str(output_path)
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise


def correct_atmospheric_simple(input_path: str) -> np.ndarray:
    """
    Apply simple atmospheric correction using Sentinel-2 scaling.
    
    Sentinel-2 L2A products are already atmospherically corrected.
    We just apply the scaling factor to get surface reflectance.
    
    Returns:
        Surface reflectance array [0.0, 1.0]
    """
    with rasterio.open(input_path) as src:
        data = src.read(1).astype(np.float32)
    
    # Sentinel-2 scaling: divide by 10000 to get reflectance
    reflectance = data / 10000.0
    
    # Clamp to valid range
    reflectance = np.clip(reflectance, 0.0, 1.0)
    
    return reflectance


def compute_ndvi(red_path: str, nir_path: str) -> np.ndarray:
    """
    Calculate Normalized Difference Vegetation Index (NDVI).
    
    NDVI = (NIR - Red) / (NIR + Red)
    
    Args:
        red_path: Path to Red band (B04) COG
        nir_path: Path to NIR band (B08) COG
        
    Returns:
        NDVI array [-1.0, 1.0]
    """
    red = correct_atmospheric_simple(red_path)
    nir = correct_atmospheric_simple(nir_path)
    
    # Avoid division by zero
    denom = nir + red
    denom = np.where(denom == 0, 1e-6, denom)
    
    ndvi = (nir - red) / denom
    return cast(np.ndarray, np.clip(ndvi, -1.0, 1.0))


def process_sentinel_tile(tile_id: str, date: str, output_dir: str = "./data/processed") -> dict:
    """
    Complete processing pipeline for a Sentinel-2 tile.
    
    Args:
        tile_id: MGRS tile ID
        date: Date string YYYY-MM-DD
        output_dir: Output directory for processed data
        
    Returns:
        Dictionary with paths to processed outputs
    """
    logger.info(f"Processing {tile_id} for {date}")
    
    # Download bands
    red_path = download_sentinel_tile(tile_id, "B04", date)
    nir_path = download_sentinel_tile(tile_id, "B08", date)
    
    # Compute NDVI
    ndvi = compute_ndvi(red_path, nir_path)
    
    # Save NDVI
    output_path = Path(output_dir) / f"{tile_id}_{date}_ndvi.tif"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with rasterio.open(red_path) as src:
        profile = src.profile
        profile.update(dtype=rasterio.float32, count=1)
        
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(ndvi.astype(rasterio.float32), 1)
    
    return {
        "tile_id": tile_id,
        "date": date,
        "ndvi_path": str(output_path),
        "ndvi_mean": float(np.mean(ndvi)),
        "ndvi_std": float(np.std(ndvi)),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Optical preprocessing module loaded.")
