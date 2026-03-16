"""
FRED Macro Economic Data — Free registration at fred.stlouisfed.org.
Provides US/global macro indicators for economic overlay on signals.
"""
import os
from datetime import datetime, timezone

import httpx

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Key macro series relevant to supply chain and commodities
MACRO_SERIES = {
    "US_CPI": "CPIAUCSL",           # Consumer Price Index
    "US_PPI": "PPIACO",             # Producer Price Index (All Commodities)
    "BALTIC_DRY": "BDIY",           # Baltic Dry Index (if available via FRED)
    "OIL_WTI": "DCOILWTICO",        # WTI Crude Oil
    "NATURAL_GAS": "DHHNGSP",       # Henry Hub Natural Gas
    "STEEL_HOT_ROLL": "PCU3312013312014",  # Steel hot-rolled price index
    "USD_INDEX": "DTWEXBGS",        # USD trade-weighted index
    "US_10Y": "DGS10",              # 10-year Treasury yield
    "FED_FUNDS": "FEDFUNDS",        # Fed Funds Rate
    "ISM_PMI": "MANEMP",            # Manufacturing employment as PMI proxy
}


def _get_fred_series(series_id: str, limit: int = 30) -> list[dict]:
    """Fetch FRED series observations."""
    if not FRED_API_KEY:
        return [{"date": "N/A", "value": "API_KEY_REQUIRED"}]
    try:
        resp = httpx.get(
            FRED_BASE,
            params={
                "series_id": series_id,
                "api_key": FRED_API_KEY,
                "file_type": "json",
                "sort_order": "desc",
                "limit": limit,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {"date": obs["date"], "value": obs["value"]}
            for obs in data.get("observations", [])
            if obs.get("value") != "."
        ]
    except Exception as e:
        return [{"date": "ERROR", "value": str(e)}]


def get_macro_dashboard() -> dict:
    """
    Returns a snapshot of key macro indicators.
    Each series returns the latest value + 30-day history.
    """
    result = {}
    for name, series_id in MACRO_SERIES.items():
        obs = _get_fred_series(series_id, limit=30)
        latest = obs[0] if obs else {}
        result[name] = {
            "series_id": series_id,
            "latest_date": latest.get("date"),
            "latest_value": latest.get("value"),
            "history": obs,
        }
    result["_as_of"] = datetime.now(datetime.UTC).isoformat()
    return result


def get_series(series_id: str, limit: int = 90) -> dict:
    """Fetch a specific FRED series by ID."""
    obs = _get_fred_series(series_id, limit=limit)
    return {
        "series_id": series_id,
        "observations": obs,
        "count": len(obs),
        "as_of": datetime.now(datetime.UTC).isoformat(),
    }
