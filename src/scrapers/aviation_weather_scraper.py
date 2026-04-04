"""
Aviation Weather Scraper - NOAA weather intelligence.

Uses NOAA Aviation Weather Center (AWC) API to track weather conditions
at major chokepoints and industrial hubs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

@dataclass
class MetarData:
    """METAR weather data."""
    icao_id: str
    obs_time: datetime
    temp: float
    wdir: int
    wspd: int
    visib: float
    raw_ob: str
    flt_cat: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'icao_id': self.icao_id,
            'obs_time': self.obs_time.isoformat(),
            'temp_c': self.temp,
            'wind_dir': self.wdir,
            'wind_speed_kt': self.wspd,
            'visibility_sm': self.visib,
            'raw': self.raw_ob,
            'flight_category': self.flt_cat,
            'source': 'aviation_weather'
        }

class AviationWeatherScraper:
    """NOAA Aviation Weather API scraper."""

    BASE_URL = "https://aviationweather.gov/api/data/metar"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (SatTrade Intelligence Bot)'
        })

    def fetch_metar(self, icao_ids: list[str]) -> list[MetarData]:
        """Fetch METAR data for list of ICAO codes."""
        if not icao_ids:
            return []

        params = {
            'ids': ','.join(icao_ids),
            'format': 'json'
        }

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            metars = []
            for item in data:
                obs_time = datetime.fromtimestamp(item.get('obsTime', 0), tz=UTC)
                metars.append(MetarData(
                    icao_id=item['icaoId'],
                    obs_time=obs_time,
                    temp=item.get('temp', 0.0),
                    wdir=item.get('wdir', 0),
                    wspd=item.get('wspd', 0),
                    visib=item.get('visib', 0.0),
                    raw_ob=item.get('rawOb', ''),
                    flt_cat=item.get('fltCat', 'VFR')
                ))

            logger.info(f"AviationWeather: Fetched {len(metars)} METARs")
            return metars

        except Exception as e:
            logger.error(f"AviationWeather fetch failed: {e}")
            return []

# Singleton
_scraper: AviationWeatherScraper | None = None

def get_aviation_weather_scraper() -> AviationWeatherScraper:
    """Get or create aviation weather scraper singleton."""
    global _scraper
    if _scraper is None:
        _scraper = AviationWeatherScraper()
    return _scraper

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = AviationWeatherScraper()
    metars = scraper.fetch_metar(['KJFK', 'KLAX', 'EGLL'])
    for m in metars:
        print(f"- {m.icao_id}: {m.temp}C, {m.wspd}kt winds, {m.flt_cat}")
