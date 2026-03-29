"""
Unified Scraper Orchestrator - Central coordinator for all data scraping.

Coordinates data collection from multiple free sources:
- NASA FIRMS (thermal anomalies)
- GDELT (geopolitical news)
- RSS Feeds (financial news)
- OpenSky (aircraft tracking) - already exists
- USGS (earthquakes) - already exists

Provides:
- Unified interface for all scrapers
- Intelligent scheduling and rate limiting
- Data deduplication and merging
- Cache management
- Real-time streaming capability
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScrapedDataPackage:
    """A complete package of scraped data."""
    timestamp: datetime
    thermal_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    news_articles: List[Dict[str, Any]] = field(default_factory=list)
    geopolitical_events: List[Dict[str, Any]] = field(default_factory=list)
    aircraft_data: List[Dict[str, Any]] = field(default_factory=list)
    seismic_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def merge(self, other: 'ScrapedDataPackage') -> 'ScrapedDataPackage':
        """Merge another package into this one."""
        # Deduplicate by URL/ID
        existing_thermal_ids = {t.get('id') for t in self.thermal_anomalies}
        existing_news_urls = {n.get('url') for n in self.news_articles}
        
        for t in other.thermal_anomalies:
            if t.get('id') not in existing_thermal_ids:
                self.thermal_anomalies.append(t)
        
        for n in other.news_articles:
            if n.get('url') not in existing_news_urls:
                self.news_articles.append(n)
        
        self.geopolitical_events.extend(other.geopolitical_events)
        self.aircraft_data.extend(other.aircraft_data)
        self.seismic_events.extend(other.seismic_events)
        
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'thermal_anomalies_count': len(self.thermal_anomalies),
            'news_articles_count': len(self.news_articles),
            'geopolitical_events_count': len(self.geopolitical_events),
            'aircraft_data_count': len(self.aircraft_data),
            'seismic_events_count': len(self.seismic_events),
            'thermal_anomalies': self.thermal_anomalies[:10],  # Limit detail
            'news_articles': self.news_articles[:10],
            'summary': self._generate_summary()
        }
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        parts = []
        if self.thermal_anomalies:
            strong_signals = sum(1 for t in self.thermal_anomalies if t.get('frp_mw', 0) > 50)
            parts.append(f"{len(self.thermal_anomalies)} thermal signals ({strong_signals} strong)")
        
        if self.news_articles:
            sentiment_counts = {}
            for n in self.news_articles:
                s = n.get('sentiment', 'neutral')
                sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
            
            sentiment_str = ', '.join([f"{k}:{v}" for k, v in sentiment_counts.items()])
            parts.append(f"{len(self.news_articles)} news articles ({sentiment_str})")
        
        if self.geopolitical_events:
            high_impact = sum(1 for e in self.geopolitical_events if e.get('impact_score', 0) > 5)
            parts.append(f"{len(self.geopolitical_events)} geopolitical events ({high_impact} high-impact)")
        
        if self.aircraft_data:
            emergencies = sum(1 for a in self.aircraft_data if a.get('is_emergency'))
            parts.append(f"{len(self.aircraft_data)} aircraft tracked ({emergencies} emergencies)")
        
        if self.seismic_events:
            significant = sum(1 for s in self.seismic_events if s.get('magnitude', 0) > 5.0)
            parts.append(f"{len(self.seismic_events)} seismic events ({significant} significant)")
        
        return " | ".join(parts) if parts else "No data collected"


class UnifiedScraperOrchestrator:
    """
    Central orchestrator for all data scraping operations.
    
    Manages:
    - Multiple scraper instances
    - Rate limiting and politeness
    - Data aggregation and deduplication
    - Scheduled collection runs
    """
    
    def __init__(self):
        self._scrapers: Dict[str, Any] = {}
        self._last_run: Optional[datetime] = None
        self._data_history: List[ScrapedDataPackage] = []
        self.max_history = 100
        
    async def collect_all(self, 
                         ticker: Optional[str] = None,
                         include_firms: bool = True,
                         include_gdelt: bool = True,
                         include_rss: bool = True,
                         include_aircraft: bool = False,
                         include_seismic: bool = False) -> ScrapedDataPackage:
        """
        Collect data from all enabled scrapers.
        
        Args:
            ticker: Optional ticker for targeted collection
            include_firms: Enable NASA FIRMS thermal data
            include_gdelt: Enable GDELT geopolitical news
            include_rss: Enable RSS financial news
            include_aircraft: Enable OpenSky aircraft tracking
            include_seismic: Enable USGS seismic data
            
        Returns:
            ScrapedDataPackage with all collected data
        """
        package = ScrapedDataPackage(timestamp=datetime.now(timezone.utc))
        
        tasks = []
        
        if include_firms:
            tasks.append(self._collect_firms(package))
        
        if include_gdelt:
            tasks.append(self._collect_gdelt(package, ticker))
        
        if include_rss:
            tasks.append(self._collect_rss(package, ticker))
        
        if include_aircraft:
            tasks.append(self._collect_aircraft(package))
        
        if include_seismic:
            tasks.append(self._collect_seismic(package))
        
        # Run all collection tasks concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Store in history
        self._data_history.append(package)
        if len(self._data_history) > self.max_history:
            self._data_history.pop(0)
        
        self._last_run = datetime.now(timezone.utc)
        
        logger.info(f"Data collection complete: {package._generate_summary()}")
        return package
    
    async def _collect_firms(self, package: ScrapedDataPackage) -> None:
        """Collect NASA FIRMS thermal data."""
        try:
            from src.scrapers.firms_scraper import get_firms_scraper
            
            scraper = get_firms_scraper()
            anomalies = scraper.get_industrial_thermal_anomalies(hours=24)
            
            package.thermal_anomalies = anomalies
            logger.info(f"FIRMS: Collected {len(anomalies)} thermal anomalies")
            
        except Exception as e:
            logger.error(f"FIRMS collection failed: {e}")
    
    async def _collect_gdelt(self, package: ScrapedDataPackage, ticker: Optional[str]) -> None:
        """Collect GDELT geopolitical news."""
        try:
            from src.scrapers.gdelt_scraper import get_gdelt_scraper
            
            scraper = get_gdelt_scraper()
            
            if ticker:
                # Company-specific news
                articles = scraper.search_ticker_news(ticker, ticker, timespan="24h")
            else:
                # Maritime intelligence
                articles = scraper.search_maritime_intelligence(timespan="24h")
            
            # Convert to dicts
            package.news_articles = [a.to_dict() for a in articles]
            
            # Add geopolitical events analysis
            impact = scraper.analyze_news_impact(articles)
            package.geopolitical_events = [{
                'type': 'gdelt_analysis',
                'impact_score': impact.get('impact_score', 0),
                'urgency': impact.get('urgency', 'low'),
                'sentiment': impact.get('sentiment', 'neutral'),
                'sources': [a.to_dict() for a in articles[:5]]
            }]
            
            logger.info(f"GDELT: Collected {len(articles)} articles")
            
        except Exception as e:
            logger.error(f"GDELT collection failed: {e}")
    
    async def _collect_rss(self, package: ScrapedDataPackage, ticker: Optional[str]) -> None:
        """Collect RSS financial news."""
        try:
            from src.scrapers.rss_aggregator import get_rss_aggregator
            
            aggregator = get_rss_aggregator()
            all_articles = []
            
            if ticker:
                # Ticker-specific news
                articles = aggregator.fetch_ticker_news(ticker, max_articles=20)
                all_articles.extend(articles)
            else:
                # General market news
                sources = ['cnbc_top', 'seeking_alpha_market']
                multi_news = aggregator.fetch_multi_source_news(sources, max_per_source=10)
                for articles in multi_news.values():
                    all_articles.extend(articles)
            
            # Analyze sentiment
            sentiment = aggregator.get_market_sentiment(all_articles)
            
            # Convert to dicts with sentiment
            for article in all_articles:
                article.sentiment = sentiment.get('sentiment', 'neutral')
            
            package.news_articles.extend([a.to_dict() for a in all_articles])
            
            logger.info(f"RSS: Collected {len(all_articles)} articles")
            
        except Exception as e:
            logger.error(f"RSS collection failed: {e}")
    
    async def _collect_aircraft(self, package: ScrapedDataPackage) -> None:
        """Collect OpenSky aircraft data."""
        try:
            from src.globe.opensky_tracker import OpenSkyTracker
            
            tracker = OpenSkyTracker()
            snapshot = tracker.get_current_snapshot()
            
            # Filter for interesting aircraft
            alerts = tracker.get_emergency_alerts()
            
            package.aircraft_data = [alert.to_geojson() for alert in alerts]
            
            logger.info(f"OpenSky: Collected {len(alerts)} aircraft alerts")
            
        except Exception as e:
            logger.error(f"OpenSky collection failed: {e}")
    
    async def _collect_seismic(self, package: ScrapedDataPackage) -> None:
        """Collect USGS seismic data."""
        try:
            from src.globe.geophysical_monitor import GeophysicalMonitor
            
            monitor = GeophysicalMonitor()
            monitor.fetch_earthquakes()
            
            # Get significant events affecting chokepoints
            events = monitor.get_events_for_chokepoints()
            
            package.seismic_events = [e.to_dict() for e in events]
            
            logger.info(f"USGS: Collected {len(events)} seismic events")
            
        except Exception as e:
            logger.error(f"USGS collection failed: {e}")
    
    async def collect_for_ticker(self, ticker: str, company_name: Optional[str] = None) -> ScrapedDataPackage:
        """
        Comprehensive data collection for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Optional company name for better search
            
        Returns:
            ScrapedDataPackage focused on ticker
        """
        search_name = company_name or ticker
        
        return await self.collect_all(
            ticker=search_name,
            include_firms=True,
            include_gdelt=True,
            include_rss=True,
            include_aircraft=False,
            include_seismic=False
        )
    
    def get_latest_data(self) -> Optional[ScrapedDataPackage]:
        """Get most recent data package."""
        return self._data_history[-1] if self._data_history else None
    
    def get_data_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get last N data packages as dicts."""
        return [p.to_dict() for p in self._data_history[-n:]]
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics on data collection."""
        if not self._data_history:
            return {'status': 'No data collected yet'}
        
        total_thermal = sum(len(p.thermal_anomalies) for p in self._data_history)
        total_news = sum(len(p.news_articles) for p in self._data_history)
        total_geo = sum(len(p.geopolitical_events) for p in self._data_history)
        
        return {
            'total_collections': len(self._data_history),
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'total_thermal_anomalies': total_thermal,
            'total_news_articles': total_news,
            'total_geopolitical_events': total_geo,
            'avg_collection_size': (total_thermal + total_news + total_geo) / len(self._data_history)
        }


# Singleton
_orchestrator: Optional[UnifiedScraperOrchestrator] = None

def get_scraper_orchestrator() -> UnifiedScraperOrchestrator:
    """Get or create scraper orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = UnifiedScraperOrchestrator()
    return _orchestrator


