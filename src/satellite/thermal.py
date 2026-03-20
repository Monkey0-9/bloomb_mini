"""
NASA FIRMS Thermal Anomaly Feed — Free with MAP_KEY registration.
Detects industrial heat signatures from steel mills, LNG terminals,
refineries and power plants — the Bloomberg-beating signal layer.

Registration: https://firms.modaps.eosdis.nasa.gov/api/area/
"""
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY", "")
FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Industrial facility clusters and their bounding boxes [West, South, East, North]
# These are the key facilities that matter for commodity signals
INDUSTRIAL_CLUSTERS = {
    "arcelor_dunkirk": {
        "bbox": "2.28,50.98,2.42,51.08",
        "name": "ArcelorMittal Dunkirk (Steel)",
        "tickers": ["MT", "STLD"],
        "commodity": "steel",
    },
    "port_tarragona_refinery": {
        "bbox": "1.12,41.05,1.25,41.15",
        "name": "Tarragona Refinery Cluster",
        "tickers": ["REPSOL.MC", "BP"],
        "commodity": "refined_oil",
    },
    "rotterdam_refinery": {
        "bbox": "4.10,51.85,4.35,51.95",
        "name": "Rotterdam Refinery Row",
        "tickers": ["SHELL", "BP", "VOPAK.AS"],
        "commodity": "oil",
    },
    "port_klang_steel": {
        "bbox": "101.35,2.95,101.55,3.10",
        "name": "Southern Steel / Port Klang Cluster",
        "tickers": ["SOUTHERN.KL"],
        "commodity": "steel",
    },
    "louisiana_lng": {
        "bbox": "-93.40,29.60,-92.90,29.90",
        "name": "Louisiana LNG Terminals (Sabine Pass)",
        "tickers": ["LNG", "CQP"],
        "commodity": "lng",
    },
    "germany_steel": {
        "bbox": "6.90,51.45,7.10,51.55",
        "name": "ThyssenKrupp Duisburg Steelworks",
        "tickers": ["TKAMY", "SALZGITTER.DE"],
        "commodity": "steel",
    },
}

# Baseline fire radiative power (FRP) thresholds for each commodity type
# Values in MW — above this means the facility is running at elevated capacity
BASELINE_FRP = {
    "steel": 120.0,
    "oil": 80.0,
    "refined_oil": 60.0,
    "lng": 50.0,
    "general": 40.0,
}


@dataclass
class ThermalAnomaly:
    facility_key: str
    facility_name: str
    lat: float
    lon: float
    brightness: float       # Kelvin — indicates temperature
    frp: float              # Fire Radiative Power in MW — indicates intensity
    acq_date: str
    acq_time: str
    satellite: str
    confidence: str
    tickers: list[str]
    commodity: str
    signal: str             # BULLISH / BEARISH / NEUTRAL
    signal_reason: str


# Global Free FIRMS URL (No Key Required, 10-min updates)
FIRMS_GLOBAL_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv"

_cached_global_csv = None
_cache_time = 0.0

def _get_global_firms_data() -> list[dict]:
    """Fetch and cache the global 24h FIRMS CSV (No API Key needed)."""
    global _cached_global_csv, _cache_time
    import time
    
    # Cache for 10 minutes
    if _cached_global_csv is not None and (time.time() - _cache_time) < 600:
        return _cached_global_csv

    try:
        resp = httpx.get(FIRMS_GLOBAL_URL, timeout=30)
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            return []
            
        headers = lines[0].strip().split(",")
        records = []
        for line in lines[1:]:
            if line.strip():
                vals = line.strip().split(",")
                if len(vals) >= len(headers):
                    records.append(dict(zip(headers, vals)))
                    
        _cached_global_csv = records
        _cache_time = time.time()
        return records
    except Exception as e:
        import structlog
        structlog.get_logger().error(f"Failed to fetch global FIRMS CSV: {e}")
        return _cached_global_csv if _cached_global_csv else []

