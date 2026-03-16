"""
News Feed Aggregator — RSS + SEC EDGAR + NewsAPI (free dev tier).
Aggregates news from multiple free sources into a unified format.
"""
import datetime
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import httpx

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# Top free RSS feeds for financial/supply chain news
RSS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "CNBC Economy": "https://search.cnbc.com/rs/search/combinedcombined/articleType/ARTICLES/hasThumbnail/true/.rss",
    "Maritime Executive": "https://maritime-executive.com/rss",
    "Lloyd's List": "https://lloydslist.maritimeintelligence.informa.com/rss",
    "SEC EDGAR": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&dateb=&owner=include&count=20&output=atom",
}


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published: str
    summary: str = ""
    tickers: list[str] = field(default_factory=list)
    category: str = "general"


def _parse_rss(source_name: str, url: str, limit: int = 10) -> list[NewsItem]:
    """Parse an RSS/Atom feed and return NewsItem objects."""
    items = []
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        # Handle both RSS and Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for entry in entries[:limit]:
            title_el = entry.find("title") or entry.find("atom:title", ns)
            link_el = entry.find("link") or entry.find("atom:link", ns)
            pub_el = (
                entry.find("pubDate")
                or entry.find("published")
                or entry.find("atom:published", ns)
            )
            desc_el = (
                entry.find("description")
                or entry.find("summary")
                or entry.find("atom:summary", ns)
            )

            title = (title_el.text or "").strip() if title_el is not None else ""
            link = ""
            if link_el is not None:
                link = link_el.get("href") or link_el.text or ""
            pub = (pub_el.text or "").strip() if pub_el is not None else ""
            desc = (desc_el.text or "").strip() if desc_el is not None else ""

            if title:
                items.append(NewsItem(
                    title=title,
                    url=link,
                    source=source_name,
                    published=pub,
                    summary=desc[:300],
                ))
    except Exception:
        pass
    return items


def _fetch_newsapi(query: str = "shipping OR LNG OR steel OR commodities", limit: int = 10) -> list[NewsItem]:
    """Fetch from NewsAPI dev tier (100 req/day free)."""
    if not NEWSAPI_KEY:
        return []
    try:
        resp = httpx.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "sortBy": "publishedAt",
                "pageSize": limit,
                "language": "en",
            },
            headers={"X-Api-Key": NEWSAPI_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            NewsItem(
                title=a.get("title", ""),
                url=a.get("url", ""),
                source=a.get("source", {}).get("name", "NewsAPI"),
                published=a.get("publishedAt", ""),
                summary=a.get("description", "")[:300],
                category="markets",
            )
            for a in data.get("articles", [])
        ]
    except Exception:
        return []


def get_news_feed(limit_per_source: int = 5) -> list[dict]:
    """Aggregate news from all free sources and return as list of dicts."""
    all_items: list[NewsItem] = []

    # RSS sources
    for name, url in RSS_FEEDS.items():
        all_items.extend(_parse_rss(name, url, limit=limit_per_source))

    # NewsAPI (if key is available)
    all_items.extend(_fetch_newsapi(limit=limit_per_source))

    # Sort by published date descending (best-effort)
    all_items.sort(key=lambda x: x.published, reverse=True)

    return [
        {
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "published": item.published,
            "summary": item.summary,
            "tickers": item.tickers,
            "category": item.category,
        }
        for item in all_items
    ]
