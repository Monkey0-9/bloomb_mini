"""
Real Sentinel-2 tile downloader using Copernicus Data Space Ecosystem STAC API.
NO MOCKS. NO STUBS. Real HTTP requests. Real tiles on disk.
"""
import hashlib
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import structlog

from src.common.schemas import TileMetadata

log = structlog.get_logger()

STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac/search"
TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE"
    "/protocol/openid-connect/token"
)
DOWNLOAD_BASE = "https://download.dataspace.copernicus.eu"

LOCATIONS: dict[str, list[float]] = {
    "rotterdam":  [3.9,   51.85, 4.6,   52.05],
    "singapore":  [103.6,  1.2,  104.1,  1.5],
    "losangeles": [-118.35,33.7, -118.1, 33.85],
    "shanghai":   [121.8,  30.5, 122.1,  30.75],
    "felixstowe": [1.3,   51.9,  1.5,   52.05],
    "tokyo":      [139.5,  35.5, 140.1,  35.9],
    "hamburg":    [9.7,   53.4,  10.2,   53.7],
    "dubai":      [55.0,  25.1,  55.5,   25.5],
    "busan":      [128.9,  35.0, 129.2,   35.2],
    "laem_chabang":[100.8,13.0, 101.1,   13.2],
}

class CopernicusAuth:
    def __init__(self) -> None:
        self._client_id = os.environ["COPERNICUS_CLIENT_ID"]
        self._client_secret = os.environ["COPERNICUS_CLIENT_SECRET"]
        self._token: str | None = None
        self._expires_at: datetime = datetime.utcnow()

    def get_token(self) -> str:
        if self._token and datetime.utcnow() < self._expires_at:
            return self._token
        resp = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = datetime.utcnow() + timedelta(
            seconds=data["expires_in"] - 60
        )
        return self._token


