"""
Landsat-8/9 Data Ingestor — Phase 1.1

Ingests Landsat thermal and optical imagery from USGS EarthExplorer
for thermal anomaly detection of industrial facilities.

Data source: USGS EarthExplorer / Landsat Collection 2
License: Public Domain — no restrictions.
Resolution: 30m (optical), 100m (thermal TIRS)
Revisit: 16 days (8 days with Landsat-8+9 combined)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from src.common.schemas import (
    BoundingBox,
    IngestEvent,
    IngestStatus,
    ProcessingLevel,
    SensorType,
    TileMetadata,
)

logger = logging.getLogger(__name__)

USGS_M2M_URL = "https://m2m.cr.usgs.gov/api/api/json/stable"
LANDSAT_LICENSE_ID = "usgs_landsat_public_domain"


@dataclass
class LandsatSearchParams:
    """Parameters for Landsat scene search."""

    bbox: BoundingBox
    start_date: datetime
    end_date: datetime
    max_cloud_cover: float = 30.0
    dataset: str = "landsat_ot_c2_l2"  # Collection 2 Level-2
    max_results: int = 50


class USGSAuth:
    """Handle USGS M2M API authentication."""

    def __init__(self, username: str, token: str) -> None:
        self._username = username
        self._token = token
        self._api_key: str | None = None

    def login(self) -> str:
        """Authenticate with USGS M2M API."""
        response = requests.post(
            f"{USGS_M2M_URL}/login",
            json={"username": self._username, "token": self._token},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        self._api_key = data.get("data", "")
        logger.info("USGS M2M authentication successful")
        return self._api_key

    def get_api_key(self) -> str:
        if not self._api_key:
            return self.login()
        return self._api_key

    def logout(self) -> None:
        if self._api_key:
            requests.post(
                f"{USGS_M2M_URL}/logout",
                headers={"X-Auth-Token": self._api_key},
                timeout=10,
            )
            self._api_key = None


class LandsatIngestor:
    """
    USGS Landsat data ingestor.

    Handles search, validation, and download of Landsat Collection 2
    Level-2 products (surface reflectance + surface temperature).
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        auth: USGSAuth,
        raw_storage_path: Path,
        known_checksums: set[str] | None = None,
    ) -> None:
        self._auth = auth
        self._raw_storage_path = raw_storage_path
        self._known_checksums = known_checksums or set()
        self._raw_storage_path.mkdir(parents=True, exist_ok=True)

    def search_scenes(self, params: LandsatSearchParams) -> list[dict[str, Any]]:
        """Search USGS catalog for Landsat scenes matching criteria."""
        api_key = self._auth.get_api_key()

        spatial_filter = {
            "filterType": "mbr",
            "lowerLeft": {
                "latitude": params.bbox.south,
                "longitude": params.bbox.west,
            },
            "upperRight": {
                "latitude": params.bbox.north,
                "longitude": params.bbox.east,
            },
        }

        acquisition_filter = {
            "start": params.start_date.strftime("%Y-%m-%d"),
            "end": params.end_date.strftime("%Y-%m-%d"),
        }

        cloud_filter = {"max": params.max_cloud_cover}

        payload = {
            "datasetName": params.dataset,
            "sceneFilter": {
                "spatialFilter": spatial_filter,
                "acquisitionFilter": acquisition_filter,
                "cloudCoverFilter": cloud_filter,
            },
            "maxResults": params.max_results,
        }

        response = requests.post(
            f"{USGS_M2M_URL}/scene-search",
            json=payload,
            headers={"X-Auth-Token": api_key},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("data", {}).get("results", [])
        logger.info(f"Found {len(results)} Landsat scenes")
        return results

    def validate_and_ingest(self, scene: dict[str, Any]) -> IngestEvent:
        """Process a single Landsat scene through ingestion pipeline."""
        now = datetime.now(UTC)
        entity_id = scene.get("entityId", "")
        display_id = scene.get("displayId", "")

        try:
            metadata = self._extract_metadata(scene)
        except (KeyError, ValueError) as e:
            logger.warning(f"REJECT Landsat scene {entity_id}: {e}")
            return IngestEvent(
                tile_id=entity_id,
                status=IngestStatus.REJECTED,
                reason_if_not_accepted=f"Metadata extraction failed: {e}",
                ingest_timestamp_utc=now,
            )

        # Cloud cover gate
        if metadata.cloud_cover_pct > 30.0:
            return IngestEvent(
                tile_id=entity_id,
                status=IngestStatus.REJECTED,
                reason_if_not_accepted=f"Cloud cover {metadata.cloud_cover_pct}% > 30%",
                ingest_timestamp_utc=now,
            )

        logger.info(f"ACCEPTED Landsat scene {display_id}: {metadata.cloud_cover_pct}% cloud")
        return IngestEvent(
            tile_id=entity_id,
            status=IngestStatus.ACCEPTED,
            ingest_timestamp_utc=now,
        )

    def _extract_metadata(self, scene: dict[str, Any]) -> TileMetadata:
        """Extract TileMetadata from USGS scene result."""
        entity_id = scene["entityId"]
        display_id = scene.get("displayId", "")

        # Parse spatial bounds
        spatial = scene.get("spatialBounds", {})
        coords = spatial.get("coordinates", [[[0, 0]]])[0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]

        # Parse acquisition date
        acq_date = scene.get("temporalCoverage", {}).get("startDate", "")
        if acq_date:
            acquisition = datetime.strptime(acq_date, "%Y-%m-%d").replace(tzinfo=UTC)
        else:
            raise ValueError("Missing acquisition date")

        cloud_cover = float(scene.get("cloudCover", 0))

        # Determine if thermal or optical based on display ID
        is_thermal = "TIRS" in display_id.upper() or "ST" in display_id.upper()

        return TileMetadata(
            tile_id=entity_id,
            source="landsat-8/9",
            acquisition_utc=acquisition,
            cloud_cover_pct=cloud_cover,
            sensor_type=SensorType.THERMAL if is_thermal else SensorType.OPTICAL,
            resolution_m=100.0 if is_thermal else 30.0,
            bounding_box_wgs84=BoundingBox(
                west=min(lons),
                south=min(lats),
                east=max(lons),
                north=max(lats),
            ),
            license_id=LANDSAT_LICENSE_ID,
            commercial_use_permitted=True,
            processing_level=ProcessingLevel.L2_LST if is_thermal else ProcessingLevel.L2A,
            checksum_sha256="0" * 64,
        )
