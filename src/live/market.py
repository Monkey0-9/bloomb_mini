"""
Real market data via yfinance.
Works for NYSE, NASDAQ, LSE, TSE, HKEX, NSE, ASX, Euronext, XETRA, KRX.
Zero key. Zero registration. All free.
"""
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import alpaca_trade_api as alpaca
import pandas as pd
import structlog
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

log = structlog.get_logger()

@dataclass
class Quote:
    ticker:     str
    name:       str
    price:      float
    prev_close: float
    change_pct: float
    volume:     int
    high:       float
    low:        float
    market_cap: int | None
    sector:     str
    exchange:   str
    source:     str = "yfinance"
    ts:         str = ""

_price_cache: dict[str, Quote] = {}
_price_ts:   float = 0.0
PRICE_TTL = 30.0  # 30 seconds

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

def get_prices(tickers: list[str] | None = None) -> dict[str, Quote]:
    """Fetch real prices for a list of tickers. Uses Alpaca primarily, fallbacks to yfinance."""
    global _price_cache, _price_ts

    now = time.time()
    if _price_cache and (now - _price_ts) < PRICE_TTL and not tickers:
        return _price_cache

    default_tickers = [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","JPM","V","XOM",
        "AMKBY","ZIM","MATX", "MT", "X", "NUE", "LNG", "LMT", "RTX", "BA"
    ]
    tickers = tickers or default_tickers

    client = get_alpaca_client()
    result = {}

    if client:
        try:
            log.info("fetching_alpaca_prices", count=len(tickers))
            # Alpaca multi-ticker snapshot
            snapshots = client.get_snapshots(tickers[:50])
            for t, s in snapshots.items():
                price = s.latest_trade.p
                prev_close = s.prev_daily_bar.c
                chg = (price - prev_close) / prev_close * 100 if prev_close else 0.0

                result[t] = Quote(
                    ticker = t,
                    name = t,
                    price = round(price, 2),
                    prev_close = round(prev_close, 2),
                    change_pct = round(chg, 2),
                    volume = int(s.daily_bar.v),
                    high = round(s.daily_bar.h, 2),
                    low = round(s.daily_bar.l, 2),
                    market_cap = None,
                    sector = "",
                    exchange = "ALPACA",
                    source = "alpaca_realtime",
                    ts = datetime.now(UTC).isoformat()
                )

            # If any tickers failed or were not supported by Alpaca (e.g. non-US), use yfinance
            remaining = [t for t in tickers if t not in result]
            if remaining:
                yf_results = _fetch_yfinance_prices(remaining)
                result.update(yf_results)

            _price_cache = result
            _price_ts = now
            return result
        except Exception as e:
            log.error("alpaca_fetch_error", error=str(e))

    # Fallback to yfinance if Alpaca fails or is not configured
    result = _fetch_yfinance_prices(tickers)
    _price_cache = result
    _price_ts = now
    return result

def _fetch_yfinance_prices(tickers: list[str]) -> dict[str, Quote]:
    """Fetch prices via yfinance fast_info (proven to work in this environment)."""
    result: dict[str, Quote] = {}
    ts_now = datetime.now(UTC).isoformat()

    for t in tickers[:50]:  # Limit to 50 to avoid rate limits
        try:
            info = yf.Ticker(t).fast_info
            # fast_info is a dataclass — use getattr, not .get()
            price      = getattr(info, "last_price", None) or getattr(info, "previous_close", None)
            prev_close = getattr(info, "previous_close", None) or price
            if not price:
                continue

            price      = float(price)
            prev_close = float(prev_close) if prev_close else price
            chg        = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0.0

            result[t] = Quote(
                ticker     = t,
                name       = t,
                price      = round(price, 2),
                prev_close = round(prev_close, 2),
                change_pct = round(chg, 2),
                volume     = int(getattr(info, "last_volume", 0) or 0),
                high       = round(float(getattr(info, "day_high", price) or price), 2),
                low        = round(float(getattr(info, "day_low", price) or price), 2),
                market_cap = getattr(info, "market_cap", None),
                sector     = "",
                exchange   = getattr(info, "exchange", "") or "",
                source     = "yfinance_fast_info",
                ts         = ts_now,
            )
            log.info("yfinance_price_ok", ticker=t, price=price, chg=round(chg, 2))
        except Exception as e:
            log.warning("yfinance_ticker_error", ticker=t, error=str(e))

    return result


def get_ohlcv(ticker: str, period: str = "3mo") -> list[dict]:
    """Get OHLCV history for charting. Uses Alpaca if possible."""
    client = get_alpaca_client()
    if client:
        try:
            # Simple mapping period to Alpaca timeframe
            # Note: Alpaca needs ISO date ranges, this is a simplified version
            # For now, keep yfinance for history as it handles "3mo" etc natively
            pass
        except Exception:
            pass

    try:
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return [
            {
                "date":   idx.strftime("%Y-%m-%d"),
                "open":   round(float(row["Open"]), 4),
                "high":   round(float(row["High"]), 4),
                "low":    round(float(row["Low"]), 4),
                "close":  round(float(row["Close"]), 4),
                "volume": int(row.get("Volume", 0)),
            }
            for idx, row in hist.iterrows()
        ]
    except Exception as e:
        log.error("ohlcv_error", ticker=ticker, error=str(e))
        return []

def get_options(ticker: str) -> dict:
    # Alpaca doesn't support options in basic tier, keep yfinance
    try:
        t = yf.Ticker(ticker)
        if not t.options: return {"ticker": ticker, "error": "no options"}
        exp = t.options[0]
        chain = t.option_chain(exp)
        cv = int(chain.calls["volume"].fillna(0).sum())
        pv = int(chain.puts["volume"].fillna(0).sum())
        return {
            "ticker": ticker, "expiry": exp, "expiries": list(t.options[:8]),
            "pcr": round(pv / max(cv, 1), 3), "calls_vol": cv, "puts_vol": pv,
            "calls": chain.calls[["strike","lastPrice","bid","ask","volume","openInterest","impliedVolatility"]].head(20).fillna(0).to_dict("records"),
            "puts": chain.puts[["strike","lastPrice","bid","ask","volume","openInterest","impliedVolatility"]].head(20).fillna(0).to_dict("records"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

def get_earnings(tickers: list[str]) -> list[dict]:
    calendar = []
    for t in tickers:
        try:
            cal = yf.Ticker(t).calendar
            if cal is not None and not cal.empty:
                ed = cal.iloc[0].get("Earnings Date")
                if ed:
                    calendar.append({
                        "ticker": t, "earnings_date": str(ed),
                        "eps_est": cal.iloc[0].get("EPS Estimate"),
                        "rev_est": cal.iloc[0].get("Revenue Estimate"),
                    })
        except Exception: pass
    return sorted(calendar, key=lambda x: x["earnings_date"])
