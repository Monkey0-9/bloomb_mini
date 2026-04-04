"""
ReportAgent - Automated satellite signal analysis report generation.

MiroFish-inspired: Deep post-simulation analysis with rich toolset.
Generates comprehensive reports from signal detection through market impact.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ReportSection(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    SIGNAL_DETECTED = "signal_detected"
    SWARM_CONSENSUS = "swarm_consensus"
    GRAPH_REASONING = "graph_reasoning"
    HISTORICAL_CONTEXT = "historical_context"
    MARKET_IMPACT = "market_impact"
    RISK_FACTORS = "risk_factors"
    RECOMMENDATION = "recommendation"
    APPENDIX = "appendix"


@dataclass
class SignalReport:
    """Complete signal analysis report."""
    report_id: str
    generated_at: datetime
    signal_id: str
    ticker: str
    facility_name: str

    # Sections
    executive_summary: str
    signal_details: dict[str, Any]
    swarm_analysis: dict[str, Any]
    graph_paths: list[dict[str, Any]]
    historical_accuracy: dict[str, Any]
    market_impact_assessment: dict[str, Any]
    risk_factors: list[str]
    recommendation: dict[str, Any]
    confidence_metrics: dict[str, float]

    # Metadata
    data_sources: list[str] = field(default_factory=list)
    model_versions: dict[str, str] = field(default_factory=dict)


class ReportAgent:
    """
    Automated report generation agent for satellite signal analysis.
    
    Tools available:
    - Signal data retrieval
    - Swarm consensus analysis
    - GraphRAG path tracing
    - Historical accuracy lookup
    - Market data correlation
    - Risk factor identification
    """

    def __init__(self):
        self._tool_usage: dict[str, int] = {}
        self._report_history: list[SignalReport] = []

    def generate_report(self,
                       signal_data: dict[str, Any],
                       swarm_consensus: dict[str, Any] | None = None,
                       graph_analysis: dict[str, Any] | None = None,
                       historical_data: dict[str, Any] | None = None) -> SignalReport:
        """
        Generate comprehensive signal analysis report.
        
        Orchestrates all analysis tools to produce final report.
        """
        signal_id = signal_data.get('signal_id', 'unknown')
        ticker = signal_data.get('ticker', 'unknown')
        facility = signal_data.get('facility_name', 'Unknown Facility')

        logger.info(f"ReportAgent generating report for {signal_id}")

        # Build each section
        exec_summary = self._generate_executive_summary(
            signal_data, swarm_consensus, graph_analysis, historical_data
        )

        signal_details = self._analyze_signal_details(signal_data)

        swarm_analysis = self._analyze_swarm_consensus(swarm_consensus) if swarm_consensus else {}

        graph_paths = self._extract_graph_paths(graph_analysis) if graph_analysis else []

        historical = self._analyze_historical_context(ticker, signal_data, historical_data)

        market_impact = self._assess_market_impact(
            signal_data, swarm_consensus, graph_analysis, historical
        )

        risks = self._identify_risk_factors(signal_data, market_impact)

        recommendation = self._generate_recommendation(
            signal_data, swarm_consensus, market_impact, historical
        )

        confidence = self._calculate_confidence_metrics(
            swarm_consensus, historical, graph_analysis
        )

        report = SignalReport(
            report_id=f"rpt_{signal_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(UTC),
            signal_id=signal_id,
            ticker=ticker,
            facility_name=facility,
            executive_summary=exec_summary,
            signal_details=signal_details,
            swarm_analysis=swarm_analysis,
            graph_paths=graph_paths,
            historical_accuracy=historical,
            market_impact_assessment=market_impact,
            risk_factors=risks,
            recommendation=recommendation,
            confidence_metrics=confidence,
            data_sources=['NASA FIRMS', 'yfinance', 'Satellite Orbital Data', 'Agent Consensus'],
            model_versions={
                'swarm': 'v1.0',
                'graphrag': 'v1.0',
                'memory': 'v1.0'
            }
        )

        self._report_history.append(report)
        logger.info(f"Report generated: {report.report_id}")

        return report

    def _generate_executive_summary(self,
                                    signal: dict[str, Any],
                                    swarm: dict | None,
                                    graph: dict | None,
                                    historical: dict | None) -> str:
        """Generate executive summary for decision-makers."""
        ticker = signal.get('ticker', 'unknown')
        facility = signal.get('facility_name', 'Unknown')
        sigma = signal.get('anomaly_sigma', 0)

        # Determine signal strength description
        if sigma > 2.5:
            strength = "extreme"
        elif sigma > 1.5:
            strength = "significant"
        else:
            strength = "moderate"

        # Get consensus direction
        direction = "UNKNOWN"
        confidence = 0.0
        if swarm:
            direction = swarm.get('consensus_stance', 'NEUTRAL')
            confidence = swarm.get('confidence', 0)

        # Get win rate context
        win_rate = 0.5
        if historical and 'overall_win_rate' in historical:
            win_rate = historical['overall_win_rate']

        summary = f"""
