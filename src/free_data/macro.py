"""
Macro Data Engine — Zero-key FRED (Federal Reserve) integration.
Fetches VIX, 10Y Yields, CPI, Oil, Gold, Unemployment via CSV endpoints.
"""
from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}"

MACRO_SERIES = {
    "VIX": "VIXCLS",
    "10Y_Yield": "DGS10",
    "CPI_YoY": "CPALTT01USM659N",
    "WTI_Oil": "DCOILWTICO",
    "Gold_Price": "GOLDAMGBD228NLBM",
    "Unemployment": "UNRATE"
}

@dataclass
class MacroPoint:
    series_id: str
    date: str
    value: float

async def get_macro_data(series_name: str) -> list[MacroPoint]:
    """Fetch macro series from FRED CSV endpoint. No key needed."""
    try:
        series_id = MACRO_SERIES.get(series_name)
        if not series_id: return []
        
        url = FRED_CSV_URL.format(id=series_id)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            rows = list(csv.DictReader(io.StringIO(resp.text)))
            
            points = []
            for r in rows:
                try:
                    val = r.get("VALUE", ".")
                    if val == ".": continue
                    points.append(MacroPoint(
                        series_id=series_id,
                        date=r["DATE"],
                        value=float(val)
                    ))
                except Exception:
                    continue
            return points[-30:] # Last 30 days/points
    except Exception as e:
        logger.error(f"Macro data error for %s: %s", series_name, e)
        return []
