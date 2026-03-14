"""
Sentinel API Client — Copernicus Data Space Ecosystem.

Handles authentication, search, and download for Sentinel-1 (SAR) and
Sentinel-2 (optical) tiles. Event-driven: emits NEW_TILE events on
successful ingestion.

Phase 1 primary data source for port throughput signal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from src.common.schemas import (
    BoundingBox,
    IngestEvent,
    IngestStatus,
    ProcessingLevel,
    SensorType,
    TileMetadata,
    compute_file_checksum,
)

logger = logging.getLogger(__name__)

# Copernicus Data Space Ecosystem (CDSE) API endpoints
CDSE_CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

# License ID for Copernicus data (FK to data_licensing_audit)
COPERNICUS_LICENSE_ID = "copernicus_open_cc_by_sa_3_igo"


@dataclass
class SentinelSearchParams:
    """Parameters for Sentinel tile search."""
    collection: str  # "SENTINEL-1" or "SENTINEL-2"
    bbox: BoundingBox
    start_date: datetime
    end_date: datetime
    max_cloud_cover: float = 30.0  # Reject above this (quality gate)
    max_results: int = 100


class CopernicusAuth:
    """Handle CDSE OAuth2 authentication."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        now = datetime.now(timezone.utc)
        if self._token and self._token_expiry and now < self._token_expiry:
            return self._token

        response = requests.post(
            CDSE_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        # Expire 60s early to avoid edge cases
        from datetime import timedelta
        self._token_expiry = now + timedelta(seconds=data.get("expires_in", 3600) - 60)
        return self._token


class SentinelIngestor:
    """
    Data Ingestor Agent for Sentinel-1 and Sentinel-2 tiles.

    Implements the Data Ingestor Agent spec:
    1. Query source API for matching tiles
    2. Validate all required metadata fields
    3. Check licensing table
    4. Compute SHA-256 and check for duplicates
    5. Write to raw/ prefix, emit events
    6. Retry with exponential backoff on failure
    """

    MAX_RETRIES = 3
    MAX_BACKOFF_SECONDS = 60

    def __init__(
        self,
        auth: CopernicusAuth,
        raw_storage_path: Path,
        known_checksums: Optional[set[str]] = None,
    ) -> None:
        self._auth = auth
        self._raw_storage_path = raw_storage_path
        self._known_checksums = known_checksums or set()
        self._raw_storage_path.mkdir(parents=True, exist_ok=True)

    def search_tiles(self, params: SentinelSearchParams) -> list[dict[str, Any]]:
        """
        Search the Copernicus catalog for tiles matching the given parameters.
        Returns raw catalog entries for further processing.
        """
        bbox_str = (
            f"{params.bbox.west},{params.bbox.south},"
            f"{params.bbox.east},{params.bbox.north}"
        )

        # OData filter for CDSE
        filter_parts = [
            f"Collection/Name eq '{params.collection}'",
            f"OData.CSL.Intersects(area=geography'SRID=4326;POLYGON(("
            f"{params.bbox.west} {params.bbox.south},"
            f"{params.bbox.east} {params.bbox.south},"
            f"{params.bbox.east} {params.bbox.north},"
            f"{params.bbox.west} {params.bbox.north},"
            f"{params.bbox.west} {params.bbox.south}))')",
            f"ContentDate/Start gt {params.start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')}",
            f"ContentDate/Start lt {params.end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')}",
        ]

        if params.collection == "SENTINEL-2":
            filter_parts.append(
                f"Attributes/OData.CSL.DoubleAttribute/any("
                f"att:att/Name eq 'cloudCover' and att/Value lt {params.max_cloud_cover})"
            )

        odata_filter = " and ".join(filter_parts)

        response = requests.get(
            CDSE_CATALOG_URL,
            params={
                "$filter": odata_filter,
                "$top": params.max_results,
                "$orderby": "ContentDate/Start desc",
            },
            headers={"Authorization": f"Bearer {self._auth.get_token()}"},
            timeout=60,
        )
        response.raise_for_status()
        results = response.json().get("value", [])
        logger.info(f"Found {len(results)} tiles for {params.collection}")
        return results

    def validate_and_ingest(self, catalog_entry: dict[str, Any]) -> IngestEvent:
        """
        Process a single catalog entry through the ingestion pipeline.

        Steps:
        1. Extract and validate metadata
        2. Check licensing (Copernicus = always permitted)
        3. Download raw file
        4. Compute checksum, check duplicates
        5. Store in raw/ prefix
        """
        tile_id = catalog_entry.get("Id", "")
        now = datetime.now(timezone.utc)

        # Step 1: Validate required fields
        try:
            metadata = self._extract_metadata(catalog_entry)
        except (KeyError, ValueError) as e:
            logger.warning(f"REJECT tile {tile_id}: missing/invalid metadata — {e}")
            return IngestEvent(
                tile_id=tile_id,
                status=IngestStatus.REJECTED,
                reason_if_not_accepted=f"Metadata validation failed: {e}",
                ingest_timestamp_utc=now,
            )

        # Step 2: Check licensing (Copernicus is always permitted)
        if not metadata.commercial_use_permitted:
            logger.warning(f"BLOCKED tile {tile_id}: commercial use not permitted")
            return IngestEvent(
                tile_id=tile_id,
                status=IngestStatus.BLOCKED,
                reason_if_not_accepted="commercial_use_permitted = false",
                ingest_timestamp_utc=now,
            )

        # Step 3: Quality gate — cloud cover
        if metadata.cloud_cover_pct > 30.0:
            logger.info(f"REJECT tile {tile_id}: cloud cover {metadata.cloud_cover_pct}% > 30%")
            return IngestEvent(
                tile_id=tile_id,
                status=IngestStatus.REJECTED,
                reason_if_not_accepted=f"Cloud cover {metadata.cloud_cover_pct}% exceeds 30% threshold",
                ingest_timestamp_utc=now,
            )

        # Step 4: Download and compute checksum
        download_url = catalog_entry.get("Assets", [{}])[0].get("DownloadLink", "")
        if not download_url:
            # Use CDSE download pattern
            download_url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({tile_id})/$value"

        local_path = self._raw_storage_path / f"{tile_id}.zip"

        try:
            self._download_with_retry(download_url, local_path)
        except Exception as e:
            logger.error(f"INGEST_FAILURE tile {tile_id}: download failed after retries — {e}")
            return IngestEvent(
                tile_id=tile_id,
                status=IngestStatus.REJECTED,
                reason_if_not_accepted=f"Download failed: {e}",
                ingest_timestamp_utc=now,
            )

        checksum = compute_file_checksum(local_path)

        # Step 5: Duplicate check
        if checksum in self._known_checksums:
            local_path.unlink(missing_ok=True)  # Clean up duplicate
            logger.info(f"DUPLICATE tile {tile_id}: checksum {checksum[:16]}... already exists")
            return IngestEvent(
                tile_id=tile_id,
                status=IngestStatus.DUPLICATE,
                reason_if_not_accepted=f"Duplicate checksum: {checksum[:16]}...",
                ingest_timestamp_utc=now,
            )

        self._known_checksums.add(checksum)

        # Step 6: Update metadata with checksum and emit ACCEPTED
        logger.info(f"ACCEPTED tile {tile_id}: {metadata.sensor_type.value}, {metadata.resolution_m}m")
        return IngestEvent(
            tile_id=tile_id,
            status=IngestStatus.ACCEPTED,
            ingest_timestamp_utc=now,
        )

    def _extract_metadata(self, entry: dict[str, Any]) -> TileMetadata:
        """Extract TileMetadata from a CDSE catalog entry."""
        tile_id = entry["Id"]
        name: str = entry.get("Name", "")

        # Determine sensor type from collection
        if "S1" in name or "SENTINEL-1" in entry.get("Collection", {}).get("Name", ""):
            sensor = SensorType.SAR
            resolution = 10.0
            processing_level = ProcessingLevel.L1_GRD
            cloud_cover = 0.0  # SAR doesn't have cloud cover
        elif "S2" in name or "SENTINEL-2" in entry.get("Collection", {}).get("Name", ""):
            sensor = SensorType.OPTICAL
            resolution = 10.0
            processing_level = ProcessingLevel.L2A
            # Extract cloud cover from attributes
            cloud_cover = 0.0
            for attr in entry.get("Attributes", []):
                if attr.get("Name") == "cloudCover":
                    cloud_cover = float(attr.get("Value", 0))
                    break
        else:
            raise ValueError(f"Unknown sensor in product name: {name}")

        # Extract bounding box from GeoFootprint
        footprint = entry.get("GeoFootprint", {})
        coords = footprint.get("coordinates", [[[0, 0]]])[0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        bbox = BoundingBox(
            west=min(lons), south=min(lats),
            east=max(lons), north=max(lats),
        )

        # Parse acquisition date
        content_date = entry.get("ContentDate", {})
        acq_str = content_date.get("Start", "")
        if acq_str:
            acquisition = datetime.fromisoformat(acq_str.replace("Z", "+00:00"))
        else:
            raise ValueError("Missing ContentDate/Start")

        return TileMetadata(
            tile_id=tile_id,
            source=f"sentinel-{1 if sensor == SensorType.SAR else 2}",
            acquisition_utc=acquisition,
            cloud_cover_pct=cloud_cover,
            sensor_type=sensor,
            resolution_m=resolution,
            bounding_box_wgs84=bbox,
            license_id=COPERNICUS_LICENSE_ID,
            commercial_use_permitted=True,  # Copernicus is always open
            processing_level=processing_level,
            checksum_sha256="0" * 64,  # Placeholder until download completes
        )

    def _download_with_retry(self, url: str, local_path: Path) -> None:
        """Download file with exponential backoff (3 retries, max 60s)."""
        import time

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {self._auth.get_token()}"},
                    stream=True,
                    timeout=300,
                )
                response.raise_for_status()
                import os
                import stat

                if local_path.exists():
                    raise FileExistsError(f"WORM violation: {local_path} already exists and cannot be overwritten.")

                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                os.chmod(local_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
                return  # Success
            except (requests.RequestException, IOError) as e:
                import random
                base_wait = min(2**attempt * 5, self.MAX_BACKOFF_SECONDS)
                wait = base_wait + random.uniform(0, base_wait * 0.1)  # 10% stochastic jitter
                logger.warning(
                    f"Download attempt {attempt + 1}/{self.MAX_RETRIES} failed: {e}. "
                    f"Retrying in {wait:.2f}s."
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(wait)
                else:
                    raise
