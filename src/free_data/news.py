"""
Free news data layer using RSS feeds.
"""
import httpx
import feedparser
import structlog
from datetime import datetime

log = structlog.get_logger(__name__)

RSS_FEEDS = {
    "YAHOO_FINANCE": "https://finance.yahoo.com/news/rssindex",
    "WSJ_MARKETS": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "FT_MARKETS": "https://www.ft.com/markets?format=rss",
    "CNBC_MARKETS": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069"
}

def get_latest_news(limit: int = 20) -> list[dict]:
    """Fetch and aggregate news from multiple free RSS feeds."""
    all_news = []
    for source, url in RSS_FEEDS.items():
        try:
            resp = httpx.get(url, timeout=10)
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:limit]:
                all_news.append({
                    "source": source,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": getattr(entry, "summary", ""),
                    "published": getattr(entry, "published", datetime.now().isoformat()),
                })
        except Exception as e:
            log.error("news_fetch_failed", source=source, error=str(e))
    
    # Sort by date if possible
    return sorted(all_news, key=lambda x: x["published"], reverse=True)[:limit]

def get_sentiment_for_ticker(ticker: str) -> dict:
    """Mock-up ticker sentiment based on news titles."""
    news = get_latest_news(50)
    relevant = [n for n in news if ticker.lower() in n["title"].lower() or ticker.lower() in n["summary"].lower()]
    
    if not relevant:
        return {"sentiment": "NEUTRAL", "count": 0}
        
    pos_keywords = ["surge", "gain", "buy", "growth", "up", "bullish"]
    neg_keywords = ["drop", "fall", "sell", "loss", "down", "bearish"]
    
    score = 0
    for n in relevant:
        text = (n["title"] + n["summary"]).lower()
        score += sum(1 for w in pos_keywords if w in text)
        score -= sum(1 for w in neg_keywords if w in text)
    
    return {
        "sentiment": "BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
        "score": score,
        "count": len(relevant)
    }
