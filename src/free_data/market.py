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

def get_prices(tickers: list[str] | None = None) -> dict:
    """
    Fetch bulk prices for any tickers on demand.
    Using yfinance for efficient data retrieval.
    """
    # If no tickers, use a diverse sample of global leaders
    if tickers is None:
        tickers = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "META", "BABA", "ASML", "BHP", "SHEL"]
    
    prices = {}
    try:
        for symbol in tickers:
            ticker_obj = yf.Ticker(symbol)
            try:
                info = ticker_obj.info
                price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
                prices[symbol] = {
                    "ticker": symbol,
                    "price": price,
                    "currency": info.get("currency", "USD"),
                    "name": info.get("longName", symbol),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as inner_e:
                log.warning("fetch_ticker_failed", ticker=symbol, error=str(inner_e))
        return prices
    except Exception as e:
        log.error("fetch_market_failed", error=str(e))
        return {}


def get_ohlcv(ticker: str, period: str = "3mo") -> list[dict]:
    """Get historical OHLCV data."""
    try:
        data = yf.Ticker(ticker).history(period=period)
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
