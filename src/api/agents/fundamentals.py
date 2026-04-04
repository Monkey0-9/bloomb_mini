import logging
from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from src.api.agents.base import BaseAgent

log = logging.getLogger(__name__)

class FundamentalAgent(BaseAgent):
    """
    The Institutional Data Layer: 10-yr Financials & Segment Analysis.
    Powered by yfinance.
    """

    def __init__(self):
        super().__init__("FUNDAMENTALS")
        self.status = "ACTIVE"
        self.last_sync = datetime.now(UTC)

    async def get_state(self) -> dict[str, Any]:
        return {
            "coverage": "GLOBAL_EQUITIES",
            "latency": "async_fetching",
            "historical_depth": "MAX"
        }

    async def get_company_profile(self, ticker: str) -> dict[str, Any]:
        """Provides FA (Financial Analysis) data equivalent to Bloomberg."""
        try:
            log.info("fetching_fundamentals", extra={"ticker": ticker})
            t = yf.Ticker(ticker)
            info = t.info

            # Transform yfinance info to premium profile format
            return {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "market_cap": f"{info.get('marketCap', 0) / 1e9:.1f}B" if info.get('marketCap') else "N/A",
                "pe_ratio": round(info.get("forwardPE", 0), 2) if info.get("forwardPE") else "N/A",
                "dividend_yield": f"{info.get('dividendYield', 0) * 100:.1f}%" if info.get('dividendYield') else "0.0%",
                "segments": [
                     {"name": "Sector", "value": info.get("sector", "N/A")},
                     {"name": "Industry", "value": info.get("industry", "N/A")},
                     {"name": "Employees", "value": f"{info.get('fullTimeEmployees', 0):,}"}
                ],
                "consensus": info.get("recommendationKey", "HOLD").upper(),
                "target_price": info.get("targetMeanPrice", "N/A"),
                "description": info.get("longBusinessSummary", "")[:500] + "..."
            }
        except Exception as e:
            log.error("fundamental_fetch_error", extra={"ticker": ticker, "error": str(e)})
            return {"ticker": ticker, "error": "Could not fetch institutional data"}

    async def get_earnings_calendar(self, tickers: list[str]) -> dict[str, Any]:
        """Fetch upcoming earnings and overlay with satellite sentiment."""
        from src.data.market_data import get_earnings_calendar
        from src.signals.composite_score import CompositeScorer

        raw_calendar = get_earnings_calendar(tickers)
        scorer = CompositeScorer()

        enriched = []
        for e in raw_calendar:
            ticker = e["ticker"]
            score_res = await scorer.score(ticker)

            enriched.append({
                **e,
                "satellite_signal": score_res["direction"].replace("LONG", "BULLISH").replace("SHORT", "BEARISH"),
                "satellite_reason": score_res["headline"],
                "alpha_opportunity": abs(score_res["final_score"]) > 0.4
            })

        return {"earnings": enriched}

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "GET_FUNDAMENTALS":
            ticker = params.get("ticker", "AAPL")
            return await self.get_company_profile(ticker)
        elif task_type == "GET_EARNINGS":
            tickers = params.get("tickers", ["AAPL", "TSLA", "NVDA", "AMZN", "MSFT", "META", "GOOGL", "ZIM", "MT"])
            return await self.get_earnings_calendar(tickers)
        elif task_type == "RESEARCH_QUERY":
            ticker = params.get("query", "AAPL").upper()
            profile = await self.get_company_profile(ticker)
            return {
                "intent": "FUNDAMENTAL_INTEL",
                "synthesis": f"Institutional Profile for '{ticker}': Market Cap {profile.get('market_cap')}. Consensus: {profile.get('consensus')}. Description: {profile.get('description', '')[:100]}...",
                "data": profile,
                "timestamp": datetime.now(UTC).isoformat()
            }
        return {"error": "Unknown task type"}
