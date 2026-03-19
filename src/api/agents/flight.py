import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone
from src.api.agents.base import BaseAgent
from src.maritime.flight_tracker import FlightTracker

log = logging.getLogger(__name__)

class FlightAgent(BaseAgent):
    """
    Agent specialized in aviation intelligence, cargo flight tracking, and logistics correlation.
    """
    
    def __init__(self, flight_tracker: FlightTracker = None):
        super().__init__("FlightIntelligence")
        self.flight_tracker = flight_tracker or FlightTracker()
        self.status = "LIVE"

    async def get_state(self) -> Dict[str, Any]:
        """Provides high-fidelity aviation telemetry state."""
        self.last_sync = datetime.now(timezone.utc)
        # In a real system, the scheduler triggers the global populate/update
        return {
            "flights": self.flight_tracker.to_geojson_feature_collection(),
            "intelligence": self.flight_tracker.get_market_intelligence(),
            "status": self.status
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "GET_FLIGHT":
            callsign = params.get("callsign")
            flight = self.flight_tracker.get_flight(callsign)
            return {"flight": flight}
        elif task_type == "LIST_OPERATOR_FLIGHTS":
            operator = params.get("operator", "")
            flights = [f for f in self.flight_tracker.get_all_flights() if operator.lower() in f.aircraft.operator.lower()]
            return {"flights": flights, "count": len(flights)}
        elif task_type == "POPULATE":
            count = params.get("count", 100)
            await self.flight_tracker.populate_global_fleet(count)
            return {"success": True, "count": count}
        return {"error": "Unknown task type"}
