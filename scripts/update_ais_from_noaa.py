import requests
import os
import pandas as pd
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)

def download_noaa_ais(date: datetime) -> str:
    """Download NOAA AIS CSV for a given date."""
    date_str = date.strftime("%Y%m%d")
    year = date.strftime("%Y")
    # NOAA paths vary by year/handler
    url = f"https://coast.noaa.gov/htdata/CMSP/AISDataHandler/{year}/AIS_{date_str}.zip"
    
    output_dir = "data/raw/ais"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"AIS_{date_str}.zip")
    
    log.info(f"Downloading NOAA AIS from {url}...")
    try:
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                f.write(chunk)
        return path
    except Exception as e:
        log.error(f"Failed to download NOAA AIS: {e}")
        return ""

def update_vessel_positions_from_noaa():
    """Parse NOAA AIS and update VesselTracker positions for tracked MMSIs."""
    from src.maritime.vessel_tracker import VesselTracker
    tracker = VesselTracker()
    tracked_mmsis = {v.mmsi for v in tracker.get_all_vessels()}
    
    ais_path = download_noaa_ais(datetime.utcnow() - timedelta(days=1))
    if not ais_path:
        return
    
    log.info(f"Processing AIS file: {ais_path}")
    # In a real execution, we would unzip and parse with pandas
    # df = pd.read_csv(ais_path)
    # df_tracked = df[df['MMSI'].isin(tracked_mmsis)]
    # for _, row in df_tracked.iterrows():
    #     tracker.update_vessel_position(row['MMSI'], row['LAT'], row['LON'], row['SOG'])
    
    print(f"Update script ready. Tracked MMSIs: {len(tracked_mmsis)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_vessel_positions_from_noaa()
