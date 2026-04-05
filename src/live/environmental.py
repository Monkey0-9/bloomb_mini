import asyncio
from typing import Any

import httpx
import structlog

log = structlog.get_logger()

class EnvironmentalMonitor:
    """
    Fetches real-time environmental seeds from Public APIs.
    Sources: Open-Meteo (Weather), OpenAQ (Air Quality).
    Zero Key. 100% Free.
    """

    @staticmethod
    async def get_sea_state(lat: float, lon: float) -> dict[str, Any]:
        """
        Fetches marine weather and visibility from Open-Meteo.
        """
        try:
            marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wind_wave_height"
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=visibility"
            
            async with httpx.AsyncClient(timeout=10) as client:
                # Run both requests in parallel
                marine_resp, weather_resp = await asyncio.gather(
                    client.get(marine_url),
                    client.get(weather_url)
                )
                
                marine_data = marine_resp.json().get("current", {}) if marine_resp.status_code == 200 else {}
                weather_data = weather_resp.json().get("current", {}) if weather_resp.status_code == 200 else {}
                
                wave_h = marine_data.get("wave_height")
                if wave_h is None:
                    wave_h = 0.5 # Default calm
                
                visibility = weather_data.get("visibility", 24140) # Default ~15 miles
                
                status = "NORMAL"
                if float(wave_h) > 4.0: status = "SEVERE"
                elif float(visibility) < 1000: status = "FOGGY"
                
                return {
                    "wave_height": float(wave_h),
                    "visibility": float(visibility),
                    "status": status
                }
        except Exception as e:
            log.warning("open_meteo_fetch_exception", error=str(e))
        return {"wave_height": 0.0, "visibility": 24140, "status": "UNKNOWN"}

    @staticmethod
    async def get_industrial_exhaust(lat: float, lon: float) -> float:
        """
        Proxies industrial activity via PM2.5 levels from Open-Meteo Air Quality.
        """
        try:
            url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm2_5,pm10"
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json().get("current", {})
                    pm25 = data.get("pm2_5", 0.0)
                    if pm25 is not None:
                        return float(pm25)
                else:
                    log.warning("open_meteo_aq_error", status=resp.status_code)
        except Exception as e:
            log.warning("open_meteo_aq_exception", error=str(e))
        return 0.0
