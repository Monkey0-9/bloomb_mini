"""
NASA FIRMS VIIRS global thermal anomaly detection.
NO API KEY. Direct public HTTP download.
Downloads ENTIRE PLANET thermal data — not just selected facilities.
Clusters detections spatially to find persistent industrial hotspots.
Reverse geocodes via OpenStreetMap Nominatim to discover facility name.
Finds stock ticker via yfinance Search automatically.
"""
import asyncio
import csv
import io
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
import structlog

log = structlog.get_logger()

FIRMS_24H = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_24h.csv"
FIRMS_7D  = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_7d.csv"

@dataclass
class ThermalCluster:
    cluster_id:     str
    lat:            float
    lon:            float
    country:        str
    facility_name:  str
    facility_type:  str
    hotspot_count:  int
    avg_frp:        float
    max_frp:        float
    baseline_frp:   float
    anomaly_sigma:  float
    signal:         str    # BULLISH / BEARISH / NEUTRAL
    signal_score:   float  # 0-100
    signal_reason:  str
    tickers:        list[str]
    data_quality:   str    # "real" or "simulated"
    detected_at:    str

    @property
    def sector(self) -> str:
        return self.facility_type

_global_hotspots_24h: list[dict] = []
_global_hotspots_7d:  list[dict] = []
_firms_ts: float = 0.0
FIRMS_TTL = 600  # 10 minutes

async def _download_firms(url: str, label: str) -> list[dict]:
    """Download FIRMS CSV from NASA. No key needed."""
    cache_file = Path(f"data/cache/firms_{label}.csv")
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        log.info("firms_downloading", url=url)
        async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        cache_file.write_bytes(resp.content)
        text = resp.text
        log.info("firms_downloaded", label=label, bytes=len(resp.content))
    except Exception as e:
        log.error("firms_download_error", label=label, error=str(e))
        if cache_file.exists():
            log.info("firms_using_cache", label=label)
            text = cache_file.read_text()
        else:
            return []

    rows = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        try:
            rows.append({
                "lat": float(row["latitude"]),
                "lon": float(row["longitude"]),
                "frp": float(row.get("frp", 0)),
                "confidence": row.get("confidence", "nominal"),
                "daynight": row.get("daynight", "D"),
            })
        except (KeyError, ValueError):
            continue
    return rows

def _cluster_points(points: list[dict], grid_km: float = 1.5) -> dict:
    """Cluster lat/lon points into grid cells."""
    grid_deg = grid_km / 111.0
    clusters = defaultdict(list)
    for p in points:
        cell_key = f"{int(p['lat']/grid_deg)}_{int(p['lon']/grid_deg)}"
        clusters[cell_key].append(p)
    return clusters

async def _reverse_geocode(lat: float, lon: float) -> dict:
    """Reverse geocode via OpenStreetMap Nominatim. Free, no key. 1 req/sec."""
    try:
        await asyncio.sleep(1.1)  # Respect Nominatim rate limit (1 req/sec)
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lon, "format": "json", "zoom": 16},
                headers={"User-Agent": "SatTrade/2.0 research@sattrade.io"},
            )
        if resp.status_code == 429:
            log.warning("nominatim_rate_limited", status=429)
            return {
                "name":    f"Industrial site {lat:.3f}°N {lon:.3f}°E",
                "type":    "industrial",
                "country": "Unknown",
            }
        data = resp.json()
        addr = data.get("address", {})
        name = (
            data.get("name") or
            addr.get("industrial") or
            addr.get("amenity") or
            addr.get("building") or
            f"Industrial site {lat:.3f}°N {lon:.3f}°E"
        )
        return {
            "name":    name,
            "type":    data.get("type", "industrial"),
            "country": addr.get("country", ""),
        }
    except Exception:
        return {
            "name":    f"Industrial site {lat:.3f}°N {lon:.3f}°E",
            "type":    "industrial",
            "country": "",
        }

def _find_tickers(facility_name: str, facility_type: str) -> list[str]:

    """Find stock tickers for a facility using yfinance Search."""
    import yfinance as yf

    # Sector ETF fallbacks by facility type keyword
    TYPE_ETFS = {
        "steel":      ["MT", "X", "NUE", "STLD"],
        "port":       ["AMKBY", "ZIM", "1919.HK"],
        "harbour":    ["AMKBY", "ZIM"],
        "refinery":   ["VLO", "MPC", "PSX"],
        "petroleum":  ["XOM", "CVX", "SHEL"],
        "oil":        ["XOM", "CVX", "BP"],
        "gas":        ["LNG", "GLNG"],
        "lng":        ["LNG", "GLOG"],
        "power":      ["XLU", "NEE"],
        "coal":       ["BTU", "ARCH"],
        "cement":     ["CRH", "EXP"],
        "aluminum":   ["AA", "RIO"],
        "copper":     ["FCX", "SCCO"],
        "mine":       ["BHP", "RIO", "VALE"],
        "smelter":    ["AA", "FCX", "MT"],
        "industrial": ["XLI", "CAT", "GE"],
    }

    # Try yfinance Search first
    tickers = []
    if len(facility_name) > 8 and "industrial site" not in facility_name.lower():
        try:
            results = yf.Search(facility_name, news_count=0, max_results=3)
            quotes = getattr(results, "quotes", [])
            for q in quotes[:2]:
                sym = q.get("symbol", "")
                if sym and len(sym) <= 12 and "." not in sym or sym.count(".") == 1:
                    tickers.append(sym)
        except Exception:
            pass

    # Fall back to type-based ETFs
    if not tickers:
        type_lower = facility_type.lower()
        for keyword, etfs in TYPE_ETFS.items():
            if keyword in type_lower or keyword in facility_name.lower():
                tickers = etfs[:2]
                break

    # Last resort: broad industrial
    if not tickers:
        tickers = ["XLI", "SPY"]

    return tickers[:3]

