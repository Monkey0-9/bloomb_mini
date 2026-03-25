"""
Global News & OSINT Engine — Zero-key RSS and GDELT integration.
Fetches real-time maritime, defense, and financial news globally.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import feedparser
import httpx

logger = logging.getLogger(__name__)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=artlist&format=json"

RSS_FEEDS = {
    "Maritime": ["https://www.tradewindsnews.com/rss/", "https://www.hellenicshippingnews.com/feed/"],
    "Defense": ["https://www.defenseone.com/rss/all/"],
    "Financial": ["https://feeds.reuters.com/reuters/businessNews", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&owner=exclude&output=atom"]
}

@dataclass
class NewsArticle:
    source: str
    title: str
    link: str
    pub_date: str
    summary: str = ""

async def get_rss_news(category: str) -> list[NewsArticle]:
    """Fetch news from multiple RSS feeds by category."""
    feeds = RSS_FEEDS.get(category, [])
    articles = []
    for f_url in feeds:
        try:
            feed = feedparser.parse(f_url)
            for entry in feed.entries[:10]:
                articles.append(NewsArticle(
                    source=category,
                    title=entry.get("title", "No Title"),
                    link=entry.get("link", ""),
                    pub_date=entry.get("published", "")
                ))
        except Exception as e:
            logger.error(f"RSS error for %s: %s", f_url, e)
    return articles

async def query_gdelt(query: str) -> list[NewsArticle]:
    """Query GDELT live API for real-time global events. No key needed."""
    try:
        url = GDELT_URL.format(query=query)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            data = resp.json()
            articles = []
            for art in data.get("articles", [])[:15]:
                articles.append(NewsArticle(
                    source="GDELT",
                    title=art["title"],
                    link=art["url"],
                    pub_date=art["seendate"],
                    summary=art.get("sourcecountry", "")
                ))
            return articles
    except Exception as e:
        logger.error(f"GDELT error for %s: %s", query, e)
        return []
