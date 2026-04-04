"""
SatTrade Earnings Data via yfinance
"""
import asyncio
from typing import Any

import structlog

log = structlog.get_logger(__name__)

async def fetch_earnings_calendar(ticker: str) -> dict[str, Any]:
    try:
        import yfinance as yf
        loop = asyncio.get_event_loop()
        ticker_obj = yf.Ticker(ticker)

        # yfinance calendar can vary by version, try `calendar` or `get_earnings_dates()`
        dates_df = await loop.run_in_executor(None, ticker_obj.get_earnings_dates, 10)

        if dates_df is None or dates_df.empty:
            return {"earnings": []}

        dates_df = dates_df.reset_index()
        records = dates_df.to_dict(orient="records")

        # Ensure it's JSON serializable
        clean_records = []
        for r in records:
            clean_records.append({str(k): str(v) for k, v in r.items()})

        return {"earnings": clean_records}
    except Exception as exc:
        log.warning("earnings_fetch_failed", ticker=ticker, error=str(exc))
        return {"earnings": []}