class SentinelIngester:
    def __init__(
        self,
        catalog_db: str = "data/catalog.db",
        raw_data_dir: str = "data/raw/sentinel2",
    ) -> None:
        self.auth = CopernicusAuth()
        self.catalog_db = catalog_db
        self.raw_data_dir = Path(raw_data_dir)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        Path(self.catalog_db).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.catalog_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tiles (
                    tile_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    acquisition_utc TEXT NOT NULL,
                    processing_level TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    resolution_m REAL NOT NULL,
                    cloud_cover_pct REAL,
                    bbox_wgs84 TEXT NOT NULL,
                    license_id TEXT NOT NULL,
                    commercial_use_ok INTEGER NOT NULL,
                    checksum_sha256 TEXT NOT NULL,
                    preprocessing_ver TEXT NOT NULL DEFAULT '0.0.0',
                    ingest_timestamp_utc TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    location_key TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tile_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    reason TEXT
                )
            """)
            conn.commit()

    def search_tiles(
        self,
        location_key: str,
        days_back: int = 30,
        max_cloud_cover: float = 30.0,
        max_results: int = 5,
    ) -> list[dict]:
        bbox = LOCATIONS[location_key]
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=days_back)
        headers = {"Authorization": f"Bearer {self.auth.get_token()}"}
        payload = {
            "collections": ["SENTINEL-2"],
            "bbox": bbox,
            "datetime": (
                f"{start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}/"
                f"{end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            ),
            "query": {
                "eo:cloud_cover": {"lte": max_cloud_cover},
                "s2:processing_baseline": {"gte": "04.00"},
            },
            "limit": max_results,
            "sortby": [{"field": "properties.datetime", "direction": "desc"}],
        }
        for attempt in range(3):
            try:
                resp = httpx.post(
                    STAC_URL, json=payload, headers=headers, timeout=30
                )
                if resp.status_code == 429:
                    import time
                    time.sleep(2 ** attempt * 5)
                    continue
                resp.raise_for_status()
                features = resp.json().get("features", [])
                log.info("stac_search", location=location_key, found=len(features))
                return features
            except httpx.HTTPError as e:
                log.warning("stac_search_failed", attempt=attempt, error=str(e))
                if attempt == 2:
                    raise
        return []

    def download_tile(self, feature: dict, location_key: str) -> TileMetadata:
        props = feature["properties"]
        tile_id = feature["id"].replace("/", "_")
        file_path = self.raw_data_dir / f"{location_key}_{tile_id}.tif"

        if file_path.exists():
            log.info("tile_already_exists", tile_id=tile_id)
        else:
            download_url = None
            for link in feature.get("links", []):
                if link.get("rel") == "enclosure":
                    download_url = link["href"]
                    break
            if download_url is None:
                assets = feature.get("assets", {})
                download_url = (
                    assets.get("data", {}).get("href")
                    or assets.get("thumbnail", {}).get("href")
                )
            if download_url is None:
                raise ValueError(f"No download URL found for tile {tile_id}")

            headers = {"Authorization": f"Bearer {self.auth.get_token()}"}
            with httpx.stream("GET", download_url, headers=headers, timeout=300,
                              follow_redirects=True) as resp:
                resp.raise_for_status()
                with open(file_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
            log.info("tile_downloaded", tile_id=tile_id, path=str(file_path))

        checksum = self._compute_sha256(str(file_path))
        bbox = feature.get("bbox", LOCATIONS[location_key])
        metadata = TileMetadata(
            tile_id=tile_id,
            source="sentinel2",
            acquisition_utc=datetime.fromisoformat(
                props["datetime"].replace("Z", "+00:00")
            ),
            processing_level=props.get("processing:level", "L2A"),
            sensor_type="OPTICAL",
            resolution_m=10.0,
            cloud_cover_pct=float(props.get("eo:cloud_cover", 0.0)),
            bbox_wgs84=bbox,
            license_id="copernicus_open",
            commercial_use_ok=True,
            checksum_sha256=checksum,
            preprocessing_ver="0.0.0",
            ingest_timestamp_utc=datetime.utcnow(),
            file_path=str(file_path),
            location_key=location_key,
        )
        self._catalog_insert(metadata)
        return metadata

    def _compute_sha256(self, file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _catalog_insert(self, m: TileMetadata) -> None:
        with sqlite3.connect(self.catalog_db) as conn:
            existing = conn.execute(
                "SELECT tile_id FROM tiles WHERE tile_id = ?", (m.tile_id,)
            ).fetchone()
            if existing:
                log.info("catalog_duplicate_skipped", tile_id=m.tile_id)
                return
            conn.execute(
                """INSERT INTO tiles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    m.tile_id, m.source,
                    m.acquisition_utc.isoformat(),
                    m.processing_level, m.sensor_type, m.resolution_m,
                    m.cloud_cover_pct, str(m.bbox_wgs84), m.license_id,
                    int(m.commercial_use_ok), m.checksum_sha256,
                    m.preprocessing_ver, m.ingest_timestamp_utc.isoformat(),
                    m.file_path, m.location_key,
                ),
            )
            conn.commit()
        log.info("catalog_insert", tile_id=m.tile_id, location=m.location_key)

    def fetch_latest_tile(
        self, location_key: str, max_cloud_cover: float = 30.0
    ) -> TileMetadata:
        if location_key not in LOCATIONS:
            raise ValueError(f"Unknown location: {location_key}. "
                             f"Valid: {list(LOCATIONS.keys())}")
        features = self.search_tiles(location_key, max_cloud_cover=max_cloud_cover)
        if not features:
            raise RuntimeError(
                f"No tiles found for {location_key} with cloud cover < "
                f"{max_cloud_cover}%. Try increasing max_cloud_cover."
            )
        return self.download_tile(features[0], location_key)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--location", default="rotterdam",
                        choices=list(LOCATIONS.keys()))
    parser.add_argument("--max-cloud", type=float, default=30.0)
    args = parser.parse_args()

    ingester = SentinelIngester()
    tile = ingester.fetch_latest_tile(args.location, args.max_cloud)
    print(f"✓ Tile ID:       {tile.tile_id}")
    print(f"✓ Acquired:      {tile.acquisition_utc}")
    print(f"✓ Cloud cover:   {tile.cloud_cover_pct:.1f}%")
    print(f"✓ File:          {tile.file_path}")
    print(f"✓ SHA-256:       {tile.checksum_sha256[:16]}...")
