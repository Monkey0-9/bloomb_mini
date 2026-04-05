"""
Swarm Intelligence Signal Engine - Multi-agent consensus for satellite signals.

Inspired by MiroFish swarm intelligence architecture:
- Multiple specialized agents interpret the same satellite data
- Each agent has a persona (bull, bear, skeptic, quant)
- Collective consensus emerges from agent debate
- Memory of past predictions improves future accuracy
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentStance(Enum):
    """Possible stances an agent can take."""
    STRONG_BULL = 5
    BULL = 4
    NEUTRAL = 3
    BEAR = 2
    STRONG_BEAR = 1


@dataclass
class AgentPersona:
    """Personality and decision-making style of a signal agent."""
    name: str
    type: str  # 'technical', 'fundamental', 'sentiment', 'contrarian', 'macro'
    confidence_threshold: float
    risk_tolerance: str
    time_horizon: str
    bias: float
    specialties: list[str]

    def interpret_signal(self, signal_data: dict[str, Any]) -> AgentStance:
        """
        Interpret satellite signal based on persona.
        """
        raw_score = signal_data.get('score', 50)
        signal_type = signal_data.get('type', 'unknown')

        specialty_bonus = 1.2 if signal_type in self.specialties else 1.0
        adjusted_score = raw_score + (self.bias * 10) * specialty_bonus

        threshold_val = self.confidence_threshold * 10
        if adjusted_score < 50 - threshold_val:
            return AgentStance.STRONG_BEAR if adjusted_score < 30 \
                else AgentStance.BEAR
        elif adjusted_score > 50 + threshold_val:
            return AgentStance.STRONG_BULL if adjusted_score > 70 \
                else AgentStance.BULL
        return AgentStance.NEUTRAL


@dataclass
class AgentVote:
    """A single agent's vote on a signal."""
    agent: AgentPersona
    stance: AgentStance
    conviction: float  # 0.0 to 1.0
    reasoning: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SwarmConsensus:
    """Consensus result from multi-agent debate."""
    signal_id: str
    ticker: str
    votes: list[AgentVote]
    consensus_stance: AgentStance
    consensus_score: float  # 0-100
    bull_votes: int
    bear_votes: int
    neutral_votes: int
    confidence: float
    reasoning_summary: str
    dissenting_opinion: str | None


