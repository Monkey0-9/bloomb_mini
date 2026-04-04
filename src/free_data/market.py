"""
Market Data Engine — Zero-key yfinance integration.
Fetches bulk prices, charts, options, and earnings calendars.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)

@dataclass
class MarketSnapshot:
    ticker: str
    price: float
    change_pct: float
    volume: int
    earnings_date: str | None = None

async def get_market_snapshot(tickers: list[str]) -> list[MarketSnapshot]:
    """Fetch real-time prices for a list of tickers via yfinance."""
    try:
        if not tickers: return []
        data = yf.download(tickers, period="2d", group_by="ticker", progress=False)

        snapshots = []
        for t in tickers:
            try:
                hist = data[t] if len(tickers) > 1 else data
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
                snapshots.append(MarketSnapshot(
                    ticker=t, price=current,
                    change_pct=round((current/prev - 1) * 100, 2),
                    volume=int(hist["Volume"].iloc[-1])
                ))
            except Exception:
                continue
        return snapshots
    except Exception as e:
        logger.error(f"Market data error: {e}")
        return []

async def get_ticker_details(ticker: str) -> dict[str, Any]:
    """Get full details including options, analyst estimates, and earnings."""
    try:
        t = yf.Ticker(ticker)
        return {
            "calendar": t.calendar,
            "analyst_price_target": t.analyst_price_target,
            "major_holders": t.major_holders.to_dict() if t.major_holders is not None else {},
            "options": t.options
        }
    except Exception as e:
        logger.error("Ticker details error for %s: %s", ticker, e)
        return {}

def get_ohlcv_history(ticker: str, period: str = "3mo") -> Any:
    """Download historical OHLCV data for charting."""
    return yf.download(ticker, period=period, progress=False)
