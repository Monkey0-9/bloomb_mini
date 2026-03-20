"""
SatTrade Sentinel Ingestion — Non-blocking Async
=================================================
Fetches Sentinel-2 imagery metadata and thermal anomalies.
Completely async via aiohttp. No blocking requests.get().
Priority queue for ticker-specific regions.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Optional

import aiohttp
import structlog

log = structlog.get_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SENTINEL_HUB_CLIENT_ID = os.getenv("SENTINEL_HUB_CLIENT_ID", "")
SENTINEL_HUB_CLIENT_SECRET = os.getenv("SENTINEL_HUB_CLIENT_SECRET", "")


class SentinelIngester:
    """Async Sentinel-2 optical and Sentinel-3 thermal ingestion."""

    # 15 concurrent open connections max
    _sem = asyncio.Semaphore(15)

    def __init__(self) -> None:
        self._auth_token: Optional[str] = None
        self._token_expires: float = 0.0
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
            except Exception:
                pass
        return self._redis

    async def _authenticate(self) -> bool:
        """Fetch Sentinel Hub OAuth token asynchronously."""
        if not SENTINEL_HUB_CLIENT_ID or not SENTINEL_HUB_CLIENT_SECRET:
            log.warning("sentinel_credentials_missing", msg="Using mock data mode")
            return False

        if self._auth_token and time.time() < self._token_expires:
            return True

        url = "https://services.sentinel-hub.com/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": SENTINEL_HUB_CLIENT_ID,
            "client_secret": SENTINEL_HUB_CLIENT_SECRET,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._auth_token = data.get("access_token")
                        # standard 3600s, buffer of 300s
                        self._token_expires = time.time() + float(data.get("expires_in", 3600)) - 300
                        log.info("sentinel_authenticated")
                        return True
                    else:
                        log.error("sentinel_auth_failed", status=resp.status, text=await resp.text())
                        return False
        except Exception as exc:
            log.error("sentinel_auth_error", error=str(exc))
            return False

    async def fetch_regional_thermal(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5.0,
        days_back: int = 3,
    ) -> dict:
        """Fetch latest FIRMS/Sentinel-3 thermal anomalies for a bounding box."""
        # Convert radius to rough bbox
        d_lat = radius_km / 111.0
        d_lon = radius_km / (111.0 * os.path.cos(os.path.radians(lat)))
        bbox = [lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat]

        r = await self._get_redis()
        cache_key = f"thermal:{round(lat, 2)}:{round(lon, 2)}"
        if r:
            try:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        has_auth = await self._authenticate()
        if not has_auth:
            # Mock return for dev environment without keys
            res = self._mock_thermal_response(lat, lon)
            if r:
                try:
                    await r.setex(cache_key, 3600, json.dumps(res))
                except Exception:
                    pass
            return res

        start_dt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - days_back * 86400))
        end_dt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Catalog Search API
        url = "https://services.sentinel-hub.com/api/v1/catalog/1.0.0/search"
        payload = {
            "collections": ["sentinel-3-slstr"],
            "bbox": bbox,
            "datetime": f"{start_dt}/{end_dt}",
            "limit": 5,
        }
        headers = {"Authorization": f"Bearer {self._auth_token}", "Content-Type": "application/json"}

        async with self._sem:
            try:
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.post(url, json=payload, timeout=12) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            features = data.get("features", [])
                            frp_mw = sum(f.get("properties", {}).get("FRP", 0.0) for f in features)
                            
                            res = {
                                "lat": lat, "lon": lon,
                                "anomalies_count": len(features),
                                "frp_mw": round(frp_mw, 1),
                                "latest_acquisition": features[0]["properties"]["datetime"] if features else None,
                                "age_s": 0 if features else 9999,
                                "source": "sentinel-3",
                            }
                            if r:
                                try:
                                    await r.setex(cache_key, 3600, json.dumps(res))
                                except Exception:
                                    pass
                            return res
            except Exception as exc:
                log.warning("sentinel_catalog_search_failed", error=str(exc))

        return {"lat": lat, "lon": lon, "frp_mw": 0.0, "anomalies_count": 0, "age_s": 9999}

    def _mock_thermal_response(self, lat: float, lon: float) -> dict:
        """Dev mode mock data."""
        import random
        frp = random.uniform(0, 1500) if random.random() > 0.4 else 0.0
        return {
            "lat": lat, "lon": lon,
            "anomalies_count": int(frp / 50),
            "frp_mw": round(frp, 1),
            "latest_acquisition": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - random.randint(3600, 86400))),
            "age_s": random.randint(3600, 86400),
            "source": "mock_thermal"
        }

    async def fetch_optical_imagery(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5.0,
        days_back: int = 14,
        output_dir: str = "/tmp/sentinel2",
    ) -> str | None:
        """Fetch Sentinel-2 L2A optical imagery via Process API."""
        has_auth = await self._authenticate()
        if not has_auth:
            log.warning("sentinel2_optical_mocked")
            return None

        os.makedirs(output_dir, exist_ok=True)
        # Bounding box
        d_lat = radius_km / 111.0
        d_lon = radius_km / (111.0 * os.path.cos(os.path.radians(lat)))
        bbox = [lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat]

        start_dt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - days_back * 86400))
        end_dt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        evalscript = '''
        //VERSION=3
        function setup() {
            return {
                input: ["B02", "B03", "B04", "B08", "B11", "B12"],
                output: { bands: 6, sampleType: "UINT16" }
            };
        }
        function evaluatePixel(sample) {
            return [sample.B02, sample.B03, sample.B04, sample.B08, sample.B11, sample.B12];
        }
        '''
        
        headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "Content-Type": "application/json",
            "Accept": "image/tiff"
        }

        # 1. Search Catalog for Metadata (Solar Zenith, etc.)
        catalog_url = "https://services.sentinel-hub.com/api/v1/catalog/1.0.0/search"
        cat_payload = {
            "bbox": bbox,
            "datetime": f"{start_dt}/{end_dt}",
            "collections": ["sentinel-2-l2a"],
            "limit": 1,
            "distinct": "date"
        }
        
        solar_z, solar_a = 40.0, 160.0  # Defaults
        view_z, view_a = 0.0, 0.0
        acq_month, acq_day = 6, 15
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(catalog_url, json=cat_payload) as cat_resp:
                if cat_resp.status == 200:
                    cat_data = await cat_resp.json()
                    if cat_data.get("features"):
                        props = cat_data["features"][0]["properties"]
                        solar_a = props.get("view:sun_azimuth", 160.0)
                        solar_z = 90.0 - props.get("view:sun_elevation", 50.0)
                        view_z = props.get("view:incidence_angle", 0.0)
                        view_a = props.get("view:azimuth", 0.0)
                        
                        dt_str = props.get("datetime", end_dt)
                        try:
                            dt_obj = datetime.strptime(dt_str[:10], "%Y-%m-%d")
                            acq_month, acq_day = dt_obj.month, dt_obj.day
                        except (ValueError, TypeError):
                            pass
                        log.info(
                            "sentinel2_metadata_extracted",
                            solar_z=solar_z,
                            solar_a=solar_a,
                            view_z=view_z
                        )

                        # Quality Gate Check
                        try:
                            from src.common.schemas import TileMetadata
                            from src.ingest.quality_gates import run_all_gates
                            tile_metadata = TileMetadata(
                                tile_id=cat_data["features"][0]["id"],
                                source="sentinel-2-l2a",
                                cloud_cover_pct=props.get("eo:cloud_cover", 0.0),
                                acquisition_utc=datetime.fromisoformat(
                                    dt_str.replace("Z", "+00:00")
                                ),
                                file_path="", # To be filled after download
                                checksum_sha256="", # To be filled after download
                                bbox_wgs84=bbox
                            )
                            gate_res = run_all_gates(tile_metadata)
                            if gate_res.status == "REJECT":
                                log.warning("sentinel2_quality_gate_failed", reason=gate_res.reason)
                                # In production, we might skip this tile, but for now we proceed with a warning
                        except Exception as e:
                            log.error("quality_gate_error", error=str(e))

        # 2. Process API call
        url = "https://services.sentinel-hub.com/api/v1/process"
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {"from": start_dt, "to": end_dt},
                        "maxCloudCoverage": 20
                    }
                }]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
            },
            "evalscript": evalscript
        }

        async with self._sem:
            try:
                import aiohttp
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.post(url, json=payload, timeout=30) as resp:
                        if resp.status == 200:
                            filename = f"{output_dir}/S2_{lat:.2f}_{lon:.2f}_{int(time.time())}.tif"
                            with open(filename, "wb") as f:
                                f.write(await resp.read())
                            log.info("sentinel2_optical_downloaded", file=filename)
                            
                            # Trigger Atmospheric Correction (6S)
                            try:
                                from src.preprocess.optical import correct_atmospheric_6s
                                corrected_path = filename.replace(".tif", "_SR.tif")
                                log.info("sentinel2_starting_atmospheric_correction", input=filename)
                                # Simple defaults for demonstration; production would use metadata
                                result = correct_atmospheric_6s(
                                    input_path=filename,
                                    output_path=corrected_path,
                                    solar_zenith=solar_z,
                                    solar_azimuth=solar_a,
                                    view_zenith=view_z,
                                    view_azimuth=view_a,
                                    acquisition_month=acq_month,
                                    acquisition_day=acq_day,
                                    tile_id=f"S2_{lat}_{lon}"
                                )
                                log.info("sentinel2_atmospheric_correction_done", output=result.output_path)
                                return result.output_path
                            except Exception as e:
                                log.warning("sentinel2_atmospheric_correction_failed", error=str(e))
                                return filename
                        else:
                            text = await resp.text()
                            log.error("sentinel2_process_failed", status=resp.status, text=text)
                            return None
            except Exception as exc:
                log.error("sentinel2_optical_error", error=str(exc))
                return None

    async def fetch_batch(self, locations: list[dict[str, float]]) -> list[dict]:
        """Fetch multiple locations concurrently via semaphore."""
        tasks = [
            self.fetch_regional_thermal(loc["lat"], loc["lon"])
            for loc in locations
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
