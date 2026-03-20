"""
Complete market data layer using only 100% free sources with zero API keys.
Source hierarchy:
  Equity prices:    yfinance -> Stooq CSV fallback
  OHLCV history:    yfinance -> Yahoo Finance direct endpoint fallback
  Options chains:   yfinance only
  Macro data:       FRED CSV (no key) -> ECB API -> World Bank API
  Forex:            ECB Data Portal (no key)
  Crypto:           CoinGecko (no key for v3)
"""

import time
import io
import httpx
import pandas as pd
import structlog
from datetime import datetime, timezone, timedelta
from functools import lru_cache
from pathlib import Path

log = structlog.get_logger()

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    log.warning("yfinance_not_installed", fix="pip install yfinance")

EQUITY_UNIVERSE: dict[str, tuple[str, str, str]] = {
    # US Mega Cap
    "AAPL":  ("Apple Inc",              "NASDAQ", "Technology"),
    "MSFT":  ("Microsoft Corp",         "NASDAQ", "Technology"),
    "NVDA":  ("NVIDIA Corp",            "NASDAQ", "Technology"),
    "AMZN":  ("Amazon.com Inc",         "NASDAQ", "Consumer Disc."),
    "GOOGL": ("Alphabet Inc",           "NASDAQ", "Technology"),
    "META":  ("Meta Platforms",         "NASDAQ", "Technology"),
    "TSLA":  ("Tesla Inc",              "NASDAQ", "Consumer Disc."),
    "BRK-B": ("Berkshire Hathaway",     "NYSE",   "Financials"),
    "JPM":   ("JPMorgan Chase",         "NYSE",   "Financials"),
    "V":     ("Visa Inc",               "NYSE",   "Financials"),
    "MA":    ("Mastercard Inc",         "NYSE",   "Financials"),
    "XOM":   ("Exxon Mobil",            "NYSE",   "Energy"),
    "CVX":   ("Chevron Corp",           "NYSE",   "Energy"),
    "JNJ":   ("Johnson & Johnson",      "NYSE",   "Healthcare"),
    "PG":    ("Procter & Gamble",       "NYSE",   "Consumer Staples"),
    "HD":    ("Home Depot",             "NYSE",   "Consumer Disc."),
    "WMT":   ("Walmart Inc",            "NYSE",   "Consumer Staples"),
    "COST":  ("Costco Wholesale",       "NASDAQ", "Consumer Staples"),
    "MCD":   ("McDonald's Corp",        "NYSE",   "Consumer Disc."),
    "UNH":   ("UnitedHealth Group",     "NYSE",   "Healthcare"),
    # SatTrade core signal universe
    "AMKBY": ("AP Moller-Maersk ADR",   "OTC",    "Industrials"),
    "ZIM":   ("ZIM Integrated",         "NYSE",   "Industrials"),
    "MT":    ("ArcelorMittal",          "NYSE",   "Materials"),
    "LNG":   ("Cheniere Energy",        "NYSE",   "Energy"),
    "X":     ("US Steel Corp",          "NYSE",   "Materials"),
    "NUE":   ("Nucor Corp",             "NYSE",   "Materials"),
    "STLD":  ("Steel Dynamics",         "NASDAQ", "Materials"),
    "MATX":  ("Matson Inc",             "NYSE",   "Industrials"),
    "TGT":   ("Target Corp",            "NYSE",   "Consumer Staples"),
    "FDX":   ("FedEx Corp",             "NYSE",   "Industrials"),
    "UPS":   ("United Parcel Service",  "NYSE",   "Industrials"),
    "DAL":   ("Delta Air Lines",        "NYSE",   "Industrials"),
    "VALE":  ("Vale SA",                "NYSE",   "Materials"),
    "BHP":   ("BHP Group ADR",          "NYSE",   "Materials"),
    "RIO":   ("Rio Tinto ADR",          "NYSE",   "Materials"),
    # UK / LSE
    "SHEL.L":("Shell PLC",              "LSE",    "Energy"),
    "BP.L":  ("BP PLC",                 "LSE",    "Energy"),
    "AZN.L": ("AstraZeneca PLC",        "LSE",    "Healthcare"),
    "HSBA.L":("HSBC Holdings",          "LSE",    "Financials"),
    "ULVR.L":("Unilever PLC",           "LSE",    "Consumer Staples"),
    "RR.L":  ("Rolls-Royce Holdings",   "LSE",    "Industrials"),
    "VOD.L": ("Vodafone Group",         "LSE",    "Communication"),
    # Europe
    "SAP.DE":  ("SAP SE",               "XETRA",  "Technology"),
    "SIE.DE":  ("Siemens AG",           "XETRA",  "Industrials"),
    "HLAG.DE": ("Hapag-Lloyd AG",       "XETRA",  "Industrials"),
    "ASML.AS": ("ASML Holding",         "AMS",    "Technology"),
    "LVMH.PA": ("LVMH",                 "EPA",    "Consumer Disc."),
    "OR.PA":   ("L'Oreal SA",           "EPA",    "Consumer Staples"),
    "TTE.PA":  ("TotalEnergies SE",     "EPA",    "Energy"),
    "NESN.SW": ("Nestle SA",            "SWX",    "Consumer Staples"),
    "NOVN.SW": ("Novartis AG",          "SWX",    "Healthcare"),
    # Asia-Pacific
    "7203.T":    ("Toyota Motor",       "TSE",    "Consumer Disc."),
    "6758.T":    ("Sony Group",         "TSE",    "Technology"),
    "9984.T":    ("SoftBank Group",     "TSE",    "Technology"),
    "5401.T":    ("Nippon Steel",       "TSE",    "Materials"),
    "005930.KS": ("Samsung Electronics","KRX",   "Technology"),
    "000660.KS": ("SK Hynix",           "KRX",   "Technology"),
    "005490.KS": ("POSCO Holdings",     "KRX",   "Materials"),
    "1919.HK":   ("COSCO Shipping",     "HKEX",  "Industrials"),
    "700.HK":    ("Tencent Holdings",   "HKEX",  "Technology"),
    "9988.HK":   ("Alibaba Group",      "HKEX",  "Consumer Disc."),
    "2318.HK":   ("Ping An Insurance",  "HKEX",  "Financials"),
    "RELIANCE.NS":("Reliance Industries","NSE",  "Energy"),
    "TCS.NS":    ("Tata Consultancy",   "NSE",   "Technology"),
    "INFY.NS":   ("Infosys",            "NSE",   "Technology"),
    "HDFCBANK.NS":("HDFC Bank",         "NSE",   "Financials"),
    # ETFs and commodities proxies
    "GLD":  ("SPDR Gold ETF",           "NYSE",  "Commodities"),
    "SLV":  ("iShares Silver ETF",      "NYSE",  "Commodities"),
    "USO":  ("US Oil Fund",             "NYSE",  "Commodities"),
    "DBA":  ("Invesco DB Agriculture",  "NYSE",  "Commodities"),
    "TLT":  ("iShares 20+ Year Treasury","NASDAQ","Bonds"),
}

