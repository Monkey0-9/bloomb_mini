"""
BlackSwanDetector - Identifying high-impact, low-probability events.

Uses GDELT news and the FacilityMarketGraph to detect potential 
systemic disruptions before they manifest in price.
"""
import logging
from typing import Any

from src.swarm.graphrag_engine import get_graphrag_engine
from src.live.news import get_all_news

logger = logging.getLogger(__name__)

class BlackSwanDetector:
    def __init__(self):
        self.graph_engine = get_graphrag_engine()
        self.high_risk_keywords = [
            "blockade", "sanction", "seizure", "cyberattack", 
            "assassination", "coup", "nuclear", "embargo",
            "tsunami", "eruption", "unrest", "revolution"
        ]

    async def detect_events(self) -> list[dict[str, Any]]:
        """
        Analyzes news for Black Swan events and maps them to graph nodes.
        """
        news = await get_all_news(max_per_feed=50)
        alerts = []

        for item in news:
            title_upper = item.title.upper()
            
            # Check for high-risk keywords
            matches = [kw for kw in self.high_risk_keywords if kw.upper() in title_upper]
            if not matches:
                continue

            # Identify affected entities from the graph
            affected_nodes = []
            for node_id, node in self.graph_engine.graph.nodes.items():
                if node.name.upper() in title_upper or node.id.upper() in title_upper:
                    affected_nodes.append(node)

            if affected_nodes:
                # Calculate systemic impact
                severity = 0.8 # Default for black swan keywords
                impacts = []
                for node in affected_nodes:
                    impact = self.graph_engine.analyze_facility_event(node.id, "black_swan", severity)
                    impacts.append(impact)

                alerts.append({
                    "event": item.title,
                    "url": item.url,
                    "keywords": matches,
                    "affected_entities": [n.name for n in affected_nodes],
                    "systemic_impact": impacts,
                    "severity": severity,
                    "timestamp": item.published
                })

        return sorted(alerts, key=lambda x: x['severity'], reverse=True)

# Singleton
_detector: BlackSwanDetector | None = None

def get_black_swan_detector() -> BlackSwanDetector:
    global _detector
    if _detector is None:
        _detector = BlackSwanDetector()
    return _detector
