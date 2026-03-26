"""
Real market data via yfinance.
Works for NYSE, NASDAQ, LSE, TSE, HKEX, NSE, ASX, Euronext, XETRA, KRX.
Zero key. Zero registration. All free.
"""
import time
import structlog
import yfinance as yf
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timezone

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

def get_prices(tickers: list[str] | None = None) -> dict[str, Quote]:
    """Fetch real prices for a list of tickers. Zero key."""
    global _price_cache, _price_ts

    now = time.time()
    if _price_cache and (now - _price_ts) < PRICE_TTL and not tickers:
        return _price_cache

    tickers = tickers or [
        # Core SatTrade universe — diversified global coverage
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","JPM","V","XOM",
        "CVX","WMT","HD","COST","JNJ","UNH","PG","MA","BAC","GS",
        # Shipping / freight — satellite port signals
        "AMKBY","ZIM","MATX","FDX","UPS","DAL","AAL",
        # Materials — thermal signals
        "MT","X","NUE","STLD","VALE","BHP","RIO","FCX","SCCO","AA",
        # Energy — pipeline / LNG / oil
        "LNG","GLNG","GLOG","FLEX","STNG","INSW","EURN","FRO",
        "VLO","MPC","PSX",
        # Defence — military aircraft signals
        "LMT","RTX","NOC","BA","GD","HII",
        # International
        "SHEL","BP","AZN","HSBC","TSM","TM","SONY",
        # ETFs / macro
        "GLD","SLV","USO","TLT","HYG","GDX",
    ]

    try:
        raw = yf.download(
            tickers[:100],
            period        = "2d",
            auto_adjust   = True,
            progress      = False,
            threads       = True,
            group_by      = "ticker",
        )
        result = {}
        for t in tickers[:100]:
            try:
                if hasattr(raw.columns, "get_level_values"):
                    if t not in raw.columns.get_level_values(0):
                        continue
                    rows = raw[t].dropna()
                else:
                    rows = raw.dropna()

                if len(rows) < 1:
                    continue

                price    = float(rows["Close"].iloc[-1])
                prev     = float(rows["Close"].iloc[-2]) if len(rows) > 1 else price
                chg      = (price - prev) / prev * 100 if prev > 0 else 0.0

                result[t] = Quote(
                    ticker     = t,
                    name       = t,  # Fast mode — no per-ticker .info call
                    price      = round(price, 2),
                    prev_close = round(prev, 2),
                    change_pct = round(chg, 2),
                    volume     = int(rows.get("Volume", pd.Series([0])).iloc[-1]) if "Volume" in rows else 0,
                    high       = round(float(rows.get("High",  pd.Series([price])).iloc[-1]), 2),
                    low        = round(float(rows.get("Low",   pd.Series([price])).iloc[-1]), 2),
                    market_cap = None,
                    sector     = "",
                    exchange   = "",
                    ts         = datetime.now(timezone.utc).isoformat(),
                )
            except Exception:
                pass

        _price_cache = result
        _price_ts    = now
        log.info("prices_fetched", count=len(result))
        return result

    except Exception as e:
        log.error("yfinance_error", error=str(e))
        return _price_cache

def get_ohlcv(ticker: str, period: str = "3mo") -> list[dict]:
    """Get OHLCV history for charting. Zero key."""
    try:
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return [
            {
                "date":   idx.strftime("%Y-%m-%d"),
                "open":   round(float(row["Open"]),   4),
                "high":   round(float(row["High"]),   4),
                "low":    round(float(row["Low"]),    4),
                "close":  round(float(row["Close"]),  4),
                "volume": int(row.get("Volume", 0)),
            }
            for idx, row in hist.iterrows()
        ]
    except Exception as e:
        log.error("ohlcv_error", ticker=ticker, error=str(e))
        return []

def get_options(ticker: str) -> dict:
    """Full options chain. Zero key."""
    try:
        t = yf.Ticker(ticker)
        if not t.options:
            return {"ticker": ticker, "error": "no options"}
        exp   = t.options[0]
        chain = t.option_chain(exp)
        cv    = int(chain.calls["volume"].fillna(0).sum())
        pv    = int(chain.puts["volume"].fillna(0).sum())
        return {
            "ticker":    ticker,
            "expiry":    exp,
            "expiries":  list(t.options[:8]),
            "pcr":       round(pv / max(cv, 1), 3),
            "calls_vol": cv,
            "puts_vol":  pv,
            "calls":     chain.calls[["strike","lastPrice","bid","ask","volume","openInterest","impliedVolatility"]].head(20).fillna(0).to_dict("records"),
            "puts":      chain.puts [["strike","lastPrice","bid","ask","volume","openInterest","impliedVolatility"]].head(20).fillna(0).to_dict("records"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

def get_earnings(tickers: list[str]) -> list[dict]:
    """Upcoming earnings calendar. Zero key."""
    calendar = []
    for t in tickers:
        try:
            cal = yf.Ticker(t).calendar
            if cal is not None and not cal.empty:
                ed = cal.iloc[0].get("Earnings Date")
                if ed:
                    calendar.append({
                        "ticker":       t,
                        "earnings_date": str(ed),
                        "eps_est":      cal.iloc[0].get("EPS Estimate"),
                        "rev_est":      cal.iloc[0].get("Revenue Estimate"),
                    })
        except Exception:
            pass
    return sorted(calendar, key=lambda x: x["earnings_date"])
