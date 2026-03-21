import feedparser  # type: ignore[import-untyped]
import httpx
import structlog  # type: ignore[import-untyped]
from datetime import datetime, timezone
from dataclasses import dataclass
from email.utils import parsedate_to_datetime

log = structlog.get_logger()

RSS_FEEDS = {
    # Financial
    "reuters_markets":    "https://feeds.reuters.com/reuters/businessNews",
    "reuters_world":      "https://feeds.reuters.com/Reuters/worldNews",
    "ft_markets":         "https://www.ft.com/rss/home/uk",
    "cnbc_markets":       "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "wsj_markets":        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    # Shipping / Maritime
    "tradewinds":         "https://www.tradewindsnews.com/rss",
    "hellenicshipping":   "https://www.hellenicshippingnews.com/feed/",
    "splash247":          "https://splash247.com/feed/",
    "marinelink":         "https://www.marinelink.com/rss/news",
    "lloydslist":         "https://lloydslist.maritimeintelligence.informa.com/rss",
    # Energy
    "oilprice":           "https://oilprice.com/rss/main",
    "naturalgasintel":    "https://www.naturalgasintel.com/rss",
    # Commodities
    "mineweb":            "https://www.mining.com/feed/",
    # SEC Filings — real-time 8-K events
    "sec_8k":             ("https://www.sec.gov/cgi-bin/browse-edgar"
                           "?action=getcurrent&type=8-K&dateb=&owner=include"
                           "&count=40&search_text=&output=atom"),
    # OSINT / Defence
    "janes":              "https://www.janes.com/feeds/news",
    "defenseone":         "https://www.defenseone.com/rss/all/",
    "spaceweather":       "https://spaceweather.com/rss.xml",
}

TOPIC_KEYWORDS = {
    "shipping": ["vessel","ship","port","container","freight","cargo","TEU","BDI"],
    "energy":   ["LNG","crude","oil","pipeline","refinery","OPEC","tanker"],
    "metals":   ["steel","iron ore","aluminium","copper","zinc","ArcelorMittal"],
    "macro":    ["Fed","ECB","inflation","GDP","recession","rate","treasury"],
    "satellite":["satellite","Sentinel","launch","orbit","SpaceX","ESA","NASA"],
    "geopolitics":["sanctions","missile","military","navy","conflict","war","NATO"],
    "tech":     ["semiconductor","chip","AI","TSMC","NVIDIA","supply chain"],
}


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    published: str
    topics: list[str]
    tickers_mentioned: list[str]


def fetch_all_news(max_per_feed: int = 5) -> list[NewsItem]:
    """
    Fetch news from all RSS feeds.
    Returns items sorted by recency, topic-tagged, ticker-matched.
    """
    all_items = []
    ticker_to_name = {
        "AMKBY": ["maersk","apm"], "ZIM": ["zim integrated"],
        "MT": ["arcelormittal","arcelor"], "LNG": ["cheniere"],
        "AAPL": ["apple"], "NVDA": ["nvidia"], "TSLA": ["tesla"],
        "SHEL.L": ["shell"], "BP.L": ["bp plc","british petroleum"],
        "XOM": ["exxon"], "CVX": ["chevron"],
        "BHP": ["bhp"], "VALE": ["vale sa"],
        "7203.T": ["toyota"], "005930.KS": ["samsung"],
        "1919.HK": ["cosco"], "700.HK": ["tencent"],
    }

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            headers = {"User-Agent": "SatTrade/1.0 (research; contact@sattrade.io)"}
            feed = feedparser.parse(feed_url, request_headers=headers)
            entries = feed.entries[:max_per_feed]

            for entry in entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")[:300]
                link = entry.get("link", "")
                published_str = entry.get("published", "")

                # Topic classification
                text_lower = (title + " " + summary).lower()
                topics = [
                    topic for topic, keywords in TOPIC_KEYWORDS.items()
                    if any(kw.lower() in text_lower for kw in keywords)
                ]
                if not topics:
                    topics = ["general"]

                # Ticker mention detection
                tickers = [
                    ticker for ticker, keywords in ticker_to_name.items()
                    if any(kw in text_lower for kw in keywords)
                ]

                # Parse publication time
                try:
                    pub_dt = parsedate_to_datetime(published_str)
                    pub_iso = pub_dt.isoformat()
                except Exception:
                    pub_iso = datetime.now(timezone.utc).isoformat()

                all_items.append(NewsItem(
                    title=title,
                    summary=summary,
                    url=link,
                    source=source_name,
                    published=pub_iso,
                    topics=topics,
                    tickers_mentioned=tickers,
                ))

        except Exception as e:
            log.warning("rss_feed_error", source=source_name, error=str(e))

    # Sort by recency
    all_items.sort(key=lambda x: x.published, reverse=True)
    return all_items[:200]  # return top 200 most recent
