from datetime import UTC, datetime
from typing import Any

from src.api.agents.base import BaseAgent
from src.data.economic_data import get_macro_dashboard


class MacroAgent(BaseAgent):
    """Agent for macroeconomic indicators, FRED data, and correlation analysis."""

    def __init__(self):
        super().__init__("macro")
        self.status = "LIVE"

    async def get_state(self) -> dict[str, Any]:
        self.last_sync = datetime.now(UTC)
        return await get_macro_dashboard()

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "GET_CORRELATION":
            # Simplified for BE-1
            return {
                "base": "Satellite Thermal FRP",
                "target": "US Industrial Production",
                "rho": 0.68
            }
        elif task_type == "RESEARCH_QUERY":
            query = params.get("query", "")
            dashboard = await get_macro_dashboard()
            # Find relevant indicators
            indicators = [i for i in dashboard.get("indicators", []) if query.lower() in i.get("name", "").lower()]
            return {
                "intent": "MACRO_INTEL",
                "synthesis": f"Macro Surveillance for '{query}': {len(indicators)} indicators match query. Current FRED VIX at {dashboard.get('vix', 'N/A')}. Regime: {'STABLE' if (dashboard.get('vix') or 0) < 20 else 'VOLATILE'}.",
                "data": {"vix": dashboard.get("vix"), "indicators": indicators[:3]},
                "timestamp": datetime.now(UTC).isoformat()
            }
        return {"error": "Unknown task type"}
