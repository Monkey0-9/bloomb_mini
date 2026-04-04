"""
Spaceflight News Scraper - Satellite and launch intelligence.

Uses Spaceflight News API (SNAPI) v4 to track satellite launches, 
space industry news, and potential disruptions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

@dataclass
class SpaceflightArticle:
    """A single spaceflight news article."""
    id: int
    title: str
    url: str
    summary: str
    news_site: str
    published_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'summary': self.summary,
            'news_site': self.news_site,
            'published_at': self.published_at.isoformat(),
            'source': 'spaceflight_news'
        }

class SpaceflightNewsScraper:
    """
    Spaceflight News API (SNAPI) v4 scraper.
    
    API Docs: https://api.spaceflightnewsapi.net/v4/docs/
    """

    BASE_URL = "https://api.spaceflightnewsapi.net/v4/articles/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (SatTrade Intelligence Bot)'
        })

    def fetch_latest_news(self, limit: int = 50) -> list[SpaceflightArticle]:
        """Fetch latest spaceflight news."""
        params = {
            'limit': limit,
            'ordering': '-published_at'
        }

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            articles = []
            for item in data.get('results', []):
                articles.append(SpaceflightArticle(
                    id=item['id'],
                    title=item['title'],
                    url=item['url'],
                    summary=item['summary'],
                    news_site=item['news_site'],
                    published_at=datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                ))

            logger.info(f"SpaceflightNews: Fetched {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"SpaceflightNews fetch failed: {e}")
            return []

    def search_news(self, query: str, limit: int = 20) -> list[SpaceflightArticle]:
        """Search spaceflight news by keyword."""
        params = {
            'search': query,
            'limit': limit,
            'ordering': '-published_at'
        }

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            articles = []
            for item in data.get('results', []):
                articles.append(SpaceflightArticle(
                    id=item['id'],
                    title=item['title'],
                    url=item['url'],
                    summary=item['summary'],
                    news_site=item['news_site'],
                    published_at=datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                ))

            return articles

        except Exception as e:
            logger.error(f"SpaceflightNews search failed for '{query}': {e}")
            return []

# Singleton
_scraper: SpaceflightNewsScraper | None = None

def get_spaceflight_scraper() -> SpaceflightNewsScraper:
    """Get or create spaceflight scraper singleton."""
    global _scraper
    if _scraper is None:
        _scraper = SpaceflightNewsScraper()
    return _scraper

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SpaceflightNewsScraper()
    articles = scraper.fetch_latest_news(limit=5)
    for a in articles:
        print(f"- {a.title} ({a.news_site})")
