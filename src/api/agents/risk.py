from src.api.agents.base import BaseAgent
from src.risk.engine import get_risk_engine, PortfolioState
from datetime import datetime, timezone
from typing import Any, Dict, List

class RiskAgent(BaseAgent):
    """
    Agent specialized in portfolio risk, VaR calculation, and institutional pre-trade audits.
    """
    
    def __init__(self):
        super().__init__("RiskManagement")
        self.risk_engine = get_risk_engine()
        self.status = "LIVE"

    async def get_state(self) -> Dict[str, Any]:
        """Provides high-fidelity risk telemetry state."""
        self.last_sync = datetime.now(timezone.utc)
        
        # In a production environment, this data is pulled from the Ledger/Accounting service
        # For the terminal demo, we provide high-conviction synthetic state
        return {
            "entity": "SatTrade_Master_Fund",
            "equity": 50_482_100.0,
            "gross_exposure_pct": 0.65,
            "net_exposure_pct": 0.12,
            "var_99_1d_pct": 0.0082,
            "kill_switch_active": self.risk_engine._kill_switch,
            "status": self.status,
            "as_of": self.last_sync.isoformat()
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "RUN_AUDIT":
            order = params.get("order", {})
            # Construct synthetic portfolio state for the audit if not provided
            portfolio_data = params.get("portfolio")
            if portfolio_data:
                portfolio = PortfolioState(**portfolio_data)
            else:
                portfolio = PortfolioState(
                    equity=50_000_000,
                    gross_exposure=32_000_000,
                    net_exposure=6_000_000,
                    positions={"AAPL": 5_000_000, "TSLA": 2_000_000},
                    sector_exposure={"TECH": 7_000_000}
                )
            
            results = self.risk_engine.check_gates(order, portfolio)
            passed = all(r.passed for r in results)
            
            return {
                "results": [
                    {
                        "gate": r.gate_name,
                        "passed": r.passed,
                        "value": r.value,
                        "threshold": r.threshold,
                        "message": r.message
                    } for r in results
                ],
                "passed": passed,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        elif task_type == "SET_KILL_SWITCH":
            active = params.get("active", False)
            witness = params.get("witness_id", "SYSTEM_AUTO_HALT")
            self.risk_engine.set_kill_switch(active, witness)
            return {"success": True, "active": active}

        return {"error": "Unknown task type"}
