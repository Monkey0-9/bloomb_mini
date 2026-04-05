"""
SatTrade Weather Intelligence — Open-Meteo Fusion.
Correlates global weather patterns with supply chain disruptions.
"""
from datetime import UTC, datetime
from typing import Any, cast

import httpx
import structlog
from .base import SeedProvider

log = structlog.get_logger()

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

class WeatherProvider(SeedProvider):
    """
    Open-Meteo Weather Seed Provider.
    Inspired by GodMode's Provider pattern.
    """
    
    async def fetch(self, lat: float, lon: float) -> dict[str, Any]:
        """Fetch current weather for a specific coordinate."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    OPEN_METEO_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current_weather": "true",
                        "windspeed_unit": "kn",
                    }
                )
                if resp.status_code == 200:
                    data = resp.json().get("current_weather", {})
                    return cast(dict[str, Any], data)
        except Exception as e:
            log.error("weather_fetch_failed", error=str(e))
        return {}

    def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert raw Open-Meteo data into a risk score."""
        wind_speed = data.get("windspeed", 0)
        risk_level = "LOW"
        if wind_speed > 35: risk_level = "CRITICAL"
        elif wind_speed > 25: risk_level = "HIGH"

        return {
            "wind_speed_knots": wind_speed,
            "condition_code": data.get("weathercode", 0),
            "risk_level": risk_level,
            "timestamp": datetime.now(UTC).isoformat()
        }

async def get_marine_weather(lat: float, lon: float) -> dict[str, Any]:
    """Helper for backward compatibility."""
    provider = WeatherProvider()
    data = await provider.fetch(lat, lon)
    return provider.process(data)

