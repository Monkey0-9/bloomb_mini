import asyncio
from datetime import UTC, datetime
from typing import Any

from src.api.agents.base import BaseAgent
from src.live.aircraft import fetch_aircraft, to_geojson


class FlightAgent(BaseAgent):
    """
    Agent specialized in aviation intelligence, cargo flight tracking, and logistics correlation.
    """

    def __init__(self, flight_tracker=None):
        super().__init__("FlightIntelligence")
        self.status = "LIVE"

    async def get_state(self) -> dict[str, Any]:
        """Provides high-fidelity aviation telemetry state."""
        self.last_sync = datetime.now(UTC)
        aircraft = await asyncio.to_thread(fetch_aircraft)
        geojson = to_geojson(aircraft)

        return {
            "flights": geojson,
            "status": self.status,
            "count": len(aircraft)
        }

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "GET_FLIGHT":
            icao24 = params.get("icao24")
            aircraft = await asyncio.to_thread(fetch_aircraft)
            flight = next((a for a in aircraft if a.icao24 == icao24), None)
            return {"flight": flight.__dict__ if flight else None}
        elif task_type == "LIST_CARGO":
            aircraft = await asyncio.to_thread(fetch_aircraft, ["CARGO"])
            return {"flights": [a.__dict__ for a in aircraft], "count": len(aircraft)}
        return {"error": "Unknown task type"}
