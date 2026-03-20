import asyncio
from typing import Any, Dict
from src.api.agents.base import BaseAgent
from src.data.news import fetch_all_news

class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__("news")

    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.log.info("processing_news_task", task_id=task.get("id"))
        news_items = await asyncio.to_thread(fetch_all_news)
        
        # Check if we have input from a previous task
        thermal_input = task.get("input_t1", {})
        if thermal_input:
            # Maybe filter news based on tickers found in thermal anomalies
            tickers = set()
            for a in thermal_input.get("anomalies", []):
                tickers.update(a.get("tickers", []))
            
            if tickers:
                news_items = [i for i in news_items if any(t in i.tickers_mentioned for t in tickers)]

        return {
            "status": "success",
            "count": len(news_items),
            "news": [
                {"title": i.title, "source": i.source, "tickers": i.tickers_mentioned}
                for i in news_items[:5]
            ]
        }
