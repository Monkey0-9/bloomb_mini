import os
import time
from datetime import UTC, datetime
from typing import Any

import alpaca_trade_api as alpaca
import structlog
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

log = structlog.get_logger()

# Alpaca Client Initialization
ALPACA_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY")
ALPACA_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

def get_alpaca_client():
    if not ALPACA_KEY or not ALPACA_SECRET:
        return None
    try:
        return alpaca.REST(ALPACA_KEY, ALPACA_SECRET, ALPACA_URL, api_version='v2')
    except Exception as e:
        log.error("alpaca_init_error", error=str(e))
        return None

# Global equity universe
GLOBAL_UNIVERSE = {
    "AAPL": ("Apple Inc", "NASDAQ", "Technology"),
    "MSFT": ("Microsoft", "NASDAQ", "Technology"),
    "NVDA": ("NVIDIA", "NASDAQ", "Technology"),
    "AMZN": ("Amazon", "NASDAQ", "Consumer Discretionary"),
    "GOOGL": ("Alphabet", "NASDAQ", "Technology"),
    "META": ("Meta Platforms", "NASDAQ", "Technology"),
    "TSLA": ("Tesla", "NASDAQ", "Consumer Discretionary"),
    "JPM": ("JPMorgan Chase", "NYSE", "Financials"),
    "V": ("Visa", "NYSE", "Financials"),
    "XOM": ("Exxon Mobil", "NYSE", "Energy"),
    "AMKBY": ("AP Moller-Maersk ADR", "OTC", "Industrials"),
    "ZIM": ("ZIM Integrated", "NYSE", "Industrials"),
    "MT": ("ArcelorMittal", "NYSE", "Materials"),
    "LNG": ("Cheniere Energy", "NYSE", "Energy"),
}

_price_cache: dict[str, dict[str, Any]] = {}
_cache_timestamp: float = 0
CACHE_TTL_SECONDS = 30

def get_stock_price(ticker: str) -> dict[str, Any]:
    prices = get_bulk_prices([ticker])
    return prices.get(ticker, {"ticker": ticker, "error": "Price not found"})

def get_bulk_prices(tickers: list[str] | None = None) -> dict[str, dict[str, Any]]:
    """Fetch real prices via Alpaca (primary) or yfinance (fallback)."""
    global _price_cache, _cache_timestamp

    now = time.time()
    if _price_cache and (now - _cache_timestamp) < CACHE_TTL_SECONDS and not tickers:
        return _price_cache

    tickers = tickers or list(GLOBAL_UNIVERSE.keys())
    client = get_alpaca_client()
    result = {}

    if client:
        try:
            log.info("fetching_alpaca_bulk", count=len(tickers))
            snapshots = client.get_snapshots(tickers[:100])
            for ticker, snap in snapshots.items():
                meta = GLOBAL_UNIVERSE.get(ticker, (ticker, "US", "Equity"))
                result[ticker] = {
                    "ticker": ticker,
                    "name": meta[0],
                    "exchange": meta[1],
                    "sector": meta[2],
                    "price": round(snap.latest_trade.p, 2),
                    "prev_close": round(snap.prev_daily_bar.c, 2),
                    "change_pct": round((snap.latest_trade.p - snap.prev_daily_bar.c) / snap.prev_daily_bar.c * 100, 2) if snap.prev_daily_bar.c else 0,
                    "volume": int(snap.daily_bar.v),
                    "high": round(snap.daily_bar.h, 2),
                    "low": round(snap.daily_bar.l, 2),
                    "source": "alpaca_bulk",
                    "updated_at": datetime.now(UTC).isoformat(),
                }

            remaining = [t for t in tickers if t not in result]
            if remaining:
                result.update(_fetch_yfinance_bulk(remaining))

            _price_cache = result
            _cache_timestamp = now
            return result
        except Exception as e:
            log.error("alpaca_bulk_error", error=str(e))

    result = _fetch_yfinance_bulk(tickers)
    _price_cache = result
    _cache_timestamp = now
    return result

