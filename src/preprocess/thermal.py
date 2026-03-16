"""
NASA FIRMS Thermal Preprocessing Pipeline.
Direct NO-KEY parsing of VIIRS 375m and MODIS active fire CSVs.
Extracts industrial heat patterns using Fire Radiative Power (FRP).
"""

import csv
import httpx
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

# NASA FIRMS Public NO-KEY Rolling CSV Endpoints
FIRMS_CSV_VIIRS_SNPP = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_NPP_VIIRS_C2_Global_24h.csv"
FIRMS_CSV_MODIS = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv"

@dataclass
class ThermalPreprocessingResult:
    """Result of global thermal scan."""
    tile_id: str
    success: bool
    total_anomalies: int = 0
    max_frp: float = 0.0
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0

class ThermalPipeline:
    """
    Parses FIRMS NO-KEY global CSVs to find active industrial heat spikes.
    No rasterio overhead. Pure scalable tabular ingest.
    """

    def __init__(self, output_dir: Path = Path("data/processed/thermal")):
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def process(self, tile_id: str = "GLOBAL", **kwargs) -> ThermalPreprocessingResult:
        import time
        start = time.time()
        result = ThermalPreprocessingResult(tile_id=tile_id, success=False)

        try:
            logger.info("Fetching FIRMS VIIRS 24h CSV...")
            resp = httpx.get(FIRMS_CSV_VIIRS_SNPP, timeout=60)
            resp.raise_for_status()
            
            lines = resp.text.splitlines()
            result.steps_completed.append("csv_download")
            
            reader = csv.DictReader(lines)
            anomalies = []
            
            # Columns: latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
            for row in reader:
                try:
                    frp = float(row['frp'])
                    if frp > 10.0: # Filter for significant industrial/fire heat
                        anomalies.append({
                            "lat": float(row['latitude']),
                            "lon": float(row['longitude']),
                            "frp": frp,
                            "confidence": row['confidence']
                        })
                except (KeyError, ValueError):
                    pass
            
            result.steps_completed.append("csv_parsed")

            # Save extracted anomalies to JSON for the Signal Engine
            import json
            out_file = self._output_dir / f"firms_anomalies_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
            with open(out_file, "w") as f:
                json.dump({"anomalies": anomalies}, f)

            result.total_anomalies = len(anomalies)
            result.max_frp = max([a["frp"] for a in anomalies]) if anomalies else 0.0
            result.success = True
            logger.info(f"Thermal parsing complete. Found {result.total_anomalies} anomalies. Max FRP: {result.max_frp}")

        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Thermal pipeline failed: {e}")

        result.processing_time_seconds = time.time() - start
        return result

if __name__ == "__main__":
    pipeline = ThermalPipeline()
    res = pipeline.process()
    print("FIRMS Ingest Result:", res)
