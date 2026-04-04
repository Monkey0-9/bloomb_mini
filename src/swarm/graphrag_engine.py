"""
GraphRAG Knowledge Engine - Facility to market relationship graph.

Inspired by MiroFish GraphRAG architecture:
- Extracts reality seeds (facilities, companies, tickers, sectors)
- Builds knowledge graph of relationships
- Enables multi-hop reasoning (facility → company → sector → market impact)
- Supports emergent insight from graph traversal
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""
    id: str
    type: str  # 'facility', 'company', 'ticker', 'sector', 'commodity', 'chokepoint', 'region'
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0  # 0.0 to 1.0


@dataclass
class KnowledgeEdge:
    """An edge/relationship in the knowledge graph."""
    source: str  # Node ID
    target: str  # Node ID
    relation: str  # 'operates', 'owns', 'supplies', 'competes_with', 'located_in', 'ships_through', 'depends_on'
    strength: float  # 0.0 to 1.0, how strong the relationship
    evidence: list[str] = field(default_factory=list)  # Source of this relationship


@dataclass
class GraphPath:
    """A path through the knowledge graph with reasoning."""
    nodes: list[KnowledgeNode]
    edges: list[KnowledgeEdge]
    reasoning: str
    impact_score: float  # Estimated market impact along this path


class FacilityMarketGraph:
    """
    Knowledge graph linking satellite-detectable facilities to market impact.
    
    Enables queries like:
    - "What tickers are affected by ArcelorMittal Dunkirk activity?"
    - "Which companies compete with this facility?"
    - "What happens to X if Hormuz has a disruption?"
    """

    def __init__(self):
        self.nodes: dict[str, KnowledgeNode] = {}
        self.edges: dict[str, list[KnowledgeEdge]] = defaultdict(list)  # source -> edges
        self._reverse_edges: dict[str, list[KnowledgeEdge]] = defaultdict(list)  # target -> edges

    def add_node(self, node: KnowledgeNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: KnowledgeEdge) -> None:
        """Add an edge to the graph."""
        self.edges[edge.source].append(edge)
        self._reverse_edges[edge.target].append(edge)

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, relation: str | None = None) -> list[KnowledgeNode]:
        """Get all nodes connected to given node."""
        edges = self.edges.get(node_id, [])
        if relation:
            edges = [e for e in edges if e.relation == relation]
        return [self.nodes[e.target] for e in edges if e.target in self.nodes]

    def find_paths(self,
                   start_id: str,
                   end_id: str,
                   max_depth: int = 4) -> list[GraphPath]:
        """
        Find all paths between two nodes up to max_depth hops.
        
        Uses BFS to find paths with reasoning about market impact.
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return []

        paths = []
        visited = set()

        # BFS with path tracking
        queue = [(start_id, [start_id], [], 0)]

        while queue:
            current, node_path, edge_path, depth = queue.pop(0)

            if current == end_id and depth > 0:
                # Found a path
                nodes = [self.nodes[n] for n in node_path]
                reasoning = self._generate_path_reasoning(nodes, edge_path)
                impact = self._calculate_path_impact(edge_path)

                paths.append(GraphPath(
                    nodes=nodes,
                    edges=edge_path,
                    reasoning=reasoning,
                    impact_score=impact
                ))
                continue

            if depth >= max_depth:
                continue

            # Explore neighbors
            for edge in self.edges.get(current, []):
                if edge.target not in visited and edge.target not in node_path:
                    queue.append((
                        edge.target,
                        node_path + [edge.target],
                        edge_path + [edge],
                        depth + 1
                    ))

        # Sort by impact score
        paths.sort(key=lambda p: p.impact_score, reverse=True)
        return paths

    def query_impact(self, facility_id: str) -> dict[str, Any]:
        """
        Query what tickers/sectors are impacted by a facility event.
        
        Returns:
            Dict with affected tickers, sectors, and impact reasoning
        """
        if facility_id not in self.nodes:
            return {'error': f'Facility {facility_id} not found'}

        facility = self.nodes[facility_id]

        # Find all paths from facility to tickers
        ticker_paths = []
        for node_id, node in self.nodes.items():
            if node.type == 'ticker':
                paths = self.find_paths(facility_id, node_id, max_depth=3)
                if paths:
                    ticker_paths.append({
                        'ticker': node,
                        'best_path': paths[0],  # Highest impact
                        'all_paths': paths
                    })

        # Sort by impact
        ticker_paths.sort(key=lambda x: x['best_path'].impact_score, reverse=True)

        # Group by sector
        sectors = defaultdict(list)
        for tp in ticker_paths:
            sector = tp['ticker'].attributes.get('sector', 'Unknown')
            sectors[sector].append(tp['ticker'].name)

        return {
            'facility': facility,
            'direct_tickers': [tp['ticker'].name for tp in ticker_paths[:5]],
            'all_tickers': [tp['ticker'].name for tp in ticker_paths],
            'sectors': dict(sectors),
            'total_paths': len(ticker_paths),
            'max_impact_score': ticker_paths[0]['best_path'].impact_score if ticker_paths else 0,
            'reasoning': ticker_paths[0]['best_path'].reasoning if ticker_paths else 'No direct impact paths found'
        }

    def _generate_path_reasoning(self, nodes: list[KnowledgeNode], edges: list[KnowledgeEdge]) -> str:
        """Generate human-readable reasoning for a path."""
        if not nodes or len(nodes) < 2:
            return "No path"

        parts = [f"{nodes[0].name}"]

        for i, edge in enumerate(edges):
            relation_desc = {
                'operates': 'operates',
                'owns': 'owns',
                'supplies': 'supplies to',
                'competes_with': 'competes with',
                'located_in': 'located in',
                'ships_through': 'ships through',
                'depends_on': 'depends on',
                'parent_of': 'is parent of',
                'subsidiary_of': 'is subsidiary of'
            }.get(edge.relation, edge.relation)

            parts.append(f" {relation_desc} {nodes[i+1].name}")

        return " → ".join(parts)

    def _calculate_path_impact(self, edges: list[KnowledgeEdge]) -> float:
        """Calculate cumulative impact score along a path."""
        if not edges:
            return 0.0

        # Impact decays with each hop
        total_impact = 1.0
        for i, edge in enumerate(edges):
            hop_decay = 0.8 ** i  # 1.0, 0.8, 0.64, ...
            total_impact *= edge.strength * hop_decay

        return round(total_impact, 3)

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dict."""
        return {
            'nodes': [
                {
                    'id': n.id,
                    'type': n.type,
                    'name': n.name,
                    'attributes': n.attributes,
                    'importance': n.importance
                }
                for n in self.nodes.values()
            ],
            'edges': [
                {
                    'source': e.source,
                    'target': e.target,
                    'relation': e.relation,
                    'strength': e.strength,
                    'evidence': e.evidence
                }
                for edges in self.edges.values()
                for e in edges
            ]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FacilityMarketGraph:
        """Deserialize graph from dict."""
        graph = cls()

        for n in data.get('nodes', []):
            graph.add_node(KnowledgeNode(
                id=n['id'],
                type=n['type'],
                name=n['name'],
                attributes=n.get('attributes', {}),
                importance=n.get('importance', 1.0)
            ))

        for e in data.get('edges', []):
            graph.add_edge(KnowledgeEdge(
                source=e['source'],
                target=e['target'],
                relation=e['relation'],
                strength=e['strength'],
                evidence=e.get('evidence', [])
            ))

        return graph


class GraphRAGEngine:
    """
    GraphRAG engine for facility-market knowledge extraction.
    
    Builds and maintains the knowledge graph from:
    - Public company filings
    - Industry databases  
    - Satellite facility detections
    - News/chronicle extraction
    """

    def __init__(self):
        self.graph = FacilityMarketGraph()
        self._initialize_core_graph()

    def _initialize_core_graph(self):
        """Initialize with core industrial facility relationships."""
        # ArcelorMittal network
        self._add_facility_network(
            facility_id='arcelor_dunkirk',
            facility_name='ArcelorMittal Dunkirk',
            facility_type='steel_mill',
            company='ArcelorMittal',
            ticker='MT',
            sector='Materials',
            region='Europe',
            competitors=['X', 'NUE', 'TS'],
            supplies_to=['auto', 'construction', 'shipbuilding']
        )

        # Cheniere LNG network
        self._add_facility_network(
            facility_id='sabine_pass',
            facility_name='Sabine Pass LNG',
            facility_type='lng_terminal',
            company='Cheniere Energy',
            ticker='LNG',
            sector='Energy',
            region='North America',
            competitors=['GLNG', 'GLOG'],
            supplies_to=['Europe', 'Asia', 'power_utilities']
        )

        # Port networks
        self._add_port_network(
            port_id='rotterdam',
            port_name='Port of Rotterdam',
            country='Netherlands',
            major_players=['AMKBY', 'HLAG.DE'],
            chokepoint_dependencies=['suez', 'bosphorus']
        )

        self._add_port_network(
            port_id='singapore',
            port_name='Singapore PSA',
            country='Singapore',
            major_players=['ZIM', '1919.HK'],
            chokepoint_dependencies=['malacca', 'suez']
        )

        # Chokepoints
        self._add_chokepoint('hormuz', 'Strait of Hormuz', ['XOM', 'CVX', 'LNG'], 0.20)
        self._add_chokepoint('suez', 'Suez Canal', ['AMKBY', 'ZIM', '1919.HK'], 0.12)
        self._add_chokepoint('malacca', 'Strait of Malacca', ['AMKBY', 'ZIM', 'XOM'], 0.80)

        logger.info(f"Initialized core graph with {len(self.graph.nodes)} nodes, {sum(len(e) for e in self.graph.edges.values())} edges")

    def _add_facility_network(self, **kwargs):
        """Add a complete facility-company-ticker network."""
        # Facility node
        self.graph.add_node(KnowledgeNode(
            id=kwargs['facility_id'],
            type='facility',
            name=kwargs['facility_name'],
            attributes={
                'facility_type': kwargs['facility_type'],
                'region': kwargs['region']
            },
            importance=0.9
        ))

        # Company node
        company_id = f"company_{kwargs['company'].lower().replace(' ', '_')}"
        self.graph.add_node(KnowledgeNode(
            id=company_id,
            type='company',
            name=kwargs['company'],
            attributes={'sector': kwargs['sector']},
            importance=0.8
        ))

        # Ticker node
        self.graph.add_node(KnowledgeNode(
            id=f"ticker_{kwargs['ticker']}",
            type='ticker',
            name=kwargs['ticker'],
            attributes={'sector': kwargs['sector']},
            importance=0.7
        ))

        # Sector node
        sector_id = f"sector_{kwargs['sector'].lower()}"
        if sector_id not in self.graph.nodes:
            self.graph.add_node(KnowledgeNode(
                id=sector_id,
                type='sector',
                name=kwargs['sector'],
                importance=0.6
            ))

        # Edges
        self.graph.add_edge(KnowledgeEdge(
            source=company_id,
            target=kwargs['facility_id'],
            relation='operates',
            strength=1.0,
            evidence=['Company filings', 'Satellite imagery']
        ))

        self.graph.add_edge(KnowledgeEdge(
            source=company_id,
            target=f"ticker_{kwargs['ticker']}",
            relation='trades_as',
            strength=1.0,
            evidence=['Exchange listing']
        ))

        self.graph.add_edge(KnowledgeEdge(
            source=f"ticker_{kwargs['ticker']}",
            target=sector_id,
            relation='belongs_to',
            strength=1.0
        ))

        # Competitor edges
        for comp in kwargs.get('competitors', []):
            comp_id = f"ticker_{comp}"
            if comp_id in self.graph.nodes:
                self.graph.add_edge(KnowledgeEdge(
                    source=f"ticker_{kwargs['ticker']}",
                    target=comp_id,
                    relation='competes_with',
                    strength=0.6
                ))

    def _add_port_network(self, **kwargs):
        """Add port and shipping network."""
        port_node_id = f"port_{kwargs['port_id']}"

        self.graph.add_node(KnowledgeNode(
            id=port_node_id,
            type='facility',
            name=kwargs['port_name'],
            attributes={'type': 'port', 'country': kwargs['country']},
            importance=0.85
        ))

        # Connect shipping tickers
        for ticker in kwargs.get('major_players', []):
            ticker_id = f"ticker_{ticker}"
            if ticker_id in self.graph.nodes:
                self.graph.add_edge(KnowledgeEdge(
                    source=ticker_id,
                    target=port_node_id,
                    relation='operates_through',
                    strength=0.7
                ))

        # Chokepoint dependencies
        for choke in kwargs.get('chokepoint_dependencies', []):
            choke_id = f"chokepoint_{choke}"
            if choke_id in self.graph.nodes:
                self.graph.add_edge(KnowledgeEdge(
                    source=port_node_id,
                    target=choke_id,
                    relation='depends_on',
                    strength=0.9
                ))

    def _add_chokepoint(self, choke_id: str, name: str, affected_tickers: list[str], global_trade_pct: float):
        """Add a strategic chokepoint."""
        node_id = f"chokepoint_{choke_id}"

        self.graph.add_node(KnowledgeNode(
            id=node_id,
            type='chokepoint',
            name=name,
            attributes={'global_trade_pct': global_trade_pct},
            importance=0.95
        ))

        for ticker in affected_tickers:
            ticker_id = f"ticker_{ticker}"
            if ticker_id in self.graph.nodes:
                self.graph.add_edge(KnowledgeEdge(
                    source=node_id,
                    target=ticker_id,
                    relation='affects',
                    strength=0.8
                ))

    def analyze_facility_event(self, facility_id: str, event_type: str, severity: float) -> dict[str, Any]:
        """
        Analyze market impact of a facility event using graph reasoning.
        
        Args:
            facility_id: The facility experiencing the event
            event_type: Type of event ('production_surge', 'outage', 'maintenance')
            severity: 0.0 to 1.0 severity of the event
            
        Returns:
            Impact analysis with affected tickers and reasoning
        """
        # Get base impact paths
        base_impact = self.graph.query_impact(facility_id)

        if 'error' in base_impact:
            return base_impact

        # Adjust based on event type and severity
        event_multipliers = {
            'production_surge': 1.2 if severity > 0.7 else 0.8,
            'outage': -1.5 if severity > 0.5 else -0.8,
            'maintenance': -0.3,
            'thermal_anomaly': 0.6 if severity > 0.8 else 0.3
        }

        multiplier = event_multipliers.get(event_type, 0.5)

        # Calculate adjusted impact scores
        adjusted_tickers = []
        for ticker_name in base_impact.get('all_tickers', []):
            ticker_id = f"ticker_{ticker_name}"
            paths = self.graph.find_paths(facility_id, ticker_id, max_depth=3)

            if paths:
                base_score = paths[0].impact_score
                adjusted_score = base_score * severity * multiplier

                adjusted_tickers.append({
                    'ticker': ticker_name,
                    'impact_score': round(adjusted_score, 3),
                    'direction': 'BULLISH' if adjusted_score > 0 else 'BEARISH',
                    'confidence': min(0.95, abs(adjusted_score)),
                    'reasoning': paths[0].reasoning
                })

        # Sort by absolute impact
        adjusted_tickers.sort(key=lambda x: abs(x['impact_score']), reverse=True)

        # Get primary ticker safely
        direct_tickers = base_impact.get('direct_tickers', [])
        primary_ticker = direct_tickers[0] if direct_tickers else None

        return {
            'event': {'facility': facility_id, 'type': event_type, 'severity': severity},
            'primary_ticker': primary_ticker,
            'affected_tickers': adjusted_tickers[:10],
            'sectors': base_impact.get('sectors', {}),
            'total_impact_score': sum(abs(t['impact_score']) for t in adjusted_tickers),
            'market_sentiment': 'BULLISH' if multiplier > 0 else 'BEARISH',
            'graph_reasoning': base_impact.get('reasoning', '')
        }

    def get_graph_summary(self) -> dict[str, Any]:
        """Get summary statistics of the knowledge graph."""
        node_types = defaultdict(int)
        for node in self.graph.nodes.values():
            node_types[node.type] += 1

        relation_types = defaultdict(int)
        for edges in self.graph.edges.values():
            for edge in edges:
                relation_types[edge.relation] += 1

        return {
            'total_nodes': len(self.graph.nodes),
            'total_edges': sum(len(e) for e in self.graph.edges.values()),
            'node_types': dict(node_types),
            'relation_types': dict(relation_types),
            'coverage': 'Core industrial facilities, ports, chokepoints'
        }


# Singleton
_graph_engine: GraphRAGEngine | None = None

def get_graphrag_engine() -> GraphRAGEngine:
    """Get or create the GraphRAG engine."""
    global _graph_engine
    if _graph_engine is None:
        _graph_engine = GraphRAGEngine()
    return _graph_engine


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    engine = GraphRAGEngine()

    print("\nGraphRAG Engine Summary:")
    summary = engine.get_graph_summary()
    print(f"  Nodes: {summary['total_nodes']}")
    print(f"  Edges: {summary['total_edges']}")
    print(f"  Node types: {summary['node_types']}")

    # Example: Analyze ArcelorMittal thermal anomaly
    print("\n" + "="*60)
    print("Event Analysis: ArcelorMittal Dunkirk Production Surge")
    print("="*60)

    analysis = engine.analyze_facility_event('arcelor_dunkirk', 'production_surge', 0.85)

    print(f"\nEvent: {analysis['event']}")
    print(f"Primary Ticker: {analysis['primary_ticker']}")
    print(f"Market Sentiment: {analysis['market_sentiment']}")
    print("\nAffected Tickers:")
    for t in analysis['affected_tickers'][:5]:
        print(f"  {t['ticker']}: {t['direction']} (score: {t['impact_score']}, confidence: {t['confidence']})")
        print(f"    → {t['reasoning'][:60]}...")
