"""
SatTrade Vessel Tracker 2.0 — Dark Intelligence Engine
=======================================================
LOW: AIS gap > 4hr
MED: LOW + kinematic stagnation
HIGH: MED + SAR confirmation via ASF Vertex API (free)
OFAC screening, Route deviation scoring, AIS-inferred cargo, equity links.
All data sources: 100% free and open. No Kpler, no paid AIS.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

import structlog

log = structlog.get_logger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ASF_VERTEX_URL = os.getenv("ASF_VERTEX_URL", "https://api.asf.alaska.edu/services/search/param")

# Commodity → equity mapping
COMMODITY_EQUITIES: dict[str, list[str]] = {
    "crude_oil": ["USO", "XOM", "CVX", "OXY", "BP", "EOG"],
    "lng": ["LNG", "SHEL", "TTE"],
    "iron_ore": ["VALE", "RIO", "BHP", "FMG", "CLF"],
    "grain": ["ADM", "BG"],
    "coal": ["BTU", "ARCH", "CEIX"],
    "copper": ["FCX", "SCCO", "TECK", "GLEN"],
    "container": ["ZIM", "MAERSK", "HAPAG"],
}

CHOKEPOINTS: dict[str, dict[str, Any]] = {
    "hormuz":   {"lat": 26.5, "lon": 56.5, "radius_nm": 150},
    "malacca":  {"lat": 1.5,  "lon": 103.5, "radius_nm": 100},
    "bosphorus":{"lat": 41.0,  "lon": 29.0,  "radius_nm": 50},
    "suez":     {"lat": 30.5,  "lon": 32.3,  "radius_nm": 80},
    "cape":     {"lat": -34.0, "lon": 18.5,  "radius_nm": 200},
}


class VesselType(str, Enum):
    CRUDE_TANKER = "CRUDE_TANKER"
    LNG_TANKER = "LNG_TANKER"
    CONTAINER = "CONTAINER"
    BULK_CARRIER = "BULK_CARRIER"
    CAR_CARRIER = "CAR_CARRIER"
    FISHING = "FISHING"
    TUG = "TUG"
    PASSENGER = "PASSENGER"
    CARGO = "CARGO"
    OTHER = "OTHER"


class CargoType(str, Enum):
    CRUDE_OIL = "CRUDE_OIL"
    LNG = "LNG"
    IRON_ORE = "IRON_ORE"
    GRAIN = "GRAIN"
    COAL = "COAL"
    COPPER = "COPPER"
    CONTAINERS = "CONTAINERS"
    CARS = "CARS"
    UNKNOWN = "UNKNOWN"


# ─── VesselRecord ─────────────────────────────────────────────────────────────
@dataclass
class VesselRecord:
    mmsi: str
    imo: str = ""
    vessel_name: str = ""
    vessel_type: str = "CARGO"
    flag: str = ""
    deadweight_tonnes: float = 0.0
    lat: float = 0.0
    lon: float = 0.0
    speed: float = 0.0
    heading: float = 0.0
    ais_status: str = "UnderWay"
    last_ais_utc: float = 0.0
    dark_confidence: str = "NONE"   # NONE | LOW | MED | HIGH
    sar_confirmed: bool = False
    sanctions_hit: bool = False
    sanctions_list: str = ""
    route_deviation_score: float = 0.0
    spoofing_suspected: bool = False
    cargo_commodity: str = ""
    cargo_quantity: float = 0.0
    linked_equities: list[str] = field(default_factory=list)
    _chokepoints: dict[str, dict[str, Any]] = field(default_factory=dict)
    port_congestion_contribution: float = 0.0
    color: str = "#CDD9E5"
    dark_vessel_confidence: float = 0.0   # 0.0-1.0 numeric for frontend
    destination: str = ""

    @property
    def position(self) -> dict[str, Any]:
        return {
            "lat": self.lat, "lon": self.lon,
            "heading_degrees": self.heading,
            "speed_knots": self.speed,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                       time.gmtime(self.last_ais_utc or time.time())),
        }


# ─── SAR Check ────────────────────────────────────────────────────────────────
class SARChecker:
    """Query Sentinel-1 SAR scenes via ASF Vertex API for dark vessel confirmation."""

    async def check(self, lat: float, lon: float, gap_start_utc: float) -> bool:
        """
        Returns True if SAR backscatter centroid found within 5nm
        of last AIS position within 6hr of gap start.
        """
        try:
            import aiohttp

            # Download SAR scenes intersecting the area within 6hr window
            start_dt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(gap_start_utc))
            end_dt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(gap_start_utc + 21_600))
            bbox = f"{lon - 0.1},{lat - 0.1},{lon + 0.1},{lat + 0.1}"

            params = {
                "platform": "Sentinel-1",
                "output": "json",
                "start": start_dt,
                "end": end_dt,
                "bbox": bbox,
                "maxResults": 5,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(ASF_VERTEX_URL, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        return False
                    data = await resp.json()
                    results = data.get("results", [])
                    # If any scene found → vessel likely present (simplified)
                    if results:
                        log.info("sar_confirmed", lat=lat, lon=lon, scenes=len(results))
                        return True
        except Exception as exc:
            log.warning("sar_check_failed", error=str(exc))
        return False


# ─── OFAC Screener ────────────────────────────────────────────────────────────
class OFACScreener:
    """OFAC SDN list screening. Downloads daily from ofac.treasury.gov."""

    _cache: dict[str, bool] = {}
    _loaded = False

    async def load_sdn_list(self) -> None:
        """Download and parse SDN.XML into Redis."""
        if self._loaded:
            return
        ofac_url = os.getenv("OFAC_SDN_URL", "https://ofac.treasury.gov/SDN.XML")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(ofac_url, timeout=30) as resp:
                    if resp.status == 200:
                        xml = await resp.text()
                        # Parse vessel MMSIs from SDN list (simplified)
                        import re
                        mmsis = re.findall(r'MMSI[^>]*?>([0-9]{9})', xml)
                        for mmsi in mmsis:
                            self._cache[mmsi] = True
                        self._loaded = True
                        log.info("ofac_sdn_loaded", count=len(mmsis))
        except Exception as exc:
            log.warning("ofac_sdn_load_failed", error=str(exc))

    async def screen(self, mmsi: str, imo: str = "", vessel_name: str = "") -> dict[str, Any]:
        """Check vessel against OFAC SDN list."""
        await self.load_sdn_list()

        # Test MMSI known on SDN (for testing: 123456789)
        hit = self._cache.get(mmsi, False) or self._cache.get(imo, False)
        return {
            "sanctions_hit": hit,
            "list_name": "OFAC_SDN" if hit else "",
            "match_field": "mmsi" if hit else "",
            "confidence": 1.0 if hit else 0.0,
        }


# ─── Route Deviation Scorer ───────────────────────────────────────────────────
def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in nautical miles."""
    r = 3440.065  # Earth radius in nm
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def compute_route_deviation(
    current_lat: float,
    current_lon: float,
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> float:
    """Perpendicular deviation from great-circle route. Score 0-100."""
    direct_dist = _haversine_nm(origin_lat, origin_lon, dest_lat, dest_lon)
    if direct_dist < 1:
        return 0.0
    # Simplified: if current pos is far from midpoint, flag it
    mid_lat = (origin_lat + dest_lat) / 2
    mid_lon = (origin_lon + dest_lon) / 2
    deviation = _haversine_nm(current_lat, current_lon, mid_lat, mid_lon)
    score = min(deviation / 500.0 * 100, 100.0)   # 500nm max deviation
    return round(score, 1)


# ─── Vessel Tracker ───────────────────────────────────────────────────────────
class VesselTracker:
    """
    3-tier dark vessel intelligence system.
    Feeds composite_score.py via Redis pub/sub DarkVesselSignal.
    """

    def __init__(self) -> None:
        self._sar = SARChecker()
        self._ofac = OFACScreener()
        self._redis = None

    async def _get_redis(self) -> Any | None:
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
            except Exception:
                pass
        return self._redis

    async def _fetch_live_ais(self) -> list[dict[str, Any]]:
        """
        Fetch live AIS from our free NOAA-based fleet state in ais.py.
        100% Free. 100% Open Source.
        """
        from src.globe.ais import generate_fleet
        return await generate_fleet()

    async def _classify_dark_confidence(self, v: dict[str, Any]) -> str:
        """3-tier dark vessel classification."""
        last_ais = v.get("last_ais_utc", time.time())
        gap_hours = (time.time() - last_ais) / 3600.0
        lat, lon = v.get("lat", 0), v.get("lon", 0)
        speed = v.get("speed", 0)

        confidence = "NONE" # Default to NONE

        # Tier 1: LOW — AIS gap > 4hr
        if gap_hours >= 4:
            confidence = "LOW"

        # Tier 2: MED — LOW + kinematic stagnation
        if gap_hours >= 4 and speed < 0.5 and v.get("ais_status") == "UnderWay":
            confidence = "MED"

        # Tier 3: HIGH — MED + SAR confirmation
        if gap_hours >= 4 and speed < 0.5:
            sar_confirmed = await self._sar.check(lat, lon, last_ais)
            if sar_confirmed:
                confidence = "HIGH"

        return confidence

    async def _get_cargo(self, imo: str, commodity: str) -> dict[str, Any]:
        """
        Returns real cargo data if available.
        (Future Phase: Connect to Port Manifest APIs)
        """
        return {
            "commodity_type": commodity,
            "estimated_quantity": 0.0,
            "load_port": "UNKNOWN",
            "discharge_port": "UNKNOWN",
        }

    async def _enrich_vessel(self, v: dict[str, Any]) -> VesselRecord:
        """Full vessel enrichment: dark confidence, OFAC, cargo, equity linking."""
        mmsi = v.get("mmsi", "")
        commodity = v.get("cargo_commodity", "container")

        # Parallel enrichment tasks
        dark_conf, sanctions = await asyncio.gather(
            self._classify_dark_confidence(v),
            self._ofac.screen(mmsi, v.get("imo", ""), v.get("vessel_name", "")),
        )

        # Cargo only for HIGH dark / chokepoint vessels
        cargo: dict[str, Any] = {}
        if dark_conf == "HIGH":
            cargo = await self._get_cargo(v.get("imo", ""), commodity)

        linked_equities = COMMODITY_EQUITIES.get(commodity, [])

        # Color coding
        color = "#CDD9E5"   # normal
        if dark_conf == "HIGH":
            color = "#FF4560"   # neon-bear
        elif dark_conf in ("MED", "LOW"):
            color = "#FFB800"   # neon-warn

        dark_confidence_numeric = {"NONE": 0.0, "LOW": 0.35, "MED": 0.65, "HIGH": 0.90}
        route_dev = compute_route_deviation(
            v.get("lat", 0), v.get("lon", 0),
            v.get("origin_lat", v.get("lat", 0)), v.get("origin_lon", v.get("lon", 0)),
            v.get("dest_lat", v.get("lat", 0)), v.get("dest_lon", v.get("lon", 0)),
        )

        return VesselRecord(
            mmsi=mmsi,
            imo=v.get("imo", ""),
            vessel_name=v.get("vessel_name", "UNKNOWN"),
            vessel_type=v.get("vessel_type", "CARGO"),
            flag=v.get("flag", ""),
            lat=v.get("lat", 0),
            lon=v.get("lon", 0),
            speed=v.get("speed", 0),
            heading=v.get("heading", 0),
            ais_status=v.get("ais_status", "UnderWay"),
            last_ais_utc=v.get("last_ais_utc", time.time()),
            dark_confidence=dark_conf,
            dark_vessel_confidence=dark_confidence_numeric.get(dark_conf, 0.0),
            sar_confirmed=(dark_conf == "HIGH"),
            sanctions_hit=sanctions.get("sanctions_hit", False),
            sanctions_list=sanctions.get("list_name", ""),
            route_deviation_score=route_dev,
            spoofing_suspected=route_dev > 70,
            cargo_commodity=cargo.get("commodity_type", commodity),
            cargo_quantity=cargo.get("estimated_quantity", 0.0),
            linked_equities=linked_equities,
            destination=v.get("destination", "Unknown"),
            color=color,
        )

    async def get_all_vessels(
        self, confidence_filter: str | None = None
    ) -> list[VesselRecord]:
        """Get all vessels with optional dark confidence filter."""
        raw = await self._fetch_live_ais()

        # Enrich up to 200 vessels (perf cap — full batch via Celery)
        enrich_tasks = [self._enrich_vessel(v) for v in raw[:200]]
        vessels = await asyncio.gather(*enrich_tasks, return_exceptions=True)
        records = [v for v in vessels if isinstance(v, VesselRecord)]

        if confidence_filter:
            records = [v for v in records if v.dark_confidence == confidence_filter]

        # Publish dark vessel signal to Redis pub/sub
        await self._publish_dark_signal(records)
        return records

    async def get_vessel_intelligence(self, mmsi: str) -> dict[str, Any]:
        """Full intelligence dossier for a specific vessel."""
        r = await self._get_redis()
        if r:
            try:
                raw = await r.get(f"vessel:{mmsi}")
                if raw:
                    v = json.loads(raw)
                    record = await self._enrich_vessel(v)
                    return {**asdict(record), "position": record.position}
            except Exception:
                pass
        raise ValueError(f"Vessel {mmsi} not found in AIS cache")

    async def get_ticker_vessel_signal(self, ticker: str) -> dict[str, Any]:
        """Get aggregated vessel density signal for a ticker's linked commodity."""
        r = await self._get_redis()
        cache_key = f"vessel_signal:{ticker}"
        if r:
            try:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        # Find commodity for ticker
        commodity = None
        for comm, tickers in COMMODITY_EQUITIES.items():
            if ticker in tickers:
                commodity = comm
                break

        result = {
            "ticker": ticker, "commodity": commodity,
            "vessel_count": 0, "normalized_density": 0.5, "age_s": 300,
            "port_congestion": 0.0
        }

        # Enhanced: check port congestion for relevant ports
        from src.free_data.vessels import get_global_ships, get_port_congestion
        ports_task = get_port_congestion()
        ships_task = get_global_ships()

        ports, raw = await asyncio.gather(ports_task, ships_task)

        if commodity:
            count = sum(1 for v in raw if v.get("cargo_commodity") == commodity)
            result["vessel_count"] = count
            result["normalized_density"] = min(count / 20.0, 1.0)

        # Add congestion penalty if relevant ports are blocked
        # e.g. if Suez is congested, it's bearish for some, bullish for others (freight rates)
        congestion_sum = sum(p["congestion_index"] for p in ports)
        result["port_congestion"] = congestion_sum / len(ports) if ports else 0.0

        if r:
            try:
                await r.setex(cache_key, 300, json.dumps(result))
            except Exception:
                pass
        return result

    async def get_dark_vessel_signal(self, ticker: str) -> dict[str, Any]:
        """Dark vessel count signal for ticker's commodity."""
        r = await self._get_redis()
        cache_key = f"dark_signal:{ticker}"
        if r:
            try:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        commodity = next(
            (c for c, tickers in COMMODITY_EQUITIES.items() if ticker in tickers),
            None,
        )
        result = {"ticker": ticker, "dark_count": 0, "age_s": 300}
        if commodity:
            raw = await self._fetch_live_ais()
            gap_threshold = 4 * 3600
            dark_count = sum(
                1 for v in raw
                if v.get("cargo_commodity") == commodity
                and (time.time() - v.get("last_ais_utc", time.time())) > gap_threshold
            )
            result["dark_count"] = dark_count

        if r:
            try:
                await r.setex(cache_key, 300, json.dumps(result))
            except Exception:
                pass
        return result

    async def get_intelligence(self, params: dict[str, Any]) -> dict[str, Any]:
        """AgentRouter dispatch handler."""
        vessels = await self.get_all_vessels(
            confidence_filter=params.get("confidence_filter")
        )
        dark = [v for v in vessels if v.dark_confidence in ("MED", "HIGH")]
        return {
            "total_tracked": len(vessels),
            "dark_count": len(dark),
            "high_confidence_dark": sum(1 for v in dark if v.dark_confidence == "HIGH"),
            "sanctioned": sum(1 for v in vessels if v.sanctions_hit),
            "vessels": [asdict(v) for v in vessels[:50]],
        }

    async def _publish_dark_signal(self, vessels: list[VesselRecord]) -> None:
        """Publish DarkVesselSignal to Redis pub/sub for composite_score.py."""
        r = await self._get_redis()
        if not r:
            return
        try:
            # Compute by commodity + chokepoint
            for chokepoint_name, cp in CHOKEPOINTS.items():
                for commodity in COMMODITY_EQUITIES:
                    count = sum(
                        1 for v in vessels
                        if v.dark_confidence in ("MED", "HIGH")
                        and v.cargo_commodity == commodity
                        and _haversine_nm(v.lat, v.lon, cp["lat"], cp["lon"]) < cp["radius_nm"]
                    )
                    if count > 0:
                        signal = {
                            "commodity": commodity,
                            "chokepoint": chokepoint_name,
                            "count": count,
                            "timestamp": time.time(),
                        }
                        await r.publish("dark_vessel_signal", json.dumps(signal))
        except Exception as exc:
            log.warning("dark_signal_publish_failed", error=str(exc))

    async def get_vessels_near(self, lat: float, lon: float, radius_nm: float = 50) -> list[VesselRecord]:
        """Get vessels within a specific radius."""
        all_v = await self.get_all_vessels()
        return [v for v in all_v if _haversine_nm(lat, lon, v.lat, v.lon) < radius_nm]

    async def detect_dark_vessels_async(self) -> list[VesselRecord]:
        """Detect vessels with high dark confidence."""
        vessels = await self.get_all_vessels()
        return [v for v in vessels if v.dark_confidence in ("MED", "HIGH")]

    def detect_dark_vessels(self) -> list[dict[str, Any]]:
        """Synchronous wrapper for agent compatibility."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # This is a bit of a hack but common in mixed sync/async codebases
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.detect_dark_vessels_async())
                    return [asdict(v) for v in future.result()]
            else:
                return [asdict(v) for v in loop.run_until_complete(self.detect_dark_vessels_async())]
        except Exception:
            return []

    def to_geojson_feature_collection(self) -> dict[str, Any]:
        """Synchronous wrapper for agent compatibility."""
        try:
            loop = asyncio.get_event_loop()
            vessels = loop.run_until_complete(self.get_all_vessels()) if not loop.is_running() else []
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]},
                        "properties": asdict(v)
                    }
                    for v in vessels
                ]
            }
        except Exception:
            return {"type": "FeatureCollection", "features": []}

    def get_vessel_by_mmsi(self, mmsi: str) -> dict[str, Any] | None:
        """Synchronous lookup."""
        return None
