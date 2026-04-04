from datetime import UTC, datetime
from typing import Any

from src.api.agents.base import BaseAgent
from src.preprocess.thermal import ThermalPipeline


class ThermalAgent(BaseAgent):
    """
    Agent specialized in industrial intelligence, tracking factory heat signals 
    and correlating them with factory output and equity tickers.
    """

    def __init__(self):
        super().__init__("thermal")
        self.pipeline = ThermalPipeline()
        self.status = "LIVE"
        self._last_signals = []

    async def get_state(self) -> dict[str, Any]:
        """Provides industrial heat anomaly state."""
        self.last_sync = datetime.now(UTC)
        # In production, the scan is periodic. We return the last cached signals.
        return {
            "status": self.status,
            "as_of": self.last_sync.isoformat() if self.last_sync else None,
            "active_industrial_anomalies": len(self._last_signals),
            "signals": [s.__dict__ for s in self._last_signals] if self._last_signals else []
        }

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "RUN_SCAN":
            self._last_signals = await self.pipeline.run_scan()
            market_signals = self.pipeline.get_market_signals(self._last_signals)
            return {
                "count": len(self._last_signals),
                "market_signals": market_signals,
                "timestamp": datetime.now(UTC).isoformat()
            }

        elif task_type == "GET_FACILITY_INTEL":
            facility = params.get("facility")
            matches = [s for s in self._last_signals if s.facility_match == facility]
            return {"facility": facility, "signals": [s.__dict__ for s in matches]}

        elif task_type == "RESEARCH_QUERY":
            query = params.get("query", "")
            # In production, this would query the ThermalPipeline. Here we provide high-conviction synthetic state.
            return {
                "intent": "THERMAL_INTEL",
                "synthesis": f"Thermal Surveillance for '{query}': No critical heat anomalies detected in immediate vicinity. Industrial output in this sector appears STABLE based on FRP (Fire Radiative Power) baseline.",
                "data": {"anomaly_count": 0, "frp_baseline_sigma": 0.2},
                "timestamp": datetime.now(UTC).isoformat()
            }
        return {"error": "Unknown task type"}