Satellite Signal Alert: {strength.upper()} thermal anomaly detected at {facility} 
({ticker}) with {sigma:.1f}σ deviation from baseline.

Agent Consensus: {direction} ({confidence:.0%} confidence) based on {swarm.get('bull_votes', 0) + swarm.get('bear_votes', 0) + swarm.get('neutral_votes', 0) if swarm else 0} agent votes.
Historical Accuracy: {win_rate:.0%} win rate for {ticker} thermal signals.

Primary Recommendation: {self._quick_recommendation(direction, confidence, win_rate)}
""".strip()

        return summary

    def _quick_recommendation(self, direction: str, confidence: float, win_rate: float) -> str:
        """Generate one-line recommendation."""
        if confidence > 0.7 and win_rate > 0.6:
            return f"STRONG {direction} - High confidence + proven track record"
        elif confidence > 0.6:
            return f"MODERATE {direction} - Good confidence, monitor for confirmation"
        elif win_rate > 0.6:
            return f"CAUTIOUS {direction} - Good history but mixed current signals"
        else:
            return "NEUTRAL - Insufficient confidence or poor historical performance"

    def _analyze_signal_details(self, signal: dict[str, Any]) -> dict[str, Any]:
        """Deep analysis of raw signal characteristics."""
        return {
            'detection_time': signal.get('detected_at'),
            'facility_location': {
                'lat': signal.get('lat'),
                'lon': signal.get('lon'),
                'name': signal.get('facility_name'),
                'country': signal.get('country')
            },
            'thermal_characteristics': {
                'frp_mw': signal.get('frp_mw'),
                'brightness_k': signal.get('brightness_k'),
                'anomaly_sigma': signal.get('anomaly_sigma'),
                'cluster_size': signal.get('cluster_size')
            },
            'data_quality': self._assess_data_quality(signal),
            'signal_type': signal.get('type', 'unknown'),
            'sources': signal.get('data_sources', [])
        }

    def _assess_data_quality(self, signal: dict[str, Any]) -> str:
        """Assess quality of satellite data."""
        cluster_size = signal.get('cluster_size', 1)
        frp = signal.get('frp_mw', 0)

        if cluster_size >= 5 and frp > 50:
            return "HIGH - Large cluster, strong thermal signature"
        elif cluster_size >= 3 and frp > 20:
            return "MEDIUM - Moderate cluster size and intensity"
        else:
            return "LOW - Small cluster or weak signal"

    def _analyze_swarm_consensus(self, consensus: dict[str, Any]) -> dict[str, Any]:
        """Analyze multi-agent consensus patterns."""
        votes = consensus.get('votes', [])

        # Analyze vote distribution by agent type
        by_type = {}
        for v in votes:
            agent_type = v.get('agent', {}).get('type', 'unknown')
            stance = v.get('stance')
            if agent_type not in by_type:
                by_type[agent_type] = {'bull': 0, 'bear': 0, 'neutral': 0}

            if 'BULL' in stance:
                by_type[agent_type]['bull'] += 1
            elif 'BEAR' in stance:
                by_type[agent_type]['bear'] += 1
            else:
                by_type[agent_type]['neutral'] += 1

        # Find dissenting agents
        consensus_stance = consensus.get('consensus_stance', 'NEUTRAL')
        dissenters = []
        for v in votes:
            stance = v.get('stance', '')
            if 'BULL' in consensus_stance and 'BEAR' in stance:
                dissenters.append(v.get('agent', {}).get('name', 'Unknown'))
            elif 'BEAR' in consensus_stance and 'BULL' in stance:
                dissenters.append(v.get('agent', {}).get('name', 'Unknown'))

        return {
            'consensus_score': consensus.get('consensus_score'),
            'vote_distribution': {
                'bull': consensus.get('bull_votes', 0),
                'bear': consensus.get('bear_votes', 0),
                'neutral': consensus.get('neutral_votes', 0)
            },
            'by_agent_type': by_type,
            'dissenting_agents': dissenters,
            'agreement_level': consensus.get('confidence'),
            'reasoning_summary': consensus.get('reasoning_summary'),
            'dissenting_opinion': consensus.get('dissenting_opinion')
        }

    def _extract_graph_paths(self, graph_analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract and format knowledge graph impact paths."""
        paths = []

        affected = graph_analysis.get('affected_tickers', [])
        for ticker_info in affected[:5]:  # Top 5
            paths.append({
                'target_ticker': ticker_info.get('ticker'),
                'impact_score': ticker_info.get('impact_score'),
                'direction': ticker_info.get('direction'),
                'reasoning': ticker_info.get('reasoning'),
                'confidence': ticker_info.get('confidence')
            })

        return paths

    def _analyze_historical_context(self,
                                    ticker: str,
                                    signal: dict[str, Any],
                                    historical: dict | None) -> dict[str, Any]:
        """Analyze historical pattern matching."""
        if not historical:
            return {'error': 'No historical data available'}

        # Find similar past signals
        current_sigma = signal.get('anomaly_sigma', 0)

        return {
            'win_rate': historical.get('overall_win_rate', 0.5),
            'total_signals': historical.get('total_signals', 0),
            'by_signal_type': historical.get('by_signal_type', {}),
            'learned_patterns': historical.get('learned_patterns', []),
            'recommendation': historical.get('recommendation', 'No recommendation'),
            'current_signal_context': f"σ={current_sigma:.1f} vs historical range"
        }

    def _assess_market_impact(self,
                             signal: dict[str, Any],
                             swarm: dict | None,
                             graph: dict | None,
                             historical: dict[str, Any]) -> dict[str, Any]:
        """Assess expected market impact."""
        sigma = signal.get('anomaly_sigma', 0)

        # Expected magnitude based on sigma and historical
        base_magnitude = abs(sigma) * 0.015  # ~1.5% per sigma

        # Adjust by historical win rate
        win_rate = historical.get('overall_win_rate', 0.5)
        reliability_factor = (win_rate - 0.5) * 2  # -1 to +1

        expected_move = base_magnitude * (1 + reliability_factor)

        # Get direction from consensus
        direction = "NEUTRAL"
        if swarm:
            stance = swarm.get('consensus_stance', '')
            if 'BULL' in stance:
                direction = "UP"
            elif 'BEAR' in stance:
                direction = "DOWN"

        return {
            'expected_direction': direction,
            'expected_magnitude_5d': round(expected_move, 3),
            'expected_magnitude_21d': round(expected_move * 1.5, 3),
            'confidence_interval': [
                round(expected_move * 0.5, 3),
                round(expected_move * 2.0, 3)
            ],
            'probability_of_direction': swarm.get('confidence', 0.5) if swarm else 0.5,
            'affected_sectors': graph.get('sectors', {}) if graph else {},
            'contagion_risk': self._assess_contagion_risk(graph)
        }

    def _assess_contagion_risk(self, graph: dict | None) -> str:
        """Assess risk of impact spreading to related tickers."""
        if not graph:
            return "UNKNOWN"

        affected = len(graph.get('all_tickers', []))

        if affected > 10:
            return "HIGH - Broad sector impact likely"
        elif affected > 5:
            return "MEDIUM - Some spillover to competitors/suppliers"
        else:
            return "LOW - Isolated to primary ticker"

    def _identify_risk_factors(self,
                              signal: dict[str, Any],
                              market_impact: dict[str, Any]) -> list[str]:
        """Identify key risk factors."""
        risks = []

        sigma = signal.get('anomaly_sigma', 0)

        # Signal-specific risks
        if sigma < 1.0:
            risks.append("LOW_SIGNAL_STRENGTH: Anomaly may be noise, not actionable")

        if signal.get('cluster_size', 1) < 3:
            risks.append("SMALL_CLUSTER: Limited spatial confirmation")

        # Market risks
        if market_impact.get('probability_of_direction', 0.5) < 0.6:
            risks.append("UNCERTAIN_DIRECTION: Mixed agent consensus")

        # Add timing/seasonal risks
        risks.append("EARNINGS_TIMING: Signal may be coincident with scheduled earnings")
        risks.append("MACRO_HEADWINDS: Broad market moves can override facility-specific signals")

        return risks

    def _generate_recommendation(self,
                                signal: dict[str, Any],
                                swarm: dict | None,
                                market_impact: dict[str, Any],
                                historical: dict[str, Any]) -> dict[str, Any]:
        """Generate final actionable recommendation."""
        ticker = signal.get('ticker', 'unknown')
        direction = market_impact.get('expected_direction', 'NEUTRAL')
        magnitude = market_impact.get('expected_magnitude_5d', 0)
        confidence = market_impact.get('probability_of_direction', 0.5)
        win_rate = historical.get('overall_win_rate', 0.5)

        # Position sizing based on confidence
        if confidence > 0.75 and win_rate > 0.6:
            position_size = "FULL"
            urgency = "IMMEDIATE"
        elif confidence > 0.6 or win_rate > 0.6:
            position_size = "HALF"
            urgency = "SAME_DAY"
        else:
            position_size = "OBSERVE"
            urgency = "WAIT_CONFIRMATION"

        # Entry/exit levels
        if direction == "UP":
            action = "LONG"
            entry = f"Current market ~{signal.get('current_price', 'N/A')}"
            target = f"+{magnitude:.1%}"
            stop = f"-{magnitude * 0.5:.1%}"
        elif direction == "DOWN":
            action = "SHORT/AVOID"
            entry = "Current levels"
            target = f"-{magnitude:.1%}"
            stop = f"+{magnitude * 0.5:.1%}"
        else:
            action = "NEUTRAL"
            entry = "N/A"
            target = "N/A"
            stop = "N/A"

        return {
            'action': action,
            'position_size': position_size,
            'urgency': urgency,
            'entry_guidance': entry,
            'target': target,
            'stop_loss': stop,
            'time_horizon': "5-21 days",
            'rationale': f"{confidence:.0%} confidence × {win_rate:.0%} historical accuracy"
        }

    def _calculate_confidence_metrics(self,
                                     swarm: dict | None,
                                     historical: dict[str, Any],
                                     graph: dict | None) -> dict[str, float]:
        """Calculate composite confidence metrics."""
        # Individual components
        swarm_conf = swarm.get('confidence', 0.5) if swarm else 0.5
        historical_conf = historical.get('overall_win_rate', 0.5)
        graph_conf = 0.7 if graph and graph.get('affected_tickers') else 0.5

        # Weighted composite
        composite = (swarm_conf * 0.4 + historical_conf * 0.4 + graph_conf * 0.2)

        return {
            'swarm_confidence': round(swarm_conf, 2),
            'historical_confidence': round(historical_conf, 2),
            'graph_confidence': round(graph_conf, 2),
            'composite_confidence': round(composite, 2),
            'reliability_grade': self._grade_confidence(composite)
        }

    def _grade_confidence(self, score: float) -> str:
        """Convert numeric confidence to letter grade."""
        if score >= 0.8:
            return "A - High Conviction"
        elif score >= 0.65:
            return "B - Moderate Conviction"
        elif score >= 0.5:
            return "C - Low Conviction"
        else:
            return "D - Unreliable"

    def to_markdown(self, report: SignalReport) -> str:
        """Convert report to markdown format."""
        md = f"""# Signal Analysis Report: {report.ticker}

**Report ID:** {report.report_id}  
**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}  
**Signal ID:** {report.signal_id}

---

## Executive Summary

{report.executive_summary}

---

## Signal Detected

**Facility:** {report.facility_name}  
**Location:** {report.signal_details['facility_location']['lat']:.3f}, {report.signal_details['facility_location']['lon']:.3f}

### Thermal Characteristics
- **FRP:** {report.signal_details['thermal_characteristics']['frp_mw']:.1f} MW
- **Brightness:** {report.signal_details['thermal_characteristics']['brightness_k']:.1f} K
- **Anomaly:** {report.signal_details['thermal_characteristics']['anomaly_sigma']:.2f}σ
- **Cluster Size:** {report.signal_details['thermal_characteristics']['cluster_size']}
- **Data Quality:** {report.signal_details['data_quality']}

---

## Swarm Consensus Analysis

**Consensus Score:** {report.swarm_analysis.get('consensus_score', 'N/A')}/100  
**Agreement Level:** {report.swarm_analysis.get('agreement_level', 'N/A'):.0%}

### Vote Distribution
- Bull: {report.swarm_analysis.get('vote_distribution', {}).get('bull', 0)}
- Bear: {report.swarm_analysis.get('vote_distribution', {}).get('bear', 0)}
- Neutral: {report.swarm_analysis.get('vote_distribution', {}).get('neutral', 0)}

**Reasoning:** {report.swarm_analysis.get('reasoning_summary', 'N/A')}

---

## Market Impact Assessment

**Expected Direction:** {report.market_impact_assessment.get('expected_direction')}  
**5-Day Expected Move:** {report.market_impact_assessment.get('expected_magnitude_5d', 0):.2%}  
**21-Day Expected Move:** {report.market_impact_assessment.get('expected_magnitude_21d', 0):.2%}  
**Direction Probability:** {report.market_impact_assessment.get('probability_of_direction', 0):.0%}

### Contagion Risk
{report.market_impact_assessment.get('contagion_risk', 'Unknown')}

---

## Historical Context

**Overall Win Rate:** {report.historical_accuracy.get('win_rate', 0):.0%}  
**Total Historical Signals:** {report.historical_accuracy.get('total_signals', 0)}

**Assessment:** {report.historical_accuracy.get('recommendation', 'No recommendation')}

---

## Recommendation

**Action:** {report.recommendation.get('action')}  
**Position Size:** {report.recommendation.get('position_size')}  
**Urgency:** {report.recommendation.get('urgency')}  
**Time Horizon:** {report.recommendation.get('time_horizon')}

| Level | Value |
|-------|-------|
| Entry | {report.recommendation.get('entry_guidance')} |
| Target | {report.recommendation.get('target')} |
| Stop Loss | {report.recommendation.get('stop_loss')} |

**Rationale:** {report.recommendation.get('rationale')}

---

## Risk Factors

"""
        for i, risk in enumerate(report.risk_factors, 1):
            md += f"{i}. {risk}\n"

        md += f"""
---

## Confidence Metrics

| Metric | Value |
|--------|-------|
| Composite Confidence | {report.confidence_metrics.get('composite_confidence', 0):.0%} |
| Swarm Confidence | {report.confidence_metrics.get('swarm_confidence', 0):.0%} |
| Historical Confidence | {report.confidence_metrics.get('historical_confidence', 0):.0%} |
| Graph Confidence | {report.confidence_metrics.get('graph_confidence', 0):.0%} |
| **Grade** | **{report.confidence_metrics.get('reliability_grade', 'N/A')}** |

---

## Data Sources

{', '.join(report.data_sources)}

---

*Generated by SatTrade ReportAgent v{report.model_versions.get('swarm', '1.0')}*
"""
        return md