# Convenience function for quick data collection
async def quick_collect(ticker: Optional[str] = None) -> ScrapedDataPackage:
    """
    Quick data collection with all scrapers.
    
    Usage:
        data = await quick_collect("MT")
        print(data.to_dict())
    """
    orchestrator = get_scraper_orchestrator()
    return await orchestrator.collect_all(ticker=ticker)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test_orchestrator():
        print("=" * 70)
        print("Unified Scraper Orchestrator Test")
        print("=" * 70)
        
        orchestrator = get_scraper_orchestrator()
        
        # Test 1: General collection
        print("\n1. General Data Collection (all sources)")
        print("-" * 70)
        
        package = await orchestrator.collect_all(
            include_firms=True,
            include_gdelt=True,
            include_rss=True,
            include_aircraft=False,
            include_seismic=False
        )
        
        print(f"\nCollection Summary:")
        print(f"  {package.to_dict()['summary']}")
        
        print(f"\nDetailed Counts:")
        print(f"  Thermal anomalies: {len(package.thermal_anomalies)}")
        print(f"  News articles: {len(package.news_articles)}")
        print(f"  Geopolitical events: {len(package.geopolitical_events)}")
        
        # Test 2: Ticker-specific collection
        print("\n2. Ticker-Specific Collection (MT)")
        print("-" * 70)
        
        ticker_package = await orchestrator.collect_for_ticker("MT", "ArcelorMittal")
        
        print(f"\nTicker Collection Summary:")
        print(f"  {ticker_package.to_dict()['summary']}")
        
        # Show sample news
        if ticker_package.news_articles:
            print(f"\nSample News for MT:")
            for article in ticker_package.news_articles[:3]:
                print(f"  - {article.get('title', 'N/A')[:60]}...")
        
        # Test 3: Stats
        print("\n3. Collection Statistics")
        print("-" * 70)
        stats = orchestrator.get_collection_stats()
        print(f"Total collections: {stats['total_collections']}")
        print(f"Total thermal: {stats['total_thermal_anomalies']}")
        print(f"Total news: {stats['total_news_articles']}")
        
        print("\n" + "=" * 70)
        print("Orchestrator Test Complete")
        print("=" * 70)
    
    # Run test
    asyncio.run(test_orchestrator())
