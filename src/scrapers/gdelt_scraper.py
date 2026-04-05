"""
GDELT News Scraper - Free geopolitical news intelligence.

GDELT Project provides free access to global news data without API keys.
Supports 65 languages, real-time monitoring, and sentiment analysis.

Data sources:
- GDELT DOC 2.0 API (free, no key required)
- Article lists with full-text URLs
- Tone/sentiment analysis
- Geographic tagging
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GDELTArticle:
    """A single GDELT news article."""
    url: str
    title: str
    seendate: datetime
    domain: str
    language: str
    sourcecountry: str
    tone: float  # -10 (negative) to +10 (positive)
    sentiment: str  # 'positive', 'negative', 'neutral'
    themes: list[str]
    persons: list[str]
    organizations: list[str]
    locations: list[dict[str, Any]]  # Geo-tagged locations

    def to_dict(self) -> dict[str, Any]:
        return {
            'url': self.url,
            'title': self.title,
            'seendate': self.seendate.isoformat(),
            'domain': self.domain,
            'language': self.language,
            'sourcecountry': self.sourcecountry,
            'tone': self.tone,
            'sentiment': self.sentiment,
            'themes': self.themes,
            'persons': self.persons,
            'organizations': self.organizations,
            'locations': self.locations
        }


class GDELTNewsScraper:
    """
    GDELT DOC 2.0 API scraper for geopolitical news intelligence.

    Features:
    - Search by keyword/topic
    - Tone/sentiment analysis built-in
    - Geographic extraction
    - Entity extraction (persons, organizations)
    - Multi-language support (65 languages)
    - No API key required

    Base URL: https://api.gdeltproject.org/api/v2/doc/doc
    """

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    # Search queries for maritime/shipping intelligence
    MARITIME_QUERIES = [
        '"Strait of Hormuz" OR "Hormuz"',
        '"Suez Canal" OR "Suez"',
        '"Strait of Malacca" OR "Malacca"',
        '"shipping disruption" OR "port closure"',
        '"oil tanker" OR "LNG carrier"',
        '"supply chain" AND (disruption OR delay)',
        '"piracy" OR "hijacking" OR vessel seizure',
        '"trade war" OR tariffs OR sanctions',
        '"steel production" OR "iron ore"',
        '"energy crisis" OR "gas shortage"'
    ]

    def __init__(self) -> None:
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (SatTrade Intelligence Bot)'
        }

    async def search_articles(self,
                              query: str,
                              max_records: int = 50,
                              timespan: str = "1d") -> list[GDELTArticle]:
        """
        Search for articles matching query.
        """
        params = {
            'query': query,
            'mode': 'artlist',
            'maxrecords': min(max_records, 250),
            'timespan': timespan,
            'format': 'json',
            'sort': 'DateDesc'
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.BASE_URL,
                                            params=params,
                                            headers=self.headers)
                response.raise_for_status()

            try:
                data = response.json()
                if not data or not isinstance(data, dict):
                    logger.warning(
                        f"GDELT returned empty or non-dict JSON: {query[:30]}"
                    )
                    return []
            except Exception as e:
                logger.error(f"GDELT JSON parse error for '{query[:30]}': {e}")
                logger.debug(f"Raw response: {response.text[:200]}")
                return []

            articles: list[GDELTArticle] = []
            for item in data.get('articles', []):
                article = self._parse_article(item)
                if article:
                    articles.append(article)
            return articles

        except httpx.HTTPError as e:
            logger.error(f"GDELT API error for query '{query[:30]}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in GDELT search: {e}")
            return []

    async def get_maritime_intelligence(self) -> list[GDELTArticle]:
        """
        Get latest maritime intelligence articles across standard queries.
        """
        all_articles: list[GDELTArticle] = []
        seen_urls: set[str] = set()

        for query in self.MARITIME_QUERIES:
            articles = await self.search_articles(query, max_records=20)
            for article in articles:
                if article.url not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(article.url)

        # Sort by date, newest first
        all_articles.sort(key=lambda x: x.seendate, reverse=True)
        return all_articles

    def _parse_article(self, item: dict[str, Any]) -> GDELTArticle | None:
        """Parse a single GDELT article JSON item."""
        try:
            url = item.get('url', '')
            if not url:
                return None

            seendate_str = item.get('seendate', '')
            try:
                # GDELT date format: 20240325T114424Z
                seendate = datetime.strptime(seendate_str, '%Y%m%dT%H%M%SZ')
                seendate = seendate.replace(tzinfo=UTC)
            except (ValueError, TypeError):
                seendate = datetime.now(UTC)

            tone_str = item.get('tone', '0')
            try:
                tone = float(tone_str)
            except (ValueError, TypeError):
                tone = 0.0

            sentiment = 'neutral'
            if tone > 2:
                sentiment = 'positive'
            elif tone < -2:
                sentiment = 'negative'

            return GDELTArticle(
                url=url,
                title=item.get('title', 'Unknown Title'),
                seendate=seendate,
                domain=item.get('domain', 'unknown'),
                language=item.get('language', 'English'),
                sourcecountry=item.get('sourcecountry', 'Unknown'),
                tone=tone,
                sentiment=sentiment,
                themes=item.get('themes', []),
                persons=item.get('persons', []),
                organizations=item.get('organizations', []),
                locations=item.get('locations', [])
            )
        except Exception as e:
            logger.debug(f"Error parsing GDELT article: {e}")
            return None
