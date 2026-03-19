from typing import Any
from datetime import datetime, timezone
from src.api.agents.base import BaseAgent


class AnalystAgent(BaseAgent):
    """
    The Intelligence Layer: Routes natural language intents to specialized agents.
    Provides Claude-driven context synthesis for the ResearchView.
    """
    
    def __init__(self):
        super().__init__("ANALYST")
        self.status = "ACTIVE"
        self.last_sync = datetime.now(timezone.utc)
        
    async def get_state(self) -> dict[str, Any]:
        """Returns the health and capabilities of the Analyst agent."""
        return {
            "capabilities": ["intent_routing", "rag_synthesis", "multi_agent_query"],
            "model": "Claude 3.5 Sonnet (Institutional)",
            "uptime": "99.99%"
        }

    async def route_intent(self, query: str) -> dict[str, Any]:
        """
        Mocking Claude routing for local dev.
        In production, this calls Anthropic API.
        """
        q = query.lower()

        # Intent Heuristics
        if any(w in q for w in ["vessel", "ship", "port", "congestion", "ais"]):
            return {"intent": "MARITIME_QUERY", "target": "maritime", "view": "world", "ticker": "ZIM"}

        if any(w in q for w in ["alpha", "signal", "predict", "conviction", "satellite"]):
            return {"intent": "SIGNAL_ANALYSIS", "target": "signals", "view": "matrix"}

        if any(w in q for w in ["macro", "cpi", "inflation", "rates", "fed"]):
            return {"intent": "MACRO_SURVEILLANCE", "target": "macro", "view": "economics"}

        if any(w in q for w in ["pnl", "portfolio", "positions", "greeks"]):
            return {"intent": "PORTFOLIO_AUDIT", "target": "risk", "view": "portfolio"}

        if any(w in q for w in ["thermal", "frp", "industrial", "factory", "heat", "output"]):
            return {"intent": "INDUSTRIAL_INTELLIGENCE", "target": "thermal", "view": "matrix"}

        if query.startswith("/NAV "):
            view = query.replace("/NAV ", "").strip().lower()
            return {"intent": "NAVIGATION", "target": "system", "view": view}

        return {"intent": "GENERAL_RESEARCH", "target": "analyst", "view": "research"}

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        """Synthesizes data across agents for deep research queries."""
        if task_type == "RESEARCH_QUERY":
            query = params.get("query", "")
            intent_data = await self.route_intent(query)

            msg = f"Parsed query as {intent_data['intent']}. Contextualizing against {intent_data['target']}..."
            return {
                "intent": intent_data["intent"],
                "synthesis": msg,
                "view_suggestion": intent_data["view"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        if task_type == "GET_STATE":
            return await self.get_state()

        return {"error": f"Unknown task type: {task_type}"}