class SignalAgentSwarm:
    """
    Multi-agent swarm for satellite signal interpretation.
    """

    def __init__(self) -> None:
        self.agents: list[AgentPersona] = self._initialize_agents()
        self._consensus_history: dict[str, list[SwarmConsensus]] = {}

    def _initialize_agents(self) -> list[AgentPersona]:
        """Create the agent swarm with diverse personas."""
        return [
            AgentPersona(
                name="TechnicalTony",
                type="technical",
                confidence_threshold=0.3,
                risk_tolerance="medium",
                time_horizon="short",
                bias=0.1,
                specialties=["PORT_THROUGHPUT", "INDUSTRIAL_THERMAL"]
            ),
            AgentPersona(
                name="FundamentalFiona",
                type="fundamental",
                confidence_threshold=0.5,
                risk_tolerance="low",
                time_horizon="long",
                bias=0.0,
                specialties=["INDUSTRIAL_THERMAL", "RETAIL_FOOTFALL"]
            ),
            AgentPersona(
                name="SentimentSam",
                type="sentiment",
                confidence_threshold=0.2,
                risk_tolerance="high",
                time_horizon="short",
                bias=0.2,
                specialties=["RETAIL_FOOTFALL", "PORT_THROUGHPUT"]
            ),
            AgentPersona(
                name="ContrarianCarl",
                type="contrarian",
                confidence_threshold=0.4,
                risk_tolerance="high",
                time_horizon="medium",
                bias=-0.3,
                specialties=[]
            ),
            AgentPersona(
                name="MacroMaya",
                type="macro",
                confidence_threshold=0.6,
                risk_tolerance="medium",
                time_horizon="medium",
                bias=0.0,
                specialties=["INDUSTRIAL_THERMAL", "PORT_THROUGHPUT"]
            ),
            AgentPersona(
                name="QuantQuentin",
                type="quant",
                confidence_threshold=0.4,
                risk_tolerance="medium",
                time_horizon="short",
                bias=0.0,
                specialties=["INDUSTRIAL_THERMAL", "PORT_THROUGHPUT",
                             "RETAIL_FOOTFALL"]
            ),
        ]

    def debate_signal(self, signal_data: dict[str, Any]) -> SwarmConsensus:
        """Run multi-agent debate on a satellite signal."""
        signal_id = signal_data.get('signal_id', 'unknown')
        ticker = signal_data.get('ticker', 'unknown')

        votes = []
        for agent in self.agents:
            stance = agent.interpret_signal(signal_data)

            base_conviction = random.uniform(0.6, 0.9)
            if signal_data.get('type') in agent.specialties:
                conviction = min(0.95, base_conviction + 0.15)
            else:
                conviction = base_conviction * 0.8

            reasoning = self._generate_reasoning(agent, stance, signal_data)
            votes.append(AgentVote(
                agent=agent,
                stance=stance,
                conviction=conviction,
                reasoning=reasoning
            ))

        bull_votes = sum(
            1 for v in votes
            if v.stance in (AgentStance.BULL, AgentStance.STRONG_BULL)
        )
        bear_votes = sum(
            1 for v in votes
            if v.stance in (AgentStance.BEAR, AgentStance.STRONG_BEAR)
        )
        neutral_votes = sum(1 for v in votes if v.stance == AgentStance.NEUTRAL)

        total_weight = sum(v.conviction for v in votes)
        bull_weight = sum(
            v.conviction for v in votes
            if v.stance in (AgentStance.BULL, AgentStance.STRONG_BULL)
        )
        bear_weight = sum(
            v.conviction for v in votes
            if v.stance in (AgentStance.BEAR, AgentStance.STRONG_BEAR)
        )

        c_score = 50.0
        if total_weight > 0:
            c_score = 50 + ((bull_weight - bear_weight) / total_weight) * 50

        if c_score >= 70:
            c_stance = AgentStance.STRONG_BULL if c_score >= 85 \
                else AgentStance.BULL
        elif c_score <= 30:
            c_stance = AgentStance.STRONG_BEAR if c_score <= 15 \
                else AgentStance.BEAR
        else:
            c_stance = AgentStance.NEUTRAL

        max_v = max(bull_votes, bear_votes, neutral_votes)
        confidence = max_v / len(votes)

        reasoning_summary = self._summarize_consensus(votes, c_stance)

        dissenting = None
        if c_stance in (AgentStance.STRONG_BULL, AgentStance.BULL) \
           and bear_votes > 0:
            dissenting = " | ".join([
                v.reasoning for v in votes
                if v.stance in (AgentStance.BEAR, AgentStance.STRONG_BEAR)
            ])
        elif c_stance in (AgentStance.STRONG_BEAR, AgentStance.BEAR) \
             and bull_votes > 0:
            dissenting = " | ".join([
                v.reasoning for v in votes
                if v.stance in (AgentStance.BULL, AgentStance.STRONG_BULL)
            ])

        consensus = SwarmConsensus(
            signal_id=signal_id,
            ticker=ticker,
            votes=votes,
            consensus_stance=c_stance,
            consensus_score=round(float(c_score), 1),
            bull_votes=bull_votes,
            bear_votes=bear_votes,
            neutral_votes=neutral_votes,
            confidence=round(float(confidence), 2),
            reasoning_summary=reasoning_summary,
            dissenting_opinion=dissenting
        )

        if ticker not in self._consensus_history:
            self._consensus_history[ticker] = []
        self._consensus_history[ticker].append(consensus)

        logger.info(
            f"Swarm consensus for {signal_id}: {c_stance.name} "
            f"(score: {c_score:.1f}, confidence: {confidence:.2f})"
        )
        return consensus

    def _generate_reasoning(self, agent: AgentPersona, stance: AgentStance,
                           signal: dict[str, Any]) -> str:
        """Generate agent-specific reasoning for their stance."""
        sigma = signal.get('anomaly_sigma', 0.0)
        frp = signal.get('frp_mw', 0.0)
        facility = signal.get('facility_name', 'Unknown')

        templates: dict[str, dict[AgentStance, str]] = {
            'technical': {
                AgentStance.STRONG_BULL: f"Breakout: {sigma:+.10s}σ anomaly.",
                AgentStance.BULL: f"Uptrend: {sigma:+.10s}σ elevated activity.",
                AgentStance.NEUTRAL: f"Consolidation: {sigma:+.10s}σ normal.",
                AgentStance.BEAR: f"Weak momentum: {sigma:+.10s}σ below threshold.",
                AgentStance.STRONG_BEAR: "Breakdown risk detected."
            },
            'fundamental': {
                AgentStance.STRONG_BULL: f"{facility} peak: {frp:.0f}MW FRP.",
                AgentStance.BULL: "Production beat likely.",
                AgentStance.NEUTRAL: "In-line expectations.",
                AgentStance.BEAR: "Margin pressure concerns.",
                AgentStance.STRONG_BEAR: "Demand destruction signs."
            }
        }
        # Fallback for other agent types
        if agent.type not in templates:
            return f"{agent.name} sees {stance.name} stance."
        return templates[agent.type].get(stance, "No clear view.")

    def _summarize_consensus(self, votes: list[AgentVote],
                             consensus: AgentStance) -> str:
        """Generate consensus summary from votes."""
        if consensus in (AgentStance.STRONG_BULL, AgentStance.BULL):
            return "Bullish consensus: Production momentum confirmed."
        elif consensus in (AgentStance.STRONG_BEAR, AgentStance.BEAR):
            return "Bearish consensus: Concerns on sustainability."
        return "Mixed views: Camps divided. Await clarification."

    def get_historical_accuracy(self, ticker: str,
                                lookback: int = 20) -> float:
        """Calculate swarm's historical prediction accuracy."""
        history = self._consensus_history.get(ticker, [])
        if len(history) < 5:
            return 0.5
        recent = history[-lookback:]
        # Simplified logic for demonstration
        correct = sum(
            1 for h in recent
            if h.confidence > 0.7 and
            h.consensus_stance in (AgentStance.BULL, AgentStance.STRONG_BULL)
        )
        return float(correct / len(recent))


_swarm: SignalAgentSwarm | None = None


def get_signal_swarm() -> SignalAgentSwarm:
    """Get or create the signal agent swarm."""
    global _swarm
    if _swarm is None:
        _swarm = SignalAgentSwarm()
    return _swarm
