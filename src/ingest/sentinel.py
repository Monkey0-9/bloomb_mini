"""
Sentinel-2 WMTS XYZ Tile Invester (NO-KEY).
Downloads true colour 10m Sentinel-2 tiles publicly from EOX/Copernicus WMTS.
"""

import math
import sqlite3
import httpx
import hashlib
from datetime import UTC, datetime
from pathlib import Path
import structlog
from typing import Any, cast

log = cast(Any, structlog.get_logger())

# NO KEY public ESA/Copernicus s2cloudless WMTS
WMTS_TEMPLATE = (
    "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2023/default/g/"
    "{z}/{y}/{x}.jpg"
)

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
    " laem_chabang": [100.8, 13.0, 101.1, 13.2],
}


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


class SentinelIngester:
    def __init__(
        self,
        catalog_db: str = "data/catalog.db",
        raw_data_dir: str = "data/raw/sentinel2"
    ) -> None:
        self.catalog_db = catalog_db
        self.raw_data_dir = Path(raw_data_dir)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        Path(self.catalog_db).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.catalog_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wmts_tiles (
                    tile_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    ingest_timestamp_utc TEXT NOT NULL,
                    bbox_wgs84 TEXT NOT NULL,
                    checksum_sha256 TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    location_key TEXT NOT NULL
                )
            """)
            conn.commit()

    def fetch_latest_tile(
        self,
        location_key: str,
        zoom: int = 14
    ) -> dict:
        if location_key not in LOCATIONS:
            raise ValueError(f"Unknown location: {location_key}")

        bbox = LOCATIONS[location_key]
        center_lon = (bbox[0] + bbox[2]) / 2.0
        center_lat = (bbox[1] + bbox[3]) / 2.0
        x, y = deg2num(center_lat, center_lon, zoom)

        url = WMTS_TEMPLATE.format(z=zoom, x=x, y=y)
        tile_id = f"s2cloudless_z{zoom}_x{x}_y{y}_{location_key}"
        file_path = self.raw_data_dir / f"{tile_id}.jpg"

        if file_path.exists():
            log.info("sentinel_tile_exists", file=str(file_path))
        else:
            log.info("sentinel_wmts_download", url=url)
            resp = httpx.get(url, timeout=30)
            resp.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(resp.content)
            log.info("sentinel_tile_saved", file=str(file_path))

        h = hashlib.sha256()
        h.update(file_path.read_bytes())
        checksum = h.hexdigest()

        with sqlite3.connect(self.catalog_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO wmts_tiles VALUES (?,?,?,?,?,?,?)",
                (
                    tile_id, "copernicus-wmts-s2",
                    datetime.now(UTC).isoformat(), str(bbox),
                    checksum, str(file_path), location_key
                )
            )
            conn.commit()

        return {
            "tile_id": tile_id,
            "file_path": str(file_path),
            "zoom": zoom,
            "url": url
        }


if __name__ == "__main__":
    ingester = SentinelIngester()
    res = ingester.fetch_latest_tile("rotterdam", zoom=14)
    print("Downloaded WMTS S2 Tile:", res)
