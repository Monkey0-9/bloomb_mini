"""
SatTrade Live News Feed via RSS
"""
import asyncio
import time
import structlog
from typing import List, Dict

log = structlog.get_logger(__name__)

async def fetch_news(ticker: str = "") -> List[Dict]:
    """Fetch live news via RSS. If ticker provided, get Yahoo Finance, else CNBC general."""
    try:
        import feedparser
    except ImportError:
        log.warning("feedparser_missing")
        return []

    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US" if ticker else "https://search.cnbc.com/rs/search/combinedcms/view.xml?profile=120000000&id=10000664"
    
    try:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)
        
        results = []
        for entry in feed.entries[:20]:
            results.append({
                "title": entry.get("title", "No Title"),
                "link": entry.get("link", ""),
                "published_utc": entry.get("published", ""),
                "source": "Yahoo" if ticker else "CNBC",
                "summary": entry.get("summary", "")[:200]
            })
        return results
    except Exception as exc:
        log.warning("news_fetch_failed", error=str(exc))
        return []
