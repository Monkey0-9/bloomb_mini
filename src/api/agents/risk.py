from src.api.agents.base import BaseAgent
from src.risk.engine import RiskEngine
from datetime import datetime, timezone
from typing import Any, Dict

class RiskAgent(BaseAgent):
    """Agent specialized in portfolio risk, VaR calculation, and pre-trade audits."""
    
    def __init__(self, risk_engine: RiskEngine = None):
        super().__init__("RiskManagement")
        self.risk_engine = risk_engine or RiskEngine()
        self.status = "LIVE"

    async def get_state(self) -> Dict[str, Any]:
        self.last_sync = datetime.now(timezone.utc)
        # Placeholder for real state until BE-4
        return {
            "equity": 50_482_100.0,
            "gross_exposure_pct": 0.25,
            "var_99_1d_pct": 0.0082,
            "kill_switch_active": False
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "RUN_AUDIT":
            order = params.get("order")
            portfolio = params.get("portfolio")
            results = self.risk_engine.run_pre_trade_audit(order, portfolio)
            return {"results": results, "passed": all(r.passed for r in results)}
        return {"error": "Unknown task type"}
