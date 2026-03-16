from src.api.agents.base import BaseAgent
from src.maritime.vessel_tracker import VesselTracker
from datetime import datetime, timezone
from typing import Any, Dict

class MaritimeAgent(BaseAgent):
    """Agent specialized in maritime intelligence, AIS tracking, and dark fleet detection."""
    
    def __init__(self, vessel_tracker: VesselTracker = None):
        super().__init__("MaritimeIntelligence")
        self.vessel_tracker = vessel_tracker or VesselTracker()
        self.status = "LIVE"

    async def get_state(self) -> Dict[str, Any]:
        self.last_sync = datetime.now(timezone.utc)
        return {
            "vessels": self.vessel_tracker.to_geojson_feature_collection(),
            "dark_fleet": self.vessel_tracker.detect_dark_vessels()
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "DETECT_ANOMALIES":
            anomalies = self.vessel_tracker.detect_dark_vessels()
            return {"anomalies": anomalies, "count": len(anomalies)}
        elif task_type == "GET_VESSEL":
            mmsi = params.get("mmsi")
            vessel = self.vessel_tracker.get_vessel_by_mmsi(mmsi)
            return {"vessel": vessel}
        return {"error": "Unknown task type"}
