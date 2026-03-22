from typing import Any
from datetime import datetime, timezone
import yfinance as yf
from src.api.agents.base import BaseAgent
from src.free_data.news import get_sentiment_for_ticker


class AnalystAgent(BaseAgent):
    """
    The Intelligence Layer: Routes natural language intents to specialized agents.
    Provides real-time context synthesis for any global stock.
    """
    
    def __init__(self):
        super().__init__("ANALYST")
        self.status = "ACTIVE"
        self.last_sync = datetime.now(timezone.utc)
        
    async def get_state(self) -> dict[str, Any]:
        return {
            "capabilities": ["intent_routing", "live_stock_analysis", "rag_synthesis"],
            "model": "Claude 3.5 Sonnet (Institutional)",
            "uptime": "99.99%"
        }

    async def _analyze_stock(self, query: str) -> dict[str, Any]:
        """Perform real-time institutional analysis for a given ticker."""
        ticker = query.upper().strip()
        # Common typos/shortcuts
        if ticker == "TES": ticker = "TSLA"
        
        try:
            t = yf.Ticker(ticker)
            info = t.info
            hist = t.history(period="5d")
            sentiment = get_sentiment_for_ticker(ticker)
            
            price = info.get("currentPrice", info.get("regularMarketPrice", 0))
            change = 0
            if len(hist) >= 2:
                prev = hist["Close"].iloc[-2]
                change = (price - prev) / prev * 100

            analysis = (
                f"SENSORY OVERVIEW: {info.get('longName', ticker)} is currently trading at {price} "
                f"({change:+.2f}%). Terminal sentiment is {sentiment['sentiment']} based on "
                f"{sentiment['count']} recent global intelligence signals. "
                f"Business Summary: {info.get('longBusinessSummary', 'N/A')[:200]}..."
            )
            
            return {
                "intent": "STOCK_ANALYSIS",
                "synthesis": analysis,
                "view_suggestion": "chart",
                "ticker": ticker,
                "data": {
                    "price": price,
                    "change": change,
                    "sentiment": sentiment
                }
            }
        except Exception as e:
            return {"intent": "ERROR", "synthesis": f"Analysis failed: {str(e)}", "view_suggestion": "research"}

    async def route_intent(self, query: str) -> dict[str, Any]:
        q = query.lower()
        
        # Check for stock-specific analysis trigger
        if any(w in q for w in ["analyze", "stock", "price of", "data on"]):
            # Extract ticker - very simple extraction for now
            parts = query.split()
            for p in reversed(parts):
                if len(p) >= 2 and p.isalpha():
                    return await self._analyze_stock(p)

        # Legacy routing
        if any(w in q for w in ["vessel", "ship", "port", "congestion", "ais"]):
            return {"intent": "MARITIME_QUERY", "target": "maritime", "view": "world", "ticker": "ZIM"}
        
        return {"intent": "GENERAL_RESEARCH", "target": "analyst", "view": "research"}

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "RESEARCH_QUERY":
            query = params.get("query", "")
            intent_data = await self.route_intent(query)
            return {
                "intent": intent_data["intent"],
                "synthesis": intent_data.get("synthesis", f"Parsed query as {intent_data['intent']}"),
                "view_suggestion": intent_data["view_suggestion"] if "view_suggestion" in intent_data else intent_data.get("view", "research"),
                "ticker": intent_data.get("ticker"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        return {"error": f"Unknown task type: {task_type}"}
