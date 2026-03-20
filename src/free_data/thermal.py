"""
Industrial thermal anomaly detection using NASA FIRMS public CSV files.
NO API KEY. NO REGISTRATION. Direct public HTTP download.
"""

import csv
import io
import time
import httpx
import structlog
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = structlog.get_logger()

FIRMS_URLS = {
    "viirs_24h": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_24h.csv",
    "viirs_7d":  "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_7d.csv",
    "modis_24h": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/Global/MODIS_C6_1_Global_24h.csv",
    "noaa20_24h":"https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/Global/J1_VIIRS_C2_Global_24h.csv",
}

FACILITIES = [
    {
        "id": "arcelor_dunkirk",
        "name": "ArcelorMittal Dunkirk Integrated Steel Plant",
        "type": "STEEL_MILL",
        "country": "France",
        "bbox": (2.20, 50.92, 2.60, 51.12),
        "center": (51.04, 2.38),
        "tickers": ["MT", "X", "NUE", "STLD"],
        "baseline_frp": 35.0,
        "capacity_mt_year": 6_500_000,
    },
    {
        "id": "arcelor_ghent",
        "name": "ArcelorMittal Ghent Steel Plant",
        "type": "STEEL_MILL",
        "country": "Belgium",
        "bbox": (3.60, 51.02, 3.90, 51.22),
        "center": (51.12, 3.75),
        "tickers": ["MT", "X"],
        "baseline_frp": 28.0,
        "capacity_mt_year": 5_000_000,
    },
    {
        "id": "arcelor_taranto",
        "name": "Acciaierie d'Italia Taranto",
        "type": "STEEL_MILL",
        "country": "Italy",
        "bbox": (17.15, 40.44, 17.35, 40.54),
        "center": (40.49, 17.25),
        "tickers": ["MT", "ENEL.MI"],
        "baseline_frp": 22.0,
        "capacity_mt_year": 3_500_000,
    },
    {
        "id": "baowu_baoshan",
        "name": "China Baowu Steel Baoshan Works",
        "type": "STEEL_MILL",
        "country": "China",
        "bbox": (121.38, 31.36, 121.58, 31.50),
        "center": (31.43, 121.48),
        "tickers": ["600019.SS", "MT", "VALE"],
        "baseline_frp": 85.0,
        "capacity_mt_year": 20_000_000,
    },
    {
        "id": "posco_pohang",
        "name": "POSCO Pohang Steel Works",
        "type": "STEEL_MILL",
        "country": "South Korea",
        "bbox": (129.33, 35.98, 129.52, 36.10),
        "center": (36.04, 129.43),
        "tickers": ["005490.KS", "MT", "BHP"],
        "baseline_frp": 92.0,
        "capacity_mt_year": 21_000_000,
    },
    {
        "id": "nippon_kimitsu",
        "name": "Nippon Steel Kimitsu Works",
        "type": "STEEL_MILL",
        "country": "Japan",
        "bbox": (139.86, 35.30, 139.98, 35.40),
        "center": (35.35, 139.92),
        "tickers": ["5401.T", "MT"],
        "baseline_frp": 55.0,
        "capacity_mt_year": 8_000_000,
    },
    {
        "id": "tata_jamshedpur",
        "name": "Tata Steel Jamshedpur Works",
        "type": "STEEL_MILL",
        "country": "India",
        "bbox": (86.10, 22.74, 86.26, 22.86),
        "center": (22.80, 86.18),
        "tickers": ["TATASTEEL.NS", "MT"],
        "baseline_frp": 42.0,
        "capacity_mt_year": 10_000_000,
    },
    {
        "id": "sabine_pass",
        "name": "Sabine Pass LNG Terminal",
        "type": "LNG_TERMINAL",
        "country": "USA",
        "bbox": (-93.95, 29.67, -93.79, 29.79),
        "center": (29.73, -93.87),
        "tickers": ["LNG", "GLOG", "GLNG", "FLEX"],
        "baseline_frp": 45.0,
        "capacity_mtpa": 30.0,
    },
    {
        "id": "corpus_christi",
        "name": "Corpus Christi LNG Terminal",
        "type": "LNG_TERMINAL",
        "country": "USA",
        "bbox": (-97.35, 27.79, -97.22, 27.88),
        "center": (27.83, -97.29),
        "tickers": ["LNG"],
        "baseline_frp": 30.0,
        "capacity_mtpa": 15.0,
    },
    {
        "id": "freeport_lng",
        "name": "Freeport LNG Terminal Train 1-3",
        "type": "LNG_TERMINAL",
        "country": "USA",
        "bbox": (-95.37, 28.94, -95.28, 29.00),
        "center": (28.97, -95.32),
        "tickers": ["FLEX", "LNG"],
        "baseline_frp": 28.0,
        "capacity_mtpa": 15.0,
    },
    {
        "id": "ras_laffan",
        "name": "Ras Laffan LNG Complex",
        "type": "LNG_TERMINAL",
        "country": "Qatar",
        "bbox": (51.47, 25.84, 51.63, 25.96),
        "center": (25.90, 51.55),
        "tickers": ["LNG", "GLNG", "FLEX"],
        "baseline_frp": 120.0,
        "capacity_mtpa": 77.0,
    },
    {
        "id": "darwin_lng",
        "name": "Darwin LNG Terminal",
        "type": "LNG_TERMINAL",
        "country": "Australia",
        "bbox": (130.87, -12.63, 130.97, -12.52),
        "center": (-12.58, 130.92),
        "tickers": ["STO.AX", "COP", "LNG"],
        "baseline_frp": 25.0,
        "capacity_mtpa": 3.7,
    },
    {
        "id": "shell_pernis",
        "name": "Shell Pernis Refinery Rotterdam",
        "type": "REFINERY",
        "country": "Netherlands",
        "bbox": (4.30, 51.86, 4.44, 51.94),
        "center": (51.90, 4.37),
        "tickers": ["SHEL", "IMO"],
        "baseline_frp": 60.0,
        "capacity_bpd": 404_000,
    },
    {
        "id": "port_arthur",
        "name": "Port Arthur Refinery Complex TX",
        "type": "REFINERY",
        "country": "USA",
        "bbox": (-93.98, 29.85, -93.84, 29.96),
        "center": (29.90, -93.91),
        "tickers": ["VLO", "MPC", "PSX"],
        "baseline_frp": 75.0,
        "capacity_bpd": 850_000,
    },
    {
        "id": "ulsan_refinery",
        "name": "SK Energy Ulsan Refinery",
        "type": "REFINERY",
        "country": "South Korea",
        "bbox": (129.30, 35.48, 129.45, 35.60),
        "center": (35.54, 129.38),
        "tickers": ["096770.KS"],
        "baseline_frp": 55.0,
        "capacity_bpd": 840_000,
    },
    {
        "id": "drax_uk",
        "name": "Drax Power Station",
        "type": "POWER_STATION",
        "country": "UK",
        "bbox": (-1.08, 53.70, -0.97, 53.77),
        "center": (53.74, -1.03),
        "tickers": ["DRX.L"],
        "baseline_frp": 40.0,
        "capacity_mw": 3_906,
    },
    {
        "id": "shandong_coal",
        "name": "Shandong Coal Power Cluster",
        "type": "POWER_STATION",
        "country": "China",
        "bbox": (117.95, 36.48, 118.35, 36.72),
        "center": (36.60, 118.15),
        "tickers": ["600795.SS", "600027.SS"],
        "baseline_frp": 95.0,
        "capacity_mw": 8_000,
    },
    {
        "id": "conch_cement",
        "name": "Anhui Conch Cement Tongling",
        "type": "CEMENT",
        "country": "China",
        "bbox": (117.85, 30.88, 118.02, 31.00),
        "center": (30.94, 117.93),
        "tickers": ["600585.SS", "CRH"],
        "baseline_frp": 35.0,
        "capacity_mt_year": 12_000_000,
    },
    {
        "id": "alba_bahrain",
        "name": "Aluminium Bahrain (ALBA) Smelter",
        "type": "SMELTER",
        "country": "Bahrain",
        "bbox": (50.58, 26.12, 50.72, 26.22),
        "center": (26.17, 50.65),
        "tickers": ["ALBA.BH", "AA", "RIO"],
        "baseline_frp": 65.0,
        "capacity_mt_year": 1_540_000,
    },
    {
        "id": "codelco_chuquicamata",
        "name": "Codelco Chuquicamata Copper Smelter",
        "type": "SMELTER",
        "country": "Chile",
        "bbox": (-68.97, -22.34, -68.87, -22.27),
        "center": (-22.31, -68.92),
        "tickers": ["FREEPORT", "SCCO", "BHP", "RIO"],
        "baseline_frp": 45.0,
        "capacity_kt_year": 400,
    },
]

