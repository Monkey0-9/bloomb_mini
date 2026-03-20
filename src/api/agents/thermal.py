from src.api.agents.base import BaseAgent
from src.preprocess.thermal import ThermalPipeline
from datetime import datetime, timezone
from typing import Any, Dict, List

class ThermalAgent(BaseAgent):
    """
    Agent specialized in industrial intelligence, tracking factory heat signals 
    and correlating them with factory output and equity tickers.
    """
    
    def __init__(self):
        super().__init__("ThermalIntelligence")
        self.pipeline = ThermalPipeline()
        self.status = "LIVE"
        self._last_signals = []

    async def get_state(self) -> Dict[str, Any]:
        """Provides industrial heat anomaly state."""
        self.last_sync = datetime.now(timezone.utc)
        # In production, the scan is periodic. We return the last cached signals.
        return {
            "status": self.status,
            "as_of": self.last_sync.isoformat() if self.last_sync else None,
            "active_industrial_anomalies": len(self._last_signals),
            "signals": [s.__dict__ for s in self._last_signals] if self._last_signals else []
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "RUN_SCAN":
            self._last_signals = await self.pipeline.run_scan()
            market_signals = self.pipeline.get_market_signals(self._last_signals)
            return {
                "count": len(self._last_signals),
                "market_signals": market_signals,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        elif task_type == "GET_FACILITY_INTEL":
            facility = params.get("facility")
            matches = [s for s in self._last_signals if s.facility_match == facility]
            return {"facility": facility, "signals": [s.__dict__ for s in matches]}

        return {"error": "Unknown task type"}