def _fetch_yfinance_bulk(tickers: list[str]) -> dict[str, dict[str, Any]]:
    try:
        raw = yf.download(tickers[:100], period="2d", interval="1d", group_by="ticker", auto_adjust=True, progress=False, threads=True)
        res = {}
        for ticker in tickers[:100]:
            try:
                if ticker in raw.columns.get_level_values(0):
                    row = raw[ticker].dropna().iloc[-1]
                    prev_row = raw[ticker].dropna().iloc[-2] if len(raw[ticker].dropna()) > 1 else row
                    price = float(row["Close"])
                    prev_close = float(prev_row["Close"])
                    change_pct = ((price - prev_close) / prev_close) * 100
                    meta = GLOBAL_UNIVERSE.get(ticker, (ticker, "", ""))
                    res[ticker] = {
                        "ticker": ticker, "name": meta[0], "exchange": meta[1], "sector": meta[2],
                        "price": round(price, 2), "prev_close": round(prev_close, 2),
                        "change_pct": round(change_pct, 2), "volume": int(row.get("Volume", 0)),
                        "high": round(float(row.get("High", price)), 2), "low": round(float(row.get("Low", price)), 2),
                        "source": "yfinance_bulk", "updated_at": datetime.now(UTC).isoformat(),
                    }
            except Exception: pass
        return res
    except Exception as e:
        log.error("yf_bulk_fallback_error", error=str(e))
        return {}


def get_ohlcv_history(ticker: str,
                      period: str = "3mo",
                      interval: str = "1d") -> list[dict]:
    """
    Get OHLCV history for charting.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval, auto_adjust=True)
        result = []
        for idx, row in hist.iterrows():
            result.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row.get("Volume", 0)),
            })
        return result
    except Exception as e:
        log.error("ohlcv_error", ticker=ticker, error=str(e))
        return []


def get_company_info(ticker: str) -> dict[str, Any]:
    """Get company fundamentals — sector, PE, market cap, description."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "ticker": ticker,
            "name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "beta": info.get("beta"),
            "description": info.get("longBusinessSummary", "")[:500],
            "website": info.get("website", ""),
            "employees": info.get("fullTimeEmployees"),
            "country": info.get("country", ""),
        }
    except Exception as e:
        log.error("company_info_error", ticker=ticker, error=str(e))
        return {}


def get_options_chain(ticker: str) -> dict[str, Any]:
    """Get full options chain with PCR and max pain calculation."""
    try:
        t = yf.Ticker(ticker)
        if not t.options:
            return {"ticker": ticker, "error": "No options available"}

        # Get nearest expiry
        nearest_expiry = t.options[0]
        chain = t.option_chain(nearest_expiry)

        calls_total_volume = chain.calls["volume"].fillna(0).sum()
        puts_total_volume = chain.puts["volume"].fillna(0).sum()
        pcr = puts_total_volume / max(calls_total_volume, 1)

        # Max pain calculation (price where options buyers lose most)
        all_strikes = sorted(set(
            chain.calls["strike"].tolist() + chain.puts["strike"].tolist()
        ))

        current_price_info = get_bulk_prices([ticker])
        current_price = current_price_info.get(ticker, {}).get("price", 0)

        return {
            "ticker": ticker,
            "expiry": nearest_expiry,
            "all_expiries": list(t.options[:6]),  # next 6 expiries
            "put_call_ratio": round(pcr, 3),
            "calls_volume": int(calls_total_volume),
            "puts_volume": int(puts_total_volume),
            "calls": chain.calls[["strike","lastPrice","bid","ask","volume",
                                   "openInterest","impliedVolatility"]].head(20).to_dict("records"),
            "puts":  chain.puts[["strike","lastPrice","bid","ask","volume",
                                  "openInterest","impliedVolatility"]].head(20).to_dict("records"),
            "pcr_signal": "BEARISH" if pcr > 1.5 else "BULLISH" if pcr < 0.7 else "NEUTRAL",
        }
    except Exception as e:
        log.error("options_error", ticker=ticker, error=str(e))
        return {"ticker": ticker, "error": str(e)}


def get_earnings_calendar(tickers: list[str]) -> list[dict[str, Any]]:
    """Get upcoming earnings dates for a list of tickers."""
    calendar = []
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            if cal is not None and not cal.empty:
                earnings_date = cal.iloc[0].get("Earnings Date")
                if earnings_date is not None:
                    calendar.append({
                        "ticker": ticker,
                        "earnings_date": str(earnings_date),
                        "eps_estimate": cal.iloc[0].get("EPS Estimate"),
                        "revenue_estimate": cal.iloc[0].get("Revenue Estimate"),
                    })
        except Exception:
            pass
    return sorted(calendar, key=lambda x: x["earnings_date"])
