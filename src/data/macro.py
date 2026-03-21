import httpx
import pandas as pd
import io
import structlog  # type: ignore[import-untyped]
from typing import Any
from datetime import datetime, timezone

log = structlog.get_logger()

# FRED series available via free CSV download — no API key needed
FRED_SERIES = {
    "VIX":            ("VIXCLS",    "CBOE Volatility Index",          "index"),
    "FED_FUNDS":      ("DFF",       "Federal Funds Rate",             "percent"),
    "YIELD_10Y2Y":    ("T10Y2Y",    "10Y-2Y Treasury Spread",         "percent"),
    "YIELD_10Y":      ("GS10",      "10-Year Treasury Rate",          "percent"),
    "YIELD_2Y":       ("GS2",       "2-Year Treasury Rate",           "percent"),
    "CPI_YOY":        ("CPIAUCSL",  "CPI All Urban Consumers",        "index"),
    "WTI_OIL":        ("DCOILWTICO","WTI Crude Oil Price",            "usd/barrel"),
    "BRENT_OIL":      ("DCOILBRENTEU","Brent Crude Oil Price",        "usd/barrel"),
    "GOLD":           ("GOLDAMGBD228NLBM","Gold London Price AM",     "usd/troy_oz"),
    "UNEMPLOYMENT":   ("UNRATE",    "US Unemployment Rate",           "percent"),
    "USD_INDEX":      ("DTWEXBGS",  "USD Broad Dollar Index",         "index"),
    "INDUSTRIAL_PROD":("INDPRO",    "Industrial Production Index",    "index"),
    "BALTIC_DRY":     ("WWGDPBL01", "Baltic Dry Index Proxy",         "index"),
}

def fetch_fred_series(series_id: str, limit: int = 252) -> list[dict[str, Any]]:
    """
    Fetch a FRED data series via free CSV endpoint.
    No API key needed. Returns last N observations.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        resp = httpx.get(url, timeout=20)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text), na_values=".")
        df.columns = ["date", "value"]
        df = df.dropna().tail(limit)
        return [
            {"date": row["date"], "value": float(row["value"])}
            for _, row in df.iterrows()
        ]
    except Exception as e:
        log.error("fred_error", series_id=series_id, error=str(e))
        return []


def get_macro_dashboard() -> dict[str, Any]:
    """Get current values of all key macro indicators."""
    result = {}
    for key, (series_id, label, unit) in FRED_SERIES.items():
        data = fetch_fred_series(series_id, limit=2)
        if data:
            current = data[-1]
            prev = data[-2] if len(data) > 1 else current
            change = current["value"] - prev["value"]
            result[key] = {
                "label": label,
                "unit": unit,
                "current_value": current["value"],
                "previous_value": prev["value"],
                "change": round(change, 4),
                "date": current["date"],
                "signal": _macro_signal(key, current["value"], prev["value"]),
            }
    return result


def _macro_signal(key: str, current: float, prev: float) -> str:
    """Simple directional signal from macro data."""
    change = current - prev
    if key == "VIX":
        return "BEARISH_MARKET" if current > 25 else "NEUTRAL" if current > 18 else "BULLISH_MARKET"
    elif key == "YIELD_10Y2Y":
        return "RECESSION_RISK" if current < -0.5 else "NEUTRAL" if current < 0.5 else "EXPANSION"
    elif key in ("WTI_OIL", "BRENT_OIL"):
        return "BULLISH_ENERGY" if change > 1 else "BEARISH_ENERGY" if change < -1 else "NEUTRAL"
    return "NEUTRAL"
