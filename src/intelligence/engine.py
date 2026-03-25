"""
Global Intelligence Engine — The Brain of SatTrade.
Discovers signals from global open data with ZERO hardcoded locations.
"""
from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
import numpy as np

logger = logging.getLogger(__name__)

FIRMS_GLOBAL_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_24h.csv"
FIRMS_7D_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_7d.csv"

@dataclass
class ThermalSignal:
    lat: float
    lon: float
    facility_name: str
    anomaly_sigma: float
    signal: str
    tickers: list[str]
    frp_mw: float
    confidence: float
    timestamp: datetime = datetime.now(timezone.utc)


class GlobalIntelligenceEngine:
    """
    Processes NASA FIRMS data to detect industrial anomalies globally.
    """
    def __init__(self):
        self._client = httpx.Client(timeout=30)
        self._nominatim_url = "https://nominatim.openstreetmap.org/reverse"

    def _reverse_geocode(self, lat: float, lon: float) -> str:
        """Find facility name using free OSM Nominatim."""
        try:
            params = {"lat": lat, "lon": lon, "format": "json", "zoom": 16}
            headers = {"User-Agent": "SatTrade/2.0 Research"}
            resp = self._client.get(self._nominatim_url, params=params, headers=headers)
            data = resp.json()
            addr = data.get("address", {})
            return (data.get("name") or 
                    addr.get("industrial") or 
                    addr.get("amenity") or 
                    addr.get("building") or 
                    f"Site @ {lat:.2f}, {lon:.2f}")
        except Exception:
            return f"Industrial Site @ {lat:.2f}, {lon:.2f}"

    def _discover_tickers(self, name: str) -> list[str]:
        """Auto-discover tickers from company name via yfinance search."""
        import yfinance as yf
        try:
            search = yf.Search(name, max_results=2)
            return [q["symbol"] for q in search.quotes if "symbol" in q][:2]
        except Exception:
            return []

    async def get_thermal_signals(self) -> list[ThermalSignal]:
        """Download and process FIRMS data for industrial anomalies."""
        try:
            resp_24h = self._client.get(FIRMS_GLOBAL_URL)
            resp_7d = self._client.get(FIRMS_7D_URL)
            
            rows_24h = list(csv.DictReader(io.StringIO(resp_24h.text)))
            rows_7d = list(csv.DictReader(io.StringIO(resp_7d.text)))
            
            # Step 1: Spatial clustering (1km cells)
            def cluster(rows):
                grid = {}
                for r in rows:
                    key = (round(float(r["latitude"]), 2), round(float(r["longitude"]), 2))
                    grid.setdefault(key, []).append(float(r["frp"]))
                return grid

            grid_24h = cluster(rows_24h)
            grid_7d = cluster(rows_7d)
            
            signals = []
            for (lat, lon), frps in grid_24h.items():
                avg_frp = np.mean(frps)
                if avg_frp < 15.0:
                    continue
                
                baseline_frps = grid_7d.get((lat, lon), frps)
                baseline_avg = np.mean(baseline_frps)
                sigma = (avg_frp - baseline_avg) / (np.std(baseline_frps) + 1.0)
                
                if abs(sigma) > 1.5:
                    facility = self._reverse_geocode(lat, lon)
                    tickers = self._discover_tickers(facility)
                    direction = "BULLISH" if sigma > 0 else "BEARISH"
                    
                    signals.append(ThermalSignal(
                        lat=lat, lon=lon, facility_name=facility,
                        anomaly_sigma=round(float(sigma), 2),
                        signal=direction, tickers=tickers,
                        frp_mw=round(float(avg_frp), 2),
                        confidence=float(np.mean([float(r.get("confidence", 0)) for r in rows_24h if round(float(r["latitude"]), 2) == lat]))
                    ))
            
            return sorted(signals, key=lambda x: abs(x.anomaly_sigma), reverse=True)[:50]
        except Exception as e:
            logger.error(f"Intelligence engine error: {e}")
            return []
