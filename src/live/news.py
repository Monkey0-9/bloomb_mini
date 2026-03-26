"""
Real news from RSS feeds and GDELT.
All free. No key. Always public.
"""
import time
import httpx
import feedparser
import structlog
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

log = structlog.get_logger()

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

_news_cache: list[NewsItem] = []
_news_ts:   float = 0.0
NEWS_TTL = 300.0  # 5 minutes

def fetch_rss(source_key: str, url: str, category: str,
              max_items: int = 6) -> list[NewsItem]:
    try:
        feed = feedparser.parse(url,
            request_headers={"User-Agent": "SatTrade/2.0 research@sattrade.io"})
        items = []
        for e in feed.entries[:max_items]:
            try:
                pub = parsedate_to_datetime(e.get("published", "")).isoformat()
            except Exception:
                pub = datetime.now(timezone.utc).isoformat()
            items.append(NewsItem(
                title    = e.get("title",   ""),
                summary  = e.get("summary", "")[:300],
                url      = e.get("link",    ""),
                source   = source_key,
                category = category,
                published= pub,
            ))
        return items
    except Exception as e:
        log.warning("rss_error", source=source_key, error=str(e))
        return []

def fetch_gdelt(query: str, max_records: int = 15) -> list[NewsItem]:
    """GDELT Article Search API — zero key, 2.5M articles/day."""
    try:
        resp = httpx.get(GDELT_URL, params={
            "query":      query,
            "mode":       "artlist",
            "maxrecords": max_records,
            "format":     "json",
            "sort":       "DateDesc",
        }, timeout=12)
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

def get_all_news(max_per_feed: int = 5) -> list[NewsItem]:
    global _news_cache, _news_ts

    now = time.time()
    if _news_cache and (now - _news_ts) < NEWS_TTL:
        return _news_cache

    items: list[NewsItem] = []
    for source_key, (url, category) in RSS_FEEDS.items():
        items.extend(fetch_rss(source_key, url, category, max_per_feed))

    # GDELT for shipping/conflict/satellite intelligence
    for query in ["shipping tanker freight", "military conflict", "satellite launch"]:
        items.extend(fetch_gdelt(query, max_records=8))

    # Deduplicate by URL
    seen: set[str] = set()
    deduped = []
    for item in items:
        if item.url and item.url not in seen:
            seen.add(item.url)
            deduped.append(item)

    deduped.sort(key=lambda x: x.published, reverse=True)
    _news_cache = deduped[:200]
    _news_ts    = now
    return _news_cache