@dataclass
class ThermalHotspot:
    lat:         float
    lon:         float
    brightness:  float
    frp:         float
    confidence:  str
    sat:         str
    acq_datetime: datetime
    daynight:    str

@dataclass
class FacilityThermal:
    facility_id:   str
    facility_name: str
    facility_type: str
    country:       str
    lat:           float
    lon:           float
    tickers:       list[str]
    hotspots:      list[ThermalHotspot]
    avg_frp:       float
    max_frp:       float
    baseline_frp:  float
    anomaly_sigma: float
    signal_score:  float
    signal_direction: str
    signal_reason: str
    data_quality:  str
    checked_at:    datetime = field(default_factory=lambda: datetime.now(timezone.utc))

_global_hotspots: list[ThermalHotspot] | None = None
_hotspots_ts: float = 0.0
FIRMS_CACHE_TTL = 600

def _fetch_global_firms(period: str = "viirs_24h") -> list[ThermalHotspot]:
    global _global_hotspots, _hotspots_ts

    now = time.time()
    if _global_hotspots is not None and (now - _hotspots_ts) < FIRMS_CACHE_TTL:
        return _global_hotspots

    url = FIRMS_URLS[period]
    cache_file = Path(f"data/cache/firms_{period}.csv")
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        log.info("firms_downloading", url=url)
        resp = httpx.get(url, timeout=60, follow_redirects=True)
        resp.raise_for_status()
        cache_file.write_bytes(resp.content)
        text = resp.text
        log.info("firms_downloaded", bytes=len(resp.content))
    except Exception as e:
        log.error("firms_download_failed", error=str(e))
        if cache_file.exists():
            log.info("firms_using_cached_file")
            text = cache_file.read_text()
        else:
            return []

    hotspots = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        try:
            hotspots.append(ThermalHotspot(
                lat        = float(row.get("latitude",  0)),
                lon        = float(row.get("longitude", 0)),
                brightness = float(row.get("bright_ti4", row.get("brightness", 300))),
                frp        = float(row.get("frp", 0)),
                confidence = str(row.get("confidence", "nominal")),
                sat        = str(row.get("satellite", "SNPP")),
                acq_datetime = datetime.now(timezone.utc),
                daynight   = str(row.get("daynight", "D")),
            ))
        except (ValueError, KeyError):
            continue

    _global_hotspots = hotspots
    _hotspots_ts = now
    log.info("firms_parsed", hotspot_count=len(hotspots))
    return hotspots