def _filter_by_bbox(records: list[dict], bbox_str: str) -> list[dict]:
    """Filter global records by a W,S,E,N bounding box."""
    try:
        w, s, e, n = [float(x) for x in bbox_str.split(",")]
    except ValueError:
        return []

    filtered = []
    for r in records:
        try:
            lat = float(r.get("latitude", 0))
            lon = float(r.get("longitude", 0))
            if s <= lat <= n and w <= lon <= e:
                filtered.append(r)
        except ValueError:
            continue
    return filtered, (w+e)/2.0, (s+n)/2.0


def _determine_signal(frp: float, commodity: str, frp_values: list[float]) -> tuple[str, str]:
    """Determine BULLISH/BEARISH/NEUTRAL based on FRP vs baseline."""
    baseline = BASELINE_FRP.get(commodity, BASELINE_FRP["general"])
    avg_frp = sum(frp_values) / max(len(frp_values), 1)

    if avg_frp > baseline * 1.15:
        return "BULLISH", f"FRP {avg_frp:.0f}MW vs {baseline:.0f}MW baseline (+{((avg_frp/baseline)-1)*100:.0f}%) — elevated production"
    elif avg_frp < baseline * 0.85:
        return "BEARISH", f"FRP {avg_frp:.0f}MW vs {baseline:.0f}MW baseline ({((avg_frp/baseline)-1)*100:.0f}%) — reduced production"
    else:
        return "NEUTRAL", f"FRP {avg_frp:.0f}MW — normal operating range"


def scan_industrial_facilities(day_range: int = 1) -> list[dict]:
    """
    Scan all tracked industrial facilities for thermal anomalies.
    Returns signals based on heat output vs baseline.
    Uses free global 24h CSV from NASA FIRMS.
    """
    results = []
    global_data = _get_global_firms_data()

    for facility_key, meta in INDUSTRIAL_CLUSTERS.items():
        records, center_lon, center_lat = _filter_by_bbox(global_data, meta["bbox"])

        if not records:
            results.append({
                "facility_key": facility_key,
                "facility_name": meta["name"],
                "lat": center_lat,
                "lon": center_lon,
                "tickers": meta["tickers"],
                "commodity": meta["commodity"],
                "anomaly_count": 0,
                "avg_frp_mw": 0,
                "signal": "NEUTRAL",
                "signal_reason": "No thermal anomalies detected in the last 24h",
                "detections": [],
                "as_of": datetime.now(timezone.utc).isoformat(),
            })
            continue

        frp_values = []
        detections = []
        for r in records:
            try:
                frp = float(r.get("frp", 0))
                brightness = float(r.get("bright_ti4") or r.get("brightness", 0))
                frp_values.append(frp)
                detections.append({
                    "lat": float(r.get("latitude", 0)),
                    "lon": float(r.get("longitude", 0)),
                    "brightness_k": brightness,
                    "frp_mw": frp,
                    "date": r.get("acq_date", ""),
                    "time": r.get("acq_time", ""),
                    "satellite": r.get("satellite", "VIIRS"),
                    "confidence": r.get("confidence", "N/A"),
                })
            except (ValueError, KeyError):
                continue

        signal, reason = _determine_signal(
            frp=max(frp_values) if frp_values else 0,
            commodity=meta["commodity"],
            frp_values=frp_values,
        )

        results.append({
            "facility_key": facility_key,
            "facility_name": meta["name"],
            "lat": center_lat,
            "lon": center_lon,
            "tickers": meta["tickers"],
            "commodity": meta["commodity"],
            "anomaly_count": len(detections),
            "avg_frp_mw": round(sum(frp_values) / max(len(frp_values), 1), 1),
            "signal": signal,
            "signal_reason": reason,
            "detections": detections,
            "as_of": datetime.now(timezone.utc).isoformat(),
        })

    return results
