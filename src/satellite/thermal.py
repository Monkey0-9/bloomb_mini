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


def _fetch_firms_csv(bbox: str, day_range: int = 2) -> list[dict]:
    """Fetch FIRMS VIIRS data for a bounding box."""
    if not FIRMS_MAP_KEY:
        return []
    try:
        url = f"{FIRMS_BASE}/{FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/{bbox}/{day_range}"
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            return []
        headers = lines[0].split(",")
        records = []
        for line in lines[1:]:
            if line.strip():
                vals = line.split(",")
                if len(vals) >= len(headers):
                    records.append(dict(zip(headers, vals)))
        return records
    except Exception:
        return []


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


def scan_industrial_facilities(day_range: int = 2) -> list[dict]:
    """
    Scan all tracked industrial facilities for thermal anomalies.
    Returns signals based on heat output vs baseline.
    This is the Bloomberg-beating alpha source.
    """
    results = []

    for facility_key, meta in INDUSTRIAL_CLUSTERS.items():
        records = _fetch_firms_csv(meta["bbox"], day_range=day_range)

        if not records:
            # If no FIRMS key, return placeholder with metadata
            results.append({
                "facility_key": facility_key,
                "facility_name": meta["name"],
                "tickers": meta["tickers"],
                "commodity": meta["commodity"],
                "anomaly_count": 0,
                "avg_frp_mw": None,
                "signal": "INSUFFICIENT_DATA",
                "signal_reason": "NASA FIRMS MAP_KEY not configured — register free at firms.modaps.eosdis.nasa.gov",
                "detections": [],
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
                    "satellite": r.get("satellite", ""),
                    "confidence": r.get("confidence", ""),
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
