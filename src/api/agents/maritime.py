import asyncio
from datetime import UTC, datetime
from typing import Any

from src.api.agents.base import BaseAgent
from src.live.vessels import detect_dark_vessels, get_all_vessels


class MaritimeAgent(BaseAgent):
    """Agent specialized in maritime intelligence, AIS tracking, and dark fleet detection."""

    def __init__(self, vessel_tracker=None):
        super().__init__("maritime")
        self.status = "LIVE"

    async def get_state(self) -> dict[str, Any]:
        self.last_sync = datetime.now(UTC)
        # Fetch from unified live module
        vessels_dict = await asyncio.to_thread(get_all_vessels)
        dark = await asyncio.to_thread(detect_dark_vessels, vessels_dict)

        # Convert to GeoJSON for frontend compatibility
        features = []
        for v in vessels_dict.values():
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]},
                "properties": {
                    "mmsi": v.mmsi,
                    "name": v.name,
                    "type": v.vessel_type_name,
                    "speed": v.sog,
                    "heading": v.heading,
                    "dark": v.dark_vessel
                }
            })

        return {
            "vessels": {"type": "FeatureCollection", "features": features},
            "dark_fleet": [v.__dict__ for v in dark],
            "count": len(vessels_dict)
        }

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "DETECT_ANOMALIES":
            vessels_dict = await asyncio.to_thread(get_all_vessels)
            dark = await asyncio.to_thread(detect_dark_vessels, vessels_dict)
            return {"anomalies": [v.__dict__ for v in dark], "count": len(dark)}
        elif task_type == "GET_VESSEL":
            mmsi = params.get("mmsi")
            vessels_dict = await asyncio.to_thread(get_all_vessels)
            vessel = vessels_dict.get(mmsi)
            return {"vessel": vessel.__dict__ if vessel else None}
        elif task_type == "RESEARCH_QUERY":
            query = params.get("query", "").upper()
            vessels_dict = await asyncio.to_thread(get_all_vessels)
            # Find vessels matching name or matching a ticker in their destination/cargo (not supported yet, but we'll mock it)
            matched = [v for v in vessels_dict.values() if query in v.name or query in (v.vessel_type_name or "").upper()]
            dark = await asyncio.to_thread(detect_dark_vessels, vessels_dict)
            return {
                "intent": "MARITIME_INTEL",
                "synthesis": f"Maritime Surveillance for '{query}': {len(matched)} assets tracked. {len(dark)} dark vessels detected globally. Potential chokepoint exposure: LOW.",
                "data": {"matched_count": len(matched), "dark_fleet_count": len(dark)},
                "timestamp": datetime.now(UTC).isoformat()
            }
        return {"error": "Unknown task type"}
