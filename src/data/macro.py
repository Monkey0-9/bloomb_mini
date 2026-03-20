"""
SatTrade Macro Data via FRED CSVs
"""
import asyncio
import io
import csv
import structlog
from typing import Dict, Any

log = structlog.get_logger(__name__)

FRED_MAPPING = {
    "US_CPI": "CPIAUCSL",
    "US_PPI": "PPIFES",
    "OIL_WTI": "DCOILWTICO",
    "NATURAL_GAS": "DHHNGSP",
    "US_10Y": "DGS10",
    "FED_FUNDS": "FEDFUNDS",
    "USD_INDEX": "DTWEXBGS",
}

async def fetch_fred_csv(series_id: str) -> list:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return []
                text = await resp.text()
                reader = csv.reader(io.StringIO(text))
                headers = next(reader, None) # skip header
                data = []
                for row in reader:
                    if len(row) == 2 and row[1] != '.':
                        data.append({"date": row[0], "value": row[1]})
                return data[-100:] # Last 100 periods
    except Exception as exc:
        log.warning("fred_fetch_failed", series=series_id, error=str(exc))
        return []

async def get_macro_data() -> Dict[str, Any]:
    tasks = [fetch_fred_csv(fred_id) for fred_id in FRED_MAPPING.values()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    output = {}
    for (key, fred_id), history in zip(FRED_MAPPING.items(), results):
        if isinstance(history, Exception) or not history:
            output[key] = {"latest_value": None, "latest_date": None, "history": []}
        else:
            output[key] = {
                "latest_value": history[-1]["value"],
                "latest_date": history[-1]["date"],
                "history": history
            }
    return output
