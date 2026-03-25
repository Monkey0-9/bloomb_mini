import yfinance as yf
import structlog
from dataclasses import dataclass
from datetime import datetime

log = structlog.get_logger()

# Sample universe for the SatTrade terminal
GLOBAL_UNIVERSE = {
    "AAPL": "Apple Inc.",
    "TSLA": "Tesla, Inc.",
    "MSFT": "Microsoft Corp.",
    "MT": "ArcelorMittal",
    "LNG": "Cheniere Energy",
    "ZIM": "ZIM Integrated Shipping",
}

import asyncio

async def get_prices(tickers: list[str] | None = None) -> dict:
    """
    Fetch bulk prices for any tickers on demand.
    Using yfinance for efficient data retrieval.
    """
    # If no tickers, use a diverse sample of global leaders
    if tickers is None:
        tickers = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "META", "BABA", "ASML", "BHP", "SHEL"]
    
    prices = {}
    try:
        # Optimization: Fetch in parallel using threads
        async def _fetch_one(symbol):
            ticker_obj = yf.Ticker(symbol)
            return await asyncio.to_thread(lambda: ticker_obj.info)

        tasks = [asyncio.create_task(_fetch_one(s)) for s in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, info in zip(tickers, results):
            if isinstance(info, Exception): 
                log.warning("fetch_ticker_failed", ticker=symbol, error=str(info))
                continue
            price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
            prices[symbol] = {
                "ticker": symbol,
                "price": price,
                "currency": info.get("currency", "USD"),
                "name": info.get("longName", symbol),
                "timestamp": datetime.now().isoformat()
            }
        return prices
    except Exception as e:
        log.error("fetch_market_failed", error=str(e))
        return {}


async def get_ohlcv(ticker: str, period: str = "3mo") -> list[dict]:
    """Get historical OHLCV data."""
    try:
        t = yf.Ticker(ticker)
        data = await asyncio.to_thread(t.history, period=period)
        result = []
        for index, row in data.iterrows():
            result.append({
                "time": index.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
        return result
    except Exception as e:
        log.error("fetch_ohlcv_failed", ticker=ticker, error=str(e))
        return []

def get_options(ticker: str) -> dict:
    """Get options chain summary."""
    try:
        t = yf.Ticker(ticker)
        dates = t.options
        if not dates:
            return {"ticker": ticker, "options": []}
        chain = t.option_chain(dates[0])
        return {
            "ticker": ticker,
            "expiry": dates[0],
            "calls": len(chain.calls),
            "puts": len(chain.puts)
        }
    except Exception as e:
        log.error("fetch_options_failed", ticker=ticker, error=str(e))
        return {"ticker": ticker, "options": []}
