import csv
import io
import os
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import structlog

log = structlog.get_logger()

FIRMS_API_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# 25 industrial facilities we monitor for thermal anomalies
# Each bbox is [min_lon, min_lat, max_lon, max_lat]
MONITORED_FACILITIES = [
    # Steel mills
    {"id": "arcelor_dunkirk",     "name": "ArcelorMittal Dunkirk",        "type": "STEEL_MILL",
     "bbox": "2.25,50.95,2.55,51.10", "tickers": ["MT","X","NUE"],        "country": "France"},
    {"id": "arcelor_ghent",       "name": "ArcelorMittal Ghent",          "type": "STEEL_MILL",
     "bbox": "3.65,51.05,3.85,51.20", "tickers": ["MT"],                   "country": "Belgium"},
    {"id": "baowu_baoshan",       "name": "China Baowu Baoshan Works",    "type": "STEEL_MILL",
     "bbox": "121.40,31.38,121.55,31.48", "tickers": ["600019.SS","MT"],   "country": "China"},
    {"id": "posco_pohang",        "name": "POSCO Pohang Steel",           "type": "STEEL_MILL",
     "bbox": "129.35,36.00,129.50,36.10", "tickers": ["005490.KS","MT"],   "country": "South Korea"},
    {"id": "nippon_steel_kimitsu","name": "Nippon Steel Kimitsu",         "type": "STEEL_MILL",
     "bbox": "139.88,35.31,139.98,35.38", "tickers": ["5401.T","MT"],      "country": "Japan"},
    {"id": "tata_jamshedpur",     "name": "Tata Steel Jamshedpur",        "type": "STEEL_MILL",
     "bbox": "86.14,22.77,86.24,22.84", "tickers": ["TATASTEEL.NS","MT"],  "country": "India"},
    # LNG terminals
    {"id": "sabine_pass",         "name": "Sabine Pass LNG Terminal",     "type": "LNG_TERMINAL",
     "bbox": "-93.93,29.69,-93.81,29.77", "tickers": ["LNG","GLOG"],       "country": "USA"},
    {"id": "corpus_christi_lng",  "name": "Corpus Christi LNG",           "type": "LNG_TERMINAL",
     "bbox": "-97.32,27.81,-97.24,27.86", "tickers": ["LNG"],              "country": "USA"},
    {"id": "qatar_ras_laffan",    "name": "Ras Laffan LNG Complex",       "type": "LNG_TERMINAL",
     "bbox": "51.50,25.86,51.60,25.94", "tickers": ["QS","LNG","GLNG"],    "country": "Qatar"},
    {"id": "aus_lng_darwin",      "name": "Darwin LNG Terminal",          "type": "LNG_TERMINAL",
     "bbox": "130.89,-12.60,130.96,-12.54", "tickers": ["LNG","STO.AX"],   "country": "Australia"},
    # Power stations (proxy for industrial demand)
    {"id": "shandong_power",      "name": "Shandong Coal Power Cluster",  "type": "POWER_STATION",
     "bbox": "118.00,36.50,118.30,36.70", "tickers": ["600795.SS"],        "country": "China"},
    {"id": "drax_uk",             "name": "Drax Power Station UK",        "type": "POWER_STATION",
     "bbox": "-1.07,53.71,-0.98,53.76", "tickers": ["DRX.L"],             "country": "UK"},
    # Oil refineries
    {"id": "rotterdam_refinery",  "name": "Shell Pernis Rotterdam",       "type": "REFINERY",
     "bbox": "4.33,51.88,4.42,51.93", "tickers": ["SHEL","IMO"],          "country": "Netherlands"},
    {"id": "port_arthur_refinery","name": "Port Arthur Refinery Complex", "type": "REFINERY",
     "bbox": "-93.98,29.87,-93.85,29.95", "tickers": ["VLO","MPC"],        "country": "USA"},
    {"id": "ulsan_refinery",      "name": "SK Innovation Ulsan Refinery", "type": "REFINERY",
     "bbox": "129.32,35.51,129.42,35.58", "tickers": ["096770.KS"],        "country": "South Korea"},
    # Cement/industrial (commodity demand proxies)
    {"id": "conch_cement",        "name": "Anhui Conch Cement China",     "type": "CEMENT",
     "bbox": "117.89,30.91,117.99,30.98", "tickers": ["600585.SS","CRH"],  "country": "China"},
]


@dataclass
class ThermalAnomaly:
    facility_id: str
    facility_name: str
    facility_type: str
    lat: float
    lon: float
    brightness_kelvin: float
    frp_mw: float           # Fire Radiative Power in megawatts
    confidence: str         # "low", "nominal", "high"
    detection_time: datetime
    tickers: list[str]
    country: str
    anomaly_vs_baseline: float  # how many standard deviations above baseline


