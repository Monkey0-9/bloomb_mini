import httpx
import structlog
from .base import SeedProvider

log = structlog.get_logger()

class TopoProvider(SeedProvider):
    """
    Open Topo Data Provider (Ocean Depth & Elevation).
    Used for simulating chokepoint navigation for VLCC tankers.
    """
    
    async def fetch(self, lat: float, lon: float) -> dict:
        """Fetch ocean depth/elevation for a specific coordinate."""
        try:
            # GEBCO 2020 dataset for ocean depth
            url = f"https://api.opentopodata.org/v1/gebco2020?locations={lat},{lon}"
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    return results[0] if results else {}
        except Exception as e:
            log.error("topo_fetch_failed", error=str(e))
        return {}

    def process(self, data: dict) -> dict:
        """Process elevation into depth and risk for deep-draft vessels."""
        elevation = data.get("elevation", 0.0)
        # Deep draft vessels (like VLCCs) need at least 20m depth
        # Elevation is negative for ocean depth
        depth = -elevation if elevation < 0 else 0
        risk_level = "LOW"
        if depth < 20 and depth > 0:
            risk_level = "HIGH" # Risk of grounding
        
        return {
            "depth_meters": depth,
            "risk_level": risk_level,
            "is_land": elevation >= 0
        }

async def get_ocean_depth(lat: float, lon: float) -> dict:
    """Helper for the swarm simulation."""
    provider = TopoProvider()
    data = await provider.fetch(lat, lon)
    return provider.process(data)
