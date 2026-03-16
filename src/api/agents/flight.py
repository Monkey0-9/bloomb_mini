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
        await self.flight_tracker.update_live_positions()
        return {
            "flights": self.flight_tracker.to_geojson_feature_collection(),
            "global_cargo_status": "MONITORING_HUBS"
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "GET_FLIGHT":
            callsign = params.get("callsign")
            flight = self.flight_tracker.get_flight(callsign)
            return {"flight": flight}
        elif task_type == "LIST_OPERATOR_FLIGHTS":
            operator = params.get("operator")
            flights = [f for f in self.flight_tracker.get_all_flights() if operator.lower() in f.aircraft.operator.lower()]
            return {"flights": flights, "count": len(flights)}
        return {"error": "Unknown task type"}
