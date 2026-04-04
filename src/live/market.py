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
    """Private helper for yfinance fallback."""
    try:
        raw = yf.download(
            tickers[:100],
            period = "2d",
            auto_adjust = True,
            progress = False,
            threads = True,
            group_by = "ticker",
        )
        result = {}
        for t in tickers[:100]:
            try:
                if hasattr(raw.columns, "get_level_values"):
                    if t not in raw.columns.get_level_values(0): continue
                    rows = raw[t].dropna()
                else:
                    rows = raw.dropna()

                if len(rows) < 1: continue

                price = float(rows["Close"].iloc[-1])
                prev = float(rows["Close"].iloc[-2]) if len(rows) > 1 else price
                chg = (price - prev) / prev * 100 if prev > 0 else 0.0

                result[t] = Quote(
                    ticker = t, name = t, price = round(price, 2),
                    prev_close = round(prev, 2), change_pct = round(chg, 2),
                    volume = int(rows.get("Volume", pd.Series([0])).iloc[-1]),
                    high = round(float(rows.get("High", price)).iloc[-1], 2) if isinstance(rows.get("High"), pd.Series) else price,
                    low = round(float(rows.get("Low", price)).iloc[-1], 2) if isinstance(rows.get("Low"), pd.Series) else price,
                    market_cap = None, sector = "", exchange = "", source = "yfinance",
                    ts = datetime.now(UTC).isoformat()
                )
            except Exception:
                pass
        return result
    except Exception as e:
        log.error("yfinance_fallback_error", error=str(e))
        return {}

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
