"""
RSS News Aggregator - Free financial news from RSS feeds.

Aggregates news from multiple free RSS sources:
- Financial Times (limited free articles)
- Reuters (RSS available)
- Bloomberg (RSS feeds)
- MarketWatch
- Seeking Alpha
- Yahoo Finance
- Google News

No API keys required for RSS access.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from typing import Any

import feedparser
import requests

logger = logging.getLogger(__name__)


@dataclass
class RSSArticle:
    """A single RSS news article."""
    title: str
    link: str
    published: datetime
    summary: str
    source: str
    categories: list[str]
    sentiment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'title': self.title,
            'link': self.link,
            'published': self.published.isoformat(),
            'summary': self.summary[:200] + '...' if len(self.summary) > 200 else self.summary,
            'source': self.source,
            'categories': self.categories,
            'sentiment': self.sentiment
        }


class RSSNewsAggregator:
    """
    Aggregates financial news from free RSS feeds.
    
    Sources:
    - Yahoo Finance (ticker-specific)
    - Seeking Alpha (market news)
    - MarketWatch
    - Google News (search-based)
    - Investing.com
    - Finviz (market pulse)
    """

    # Free RSS feed URLs
    FEEDS = {
        'yahoo_finance': {
            'base_url': 'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US',
            'description': 'Yahoo Finance ticker news'
        },
        'seeking_alpha_market': {
            'url': 'https://seekingalpha.com/market_currents.xml',
            'description': 'Seeking Alpha market news'
        },
        'marketwatch_top': {
            'url': 'https://feeds.content.dowjones.io/public/rss/mw_topstories',
            'description': 'MarketWatch top stories'
        },
        'marketwatch_markets': {
            'url': 'https://feeds.content.dowjones.io/public/rss/mw_markets',
            'description': 'MarketWatch markets'
        },
        'google_finance': {
            'base_url': 'https://news.google.com/rss/search?q={query}+finance+stock+market',
            'description': 'Google News finance search'
        },
        'cnbc_top': {
            'url': 'https://www.cnbc.com/id/19746125/device/rss/rss.xml',
            'description': 'CNBC top news'
        },
        'bloomberg_markets': {
            'url': 'https://feeds.bloomberg.com/markets/news.rss',
            'description': 'Bloomberg markets news'
        },
        'investing_com_commodities': {
            'url': 'https://www.investing.com/rss/news_commodities.rss',
            'description': 'Investing.com commodities'
        },
        'reuters_business': {
            'url': 'https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best',
            'description': 'Reuters business news'
        },
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._cache: dict[str, list[RSSArticle]] = {}
        self.cache_ttl = 300  # 5 minutes

    def fetch_ticker_news(self, ticker: str, max_articles: int = 20) -> list[RSSArticle]:
        """
        Fetch news for a specific ticker from Yahoo Finance RSS.
        
        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum articles to return
            
        Returns:
            List of RSSArticle objects
        """
        cache_key = f"ticker_{ticker}"

        # Check cache
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached and (datetime.now(UTC) - cached[0].published).total_seconds() < self.cache_ttl:
                return cached[:max_articles]

        url = self.FEEDS['yahoo_finance']['base_url'].format(ticker=ticker)
        articles = self._parse_feed(url, f'Yahoo Finance - {ticker}')

        if articles:
            self._cache[cache_key] = articles

        return articles[:max_articles]

    def fetch_market_news(self, source: str = 'seeking_alpha_market', max_articles: int = 30) -> list[RSSArticle]:
        """
        Fetch general market news from specified source.
        
        Args:
            source: Feed key from FEEDS dict
            max_articles: Maximum articles to return
        """
        if source not in self.FEEDS:
            logger.error(f"Unknown source: {source}")
            return []

        feed_info = self.FEEDS[source]
        url = feed_info.get('url')

        if not url:
            logger.error(f"No URL configured for {source}")
            return []

        articles = self._parse_feed(url, source)
        return articles[:max_articles]

    def _parse_feed(self, url: str, source_name: str) -> list[RSSArticle]:
        """Parse RSS feed and return articles."""
        articles = []

        try:
            logger.info(f"Fetching RSS: {url[:60]}...")

            # Use requests to fetch with custom headers
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse with feedparser
            feed = feedparser.parse(response.content)

            for entry in feed.entries:
                try:
                    # Parse date
                    published = self._parse_date(entry)

                    # Clean summary
                    summary = self._clean_html(entry.get('summary', ''))
                    if not summary:
                        summary = entry.get('description', '')

                    # Extract categories
                    categories = []
                    if 'tags' in entry:
                        categories = [tag.term for tag in entry.tags]

                    article = RSSArticle(
                        title=unescape(entry.get('title', '')),
                        link=entry.get('link', ''),
                        published=published,
                        summary=summary[:500],  # Limit summary length
                        source=source_name,
                        categories=categories
                    )

                    articles.append(article)

                except Exception as e:
                    logger.warning(f"Failed to parse RSS entry: {e}")
                    continue

            logger.info(f"RSS fetch successful: {len(articles)} articles from {source_name}")

        except Exception as e:
            logger.error(f"RSS fetch failed for {source_name}: {e}")

        return articles

    def _parse_date(self, entry: Any) -> datetime:
        """Parse various date formats from RSS entries."""
        import calendar
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']

        for field in date_fields:
            if hasattr(entry, field):
                date_struct = getattr(entry, field)
                if date_struct:
                    return datetime.fromtimestamp(calendar.timegm(date_struct), tz=UTC)

        # Fallback: try string parsing
        date_str = entry.get('published', '') or entry.get('updated', '')
        if date_str:
            try:
                # Try common formats
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(date_str, fmt).replace(tzinfo=UTC)
                    except ValueError:
                        continue
            except Exception:
                pass

        return datetime.now(UTC)

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags and clean text."""
        if not html:
            return ''

        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', html)

        # Unescape HTML entities
        clean = unescape(clean)

        # Normalize whitespace
        clean = ' '.join(clean.split())

        return clean.strip()

    def search_news(self, query: str, max_articles: int = 20) -> list[RSSArticle]:
        """
        Search for news using Google News RSS.
        
        Args:
            query: Search query
            max_articles: Maximum articles to return
        """
        url = self.FEEDS['google_finance']['base_url'].format(query=query.replace(' ', '+'))
        return self._parse_feed(url, f'Google News - {query}')[:max_articles]

    def fetch_multi_source_news(self,
                               sources: list[str] | None = None,
                               max_per_source: int = 10) -> dict[str, list[RSSArticle]]:
        """
        Fetch news from multiple sources.
        
        Args:
            sources: List of source keys (default: all available)
            max_per_source: Max articles per source
            
        Returns:
            Dict mapping source name to articles
        """
        if sources is None:
            # Use sources with direct URLs (not ticker-based)
            sources = [k for k, v in self.FEEDS.items() if 'url' in v]

        results = {}

        for source in sources:
            try:
                articles = self.fetch_market_news(source, max_per_source)
                results[source] = articles
            except Exception as e:
                logger.warning(f"Failed to fetch from {source}: {e}")
                results[source] = []

        return results

    def get_market_sentiment(self, articles: list[RSSArticle]) -> dict[str, Any]:
        """
        Analyze sentiment from news headlines using simple keyword analysis.
        
        Returns:
            Sentiment analysis results
        """
        positive_words = ['surge', 'rally', 'gain', 'up', 'rise', 'growth', 'profit', 'beat', 'strong', 'bull', 'soar', 'jump', 'boost']
        negative_words = ['drop', 'fall', 'decline', 'crash', 'plunge', 'loss', 'miss', 'weak', 'bear', 'sell-off', 'tumble', 'slide', 'slump']

        sentiment_scores = []

        for article in articles:
            title_lower = article.title.lower()

            pos_count = sum(1 for word in positive_words if word in title_lower)
            neg_count = sum(1 for word in negative_words if word in title_lower)

            if pos_count > neg_count:
                sentiment_scores.append(1)
                article.sentiment = 'positive'
            elif neg_count > pos_count:
                sentiment_scores.append(-1)
                article.sentiment = 'negative'
            else:
                sentiment_scores.append(0)
                article.sentiment = 'neutral'

        if not sentiment_scores:
            return {'sentiment': 'neutral', 'score': 0, 'articles_analyzed': 0}

        avg_score = sum(sentiment_scores) / len(sentiment_scores)

        if avg_score > 0.1:
            overall = 'positive'
        elif avg_score < -0.1:
            overall = 'negative'
        else:
            overall = 'neutral'

        return {
            'sentiment': overall,
            'score': round(avg_score, 2),
            'articles_analyzed': len(articles),
            'positive_count': sum(1 for s in sentiment_scores if s > 0),
            'negative_count': sum(1 for s in sentiment_scores if s < 0),
            'neutral_count': sum(1 for s in sentiment_scores if s == 0)
        }


