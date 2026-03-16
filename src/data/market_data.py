import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import structlog

log = structlog.get_logger()

def get_stock_price(ticker: str) -> dict:
    """
    Fetches current stock price and metadata using yfinance.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "ticker": ticker,
            "current_price": info.get("regularMarketPrice") or info.get("currentPrice"),
            "previous_close": info.get("regularMarketPreviousClose") or info.get("previousClose"),
            "currency": info.get("currency", "USD"),
            "long_name": info.get("longName"),
            "sector": info.get("sector"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        log.error("failed_to_fetch_stock_price", ticker=ticker, error=str(e))
        return {"ticker": ticker, "error": str(e)}

def get_options_chain(ticker: str) -> dict:
    """
    CBOE publishes options data free for major tickers.
    Implemented as per user directive.
    """
    try:
        t = yf.Ticker(ticker)
        if not t.options:
            return {"ticker": ticker, "error": "No options available"}
            
        expiry = t.options[0]  # nearest expiry
        chain = t.option_chain(expiry)
        
        return {
            "ticker": ticker,
            "expiry": expiry,
            "calls": chain.calls[["strike", "lastPrice", "volume", "impliedVolatility"]].to_dict(orient="records"),
            "puts": chain.puts[["strike", "lastPrice", "volume", "impliedVolatility"]].to_dict(orient="records"),
            "put_call_ratio": len(chain.puts) / max(len(chain.calls), 1),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        log.error("failed_to_fetch_options_chain", ticker=ticker, error=str(e))
        return {"ticker": ticker, "error": str(e)}

def get_earnings_calendar(ticker: str) -> dict:
    """
    Fetches upcoming earnings dates from yfinance.
    """
    try:
        t = yf.Ticker(ticker)
        earnings = t.calendar
        
        # yfinance.calendar can be a dict or a DataFrame depending on version
        if isinstance(earnings, dict):
            return {
                "ticker": ticker,
                "earnings_date": [d.isoformat() for d in earnings.get("Earnings Date", [])],
                "earnings_average": earnings.get("Earnings Average"),
                "earnings_low": earnings.get("Earnings Low"),
                "earnings_high": earnings.get("Earnings High"),
            }
        elif isinstance(earnings, pd.DataFrame):
            return {
                "ticker": ticker,
                "dates": earnings.to_dict(),
            }
        return {"ticker": ticker, "earnings": str(earnings)}
    except Exception as e:
        log.error("failed_to_fetch_earnings", ticker=ticker, error=str(e))
        return {"ticker": ticker, "error": str(e)}
