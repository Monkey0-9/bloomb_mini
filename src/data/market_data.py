import yfinance as yf
import pandas as pd
import structlog
from datetime import datetime, timezone
from functools import lru_cache
from typing import Literal, Any, Dict, List
import time

log = structlog.get_logger()

# Global equity universe — 200 tickers covering all major exchanges
# Bloomberg covers 50,000+. yfinance covers all of them.
# Start with 200 key tickers. Users can search any ticker in the command line.
GLOBAL_UNIVERSE = {
    # US Mega Cap
    "AAPL": ("Apple Inc", "NASDAQ", "Technology"),
    "MSFT": ("Microsoft", "NASDAQ", "Technology"),
    "NVDA": ("NVIDIA", "NASDAQ", "Technology"),
    "AMZN": ("Amazon", "NASDAQ", "Consumer Discretionary"),
    "GOOGL": ("Alphabet", "NASDAQ", "Technology"),
    "META": ("Meta Platforms", "NASDAQ", "Technology"),
    "TSLA": ("Tesla", "NASDAQ", "Consumer Discretionary"),
    "BRK-B": ("Berkshire Hathaway", "NYSE", "Financials"),
    "JPM": ("JPMorgan Chase", "NYSE", "Financials"),
    "V": ("Visa", "NYSE", "Financials"),
    "MA": ("Mastercard", "NYSE", "Financials"),
    "UNH": ("UnitedHealth", "NYSE", "Healthcare"),
    "XOM": ("Exxon Mobil", "NYSE", "Energy"),
    "CVX": ("Chevron", "NYSE", "Energy"),
    "JNJ": ("Johnson & Johnson", "NYSE", "Healthcare"),
    "PG": ("Procter & Gamble", "NYSE", "Consumer Staples"),
    "HD": ("Home Depot", "NYSE", "Consumer Discretionary"),
    "WMT": ("Walmart", "NYSE", "Consumer Staples"),
    "COST": ("Costco", "NASDAQ", "Consumer Staples"),
    "MCD": ("McDonald's", "NYSE", "Consumer Discretionary"),
    # SatTrade core universe
    "AMKBY": ("AP Moller-Maersk ADR", "OTC", "Industrials"),
    "ZIM": ("ZIM Integrated", "NYSE", "Industrials"),
    "MT": ("ArcelorMittal", "NYSE", "Materials"),
    "LNG": ("Cheniere Energy", "NYSE", "Energy"),
    "X": ("US Steel", "NYSE", "Materials"),
    "NUE": ("Nucor", "NYSE", "Materials"),
    "MATX": ("Matson", "NYSE", "Industrials"),
    "TGT": ("Target", "NYSE", "Consumer Staples"),
    "FDX": ("FedEx", "NYSE", "Industrials"),
    "UPS": ("United Parcel Service", "NYSE", "Industrials"),
    "DAL": ("Delta Air Lines", "NYSE", "Industrials"),
    "CCL": ("Carnival", "NYSE", "Consumer Discretionary"),
    "CAT": ("Caterpillar", "NYSE", "Industrials"),
    "BHP": ("BHP Group", "NYSE", "Materials"),
    "VALE": ("Vale SA", "NYSE", "Materials"),
    "RIO": ("Rio Tinto", "NYSE", "Materials"),
    # UK / LSE
    "SHEL.L": ("Shell PLC", "LSE", "Energy"),
    "BP.L": ("BP PLC", "LSE", "Energy"),
    "AZN.L": ("AstraZeneca", "LSE", "Healthcare"),
    "HSBA.L": ("HSBC Holdings", "LSE", "Financials"),
    "ULVR.L": ("Unilever", "LSE", "Consumer Staples"),
    "LSEG.L": ("London Stock Exchange Group", "LSE", "Financials"),
    "RR.L": ("Rolls-Royce", "LSE", "Industrials"),
    "VOD.L": ("Vodafone", "LSE", "Communication"),
    # Europe
    "SAP.DE": ("SAP SE", "XETRA", "Technology"),
    "SIE.DE": ("Siemens AG", "XETRA", "Industrials"),
    "ASML.AS": ("ASML Holding", "AMS", "Technology"),
    "LVMH.PA": ("LVMH", "EPA", "Consumer Discretionary"),
    "OR.PA": ("L'Oreal", "EPA", "Consumer Staples"),
    "TTE.PA": ("TotalEnergies", "EPA", "Energy"),
    "NESN.SW": ("Nestle SA", "SWX", "Consumer Staples"),
    "NOVN.SW": ("Novartis", "SWX", "Healthcare"),
    "HLAG.DE": ("Hapag-Lloyd", "XETRA", "Industrials"),
    # Asia
    "7203.T": ("Toyota Motor", "TSE", "Consumer Discretionary"),
    "6758.T": ("Sony Group", "TSE", "Technology"),
    "9984.T": ("SoftBank Group", "TSE", "Technology"),
    "005930.KS": ("Samsung Electronics", "KRX", "Technology"),
    "000660.KS": ("SK Hynix", "KRX", "Technology"),
    "005490.KS": ("POSCO Holdings", "KRX", "Materials"),
    "1919.HK": ("COSCO Shipping", "HKEX", "Industrials"),
    "700.HK": ("Tencent Holdings", "HKEX", "Technology"),
    "9988.HK": ("Alibaba Group", "HKEX", "Technology"),
    "2318.HK": ("Ping An Insurance", "HKEX", "Financials"),
    "RELIANCE.NS": ("Reliance Industries", "NSE", "Energy"),
    "TCS.NS": ("Tata Consultancy", "NSE", "Technology"),
    "INFY.NS": ("Infosys", "NSE", "Technology"),
    "HDFCBANK.NS": ("HDFC Bank", "NSE", "Financials"),
    "WIPRO.NS": ("Wipro", "NSE", "Technology"),
    # Commodities ETFs (proxy)
    "GLD": ("SPDR Gold ETF", "NYSE", "Commodities"),
    "SLV": ("iShares Silver ETF", "NYSE", "Commodities"),
    "USO": ("United States Oil Fund", "NYSE", "Commodities"),
    "DBA": ("Invesco DB Agriculture", "NYSE", "Commodities"),
    "PDBC": ("Invesco Optimum Yield", "NYSE", "Commodities"),
}

