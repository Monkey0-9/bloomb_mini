"""
Macroeconomic data layer -- FRED JSON API + World Bank + ECB (all free).
Uses authenticated FRED API (faster, more series) when FRED_API_KEY is set.
Falls back to direct CSV download (no key needed) if not configured.
"""
import io
import os

import httpx
import pandas as pd
import structlog

log = structlog.get_logger(__name__)

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_CSV_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# Core macro series tracked by SatTrade
FRED_SERIES = {
    "GDP":           "GDP",             # Gross Domestic Product
    "CPI":           "CPIAUCSL",        # Consumer Price Index
    "UNRATE":        "UNRATE",          # Unemployment Rate
    "FEDFUNDS":      "FEDFUNDS",        # Federal Funds Rate
    "RETAIL":        "RSXFS",           # Retail Sales
    "INDUSTRIAL":    "INDPRO",          # Industrial Production
    "PPI":           "PPIACO",          # Producer Price Index
    "10Y_YIELD":     "DGS10",           # 10-Year Treasury Yield (daily)
    "2Y_YIELD":      "DGS2",            # 2-Year Treasury Yield (daily)
    "VIX":           "VIXCLS",          # CBOE Volatility Index (daily)
    "OIL_WTI":       "DCOILWTICO",      # WTI Crude Oil (daily)
    "NATGAS":        "DHHNGSP",         # Natural Gas Price (daily)
    "GOLD":          "GOLDAMGBD228NLBM", # Gold Price (daily)
    "USD_INDEX":     "DTWEXBGS",        # Broad USD Index (daily)
    "TRADE_BALANCE": "BOPGSTB",         # Trade Balance
    "M2":            "M2SL",            # M2 Money Supply
}


async def get_series(series_id: str, limit: int = 100) -> pd.DataFrame:
    """
    Fetch a FRED series.
    Uses the JSON API when FRED_API_KEY is available (faster, higher rate limits).
    Falls back to the direct CSV URL (free, no key required).
    """
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        if FRED_API_KEY:
            try:
                resp = await client.get(
                    FRED_API_BASE,
                    params={
                        "series_id": series_id,
                        "api_key": FRED_API_KEY,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": limit,
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                obs = data.get("observations", [])
                df = pd.DataFrame(obs)
                if not df.empty:
                    df = df[df["value"] != "."]
                    df["DATE"] = pd.to_datetime(df["date"])
                    df["value"] = pd.to_numeric(df["value"], errors="coerce")
                    df = df.rename(columns={"value": series_id})
                    df = df[["DATE", series_id]].sort_values("DATE")
                    log.debug("fred_api_fetch", series=series_id, rows=len(df))
                    return df
            except Exception as exc:
                log.warning("fred_api_failed_fallback", series=series_id, error=str(exc))

        # Fallback: direct CSV (no key required)
        try:
            url = f"{FRED_CSV_BASE}?id={series_id}"
            resp = await client.get(url)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
            df["DATE"] = pd.to_datetime(df["DATE"])
            df.columns = ["DATE", series_id]
            return df
        except Exception as exc:
            log.error("fred_csv_failed", series=series_id, error=str(exc))
            return pd.DataFrame()


async def get_world_bank_indicator(indicator: str, country: str = "USA") -> list[dict]:
    """Fetch World Bank data using their Open API (no key required)."""
    url = (
        f"https://api.worldbank.org/v2/country/{country}"
        f"/indicator/{indicator}?format=json&per_page=100"
    )
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            data = resp.json()
            if len(data) > 1:
                return [
                    {
                        "date": item["date"],
                        "value": item["value"],
                        "indicator": item["indicator"]["value"],
                    }
                    for item in data[1]
                    if item["value"] is not None
                ]
            return []
    except Exception as exc:
        log.error("world_bank_failed", indicator=indicator, error=str(exc))
        return []


async def get_snapshot() -> dict:
    """Consolidate high-level macro indicators into a dashboard snapshot."""
    summary: dict = {}
    import asyncio
    tasks = {name: asyncio.create_task(get_series(sid, limit=5)) for name, sid in FRED_SERIES.items()}
    
    for name, task in tasks.items():
        try:
            df = await task
            sid = FRED_SERIES[name]
            if df.empty or sid not in df.columns:
                continue
            df = df.dropna(subset=[sid])
            if len(df) == 0:
                continue
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2] if len(df) > 1 else last_row
            summary[name] = {
                "latest": round(float(last_row[sid]), 4),
                "date": str(last_row["DATE"])[:10],
                "change": round(float(last_row[sid] - prev_row[sid]), 4),
                "series_id": sid,
                "source": "FRED_API" if FRED_API_KEY else "FRED_CSV",
            }
        except: continue
    return summary
