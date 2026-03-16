"""
Diagnostic script to verify the full Sentinel-2 processing pipeline.
Downloads a tile, performs atmospheric correction, and computes NDVI.
"""
import argparse
import logging
import sys
from pathlib import Path

from src.ingest.sentinel import SentinelIngester
from src.preprocess.optical import correct_atmospheric_6s, compute_ndvi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel_diagnostic")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--location", default="rotterdam", help="Location key from sentinel.py")
    parser.add_argument("--max-cloud", type=float, default=20.0, help="Max cloud cover percentage")
    args = parser.parse_args()

    logger.info(f"Starting diagnostic for location: {args.location}")
    
    try:
        ingester = SentinelIngester()
        tile = ingester.fetch_latest_tile(args.location, args.max_cloud)
        logger.info(f"Successfully downloaded tile: {tile.tile_id}")
        logger.info(f"Atmospheric correction in progress for: {tile.file_path}")
        
        # Real correction (or fallback)
        corrected = correct_atmospheric_6s(tile.file_path, "diag_corrected.tif")
        logger.info(f"Corrected tile saved to: {corrected.path}")
        
        # NDVI calculation
        ndvi_path = compute_ndvi(corrected.path)
        logger.info(f"NDVI map generated at: {ndvi_path}")
        
        logger.info("✓ Sentinel-2 Intelligence Pipeline Verified.")
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