def _point_in_bbox(lat: float, lon: float,
                   bbox: tuple[float,float,float,float]) -> bool:
    return (bbox[0] <= lon <= bbox[2]) and (bbox[1] <= lat <= bbox[3])

def get_all_facility_thermal() -> list[FacilityThermal]:
    hotspots = _fetch_global_firms("viirs_24h")
    results = []

    for fac in FACILITIES:
        facility_hotspots = [
            h for h in hotspots
            if _point_in_bbox(h.lat, h.lon, fac["bbox"])
        ]

        baseline = fac["baseline_frp"]

        if facility_hotspots:
            frp_values = [h.frp for h in facility_hotspots]
            avg_frp = sum(frp_values) / len(frp_values)
            max_frp = max(frp_values)
            sigma = (avg_frp - baseline) / (baseline * 0.20) if baseline > 0 else 0.0
            score = min(100.0, max(0.0, 50.0 + sigma * 18.0))
            direction = "BULLISH" if sigma > 0.75 else "BEARISH" if sigma < -0.75 else "NEUTRAL"
            reason = (
                f"{fac['name']}: {len(facility_hotspots)} VIIRS hotspots detected. "
                f"Avg FRP: {avg_frp:.1f}MW ({sigma:+.1f}σ vs {baseline:.0f}MW baseline). "
                f"{'Elevated production rate.' if sigma > 0.75 else 'Normal operating conditions.' if abs(sigma) <= 0.75 else 'Reduced activity.'}"
            )
            quality = "real_firms"
        else:
            avg_frp = 0.0
            max_frp = 0.0
            sigma = -2.0
            score = max(0.0, 50.0 + sigma * 18.0)
            direction = "BEARISH"
            reason = (
                f"{fac['name']}: NO thermal detections in 24h FIRMS data. "
                f"Expected baseline: {baseline:.0f}MW. "
                f"Possible: night operation, cloud cover, or reduced production."
            )
            quality = "no_detections"

        results.append(FacilityThermal(
            facility_id    = fac["id"],
            facility_name  = fac["name"],
            facility_type  = fac["type"],
            country        = fac["country"],
            lat            = fac["center"][0],
            lon            = fac["center"][1],
            tickers        = fac["tickers"],
            hotspots       = facility_hotspots,
            avg_frp        = round(avg_frp, 1),
            max_frp        = round(max_frp, 1),
            baseline_frp   = baseline,
            anomaly_sigma  = round(sigma, 2),
            signal_score   = round(score, 1),
            signal_direction = direction,
            signal_reason  = reason,
            data_quality   = quality,
        ))

    return results

def compute_signal_from_ticker(anomalies: list[FacilityThermal], ticker: str) -> dict:
    relevant = [a for a in anomalies if ticker in a.tickers]
    if not relevant:
        return {"ticker": ticker, "score": None, "direction": "INSUFFICIENT_DATA",
                "message": "No monitored facilities for this ticker"}
    
    avg_score = sum(a.signal_score for a in relevant) / len(relevant)
    avg_sigma = sum(a.anomaly_sigma for a in relevant) / len(relevant)
    
    return {
        "ticker": ticker,
        "score": round(avg_score, 1),
        "direction": "BULLISH" if avg_score > 60 else "BEARISH" if avg_score < 40 else "NEUTRAL",
        "avg_anomaly_sigma": round(avg_sigma, 2),
        "facilities": [a.facility_name for a in relevant],
        "message": f"{len(relevant)} monitored facilities. Avg thermal anomaly: {avg_sigma:+.1f}σ vs baseline."
    }