# Singleton
_aggregator: RSSNewsAggregator | None = None

def get_rss_aggregator() -> RSSNewsAggregator:
    """Get or create RSS aggregator singleton."""
    global _aggregator
    if _aggregator is None:
        _aggregator = RSSNewsAggregator()
    return _aggregator


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    aggregator = RSSNewsAggregator()

    print("=" * 70)
    print("RSS News Aggregator Test")
    print("=" * 70)

    # Test 1: Ticker-specific news
    print("\n1. Ticker News: AAPL")
    print("-" * 70)
    ticker_news = aggregator.fetch_ticker_news('AAPL', max_articles=5)
    print(f"Found {len(ticker_news)} articles")

    for article in ticker_news[:3]:
        print(f"  - {article.title[:60]}...")
        print(f"    {article.published.strftime('%Y-%m-%d %H:%M')}")

    # Test 2: Market news from multiple sources
    print("\n2. Market News (CNBC, Seeking Alpha)")
    print("-" * 70)

    sources_to_test = ['cnbc_top', 'seeking_alpha_market']
    multi_news = aggregator.fetch_multi_source_news(sources_to_test, max_per_source=5)

    for source, articles in multi_news.items():
        print(f"\n{source}: {len(articles)} articles")
        for article in articles[:2]:
            print(f"  - {article.title[:55]}...")

    # Test 3: Search
    print("\n3. News Search: 'oil price'")
    print("-" * 70)
    search_results = aggregator.search_news('oil price', max_articles=5)
    print(f"Found {len(search_results)} articles")

    for article in search_results[:3]:
        print(f"  - {article.title[:60]}...")

    # Test 4: Sentiment analysis
    print("\n4. Sentiment Analysis")
    print("-" * 70)
    all_articles = []
    for articles in multi_news.values():
        all_articles.extend(articles)

    sentiment = aggregator.get_market_sentiment(all_articles)
    print(f"Overall sentiment: {sentiment['sentiment']} (score: {sentiment['score']})")
    print(f"Articles: {sentiment['positive_count']} positive, "
          f"{sentiment['negative_count']} negative, "
          f"{sentiment['neutral_count']} neutral")

    print("\n" + "=" * 70)
    print("RSS Aggregator Test Complete")
    print("=" * 70)
