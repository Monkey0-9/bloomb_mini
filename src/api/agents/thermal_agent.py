import asyncio
from typing import Any, Dict
from src.api.agents.base import BaseAgent
from src.globe.thermal import fetch_firms_thermal

class ThermalAgent(BaseAgent):
    def __init__(self):
        super().__init__("thermal")

    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.log.info("processing_thermal_task", task_id=task.get("id"))
        # Use to_thread since fetch_firms_thermal is blocking
        anomalies = await asyncio.to_thread(fetch_firms_thermal)
        
        # Simple filtering logic if params provided
        ticker = task.get("ticker")
        if ticker:
            anomalies = [a for a in anomalies if ticker in a.tickers]
            
        return {
            "status": "success",
            "count": len(anomalies),
            "anomalies": [
                {"name": a.facility_name, "sigma": a.anomaly_vs_baseline, "tickers": a.tickers}
                for a in anomalies[:10] # limit for response size
            ]
        }