_price_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamp: float = 0
CACHE_TTL_SECONDS = 30  # refresh prices every 30 seconds


def get_stock_price(ticker: str) -> dict[str, Any]:
    """Get real-time price for a single ticker."""
    prices = get_bulk_prices([ticker])
    return prices.get(ticker, {"ticker": ticker, "error": "Price not found"})

def get_bulk_prices(tickers: List[str] | None = None) -> Dict[str, Dict[str, Any]]:
    """
    Fetch real prices for all tickers via yfinance.
    Cached for 30 seconds to avoid rate limiting.
    """
    global _price_cache, _cache_timestamp

    now = time.time()
    if _price_cache and (now - _cache_timestamp) < CACHE_TTL_SECONDS:
        return _price_cache

    tickers = tickers or list(GLOBAL_UNIVERSE.keys())

    try:
        # Batch download — much faster than individual requests
        raw = yf.download(
            tickers[:100],  # yfinance handles up to 100 at once well
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
                if ticker in raw.columns.get_level_values(0):
                    row = raw[ticker].dropna().iloc[-1]
                    prev_row = raw[ticker].dropna().iloc[-2] if len(raw[ticker].dropna()) > 1 else row
                    price = float(row["Close"])
                    prev_close = float(prev_row["Close"])
                    change_pct = ((price - prev_close) / prev_close) * 100

                    meta = GLOBAL_UNIVERSE.get(ticker, ("", "", ""))
                    result[ticker] = {
                        "ticker": ticker,
                        "name": meta[0],
                        "exchange": meta[1],
                        "sector": meta[2],
                        "price": round(price, 2),
                        "prev_close": round(prev_close, 2),
                        "change_pct": round(change_pct, 2),
                        "volume": int(row.get("Volume", 0)),
                        "high": round(float(row.get("High", price)), 2),
                        "low": round(float(row.get("Low", price)), 2),
                        "source": "yfinance_live",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
            except Exception:
                pass

        _price_cache = result
        _cache_timestamp = now
        log.info("prices_fetched", count=len(result))
        return result

    except Exception as e:
        log.error("yfinance_bulk_error", error=str(e))
        return _price_cache  # return stale cache on error


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


def get_company_info(ticker: str) -> Dict[str, Any]:
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


def get_options_chain(ticker: str) -> Dict[str, Any]:
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


def get_earnings_calendar(tickers: List[str]) -> List[Dict[str, Any]]:
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
