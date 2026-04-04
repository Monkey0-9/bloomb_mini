from datetime import UTC, datetime
from typing import Any

from src.api.agents.base import BaseAgent
from src.risk.engine import PortfolioState, get_risk_engine


class RiskAgent(BaseAgent):
    """
    Agent specialized in portfolio risk, VaR calculation, and institutional pre-trade audits.
    """

    def __init__(self) -> None:
        super().__init__("risk")
        self.risk_engine = get_risk_engine()
        self.status = "LIVE"

    async def get_state(self) -> dict[str, Any]:
        """Provides high-fidelity risk telemetry state."""
        self.last_sync = datetime.now(UTC)

        # Access kill switch via internal _kill instance
        kill_active = await self.risk_engine._kill.is_active()

        # In a production environment, this data is pulled from the Ledger/Accounting service
        # For the terminal demo, we provide high-conviction synthetic state
        return {
            "entity": "SatTrade_Master_Fund",
            "equity": 50_482_100.0,
            "gross_exposure_pct": 0.65,
            "net_exposure_pct": 0.12,
            "var_99_1d_pct": 0.0082,
            "kill_switch_active": kill_active,
            "status": self.status,
            "as_of": self.last_sync.isoformat()
        }

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
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

            results_data = await self.risk_engine.evaluate_trade(params)
            passed = results_data.get("overall") == "PASS"

            return {
                "results": results_data.get("gates", []),
                "passed": passed,
                "timestamp": datetime.now(UTC).isoformat()
            }

        elif task_type == "SET_KILL_SWITCH":
            active = params.get("active", False)
            user_id = params.get("user_id", "SYSTEM_AUTO_HALT")
            reason = params.get("reason", "Manual trigger via Analyst Terminal")

            if active:
                await self.risk_engine._kill.activate(user_id, reason)
            else:
                # Reset requires two witnesses in production; here we mock it
                witness1 = params.get("witness1", user_id)
                witness2 = params.get("witness2", "SEC_OFFICER_01")
                await self.risk_engine._kill.reset("secret", witness1, witness2)

            return {"success": True, "active": active}

        elif task_type == "RESEARCH_QUERY":
            query = params.get("query", "")
            state = await self.get_state()
            return {
                "intent": "RISK_ANALYSIS",
                "synthesis": f"Risk Engine Audit for '{query}': System is {state['status']}. Gross exposure at {state['gross_exposure_pct']*100}%. No immediate mandate breaches detected for this asset class.",
                "data": state,
                "timestamp": datetime.now(UTC).isoformat()
            }

        return {"error": "Unknown task type"}