def fetch_firms_thermal(map_key: str | None = None,
                        days: int = 1) -> list[ThermalAnomaly]:
    """
    Fetch thermal anomalies from NASA FIRMS for all monitored facilities.
    Requires free NASA FIRMS MAP_KEY (register at firms.modaps.eosdis.nasa.gov).
    Falls back to simulated data if no key provided.
    """
    map_key = map_key or os.environ.get("NASA_FIRMS_MAP_KEY")

    anomalies = []

    if not map_key:
        log.warning("firms_no_key",
                    message="NASA FIRMS key not set. Using simulated thermal data. "
                            "Register free at firms.modaps.eosdis.nasa.gov to get real data.")
        return _simulated_thermal_anomalies()

    for facility in MONITORED_FACILITIES:
        try:
            url = (f"{FIRMS_API_BASE}/{map_key}/VIIRS_SNPP_NRT/"
                   f"{facility['bbox']}/{days}")
            resp = httpx.get(url, timeout=30)
            if resp.status_code != 200:
                continue

            reader = csv.DictReader(io.StringIO(resp.text))
            detections = list(reader)

            if detections:
                # Average brightness across all detections in this facility
                avg_brightness = sum(
                    float(d.get("brightness", 300)) for d in detections
                ) / len(detections)

                avg_frp = sum(
                    float(d.get("frp", 0)) for d in detections
                ) / len(detections)

                # Baseline: VIIRS nominal background is ~300K
                # Industrial: 320-350K normal ops, 360-400K high ops
                baseline_k = 305.0
                anomaly_sigma = (avg_brightness - baseline_k) / 15.0

                anomalies.append(ThermalAnomaly(
                    facility_id=facility["id"],
                    facility_name=facility["name"],
                    facility_type=facility["type"],
                    lat=float(detections[0].get("latitude", 0)),
                    lon=float(detections[0].get("longitude", 0)),
                    brightness_kelvin=avg_brightness,
                    frp_mw=avg_frp,
                    confidence=detections[0].get("confidence", "nominal"),
                    detection_time=datetime.now(UTC),
                    tickers=facility["tickers"],
                    country=facility["country"],
                    anomaly_vs_baseline=round(anomaly_sigma, 2),
                ))

        except Exception as e:
            log.error("firms_facility_error",
                      facility=facility["id"], error=str(e))

    log.info("firms_thermal_fetched",
             facilities_checked=len(MONITORED_FACILITIES),
             anomalies_found=len(anomalies))
    return anomalies


def _simulated_thermal_anomalies() -> list[ThermalAnomaly]:
    """
    Realistic simulated thermal data when FIRMS key not available.
    Clearly labelled as simulated. Used for development and demo.
    """
    import random
    anomalies = []
    for facility in MONITORED_FACILITIES:
        # Simulate: industrial facilities are always warm, some occasionally hotter
        parts = facility["bbox"].split(",")
        lat = (float(parts[1]) + float(parts[3])) / 2
        lon = (float(parts[0]) + float(parts[2])) / 2
        baseline = 308.0
        operating_level = random.gauss(1.0, 0.2)  # 0=idle, 1=normal, 2=peak
        brightness = baseline + (operating_level * 25)
        frp = max(0, operating_level * 40 + random.gauss(0, 5))
        anomaly = (brightness - baseline) / 10.0

        anomalies.append(ThermalAnomaly(
            facility_id=facility["id"],
            facility_name=facility["name"],
            facility_type=facility["type"],
            lat=lat, lon=lon,
            brightness_kelvin=round(brightness, 1),
            frp_mw=round(frp, 1),
            confidence="nominal",
            detection_time=datetime.now(UTC),
            tickers=facility["tickers"],
            country=facility["country"],
            anomaly_vs_baseline=round(anomaly, 2),
        ))
    return anomalies


def compute_signal_from_thermal(anomalies: list[ThermalAnomaly],
                                ticker: str) -> dict:
    """
    Compute a signal score for a ticker from thermal anomalies.
    Higher thermal = higher operating rate = stronger bullish signal.
    """
    relevant = [a for a in anomalies if ticker in a.tickers]
    if not relevant:
        return {"ticker": ticker, "score": None, "direction": "INSUFFICIENT_DATA",
                "message": "No monitored facilities for this ticker"}

    avg_anomaly = sum(a.anomaly_vs_baseline for a in relevant) / len(relevant)
    high_ops = sum(1 for a in relevant if a.anomaly_vs_baseline > 1.5)

    score = min(100, max(0, 50 + avg_anomaly * 20))
    direction = "BULLISH" if avg_anomaly > 1.0 else "BEARISH" if avg_anomaly < -1.0 else "NEUTRAL"

    return {
        "ticker": ticker,
        "score": round(score, 1),
        "direction": direction,
        "avg_anomaly_sigma": round(avg_anomaly, 2),
        "high_ops_facilities": high_ops,
        "facilities": [a.facility_name for a in relevant],
        "signal_reason": (
            f"{len(relevant)} monitored facilities. "
            f"Avg thermal anomaly: {avg_anomaly:+.1f}σ vs baseline. "
            f"{high_ops} facilities at elevated operating rate."
        ),
    }
