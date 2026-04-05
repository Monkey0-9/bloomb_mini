"""
FRED macro data via public CSV endpoint — no API key for CSV.
ECB Data Portal — no key ever.
"""
import asyncio
import io
import time

import httpx
import pandas as pd
import structlog
from typing import Any

log = structlog.get_logger()

FRED_SERIES = {
    "VIX":           ("VIXCLS",          "CBOE VIX",               "index"),
    "FED_FUNDS":     ("DFF",             "Fed Funds Rate",          "pct"),
    "YIELD_10Y":     ("GS10",            "US 10-Year Treasury",     "pct"),
    "YIELD_2Y":      ("GS2",             "US 2-Year Treasury",      "pct"),
    "YIELD_SPREAD":  ("T10Y2Y",          "10Y-2Y Spread",           "pct"),
    "INFLATION_EXP": ("T10YIE",          "10Y Breakeven Inflation", "pct"),
    "CPI":           ("CPIAUCSL",        "CPI",                     "index"),
    "UNEMPLOYMENT":  ("UNRATE",          "US Unemployment Rate",    "pct"),
    "WTI_OIL":       ("DCOILWTICO",      "WTI Crude Oil",           "usd"),
    "BRENT":         ("DCOILBRENTEU",    "Brent Crude",             "usd"),
    "GOLD":          ("GOLDAMGBD228NLBM","Gold London AM",          "usd"),
    "INDUSTRIAL":    ("INDPRO",          "Industrial Production",   "index"),
    "HY_SPREAD":     ("BAMLH0A0HYM2",   "High Yield Spread",       "bps"),
    "PAYROLLS":      ("PAYEMS",          "Nonfarm Payrolls",        "k"),
    "M2_MONEY":      ("M2SL",           "M2 Money Supply",         "bn"),
    "DOLLAR_INDEX":  ("DTWEXBGS",       "USD Broad Index",         "index"),
}

_macro_cache: dict = {}
_macro_ts: float = 0.0
MACRO_TTL = 3600.0  # 1 hour

async def get_series(key: str, limit: int = 260) -> list[dict]:
    """Fetch a FRED time series via CSV. No key needed."""
    series_id = FRED_SERIES.get(key.upper(), (None,))[0]
    if not series_id:
        return []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}",
            )
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text), na_values=".").dropna()
        df.columns = ["date", "value"]
        df = df.tail(limit)
        return [{"date": r["date"], "value": float(r["value"])} for _, r in df.iterrows()]
    except Exception as e:
        log.error("fred_error", key=key, error=str(e))
        return []

async def get_macro_snapshot() -> dict:
    """Get latest value for all macro indicators."""
    global _macro_cache, _macro_ts

    now = time.time()
    if _macro_cache and (now - _macro_ts) < MACRO_TTL:
        return _macro_cache

    # 1. Fetch FRED series
    async def _fetch_one(key, series_id, label, unit):
        data = await get_series(key, limit=3)
        if data:
            curr = data[-1]
            prev = data[-2] if len(data) >= 2 else curr
            chg  = curr["value"] - prev["value"]
            return key, {
                "label":  label,
                "unit":   unit,
                "value":  curr["value"],
                "prev":   prev["value"],
                "change": round(chg, 4),
                "date":   curr["date"],
            }
        return key, None

    fred_tasks = [
        _fetch_one(key, s_id, label, unit)
        for key, (s_id, label, unit) in FRED_SERIES.items()
    ]

    # 2. Fetch Public-APIs Financial Pulse
    async def _fetch_pulse():
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                rates_resp = await client.get("https://open.er-api.com/v6/latest/USD")
                rates = rates_resp.json().get("rates", {}) if rates_resp.status_code == 200 else {}

                crypto_resp = await client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
                crypto = crypto_resp.json().get("bitcoin", {}) if crypto_resp.status_code == 200 else {}

                return {
                    "USD_CNY": {"label": "USD/CNY", "value": rates.get("CNY"), "unit": "rate"},
                    "BTC_USD": {"label": "Bitcoin", "value": crypto.get("usd"), "unit": "usd"}
                }
        except Exception:
            return {}

    pulse_task = _fetch_pulse()

    results = await asyncio.gather(*fred_tasks, pulse_task)
    pulse_data = results[-1]
    fred_results = results[:-1]

    result = {}
    for key, data in fred_results:
        if data:
            result[key] = data

    result.update(pulse_data)

    _macro_cache = result
    _macro_ts    = now
    return result
