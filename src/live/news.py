import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx
import structlog
from dotenv import load_dotenv

load_dotenv()

log = structlog.get_logger()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

RSS_FEEDS = {
    "reuters_biz":   ("https://feeds.reuters.com/reuters/businessNews", "financial"),
    "reuters_world": ("https://feeds.reuters.com/Reuters/worldNews",    "geopolitics"),
    "tradewinds":    ("https://www.tradewindsnews.com/rss",            "shipping"),
    "hellenic":      ("https://www.hellenicshippingnews.com/feed/",    "shipping"),
    "splash247":     ("https://splash247.com/feed/",                   "shipping"),
    "oilprice":      ("https://oilprice.com/rss/main",                 "energy"),
    "mining":        ("https://www.mining.com/feed/",                  "metals"),
    "defenseone":    ("https://www.defenseone.com/rss/all/",           "military"),
    "bellingcat":    ("https://www.bellingcat.com/feed/",              "osint"),
    "spaceflightnow":("https://spaceflightnow.com/feed/",             "satellite"),
    "sec_8k":        (("https://www.sec.gov/cgi-bin/browse-edgar"
                       "?action=getcurrent&type=8-K&count=20&output=atom"), "filings"),
    "marinelink":    ("https://www.marinelink.com/rss/news",           "shipping"),
}

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

@dataclass
class NewsItem:
    title:    str
    summary:  str
    url:      str
    source:   str
    category: str
    published: str
    tickers:  list[str] = field(default_factory=list)

_news_cache: list[NewsItem] = []
_news_ts:   float = 0.0
NEWS_TTL = 300.0  # 5 minutes

async def fetch_newsapi(query: str = "global trade OR shipping OR energy",
                 max_results: int = 20) -> list[NewsItem]:
    """Fetch real-time news via NewsAPI.org."""
    if not NEWSAPI_KEY:
        return []

    try:
        log.info("fetching_newsapi", query=query)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://newsapi.org/v2/everything", params={
                "q": query,
                "apiKey": NEWSAPI_KEY,
                "sortBy": "publishedAt",
                "pageSize": max_results
            })

        if resp.status_code != 200:
            log.warning("newsapi_error", status=resp.status_code, text=resp.text)
            return []

        articles = resp.json().get("articles", [])
        return [
            NewsItem(
                title = a.get("title", ""),
                summary = a.get("description", "")[:300] if a.get("description") else "",
                url = a.get("url", ""),
                source = a.get("source", {}).get("name", "NewsAPI"),
                category = "newsapi",
                published = a.get("publishedAt", "")
            )
            for a in articles
        ]
    except Exception as e:
        log.error("newsapi_exception", error=str(e))
        return []

async def fetch_rss(source_key: str, url: str, category: str,
              max_items: int = 6) -> list[NewsItem]:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "SatTrade/2.0 research@sattrade.io"})
            resp.raise_for_status()
            text = resp.text

        feed = feedparser.parse(text)
        items = []
        for e in feed.entries[:max_items]:
            try:
                pub = parsedate_to_datetime(e.get("published", "")).isoformat()
            except Exception:
                pub = datetime.now(UTC).isoformat()
            items.append(NewsItem(
                title    = e.get("title",   ""),
                summary  = e.get("summary", "")[:300] if e.get("summary") else "",
                url      = e.get("link",    ""),
                source   = source_key,
                category = category,
                published= pub,
            ))
        return items
    except Exception as e:
        log.warning("rss_error", source=source_key, error=str(e))
        return []

async def fetch_gdelt(query: str, max_records: int = 15) -> list[NewsItem]:
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(GDELT_URL, params={
                "query":      query,
                "mode":       "artlist",
                "maxrecords": max_records,
                "format":     "json",
                "sort":       "DateDesc",
            })
        articles = resp.json().get("articles", [])
        return [
            NewsItem(
                title    = a.get("title", ""),
                summary  = "",
                url      = a.get("url", ""),
                source   = f"gdelt:{a.get('domain','')}",
                category = "gdelt",
                published= a.get("seendate", ""),
            )
            for a in articles
        ]
    except Exception as e:
        log.error("gdelt_error", query=query, error=str(e))
        return []

TICKER_KEYWORDS = {
    "AAPL": ["apple", "iphone", "tim cook"],
    "TSLA": ["tesla", "elon musk", "ev market"],
    "NVDA": ["nvidia", "h100", "ai chip"],
    "XOM":  ["exxon", "crude oil", "shale"],
    "ZIM":  ["zim integrated", "container freight"],
    "MAERSK": ["maersk", "moller-maersk"],
    "AMKBY": ["maersk", "moller-maersk"],
    "MT":   ["arcelormittal", "steel production"],
    "LNG":  ["cheniere", "natural gas export"],
    "BA":   ["boeing", "737 max", "dreamliner"],
}

def _extract_tickers(text: str) -> list[str]:
    found = []
    text_lower = text.lower()
    for ticker, keywords in TICKER_KEYWORDS.items():
        if ticker.lower() in text_lower or any(kw in text_lower for kw in keywords):
            found.append(ticker)
    return found

async def get_all_news(max_per_feed: int = 5) -> list[NewsItem]:
    global _news_cache, _news_ts

    now = time.time()
    if _news_cache and (now - _news_ts) < NEWS_TTL:
        return _news_cache

    tasks = []

    # 1. Primary Source: NewsAPI
    tasks.append(fetch_newsapi())

    # 2. Secondary Sources (Enrichment)
    for source_key, (url, category) in RSS_FEEDS.items():
        tasks.append(fetch_rss(source_key, url, category, max_per_feed))

    for query in ["shipping tanker freight", "military conflict"]:
        tasks.append(fetch_gdelt(query, max_records=8))

    results = await asyncio.gather(*tasks)

    items: list[NewsItem] = []
    for res in results:
        items.extend(res)

    # Deduplicate by URL
    seen: set[str] = set()
    deduped = []
    for item in items:
        if item.url and item.url not in seen:
            seen.add(item.url)
            # Add extracted tickers
            item.tickers = _extract_tickers(item.title + " " + item.summary)
            deduped.append(item)

    deduped.sort(key=lambda x: x.published, reverse=True)
    _news_cache = deduped[:200]
    _news_ts    = now
    return _news_cache
