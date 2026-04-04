"""
SatTrade Sentinel-Free Ingestion — NASA FIRMS + ESA Copernicus STAC (100% Free)
================================================================================
Thermal data: NASA FIRMS API (free, no key required for CSV endpoint)
Optical metadata: ESA Copernicus Data Space STAC API (free, no account required)

Replaces the paid Sentinel Hub dependency entirely.
"""
from __future__ import annotations

import asyncio
import math
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

log = structlog.get_logger(__name__)

# NASA FIRMS — 24h VIIRS thermal hotspots (global, completely free)
FIRMS_CSV_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv"

# ESA Copernicus Data Space STAC API — free, no auth required for search
COPERNICUS_STAC = "https://catalogue.dataspace.copernicus.eu/stac/search"


class SentinelFreeIngester:
    """
    Free replacement for the paid SentinelIngester.
    Sources:
     - NASA FIRMS VIIRS for thermal anomaly detection
     - ESA Copernicus STAC for Sentinel-2 L2A scene metadata
    """

    def __init__(self) -> None:
        self._thermal_cache: dict[str, Any] = {}

    async def fetch_regional_thermal(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5.0,
    ) -> dict[str, Any]:
        """
        Fetch NASA FIRMS thermal anomalies within a bounding box.
        No API key needed — free CSV endpoint.
        """
        d_lat = radius_km / 111.0
        d_lon = radius_km / (111.0 * math.cos(math.radians(lat)))
        lat_min, lat_max = lat - d_lat, lat + d_lat
        lon_min, lon_max = lon - d_lon, lon + d_lon

        cache_key = f"{round(lat, 2)}:{round(lon, 2)}"
        if cache_key in self._thermal_cache:
            return self._thermal_cache[cache_key]

        count = 0
        total_frp = 0.0
        latest_ts = None

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(FIRMS_CSV_URL)
                resp.raise_for_status()
                lines = resp.text.strip().split("\n")
                header = [h.strip() for h in lines[0].split(",")]
                lat_idx = header.index("latitude")
                lon_idx = header.index("longitude")
                frp_idx = header.index("frp") if "frp" in header else -1
                ts_idx = header.index("acq_datetime") if "acq_datetime" in header else -1

                for line in lines[1:]:
                    parts = line.split(",")
                    if len(parts) < max(lat_idx, lon_idx) + 1:
                        continue
                    try:
                        v_lat = float(parts[lat_idx])
                        v_lon = float(parts[lon_idx])
                    except ValueError:
                        continue
                    if lat_min <= v_lat <= lat_max and lon_min <= v_lon <= lon_max:
                        count += 1
                        if frp_idx >= 0 and len(parts) > frp_idx:
                            try:
                                total_frp += float(parts[frp_idx])
                            except ValueError:
                                pass
                        if ts_idx >= 0 and len(parts) > ts_idx and latest_ts is None:
                            latest_ts = parts[ts_idx].strip()
        except Exception as exc:
            log.warning("firms_thermal_failed", lat=lat, lon=lon, error=str(exc))

        result: dict[str, Any] = {
            "lat": lat,
            "lon": lon,
            "anomalies_count": count,
            "frp_mw": round(total_frp, 1),
            "latest_acquisition": latest_ts,
            "age_s": 0 if count > 0 else 9999,
            "source": "nasa_firms_viirs",
        }
        self._thermal_cache[cache_key] = result
        return result

    async def fetch_sentinel2_metadata(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5.0,
        days_back: int = 14,
    ) -> list[dict[str, Any]]:
        """
        Search the free ESA Copernicus Data Space STAC for Sentinel-2 L2A scenes.
        No authentication required, 100% free.
        """
        d_lat = radius_km / 111.0
        d_lon = radius_km / (111.0 * math.cos(math.radians(lat)))
        bbox = [lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat]

        from datetime import timedelta
        end_dt = datetime.now(UTC)
        start_dt = end_dt - timedelta(days=days_back)
        time_range = f"{start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"

        payload = {
            "collections": ["SENTINEL-2"],
            "bbox": bbox,
            "datetime": time_range,
            "limit": 5,
            "filter": "eo:cloud_cover < 30",
        }

        scenes = []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(COPERNICUS_STAC, json=payload)
                resp.raise_for_status()
                data = resp.json()
                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    scenes.append({
                        "id": feature.get("id"),
                        "datetime": props.get("datetime"),
                        "cloud_cover": props.get("eo:cloud_cover"),
                        "platform": props.get("platform"),
                        "bbox": feature.get("bbox"),
                        "source": "copernicus_stac",
                    })
        except Exception as exc:
            log.warning("copernicus_stac_failed", lat=lat, lon=lon, error=str(exc))

        return scenes

    async def fetch_batch(self, locations: list[dict[str, float]]) -> list[dict[str, Any]]:
        """Fetch thermal data for multiple locations concurrently."""
        tasks = [
            self.fetch_regional_thermal(loc["lat"], loc["lon"])
            for loc in locations
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]
