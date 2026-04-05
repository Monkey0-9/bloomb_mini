"""
GraphEvolver - Autonomous Knowledge Graph Evolution.

Uses LLMs to extract new entities and relationships from news/filings 
to dynamically update the FacilityMarketGraph.
"""
import json
import logging
import os
from typing import Any

from anthropic import Anthropic
from src.swarm.graphrag_engine import KnowledgeNode, KnowledgeEdge, get_graphrag_engine

logger = logging.getLogger(__name__)

class GraphEvolver:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        self.graph_engine = get_graphrag_engine()

    async def evolve_from_news(self, news_items: list[dict[str, Any]]):
        """
        Processes a list of news items and extracts graph updates.
        """
        if not self.client:
            logger.warning("Anthropic client not available, skipping graph evolution")
            return

        # Batch news items to save tokens
        batch_size = 5
        for i in range(0, len(news_items), batch_size):
            batch = news_items[i:i+batch_size]
            await self._process_batch(batch)

    async def _process_batch(self, batch: list[dict[str, Any]]):
        """Extracts relationships from a batch of news items."""
        news_text = "\\n\\n".join([
            f"Title: {item.get('title')}\\nSummary: {item.get('summary', '')}"
            for item in batch
        ])

        system_prompt = """
        You are a Knowledge Graph Engineer for a global trade intelligence system.
        Your task is to extract corporate and industrial relationships from news summaries.
        Focus on:
        - Companies owning/operating facilities (ports, mines, factories, terminals).
        - Companies being parent/subsidiary of each other.
        - Companies supplying or competing with each other.
        - Tickers associated with companies.
        - Chokepoints (Suez, Hormuz, etc.) affecting specific tickers.

        Return ONLY a JSON object with two lists: 'nodes' and 'edges'.
        Nodes should have: id, type (facility, company, ticker, sector, chokepoint), name, attributes (dict).
        Edges should have: source, target, relation (operates, owns, supplies, competes_with, trades_as, depends_on, parent_of, subsidiary_of), strength (0.0-1.0), evidence (string).
        """

        user_prompt = f"Extract knowledge graph updates from these news items:\\n\\n{news_text}"

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            content = response.content[0].text
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            updates = json.loads(content)
            self._apply_updates(updates)
            
        except Exception as e:
            logger.error(f"Error evolving graph from news: {e}")

    def _apply_updates(self, updates: dict[str, Any]):
        """Applies extracted nodes and edges to the graph engine."""
        for node_data in updates.get('nodes', []):
            node = KnowledgeNode(
                id=node_data['id'],
                type=node_data['type'],
                name=node_data['name'],
                attributes=node_data.get('attributes', {}),
                importance=node_data.get('importance', 1.0)
            )
            self.graph_engine.graph.add_node(node)
            logger.info(f"Added/Updated Node: {node.id}")

        for edge_data in updates.get('edges', []):
            edge = KnowledgeEdge(
                source=edge_data['source'],
                target=edge_data['target'],
                relation=edge_data['relation'],
                strength=edge_data.get('strength', 0.5),
                evidence=[edge_data.get('evidence', 'Extracted from news')]
            )
            # Verify source and target exist
            if edge.source in self.graph_engine.graph.nodes and edge.target in self.graph_engine.graph.nodes:
                self.graph_engine.graph.add_edge(edge)
                logger.info(f"Added Edge: {edge.source} -> {edge.target} ({edge.relation})")
            else:
                logger.warning(f"Skipping edge {edge.source}->{edge.target}: Node missing")

# Singleton
_evolver: GraphEvolver | None = None

def get_graph_evolver() -> GraphEvolver:
    global _evolver
    if _evolver is None:
        _evolver = GraphEvolver()
    return _evolver
