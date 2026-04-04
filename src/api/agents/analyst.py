import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from src.api.agents.base import BaseAgent
from src.api.agents.research_agent import ResearchAgent

logger = logging.getLogger(__name__)

# Institutional Ticker Mapping for common names
COMMON_TICKER_MAP = {
    "apple": "AAPL", "tesla": "TSLA", "microsoft": "MSFT", "nvidia": "NVDA",
    "google": "GOOGL", "amazon": "AMZN", "meta": "META", "netflix": "NFLX",
    "exxon": "XOM", "chevron": "CVX", "zim": "ZIM", "maersk": "MAERSK",
    "fedex": "FDX", "ups": "UPS", "boeing": "BA", "airbus": "AIR.PA",
}

class AnalystAgent(BaseAgent):
    """
    The High-Density Intelligence Layer: Synthesizes multi-signal alpha 
    into institutional-grade research reports.
    Exceeds Bloomberg by fusing physical anomalies with market sentiment.
    """

    def __init__(self):
        super().__init__("analyst")
        self.status = "ACTIVE"
        self.research = ResearchAgent()
        self.last_sync = datetime.now(UTC)

    async def get_state(self) -> dict[str, Any]:
        return {
            "capabilities": ["cross_asset_synthesis", "physical_alpha_mapping", "institutional_voice"],
            "model": "SatTrade-V1-Ensemble",
            "as_of": datetime.now(UTC).isoformat()
        }

    async def _synthesize_institutional_report(self, ticker: str) -> dict[str, Any]:
        """Perform real-time deep synthesis for any ticker."""
        ticker = ticker.upper().strip()
        logger.info("analyst.synthesize_report", ticker=ticker)

        try:
            # 1. Get raw market context (with timeout-friendly fallback)
            t = yf.Ticker(ticker)
            info = await asyncio.to_thread(lambda: t.info)
            if not info or "longName" not in info:
                # Handle cases where yfinance fails or returns empty
                logger.warning("analyst.yfinance_empty", ticker=ticker)
                # We can still proceed if alternative research works

            price = info.get("currentPrice", info.get("regularMarketPrice", 0))

            # 2. Get high-fidelity Satellite/Alternative research
            research = await self.research.process_task("RESEARCH_QUERY", {"query": ticker})

            # 3. Build the "Bloomberg-Moat" Synthesis
            long_name = info.get('longName', ticker)

            synthesis = (
                f"INSTITUTIONAL OVERVIEW: {long_name} ( {ticker} ) | "
                f"Market Price: ${price:.2f} | Sentiment: {research.get('sentiment', 'NEUTRAL')} | Alpha Score: {research.get('score', 50)}/100. "
                f"\n\nSTRATEGIC ANALYSIS: {research.get('synthesis', 'No physical anomalies detected.')} "
                f"\n\nREGIME CONTEXT: Engine is in {research.get('data_points', {}).get('regime', 'standard')} mode. "
                f"Confidence: {research.get('confidence_score', 0.5)*100:.1f}% | Signal Density: {research.get('data_points', {}).get('freshness', 'LOW')}"
            )

            return {
                "intent": "STOCK_ANALYSIS",
                "synthesis": synthesis,
                "view_suggestion": "research",
                "ticker": ticker,
                "data": {
                    "price": price,
                    "research": research,
                    "info": {
                        "name": long_name,
                        "sector": info.get("sector", "N/A"),
                        "industry": info.get("industry", "N/A"),
                        "summary": (info.get("longBusinessSummary", "")[:300] + "...") if info.get("longBusinessSummary") else "No business summary available."
                    }
                }
            }
        except Exception as e:
            logger.error(f"analyst.report_failed for {ticker}: {str(e)}")
            return {
                "intent": "ERROR",
                "synthesis": f"Institutional analysis for {ticker} encountered a signal disruption: {str(e)}",
                "view_suggestion": "research"
            }

    async def route_intent(self, query: str) -> dict[str, Any]:
        q = query.lower().strip()
        parts = q.split()

        # 1. Direct Ticker Mapping
        ticker = None
        for p in parts:
            if p in COMMON_TICKER_MAP:
                ticker = COMMON_TICKER_MAP[p]
                break

        # 2. Heuristic: Look for uppercase symbols or longer words
        if not ticker:
            for p in query.split():
                if len(p) >= 2 and p.isalpha() and p.isupper():
                    ticker = p
                    break

        # 3. Fallback: First word >= 2 chars
        if not ticker:
            for p in parts:
                if len(p) >= 2 and p.isalpha() and p not in ["analyze", "research", "what", "is", "the"]:
                    ticker = p.upper()
                    break

        if ticker:
            return await self._synthesize_institutional_report(ticker)

        return {
            "intent": "GENERAL_RESEARCH",
            "synthesis": "Request acknowledged. Please specify a ticker symbol or company name (e.g., 'TSLA' or 'Apple').",
            "target": "analyst",
            "view": "research"
        }

    async def stream_research(self, query: str):
        """Streams synthesis results back to the frontend."""
        # For now, we simulate streaming by yielding chunks of the already synthesized report
        # In a real production system, this would call the LLM with stream=True
        report = await self.route_intent(query)
        synthesis = report.get("synthesis", "Processing complex multi-agent intelligence...")

        # Split into small chunks to simulate real-time thinking
        words = synthesis.split(' ')
        for i in range(0, len(words), 3):
            chunk = ' '.join(words[i:i+3]) + ' '
            yield chunk
            await asyncio.sleep(0.05)

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "RESEARCH_QUERY":
            query = params.get("query", "")
            intent_data = await self.route_intent(query)
            return {
                "intent": intent_data["intent"],
                "synthesis": intent_data.get("synthesis", "Routing query..."),
                "view_suggestion": intent_data.get("view_suggestion", "research"),
                "ticker": intent_data.get("ticker"),
                "data": intent_data.get("data"),
                "timestamp": datetime.now(UTC).isoformat()
            }
        return {"error": f"Unknown task type: {task_type}"}