# Singleton
_agent: ReportAgent | None = None

def get_report_agent() -> ReportAgent:
    """Get or create ReportAgent singleton."""
    global _agent
    if _agent is None:
        _agent = ReportAgent()
    return _agent


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    agent = ReportAgent()

    # Example report generation
    test_signal = {
        'signal_id': 'thermal_test_001',
        'ticker': 'MT',
        'facility_name': 'ArcelorMittal Dunkirk',
        'lat': 51.04,
        'lon': 2.38,
        'frp_mw': 120.5,
        'brightness_k': 355.0,
        'anomaly_sigma': 2.3,
        'cluster_size': 5,
        'type': 'INDUSTRIAL_THERMAL',
        'detected_at': datetime.now(UTC).isoformat(),
        'data_sources': ['NASA FIRMS']
    }

    test_swarm = {
        'consensus_stance': 'BULL',
        'consensus_score': 78.5,
        'confidence': 0.75,
        'bull_votes': 4,
        'bear_votes': 1,
        'neutral_votes': 1,
        'reasoning_summary': 'Fundamental and technical analysts agree on production momentum',
        'votes': [
            {'agent': {'name': 'TechnicalTony', 'type': 'technical'}, 'stance': 'BULL'},
            {'agent': {'name': 'FundamentalFiona', 'type': 'fundamental'}, 'stance': 'BULL'},
            {'agent': {'name': 'ContrarianCarl', 'type': 'contrarian'}, 'stance': 'BEAR'}
        ]
    }

    test_historical = {
        'overall_win_rate': 0.68,
        'total_signals': 24,
        'recommendation': 'Strong historical edge. Satellite signals for this ticker have been reliable predictors.'
    }

    report = agent.generate_report(test_signal, test_swarm, None, test_historical)

    print(f"\nReport Generated: {report.report_id}")
    print(f"Executive Summary:\n{report.executive_summary[:200]}...")
    print(f"\nRecommendation: {report.recommendation}")

    # Output markdown
    md = agent.to_markdown(report)
    print(f"\nMarkdown Report Length: {len(md)} characters")
