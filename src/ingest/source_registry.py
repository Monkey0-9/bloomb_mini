"""
Source Registry — Phase 1.1

Central registry of all data sources with their API endpoints,
credentials references, licensing status, and health checks.

Every data source used in the pipeline MUST be registered here.
Unregistered sources cannot be ingested.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SourceTier(str, Enum):
    FREE = "free"
    COMMERCIAL = "commercial"


class SourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    BLOCKED = "blocked"  # License issue


@dataclass
class DataSource:
    """Registered data source with complete metadata."""

    source_id: str
    name: str
    provider: str
    tier: SourceTier
    api_endpoint: str
    sensor_type: str
    resolution_m: float
    revisit_days: float
    license_id: str
    commercial_use_permitted: bool
    cost_per_month_usd: float
    credentials_secret_name: str  # AWS Secrets Manager key
    status: SourceStatus = SourceStatus.ACTIVE
    last_health_check: datetime | None = None
    notes: str = ""


class SourceRegistry:
    """
    Central registry for all data sources.

    Phase 1 sources (free tier):
      - Sentinel-1 SAR
      - Sentinel-2 Optical
      - Landsat-8/9 Thermal+Optical
      - NOAA AIS
      - Copernicus DEM
      - OpenStreetMap

    Phase 2 sources (commercial, budget-dependent):
      - Planet Labs PlanetScope
      - Capella Space SAR
      - Spire Maritime AIS
    """

    def __init__(self) -> None:
        self._sources: dict[str, DataSource] = {}
        self._register_default_sources()

    def _register_default_sources(self) -> None:
        """Register all Phase 1 and Phase 2 data sources."""

        # ── Phase 1: Free Tier ──────────────────────────────
        self.register(
            DataSource(
                source_id="sentinel-1",
                name="Sentinel-1 SAR",
                provider="ESA / Copernicus",
                tier=SourceTier.FREE,
                api_endpoint="https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
                sensor_type="SAR",
                resolution_m=10.0,
                revisit_days=6.0,
                license_id="copernicus_open_cc_by_sa_3_igo",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="sattrade/copernicus-cdse",
            )
        )

        self.register(
            DataSource(
                source_id="sentinel-2",
                name="Sentinel-2 MSI Optical",
                provider="ESA / Copernicus",
                tier=SourceTier.FREE,
                api_endpoint="https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
                sensor_type="optical",
                resolution_m=10.0,
                revisit_days=5.0,
                license_id="copernicus_open_cc_by_sa_3_igo",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="sattrade/copernicus-cdse",
            )
        )

        self.register(
            DataSource(
                source_id="landsat-8",
                name="Landsat-8/9 OLI+TIRS",
                provider="USGS",
                tier=SourceTier.FREE,
                api_endpoint="https://m2m.cr.usgs.gov/api/api/json/stable",
                sensor_type="optical+thermal",
                resolution_m=30.0,  # 100m for thermal
                revisit_days=8.0,  # Combined L8+L9
                license_id="usgs_landsat_public_domain",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="sattrade/usgs-m2m",
            )
        )

        self.register(
            DataSource(
                source_id="noaa-ais",
                name="NOAA AIS Vessel Tracking",
                provider="US Coast Guard / NOAA",
                tier=SourceTier.FREE,
                api_endpoint="https://marinecadastre.gov/ais/",
                sensor_type="AIS",
                resolution_m=0.0,  # Point data
                revisit_days=0.0,  # Continuous
                license_id="noaa_ais_public_domain",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="",  # No auth needed
            )
        )

        self.register(
            DataSource(
                source_id="copernicus-dem",
                name="Copernicus DEM 30m",
                provider="ESA",
                tier=SourceTier.FREE,
                api_endpoint="https://prism-dem-open.copernicus.eu",
                sensor_type="DEM",
                resolution_m=30.0,
                revisit_days=0.0,  # Static
                license_id="copernicus_dem_open",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="",
            )
        )

        self.register(
            DataSource(
                source_id="openstreetmap",
                name="OpenStreetMap Building Footprints",
                provider="OSM Foundation",
                tier=SourceTier.FREE,
                api_endpoint="https://overpass-api.de/api/interpreter",
                sensor_type="vector",
                resolution_m=0.0,
                revisit_days=0.0,  # Community-updated
                license_id="osm_odbl_1_0",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="",
            )
        )

        self.register(
            DataSource(
                source_id="open-meteo-marine",
                name="Open-Meteo Marine Weather",
                provider="Open-Meteo",
                tier=SourceTier.FREE,
                api_endpoint="https://marine-api.open-meteo.com/v1/marine",
                sensor_type="weather",
                resolution_m=5000.0,
                revisit_days=0.04,  # Hourly
                license_id="open_meteo_commercial_free",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="",
            )
        )

        self.register(
            DataSource(
                source_id="open-meteo-aq",
                name="Open-Meteo Air Quality",
                provider="Open-Meteo",
                tier=SourceTier.FREE,
                api_endpoint="https://air-quality-api.open-meteo.com/v1/air-quality",
                sensor_type="environmental",
                resolution_m=10000.0,
                revisit_days=0.04,  # Hourly
                license_id="open_meteo_commercial_free",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="",
            )
        )

        self.register(
            DataSource(
                source_id="fred-macro",
                name="St. Louis Fed Economic Data",
                provider="FRED",
                tier=SourceTier.FREE,
                api_endpoint="https://fred.stlouisfed.org/graph/fredgraph.csv",
                sensor_type="macroeconomic",
                resolution_m=0.0,
                revisit_days=1.0,  # Daily
                license_id="fred_public_domain",
                commercial_use_permitted=True,
                cost_per_month_usd=0.0,
                credentials_secret_name="",
            )
        )

        # ── Phase 2: Commercial ─────────────────────────────
        self.register(
            DataSource(
                source_id="planet-psscene",
                name="Planet Labs PlanetScope",
                provider="Planet Labs",
                tier=SourceTier.COMMERCIAL,
                api_endpoint="https://api.planet.com/data/v1/searches",
                sensor_type="optical",
                resolution_m=3.0,
                revisit_days=1.0,
                license_id="planet_commercial_api",
                commercial_use_permitted=True,
                cost_per_month_usd=2000.0,
                credentials_secret_name="sattrade/planet-api",
                status=SourceStatus.INACTIVE,
                notes="Activate when Phase 2 budget approved",
            )
        )

        self.register(
            DataSource(
                source_id="capella-sar",
                name="Capella Space SAR",
                provider="Capella Space",
                tier=SourceTier.COMMERCIAL,
                api_endpoint="https://api.capellaspace.com/catalog/search",
                sensor_type="SAR",
                resolution_m=0.5,
                revisit_days=1.0,
                license_id="capella_commercial_api",
                commercial_use_permitted=True,
                cost_per_month_usd=3000.0,
                credentials_secret_name="sattrade/capella-api",
                status=SourceStatus.INACTIVE,
                notes="Activate when Phase 2 budget approved",
            )
        )

        self.register(
            DataSource(
                source_id="spire-ais",
                name="Spire Maritime AIS",
                provider="Spire Global",
                tier=SourceTier.COMMERCIAL,
                api_endpoint="https://api.spire.com/v2/vessels",
                sensor_type="AIS",
                resolution_m=0.0,
                revisit_days=0.0,
                license_id="spire_commercial_api",
                commercial_use_permitted=True,
                cost_per_month_usd=1000.0,
                credentials_secret_name="sattrade/spire-api",
                status=SourceStatus.INACTIVE,
                notes="Activate when Phase 2 budget approved",
            )
        )

    def register(self, source: DataSource) -> None:
        """Register a data source."""
        if not source.commercial_use_permitted:
            logger.warning(
                f"Source '{source.name}' does NOT permit commercial use — "
                f"automatically BLOCKED per data licensing audit."
            )
            source.status = SourceStatus.BLOCKED

        self._sources[source.source_id] = source
        logger.info(
            f"Registered source: {source.source_id} ({source.name}) [{source.status.value}]"
        )

    def get(self, source_id: str) -> DataSource | None:
        """Get a registered source by ID."""
        return self._sources.get(source_id)

    def get_active_sources(self, tier: SourceTier | None = None) -> list[DataSource]:
        """Get all active sources, optionally filtered by tier."""
        sources = [s for s in self._sources.values() if s.status == SourceStatus.ACTIVE]
        if tier:
            sources = [s for s in sources if s.tier == tier]
        return sources

    def get_phase1_sources(self) -> list[DataSource]:
        """Get all sources available for Phase 1 (free tier, active)."""
        return self.get_active_sources(SourceTier.FREE)

    def validate_source(self, source_id: str) -> bool:
        """Validate that a source is registered, active, and licensed for commercial use."""
        source = self._sources.get(source_id)
        if not source:
            logger.error(f"Source '{source_id}' not registered")
            return False
        if source.status != SourceStatus.ACTIVE:
            logger.error(f"Source '{source_id}' is {source.status.value}")
            return False
        if not source.commercial_use_permitted:
            logger.error(f"Source '{source_id}' does not permit commercial use")
            return False
        return True

    def get_monthly_cost(self) -> dict[str, float]:
        """Get monthly cost breakdown for all active sources."""
        costs: dict[str, float] = {}
        for s in self._sources.values():
            if s.status == SourceStatus.ACTIVE:
                costs[s.source_id] = s.cost_per_month_usd
        costs["total"] = float(sum(costs.values()))
        return costs

    def health_check(self) -> dict[str, dict[str, Any]]:
        """Run health checks on all active sources. Returns status per source."""
        results = {}
        for source in self.get_active_sources():
            try:
                import requests

                resp = requests.head(source.api_endpoint, timeout=10)
                healthy = resp.status_code < 500
                source.last_health_check = datetime.now(UTC)
                results[source.source_id] = {
                    "healthy": healthy,
                    "status_code": resp.status_code,
                    "latency_ms": resp.elapsed.total_seconds() * 1000,
                }
            except Exception as e:
                results[source.source_id] = {
                    "healthy": False,
                    "error": str(e),
                }
        return results
