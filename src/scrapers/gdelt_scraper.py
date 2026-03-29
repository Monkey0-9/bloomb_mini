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
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote

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
    themes: List[str]
    persons: List[str]
    organizations: List[str]
    locations: List[Dict[str, Any]]  # Geo-tagged locations
    
    def to_dict(self) -> Dict[str, Any]:
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
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (SatTrade Intelligence Bot)'
        })
    
    def search_articles(self,
                       query: str,
                       max_records: int = 50,
                       timespan: str = "1d") -> List[GDELTArticle]:
        """
        Search for articles matching query.
        
        Args:
            query: Search query string
            max_records: Number of articles to return (max 250)
            timespan: Time window (e.g., '1d', '7d', '1h')
            
        Returns:
            List of GDELTArticle objects
        """
        params = {
            'query': query,
            'mode': 'ArtList',
            'maxrecords': min(max_records, 250),
            'timespan': timespan,
            'format': 'JSON'
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for item in data.get('articles', []):
                article = self._parse_article(item)
                if article:
                    articles.append(article)
            
            logger.info(f"GDELT search: '{query[:50]}...' returned {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"GDELT search failed: {e}")
            return []
    
    def _parse_article(self, item: Dict[str, Any]) -> Optional[GDELTArticle]:
        """Parse GDELT article JSON into GDELTArticle."""
        try:
            # Parse date
            seendate_str = item.get('seendate', '')
            if seendate_str:
                seendate = datetime.strptime(seendate_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
            else:
                seendate = datetime.now(timezone.utc)
            
            # Parse tone (format: "tone,pos,neg,polarity,activeref,refs")
            tone_str = item.get('tone', '0,0,0,0,0,0')
            tone_parts = tone_str.split(',')
            tone = float(tone_parts[0]) if tone_parts else 0.0
            
            # Determine sentiment
            if tone > 2:
                sentiment = 'positive'
            elif tone < -2:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            # Parse themes, persons, organizations
            themes = item.get('themes', '').split(';') if item.get('themes') else []
            persons = item.get('persons', '').split(';') if item.get('persons') else []
            organizations = item.get('organizations', '').split(';') if item.get('organizations') else []
            
            # Parse locations
            locations = []
            if item.get('locations'):
                for loc_str in item['locations'].split(';'):
                    if '#' in loc_str:
                        parts = loc_str.split('#')
                        if len(parts) >= 4:
                            locations.append({
                                'name': parts[0],
                                'lat': float(parts[1]) if parts[1] else 0,
                                'lon': float(parts[2]) if parts[2] else 0,
                                'type': parts[3] if len(parts) > 3 else 'unknown'
                            })
            
            return GDELTArticle(
                url=item.get('url', ''),
                title=item.get('title', ''),
                seendate=seendate,
                domain=item.get('domain', ''),
                language=item.get('language', 'eng'),
                sourcecountry=item.get('sourcecountry', ''),
                tone=tone,
                sentiment=sentiment,
                themes=[t.strip() for t in themes if t.strip()],
                persons=[p.strip() for p in persons if p.strip()],
                organizations=[o.strip() for o in organizations if o.strip()],
                locations=locations
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse article: {e}")
            return None
    
    def search_maritime_intelligence(self, timespan: str = "24h") -> List[GDELTArticle]:
        """
        Search for maritime/shipping related intelligence.
        
        Combines multiple maritime queries to get comprehensive coverage.
        """
        all_articles = []
        seen_urls = set()
        
        for query in self.MARITIME_QUERIES:
            articles = self.search_articles(query, max_records=25, timespan=timespan)
            for article in articles:
                if article.url not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(article.url)
            
            # Small delay between queries
            import time
            time.sleep(0.5)
        
        # Sort by recency and tone (prioritize negative news as it affects markets)
        all_articles.sort(key=lambda a: (a.seendate, abs(a.tone)), reverse=True)
        
        logger.info(f"Maritime intelligence: {len(all_articles)} unique articles")
        return all_articles
    
    def search_ticker_news(self, ticker: str, company_name: str, timespan: str = "7d") -> List[GDELTArticle]:
        """
        Search for news related to a specific company/ticker.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name for search
            timespan: Time window
        """
        # Build query with ticker and company name
        queries = [
            f'"{company_name}"',
            f'"{ticker}"',  # Some sources use ticker symbols
        ]
        
        all_articles = []
        seen_urls = set()
        
        for query in queries:
            articles = self.search_articles(query, max_records=30, timespan=timespan)
            for article in articles:
                if article.url not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(article.url)
        
        # Sort by recency
        all_articles.sort(key=lambda a: a.seendate, reverse=True)
        
        return all_articles
    
    def get_tone_timeline(self, query: str, timespan: str = "7d") -> List[Dict[str, Any]]:
        """
        Get tone/sentiment timeline for a query.
        
        Useful for tracking sentiment shifts over time.
        """
        params = {
            'query': query,
            'mode': 'timelinetone',
            'timespan': timespan,
            'format': 'JSON'
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            timeline = []
            
            for item in data.get('timeline', []):
                timeline.append({
                    'date': item.get('date'),
                    'tone': item.get('tone'),
                    'volume': item.get('volume'),
                    'positivity': item.get('pos'),
                    'negativity': item.get('neg')
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"GDELT timeline failed: {e}")
            return []
    
    def analyze_news_impact(self, articles: List[GDELTArticle]) -> Dict[str, Any]:
        """
        Analyze news articles for market impact.
        
        Returns:
            Dict with impact analysis
        """
        if not articles:
            return {'impact_score': 0, 'sentiment': 'neutral', 'urgency': 'low'}
        
        # Calculate metrics
        avg_tone = sum(a.tone for a in articles) / len(articles)
        negative_count = sum(1 for a in articles if a.sentiment == 'negative')
        positive_count = sum(1 for a in articles if a.sentiment == 'positive')
        
        # Extract key themes
        all_themes = []
        for a in articles:
            all_themes.extend(a.themes)
        
        from collections import Counter
        top_themes = Counter(all_themes).most_common(10)
        
        # Extract mentioned organizations
        all_orgs = []
        for a in articles:
            all_orgs.extend(a.organizations)
        top_organizations = Counter(all_orgs).most_common(10)
        
        # Determine urgency based on recency and negativity
        recent_negative = [
            a for a in articles 
            if a.sentiment == 'negative' and 
            (datetime.now(timezone.utc) - a.seendate) < timedelta(hours=6)
        ]
        
        if len(recent_negative) >= 3:
            urgency = 'high'
        elif len(recent_negative) >= 1:
            urgency = 'medium'
        else:
            urgency = 'low'
        
        # Impact score (-10 to +10)
        impact_score = avg_tone
        
        return {
            'impact_score': round(impact_score, 2),
            'sentiment': 'positive' if avg_tone > 1 else 'negative' if avg_tone < -1 else 'neutral',
            'urgency': urgency,
            'article_count': len(articles),
            'negative_articles': negative_count,
            'positive_articles': positive_count,
            'avg_tone': round(avg_tone, 2),
            'top_themes': top_themes,
            'top_organizations': top_organizations,
            'recent_alerts': [a.to_dict() for a in recent_negative[:5]]
        }


# Singleton
_scraper: Optional[GDELTNewsScraper] = None

def get_gdelt_scraper() -> GDELTNewsScraper:
    """Get or create GDELT scraper singleton."""
    global _scraper
    if _scraper is None:
        _scraper = GDELTNewsScraper()
    return _scraper


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scraper = GDELTNewsScraper()
    
    print("=" * 70)
    print("GDELT News Scraper Test")
    print("=" * 70)
    
    # Test 1: Maritime intelligence
    print("\n1. Maritime Intelligence (24h)")
    print("-" * 70)
    maritime_articles = scraper.search_maritime_intelligence(timespan="24h")
    print(f"Found {len(maritime_articles)} maritime-related articles")
    
    if maritime_articles:
        impact = scraper.analyze_news_impact(maritime_articles[:20])
        print(f"\nImpact Analysis:")
        print(f"  Articles: {impact['article_count']}")
        print(f"  Sentiment: {impact['sentiment']} (score: {impact['impact_score']})")
        print(f"  Urgency: {impact['urgency']}")
        print(f"  Top Themes: {[t[0] for t in impact['top_themes'][:5]]}")
        
        print(f"\nSample Articles:")
        for article in maritime_articles[:3]:
            print(f"  - {article.title[:60]}... ({article.sourcecountry}, tone: {article.tone:.1f})")
    
    # Test 2: Ticker search (ArcelorMittal)
    print("\n2. Company Search: ArcelorMittal")
    print("-" * 70)
    company_articles = scraper.search_ticker_news("MT", "ArcelorMittal", timespan="7d")
    print(f"Found {len(company_articles)} articles about ArcelorMittal")
    
    if company_articles:
        for article in company_articles[:3]:
            print(f"  - {article.title[:60]}... ({article.seendate.strftime('%Y-%m-%d')})")
    
    # Test 3: Tone timeline for Strait of Hormuz
    print("\n3. Tone Timeline: Strait of Hormuz (7d)")
    print("-" * 70)
    timeline = scraper.get_tone_timeline('"Strait of Hormuz"', timespan="7d")
    print(f"Retrieved {len(timeline)} data points")
    
    if timeline:
        for point in timeline[:5]:
            print(f"  {point['date']}: tone={point['tone']:.2f}, vol={point['volume']}")
    
    print("\n" + "=" * 70)
    print("GDELT Scraper Test Complete")
    print("=" * 70)
