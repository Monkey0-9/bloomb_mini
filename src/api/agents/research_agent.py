import logging
from typing import Any

from src.api.agents.base import BaseAgent
from src.intelligence.engine import GlobalIntelligenceEngine
from src.signals.composite_score import CompositeScorer

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """
    Uses Multi-Signal Fusion (Alternative Data) to synthesize 
    institutional-grade investment research.
    """
    def __init__(self) -> None:
        super().__init__("research")
        self.engine = GlobalIntelligenceEngine()
        self.scorer = CompositeScorer()

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        query = (params.get("query") or "").upper()
        self.log.info("processing_research_query", query=query)

        # 1. Fetch high-fidelity composite score (Alternative Data Fusion)
        result = await self.scorer.score(query)

        # 2. Extract synthesis from the score result
        sentiment = result["direction"]
        score = result["final_score"] * 50 + 50  # -1..1 -> 0..100

        # 3. Build detailed synthesis (The "Bloomberg" Why)
        reasons = []
        for sig in result.get("contributing_signals", []):
            if sig.get("impact") != "NEUTRAL":
                reasons.append(f"{sig['headline']} ({sig['impact']})")

        if not reasons:
            reasons.append("No strong physical anomalies detected; sentiment is baseline neutral.")

        return {
            "status": "success",
            "ticker": query,
            "sentiment": sentiment,
            "score": round(score, 1),
            "synthesis": (
                f"SatTrade Intelligence Synthesis for {query}: {result['headline']}. "
                f"Contributing factors: " + " | ".join(reasons[:3])
            ),
            "data_points": {
                "composite_score": result["composite_score"],
                "regime": result["regime"],
                "confidence": result["confidence"],
                "freshness": result["ic_half_life_tag"]
            },
            "signals": result["contributing_signals"],
            "ticker_confirm": query,
            "confidence_score": result["confidence"]
        }
