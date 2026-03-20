import httpx
import csv
import io
import structlog
from dataclasses import dataclass
from datetime import datetime, timezone

log = structlog.get_logger()

# NASA FIRMS C2 Global (Suomi-NPP VIIRS) 24h CSV
FIRMS_CSV_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_24h.csv"

# Sample industrial facilities (BBOX: lon_min, lat_min, lon_max, lat_max)
FACILITIES = [
    {"name": "Suez Canal", "bbox": [32.0, 29.5, 32.5, 31.5]},
    {"name": "Rotterdam Port", "bbox": [3.8, 51.8, 4.5, 52.0]},
    {"name": "Shanghai Waigaoqiao", "bbox": [121.5, 31.2, 121.7, 31.4]},
]

@dataclass
class ThermalAnomaly:
    lat: float
    lon: float
    brightness: float
    frp: float
    confidence: str
    facility: str | None = None

def fetch_thermal_data() -> list[ThermalAnomaly]:
    """
    Fetch 24h thermal anomaly data from NASA FIRMS.
    No keys required for this public CSV endpoint.
    """
    try:
        resp = httpx.get(FIRMS_CSV_URL, timeout=30)
        if resp.status_code != 200:
            return []
        
        reader = csv.DictReader(io.StringIO(resp.text))
        anomalies = []
        for row in reader:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            
            # Basic geographic filter for demo facilities
            facility_match = None
            for f in FACILITIES:
                b = f["bbox"]
                if b[0] <= lon <= b[2] and b[1] <= lat <= b[3]:
                    facility_match = f["name"]
                    break
            
            anomalies.append(ThermalAnomaly(
                lat=lat,
                lon=lon,
                brightness=float(row["bright_ti4"]),
                frp=float(row["frp"]),
                confidence=row["confidence"],
                facility=facility_match
            ))
            # Limit count for demo
            if len(anomalies) > 1000:
                break
        return anomalies
    except Exception as e:
        log.error("fetch_thermal_failed", error=str(e))
        return []

if __name__ == "__main__":
    data = fetch_thermal_data()
    print(f"Fetched {len(data)} thermal anomalies.")
    facility_hits = [a for a in data if a.facility]
    print(f"Industrial hits: {len(facility_hits)}")
