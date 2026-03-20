"""
NASA GIBS (Global Imagery Browse Services) Ingestor.
NO-KEY WMTS tile server for satellite imagery.
"""

import math
import hashlib
import aiohttp
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
import structlog
from typing import Any, cast

log = cast(Any, structlog.get_logger())

WMTS_TEMPLATE = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{layer}/default/{date}/GoogleMapsCompatible/{z}/{y}/{x}.jpg"

# Key NASA GIBS Layer names
LAYERS = {
    "viirs_true_color": "VIIRS_SNPP_CorrectedReflectance_TrueColor",
    "modis_true_color": "MODIS_Terra_CorrectedReflectance_TrueColor",
    "viirs_fires": "VIIRS_SNPP_Fires_375m_Day",
    "landsat_annual": "Landsat_WELD_CorrectedReflectance_TrueColor_Global_Annual"
}

LOCATIONS: dict[str, list[float]] = {
    "rotterdam": [3.9, 51.85, 4.6, 52.05],
    "singapore": [103.6, 1.2, 104.1, 1.5],
    "losangeles": [-118.35, 33.7, -118.1, 33.85],
    "shanghai": [121.8, 30.5, 122.1, 30.75],
    "felixstowe": [1.3, 51.9, 1.5, 52.05],
    "tokyo": [139.5, 35.5, 140.1, 35.9],
    "hamburg": [9.7, 53.4, 10.2, 53.7],
    "dubai": [55.0, 25.1, 55.5, 25.5],
    "busan": [128.9, 35.0, 129.2, 35.2],
    "laem_chabang": [100.8, 13.0, 101.1, 13.2],
}

def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

class GibsIngester:
    def __init__(self, catalog_db: str = "data/catalog.db", raw_data_dir: str = "data/raw/gibs") -> None:
        self.catalog_db = catalog_db
        self.raw_data_dir = Path(raw_data_dir)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        Path(self.catalog_db).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.catalog_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gibs_tiles (
                    tile_id TEXT PRIMARY KEY,
                    layer TEXT NOT NULL,
                    ingest_timestamp_utc TEXT NOT NULL,
                    bbox_wgs84 TEXT NOT NULL,
                    checksum_sha256 TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    location_key TEXT NOT NULL
                )
            """)
            conn.commit()

    async def fetch_latest_tile(self, location_key: str, layer_key: str = "viirs_true_color", zoom: int = 7) -> dict:
        if location_key not in LOCATIONS:
            raise ValueError(f"Unknown location: {location_key}")
        if layer_key not in LAYERS:
            raise ValueError(f"Unknown layer: {layer_key}")

        bbox = LOCATIONS[location_key]
        center_lon = (bbox[0] + bbox[2]) / 2.0
        center_lat = (bbox[1] + bbox[3]) / 2.0
        x, y = deg2num(center_lat, center_lon, zoom)
        
        # NASA GIBS uses YYYY-MM-DD for date
        date_str = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
        layer_name = LAYERS[layer_key]
        
        url = WMTS_TEMPLATE.format(layer=layer_name, date=date_str, z=zoom, x=x, y=y)
        tile_id = f"gibs_{layer_name}_z{zoom}_x{x}_y{y}_{date_str}_{location_key}"
        file_path = self.raw_data_dir / f"{tile_id}.jpg"

        if file_path.exists():
            log.info("gibs_tile_exists", file=str(file_path))
        else:
            log.info("gibs_wmts_download", url=url)
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    if resp.status == 404:
                        log.warning("gibs_tile_not_found_for_date", date=date_str)
                        # Fallback to older date
                        date_str = (datetime.now(UTC) - timedelta(days=2)).strftime("%Y-%m-%d")
                        url = WMTS_TEMPLATE.format(layer=layer_name, date=date_str, z=zoom, x=x, y=y)
                        async with session.get(url, timeout=30) as resp2:
                            resp2.raise_for_status()
                            content = await resp2.read()
                    else:
                        resp.raise_for_status()
                        content = await resp.read()
                    
                    with open(file_path, "wb") as f:
                        f.write(content)
            log.info("gibs_tile_saved", file=str(file_path))

        h = hashlib.sha256()
        h.update(file_path.read_bytes())
        checksum = h.hexdigest()

        with sqlite3.connect(self.catalog_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO gibs_tiles VALUES (?,?,?,?,?,?,?)",
                (tile_id, layer_name, datetime.now(UTC).isoformat(), str(bbox), checksum, str(file_path), location_key)
            )
            conn.commit()

        return {"tile_id": tile_id, "file_path": str(file_path), "layer": layer_name, "zoom": zoom, "url": url}

if __name__ == "__main__":
    import asyncio
    async def main():
        ingester = GibsIngester()
        res = await ingester.fetch_latest_tile("rotterdam", layer_key="viirs_fires", zoom=7)
        print("Downloaded NASA GIBS Tile:", res)
    asyncio.run(main())
