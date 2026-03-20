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

@dataclass
class TickerPrice:
    ticker: str
    price: float
    currency: str
    timestamp: datetime

def fetch_market_prices(tickers: list[str] | None = None) -> dict[str, TickerPrice]:
    """
    Fetch bulk prices for the global universe.
    Using yfinance fast_info for efficient data retrieval.
    """
    if tickers is None:
        tickers = list(GLOBAL_UNIVERSE.keys())
    
    prices = {}
    try:
        # Fetching bulk data in one go for efficiency
        group = yf.Tickers(" ".join(tickers))
        for symbol in tickers:
            ticker_obj = group.tickers[symbol]
            try:
                # Use fast_info if available, or currentPrice from info
                info = ticker_obj.info
                price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
                prices[symbol] = TickerPrice(
                    ticker=symbol,
                    price=price,
                    currency=info.get("currency", "USD"),
                    timestamp=datetime.now()
                )
            except Exception as inner_e:
                log.warning("fetch_ticker_failed", ticker=symbol, error=str(inner_e))
        return prices
    except Exception as e:
        log.error("fetch_market_failed", error=str(e))
        return {}

if __name__ == "__main__":
    market_data = fetch_market_prices()
    for symbol, data in market_data.items():
        print(f"{symbol}: ${data.price} {data.currency}")