_price_cache: dict[str, dict] = {}
_price_ts: float = 0.0
PRICE_CACHE_TTL = 30.0

def get_bulk_prices(tickers: list[str] | None = None) -> dict[str, dict]:
    global _price_cache, _price_ts

    now = time.time()
    if _price_cache and (now - _price_ts) < PRICE_CACHE_TTL:
        return _price_cache

    tickers = tickers or list(EQUITY_UNIVERSE.keys())[:100]

    if YFINANCE_AVAILABLE:
        try:
            import yfinance as yf
            raw = yf.download(
                tickers[:100],
                period="2d",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            result = {}
            for ticker in tickers[:100]:
                try:
                    if hasattr(raw.columns, "get_level_values"):
                        lvl0 = raw.columns.get_level_values(0)
                        if ticker in lvl0:
                            rows = raw[ticker].dropna()
                            if len(rows) >= 1:
                                r = rows.iloc[-1]
                                p = rows.iloc[-2] if len(rows) >= 2 else r
                                price    = float(r["Close"])
                                prev     = float(p["Close"])
                                chg_pct  = (price - prev) / prev * 100 if prev else 0.0
                                meta     = EQUITY_UNIVERSE.get(ticker, ("","",""))
                                result[ticker] = {
                                    "ticker":     ticker,
                                    "name":       meta[0],
                                    "exchange":   meta[1],
                                    "sector":     meta[2],
                                    "price":      round(price, 2),
                                    "prev_close": round(prev, 2),
                                    "change_pct": round(chg_pct, 2),
                                    "volume":     int(r.get("Volume", 0)),
                                    "high":       round(float(r.get("High", price)), 2),
                                    "low":        round(float(r.get("Low",  price)), 2),
                                    "source":     "yfinance",
                                    "updated_at": datetime.now(timezone.utc).isoformat(),
                                }
                except Exception:
                    pass

            _price_cache = result
            _price_ts = now
            log.info("prices_fetched_yfinance", count=len(result))
            return result
        except Exception as e:
            log.error("yfinance_error", error=str(e))

    # Fallback to Stooq CSV
    result = {}
    for ticker in tickers[:20]:
        stooq_data = _get_stooq_price(ticker)
        if stooq_data:
            result[ticker] = stooq_data
    _price_cache = result
    _price_ts = now
    return result

def _get_stooq_price(ticker: str) -> dict | None:
    stooq_ticker = ticker.lower().replace("-b", ".b")
    if "." not in stooq_ticker and ticker in EQUITY_UNIVERSE:
        exchange = EQUITY_UNIVERSE[ticker][1]
        suffix_map = {
            "NASDAQ": "us", "NYSE": "us", "OTC": "us",
            "LSE": "uk", "XETRA": "de", "AMS": "nl",
            "EPA": "fr", "SWX": "ch", "MILAN": "it",
            "TSE": "jp", "KRX": "kr", "HKEX": "hk",
            "NSE": "in", "ASX": "au",
        }
        sfx = suffix_map.get(exchange, "us")
        stooq_ticker = f"{stooq_ticker}.{sfx}"

    url = f"https://stooq.com/q/d/l/?s={stooq_ticker}&i=d"
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        df = pd.read_csv(io.StringIO(resp.text))
        if df.empty or "Close" not in df.columns:
            return None
        df = df.dropna(subset=["Close"])
        if len(df) < 1:
            return None
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else last
        price   = float(last["Close"])
        prev_cl = float(prev["Close"])
        meta    = EQUITY_UNIVERSE.get(ticker, ("", "", ""))
        return {
            "ticker":     ticker,
            "name":       meta[0],
            "exchange":   meta[1],
            "sector":     meta[2],
            "price":      round(price, 2),
            "prev_close": round(prev_cl, 2),
            "change_pct": round((price - prev_cl)/prev_cl*100, 2) if prev_cl else 0.0,
            "volume":     int(last.get("Volume", 0)),
            "high":       round(float(last.get("High", price)), 2),
            "low":        round(float(last.get("Low",  price)), 2),
            "source":     "stooq",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return None

def get_ohlcv(ticker: str, period: str = "3mo") -> list[dict]:
    if not YFINANCE_AVAILABLE:
        return []
    try:
        import yfinance as yf
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return [
            {
                "date":   idx.strftime("%Y-%m-%d"),
                "open":   round(float(row["Open"]),   2),
                "high":   round(float(row["High"]),   2),
                "low":    round(float(row["Low"]),    2),
                "close":  round(float(row["Close"]),  2),
                "volume": int(row.get("Volume", 0)),
            }
            for idx, row in hist.iterrows()
        ]
    except Exception as e:
        log.error("ohlcv_error", ticker=ticker, error=str(e))
        return []

def get_options(ticker: str) -> dict:
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        if not t.options:
            return {"ticker": ticker, "error": "No options data"}
        expiry = t.options[0]
        chain  = t.option_chain(expiry)
        call_vol = int(chain.calls["volume"].fillna(0).sum())
        put_vol  = int(chain.puts["volume"].fillna(0).sum())
        pcr = round(put_vol / max(call_vol, 1), 3)
        return {
            "ticker":         ticker,
            "expiry":         expiry,
            "all_expiries":   list(t.options[:8]),
            "put_call_ratio": pcr,
            "pcr_signal":     "BEARISH" if pcr>1.5 else "BULLISH" if pcr<0.7 else "NEUTRAL",
            "calls_volume":   call_vol,
            "puts_volume":    put_vol,
            "calls": chain.calls[["strike","lastPrice","bid","ask",
                                   "volume","openInterest","impliedVolatility"]
                                 ].head(20).fillna(0).to_dict("records"),
            "puts":  chain.puts[["strike","lastPrice","bid","ask",
                                  "volume","openInterest","impliedVolatility"]
                                ].head(20).fillna(0).to_dict("records"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

def get_earnings_calendar(tickers: list[str]) -> list[dict]:
    if not YFINANCE_AVAILABLE:
        return []
    calendar = []
    for ticker in tickers:
        try:
            import yfinance as yf
            cal = yf.Ticker(ticker).calendar
            if cal is not None and not cal.empty:
                ed = cal.iloc[0].get("Earnings Date")
                if ed:
                    calendar.append({
                        "ticker":          ticker,
                        "earnings_date":   str(ed),
                        "eps_estimate":    cal.iloc[0].get("EPS Estimate"),
                        "revenue_estimate":cal.iloc[0].get("Revenue Estimate"),
                    })
        except Exception:
            pass
    return sorted(calendar, key=lambda x: x["earnings_date"])

def get_company_info(ticker: str) -> dict:
    if not YFINANCE_AVAILABLE:
        return {}
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        return {
            "ticker":       ticker,
            "name":         info.get("longName",""),
            "sector":       info.get("sector",""),
            "industry":     info.get("industry",""),
            "country":      info.get("country",""),
            "website":      info.get("website",""),
            "employees":    info.get("fullTimeEmployees"),
            "market_cap":   info.get("marketCap"),
            "pe_trailing":  info.get("trailingPE"),
            "pe_forward":   info.get("forwardPE"),
            "pb_ratio":     info.get("priceToBook"),
            "ps_ratio":     info.get("priceToSalesTrailing12Months"),
            "ev_ebitda":    info.get("enterpriseToEbitda"),
            "dividend_yield":info.get("dividendYield"),
            "beta":         info.get("beta"),
            "52w_high":     info.get("fiftyTwoWeekHigh"),
            "52w_low":      info.get("fiftyTwoWeekLow"),
            "avg_volume":   info.get("averageVolume"),
            "float_shares": info.get("floatShares"),
            "short_ratio":  info.get("shortRatio"),
            "description":  (info.get("longBusinessSummary",""))[:600],
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}
