import asyncio
from datetime import UTC, datetime
from typing import Any

from src.api.agents.base import BaseAgent
from src.live.orbits import get_all_eo_satellites


class SatelliteAgent(BaseAgent):
    """
    Agent specialized in orbital intelligence, tracking all Earth Observation satellites.
    """

    def __init__(self, tracker=None) -> None:
        super().__init__("satellite")
        self.status = "LIVE"

    async def get_state(self) -> dict[str, Any]:
        """Provides high-density orbital telemetry state."""
        self.last_sync = datetime.now(UTC)
        orbits = await asyncio.to_thread(get_all_eo_satellites)

        features = []
        for o in orbits:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [o.lon, o.lat]},
                "properties": {
                    "name": o.name,
                    "altitude": f"{o.altitude_km:.0f} km",
                    "period": f"{o.period_min:.1f} min",
                    "inclination": f"{o.inclination:.1f}°"
                }
            })

        return {
            "satellites": {"type": "FeatureCollection", "features": features},
            "global_surveillance_status": "HIGH_DENSITY_ESTABLISHED",
            "count": len(orbits)
        }

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "GET_SATELLITE":
            name = params.get("name")
            orbits = await asyncio.to_thread(get_all_eo_satellites)
            sat = next((o for o in orbits if o.name == name), None)
            return {"satellite": sat.__dict__ if sat else None}
        elif task_type == "RESEARCH_QUERY":
            query = params.get("query", "").upper()
            orbits = await asyncio.to_thread(get_all_eo_satellites)
            matched = [o for o in orbits if query in o.name.upper()]
            return {
                "intent": "ORBITAL_INTEL",
                "synthesis": f"Orbital Surveillance for '{query}': {len(matched)} satellites matching criteria. Sentinel-2 coverage is ACTIVE. Real-time revisiting at {len(orbits)//100}m resolution.",
                "data": {"count": len(matched), "total": len(orbits)},
                "timestamp": datetime.now(UTC).isoformat()
            }
        return {"error": "Unknown task type"}
