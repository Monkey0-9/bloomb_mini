"""
NewsTradeSignalEngine - Generating actionable trade signals from OSINT.

Fuses live news sentiment with Knowledge Graph connectivity and 
Swarm intelligence to produce institutional-grade alpha signals.
"""
import logging
from datetime import UTC, datetime
from typing import Any

from src.swarm.graphrag_engine import get_graphrag_engine
from src.intelligence.mirofish_agent import agent as mirofish_agent
from src.live.market import get_prices
from src.swarm.performance_audit import get_swarm_auditor

logger = logging.getLogger(__name__)

class NewsTradeSignalEngine:
    def __init__(self):
        self.graph_engine = get_graphrag_engine()
        self.swarm_auditor = get_swarm_auditor()

    async def generate_signals(self, news_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Analyzes news items and generates high-conviction trade signals.
        """
        signals = []
        market_data = get_prices()

        for item in news_items:
            title = item.get('title', '')
            summary = item.get('summary', '')
            
            # 1. Identify impacted nodes via Knowledge Graph
            impacted_nodes = []
            for node_id, node in self.graph_engine.graph.nodes.items():
                if node.name.upper() in title.upper():
                    impacted_nodes.append(node)

            if not impacted_nodes:
                continue

            for node in impacted_nodes:
                # 2. Trace impact to tickers
                impact_analysis = self.graph_engine.analyze_facility_event(node.id, "news_event", 0.7)
                
                for affected in impact_analysis.get('affected_tickers', []):
                    ticker = affected['ticker']
                    
                    # 3. Validate with Swarm (Parallel Simulation)
                    swarm_forecast = await mirofish_agent.generate_forecast(
                        requirement=f"Analyze impact of '{title}' on {ticker}",
                        persona="Standard"
                    )
                    
                    # 4. Cross-reference with Performance Audit
                    persona_weights = self.swarm_auditor.get_persona_weights()
                    confidence_adj = persona_weights.get("Standard", 0.5) * affected['confidence']

                    if confidence_adj > 0.4:
                        signals.append({
                            "ticker": ticker,
                            "action": swarm_forecast.get('action', 'WATCH'),
                            "conviction": "HIGH" if confidence_adj > 0.7 else "MEDIUM",
                            "reasoning": f"News event '{title}' impacting {node.name}. Graph path: {affected['reasoning']}",
                            "confidence": round(float(confidence_adj * 100), 1),
                            "timestamp": datetime.now(UTC).isoformat(),
                            "source_news": title,
                            "price_at_signal": market_data.get(ticker, {}).get('price')
                        })

        return sorted(signals, key=lambda x: x['confidence'], reverse=True)

# Singleton
_signal_engine: NewsTradeSignalEngine | None = None

def get_news_trade_signal_engine() -> NewsTradeSignalEngine:
    global _signal_engine
    if _signal_engine is None:
        _signal_engine = NewsTradeSignalEngine()
    return _signal_engine