async def get_global_thermal(top_n: int = 150) -> list[ThermalCluster]:
    """
    Get top N industrial thermal anomalies from the entire planet.
    Fully dynamic — no hardcoded facility list.
    """
    global _global_hotspots_24h, _global_hotspots_7d, _firms_ts

    now = time.time()
    if _global_hotspots_24h and (now - _firms_ts) < FIRMS_TTL:
        return await _build_clusters(_global_hotspots_24h, _global_hotspots_7d, top_n)

    _global_hotspots_24h = await _download_firms(FIRMS_24H, "24h")
    _global_hotspots_7d  = await _download_firms(FIRMS_7D,  "7d")
    _firms_ts = now

    return await _build_clusters(_global_hotspots_24h, _global_hotspots_7d, top_n)

async def _build_clusters(points_24h: list[dict], points_7d: list[dict],
                    top_n: int) -> list[ThermalCluster]:
    clusters_24h = _cluster_points(points_24h, grid_km=1.5)
    clusters_7d  = _cluster_points(points_7d,  grid_km=1.5)

    significant = []
    geocode_cache = {}
    geocode_count = 0
    max_geocodes = 20 # Cap geocoding to prevent TLE or extreme latency

    # Filter and sort by sigma before geocoding
    candidate_clusters = []
    for cell_key, detections in clusters_24h.items():
        if len(detections) < 2:
            continue
        avg_frp = sum(d["frp"] for d in detections) / len(detections)
        if avg_frp < 15.0:
            continue
        baseline_detections = clusters_7d.get(cell_key, detections)
        baseline_frp = sum(d["frp"] for d in baseline_detections) / len(baseline_detections)
        baseline_frp = max(baseline_frp, 1.0)
        sigma = (avg_frp - baseline_frp) / (baseline_frp * 0.25)
        if abs(sigma) < 0.5:
            continue

        candidate_clusters.append({
            "cell_key": cell_key,
            "detections": detections,
            "avg_frp": avg_frp,
            "sigma": sigma,
            "baseline_frp": baseline_frp
        })

    candidate_clusters.sort(key=lambda x: abs(x["sigma"]), reverse=True)

    for cand in candidate_clusters:
        detections = cand["detections"]
        cell_key = cand["cell_key"]
        avg_frp = cand["avg_frp"]
        sigma = cand["sigma"]
        baseline_frp = cand["baseline_frp"]

        lat = sum(d["lat"] for d in detections) / len(detections)
        lon = sum(d["lon"] for d in detections) / len(detections)
        max_frp = max(d["frp"] for d in detections)

        # Reverse geocode
        geo_key = f"{round(lat,2)}_{round(lon,2)}"
        if geo_key not in geocode_cache and geocode_count < max_geocodes:
            geocode_cache[geo_key] = await _reverse_geocode(lat, lon)
            geocode_count += 1

        facility = geocode_cache.get(geo_key, {
            "name": f"Industrial site {lat:.3f}°N {lon:.3f}°E",
            "type": "industrial",
            "country": "Unknown"
        })

        # Find tickers
        tickers = _find_tickers(facility["name"], facility["type"])

        score = min(100.0, max(0.0, 50.0 + sigma * 20.0))
        direction = "BULLISH" if sigma > 0.75 else "BEARISH" if sigma < -0.75 else "NEUTRAL"
        reason = (
            f"{facility['name']}: {len(detections)} VIIRS detections. "
            f"FRP {avg_frp:.0f}MW ({sigma:+.1f}σ vs 7-day avg {baseline_frp:.0f}MW). "
            f"{'Elevated production — bullish signal.' if sigma > 0.75 else 'Reduced activity — bearish.' if sigma < -0.75 else 'Normal operating conditions.'}"
        )

        significant.append(ThermalCluster(
            cluster_id    = cell_key,
            lat           = round(lat, 4),
            lon           = round(lon, 4),
            country       = facility["country"],
            facility_name = facility["name"],
            facility_type = facility["type"],
            hotspot_count = len(detections),
            avg_frp       = round(avg_frp, 1),
            max_frp       = round(max_frp, 1),
            baseline_frp  = round(baseline_frp, 1),
            anomaly_sigma = round(sigma, 2),
            signal        = direction,
            signal_score  = round(score, 1),
            signal_reason = reason,
            tickers       = tickers,
            data_quality  = "real_nasa_firms",
            detected_at   = datetime.now(UTC).isoformat(),
        ))

    # Sort by absolute anomaly magnitude — most significant first
    significant.sort(key=lambda x: abs(x.anomaly_sigma), reverse=True)
    return significant[:top_n]
