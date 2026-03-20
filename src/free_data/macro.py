"""
Free macroeconomic data layer.
Sources: 
- FRED (via CSV direct download)
- World Bank (Open API)
- ECB (SDMX-JSON)
"""
import httpx
import pandas as pd
import io
import structlog
from datetime import datetime, timedelta

log = structlog.get_logger(__name__)

# Primary FRED series IDs (no key needed for direct CSV download)
FRED_SERIES = {
    "GDP": "GDP",
    "CPI": "CPIAUCSL",
    "UNRATE": "UNRATE",
    "FEDFUNDS": "FEDFUNDS",
    "RETAIL": "RSXFS",
    "INDUSTRIAL": "INDPRO"
}

def get_fred_data(series_id: str) -> pd.DataFrame:
    """Fetch FRED data via direct CSV download."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        df["DATE"] = pd.to_datetime(df["DATE"])
        return df
    except Exception as e:
        log.error("fred_fetch_failed", series_id=series_id, error=str(e))
        return pd.DataFrame()

def get_world_bank_indicator(indicator: str, country: str = "USA") -> list[dict]:
    """Fetch World Bank data using their Open API."""
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&per_page=100"
    try:
        resp = httpx.get(url, timeout=15)
        data = resp.json()
        if len(data) > 1:
            return [
                {
                    "date": item["date"],
                    "value": item["value"],
                    "indicator": item["indicator"]["value"]
                }
                for item in data[1] if item["value"] is not None
            ]
        return []
    except Exception as e:
        log.error("world_bank_fetch_failed", indicator=indicator, error=str(e))
        return []

def get_macro_summary() -> dict:
    """Consolidate high-level macro indicators."""
    summary = {}
    # Fetch key FRED series
    for name, sid in FRED_SERIES.items():
        df = get_fred_data(sid)
        if not df.empty:
            last_val = df.iloc[-1]
            prev_val = df.iloc[-2] if len(df) > 1 else last_val
            summary[name] = {
                "latest": float(last_val.iloc[1]),
                "date": last_val.iloc[0].strftime("%Y-%m-%d"),
                "change": float(last_val.iloc[1] - prev_val.iloc[1])
            }
    return summary
