import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from src.api.agents.base import BaseAgent
from src.live.news import get_all_news

log = logging.getLogger(__name__)

class NewsAgent(BaseAgent):
    """
    Electronic News Surveillance: Aggregates global feeds via NewsAPI, RSS, and GDELT.
    """

    def __init__(self) -> None:
        super().__init__("news")
        self.status = "ACTIVE"
        self.last_sync = datetime.now(UTC)

    async def get_state(self) -> dict[str, Any]:
        return {
            "feeds": ["NEWSAPI", "GDELT", "RSS_SHIPPING", "REUTERS"],
            "status": "OPERATIONAL",
            "overall_sentiment": "dynamic"
        }

    async def get_latest_news(self, ticker: str = None) -> list[dict[str, Any]]:
        """Fetches real-time news via unified news module."""
        try:
            # get_all_news is synchronous with caching, but we'll run it in executor if needed.
            # For simplicity, we call it directly as it has internal TTL.
            loop = asyncio.get_running_loop()
            news_items = await loop.run_in_executor(None, get_all_news)

            articles = []
            for item in news_items:
                # Basic sentiment estimation if needed, or default to 0.0
                sentiment = 0.0 # Placeholder for real NLP sentiment analysis

                # Filter by ticker if provided
                if ticker and ticker.upper() not in item.title.upper() and ticker.upper() not in item.summary.upper():
                    continue

                articles.append({
                    "title": item.title,
                    "url": item.url,
                    "summary": item.summary,
                    "source": item.source,
                    "sentiment": sentiment,
                    "urgency": "HIGH" if "escalation" in item.title.lower() or "surge" in item.title.lower() else "MEDIUM",
                    "impacted": [ticker.upper()] if ticker else [item.category.upper()],
                    "timestamp": item.published
                })

            return articles[:50]
        except Exception as e:
            log.error(f"news_agent_error: {e}")
            return []

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "NEWS_BRIEF":
            ticker = params.get("ticker")
            articles = await self.get_latest_news(ticker)
            return {"articles": articles}
        elif task_type == "RESEARCH_QUERY":
            ticker = params.get("query")
            articles = await self.get_latest_news(ticker)
            sentiment = "POSITIVE" if any(a["sentiment"] > 0 for a in articles) else "NEGATIVE" if any(a["sentiment"] < 0 for a in articles) else "NEUTRAL"
            return {
                "intent": "NEWS_INTEL",
                "synthesis": f"News Surveillance for '{ticker or 'Global'}': Found {len(articles)} relevant articles. Sentiment leaning {sentiment}. Physical disruptions mentioned in {sum(1 for a in articles if 'disrupt' in a['title'].lower())} feeds.",
                "data": {"articles": articles[:5], "sentiment": sentiment},
                "timestamp": datetime.now(UTC).isoformat()
            }

        return {"error": "Unknown task type"}
