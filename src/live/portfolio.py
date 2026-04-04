"""
Real-time portfolio and execution engine.
Connects to yfinance for live valuation of the paper portfolio.
"""
from datetime import UTC, datetime

import structlog

from src.live.market import get_prices

log = structlog.get_logger()

# Real initial portfolio based on the user's "Elite" universe
PAPER_PORTFOLIO = [
    {"ticker": "ZIM",  "quantity": 500,  "avg_cost": 16.40},
    {"ticker": "MT",   "quantity": 200,  "avg_cost": 24.10},
    {"ticker": "LNG",  "quantity": 100,  "avg_cost": 152.30},
    {"ticker": "FDX",  "quantity": 50,   "avg_cost": 248.00},
    {"ticker": "SBLK", "quantity": 300,  "avg_cost": 17.80},
    {"ticker": "CLF",  "quantity": 200,  "avg_cost": 14.60},
]

def get_portfolio_status() -> dict:
    """Calculate real-time portfolio value and P&L using live quotes."""
    tickers = [p["ticker"] for p in PAPER_PORTFOLIO]
    quotes = get_prices(tickers)

    positions = []
    total_mv = 0.0
    total_cost = 0.0

    for p in PAPER_PORTFOLIO:
        ticker = p["ticker"]
        q = quotes.get(ticker)
        curr_price = q.price if q else p["avg_cost"]

        mv = curr_price * p["quantity"]
        cost = p["avg_cost"] * p["quantity"]
        pnl = mv - cost
        pnl_pct = (pnl / cost * 100) if cost > 0 else 0

        total_mv += mv
        total_cost += cost

        positions.append({
            "ticker": ticker,
            "quantity": p["quantity"],
            "avgCost": p["avg_cost"],
            "currentPrice": curr_price,
            "mktValue": round(mv, 2),
            "pnl": round(pnl, 2),
            "pnlPct": round(pnl_pct, 2),
            "sector": q.sector if q else "General",
            "as_of": q.ts if q else datetime.now(UTC).isoformat()
        })

    total_pnl = total_mv - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

    return {
        "positions": positions,
        "total_mkt_value": round(total_mv, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "currency": "USD",
        "ts": datetime.now(UTC).isoformat()
    }
