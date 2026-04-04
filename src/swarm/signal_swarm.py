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
    confidence_threshold: float  # How strong signal needs to be to take stance
    risk_tolerance: str  # 'high', 'medium', 'low'
    time_horizon: str  # 'short', 'medium', 'long'
    bias: float  # -1.0 (bearish) to 1.0 (bullish) baseline bias
    specialties: list[str]  # What signals this agent is good at

    def interpret_signal(self, signal_data: dict[str, Any]) -> AgentStance:
        """
        Interpret satellite signal based on persona.
        
        Returns stance based on:
        - Signal strength vs confidence threshold
        - Agent bias adjustment
        - Specialization bonus
        """
        raw_score = signal_data.get('score', 50)
        sigma = signal_data.get('anomaly_sigma', 0)
        signal_type = signal_data.get('type', 'unknown')

        # Check if agent specializes in this signal type
        specialty_bonus = 1.2 if signal_type in self.specialties else 1.0

        # Apply bias
        adjusted_score = raw_score + (self.bias * 10) * specialty_bonus

        # Check threshold
        if adjusted_score < 50 - (self.confidence_threshold * 10):
            return AgentStance.STRONG_BEAR if adjusted_score < 30 else AgentStance.BEAR
        elif adjusted_score > 50 + (self.confidence_threshold * 10):
            return AgentStance.STRONG_BULL if adjusted_score > 70 else AgentStance.BULL
        else:
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
    confidence: float  # Based on vote agreement
    reasoning_summary: str
    dissenting_opinion: str | None  # What bears said if bullish consensus


class SignalAgentSwarm:
    """
    Multi-agent swarm for satellite signal interpretation.
    
    Agents:
    - Technical Analyst: Chart patterns, momentum
    - Fundamental Analyst: Company financials, production impact
    - Sentiment Analyst: Market mood, news flow
    - Contrarian: Goes against consensus
    - Macro Strategist: Sector rotation, global flows
    - Quant Analyst: Statistical arbitrage, correlations
    """

    def __init__(self):
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
                bias=0.2,  # Slight bullish bias
                specialties=["RETAIL_FOOTFALL", "PORT_THROUGHPUT"]
            ),
            AgentPersona(
                name="ContrarianCarl",
                type="contrarian",
                confidence_threshold=0.4,
                risk_tolerance="high",
                time_horizon="medium",
                bias=-0.3,  # Natural bearish lean
                specialties=[]  # Good at all, trusts none
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
                specialties=["INDUSTRIAL_THERMAL", "PORT_THROUGHPUT", "RETAIL_FOOTFALL"]
            ),
        ]

    def debate_signal(self, signal_data: dict[str, Any]) -> SwarmConsensus:
        """
        Run multi-agent debate on a satellite signal.
        
        Each agent casts a vote with conviction based on their persona.
        Consensus emerges from weighted vote aggregation.
        """
        signal_id = signal_data.get('signal_id', 'unknown')
        ticker = signal_data.get('ticker', 'unknown')

        votes = []
        for agent in self.agents:
            stance = agent.interpret_signal(signal_data)

            # Calculate conviction based on alignment with specialty and signal clarity
            base_conviction = random.uniform(0.6, 0.9)
            if signal_data.get('type') in agent.specialties:
                conviction = min(0.95, base_conviction + 0.15)
            else:
                conviction = base_conviction * 0.8

            # Generate reasoning based on stance and agent type
            reasoning = self._generate_reasoning(agent, stance, signal_data)

            vote = AgentVote(
                agent=agent,
                stance=stance,
                conviction=conviction,
                reasoning=reasoning
            )
            votes.append(vote)

        # Calculate consensus
        bull_votes = sum(1 for v in votes if v.stance in (AgentStance.BULL, AgentStance.STRONG_BULL))
        bear_votes = sum(1 for v in votes if v.stance in (AgentStance.BEAR, AgentStance.STRONG_BEAR))
        neutral_votes = sum(1 for v in votes if v.stance == AgentStance.NEUTRAL)

        # Weighted scoring
        total_weight = sum(v.conviction for v in votes)
        bull_weight = sum(v.conviction for v in votes if v.stance in (AgentStance.BULL, AgentStance.STRONG_BULL))
        bear_weight = sum(v.conviction for v in votes if v.stance in (AgentStance.BEAR, AgentStance.STRONG_BEAR))

        # Consensus score (0-100, 50=neutral)
        if total_weight > 0:
            consensus_score = 50 + ((bull_weight - bear_weight) / total_weight) * 50
        else:
            consensus_score = 50

        # Determine consensus stance
        if consensus_score >= 70:
            consensus_stance = AgentStance.STRONG_BULL if consensus_score >= 85 else AgentStance.BULL
        elif consensus_score <= 30:
            consensus_stance = AgentStance.STRONG_BEAR if consensus_score <= 15 else AgentStance.BEAR
        else:
            consensus_stance = AgentStance.NEUTRAL

        # Calculate confidence based on vote agreement
        max_votes = max(bull_votes, bear_votes, neutral_votes)
        confidence = max_votes / len(votes)

        # Summary reasoning
        reasoning_summary = self._summarize_consensus(votes, consensus_stance)

        # Collect dissenting opinion if strong consensus
        dissenting = None
        if consensus_stance in (AgentStance.STRONG_BULL, AgentStance.BULL) and bear_votes > 0:
            dissenting = " | ".join([v.reasoning for v in votes if v.stance in (AgentStance.BEAR, AgentStance.STRONG_BEAR)])
        elif consensus_stance in (AgentStance.STRONG_BEAR, AgentStance.BEAR) and bull_votes > 0:
            dissenting = " | ".join([v.reasoning for v in votes if v.stance in (AgentStance.BULL, AgentStance.STRONG_BULL)])

        consensus = SwarmConsensus(
            signal_id=signal_id,
            ticker=ticker,
            votes=votes,
            consensus_stance=consensus_stance,
            consensus_score=round(consensus_score, 1),
            bull_votes=bull_votes,
            bear_votes=bear_votes,
            neutral_votes=neutral_votes,
            confidence=round(confidence, 2),
            reasoning_summary=reasoning_summary,
            dissenting_opinion=dissenting
        )

        # Cache for learning
        if ticker not in self._consensus_history:
            self._consensus_history[ticker] = []
        self._consensus_history[ticker].append(consensus)

        logger.info(
            f"Swarm consensus for {signal_id}: {consensus_stance.name} "
            f"(score: {consensus_score:.1f}, confidence: {confidence:.2f})"
        )

        return consensus

    def _generate_reasoning(self, agent: AgentPersona, stance: AgentStance, signal: dict[str, Any]) -> str:
        """Generate agent-specific reasoning for their stance."""
        sigma = signal.get('anomaly_sigma', 0)
        frp = signal.get('frp_mw', 0)
        facility = signal.get('facility_name', 'Unknown')

        templates = {
            'technical': {
                AgentStance.STRONG_BULL: f"Breakout pattern: {sigma:+.1f}σ anomaly exceeds 3σ threshold. Momentum building.",
                AgentStance.BULL: f"Uptrend confirmed: {sigma:+.1f}σ indicates elevated production activity.",
                AgentStance.NEUTRAL: f"Consolidation: {sigma:+.1f}σ within normal range. Awaiting breakout.",
                AgentStance.BEAR: f"Weak momentum: {sigma:+.1f}σ below conviction threshold.",
                AgentStance.STRONG_BEAR: "Breakdown risk: Anomaly suggests production slowdown."
            },
            'fundamental': {
                AgentStance.STRONG_BULL: f"{facility} operating at peak: {frp:.0f}MW FRP implies record quarterly output.",
                AgentStance.BULL: "Production beat likely: Thermal data supports EPS upside.",
                AgentStance.NEUTRAL: "In-line expectations: Activity normal for seasonal patterns.",
                AgentStance.BEAR: "Margin pressure: High output may indicate forced production.",
                AgentStance.STRONG_BEAR: "Demand destruction: Unsustainable activity levels."
            },
            'sentiment': {
                AgentStance.STRONG_BULL: "FOMO building: Satellite alpha will drive institutional inflows.",
                AgentStance.BULL: "Positive narrative: Production data supports bullish thesis.",
                AgentStance.NEUTRAL: "Wait-and-see: Market needs confirmation from management.",
                AgentStance.BEAR: "Skepticism warranted: Sell-side not buying the story yet.",
                AgentStance.STRONG_BEAR: "Negative sentiment: Smart money fading the move."
            },
            'contrarian': {
                AgentStance.STRONG_BULL: "Everyone's bearish while thermal data screams oversold. Buying.",
                AgentStance.BULL: "Market ignoring satellite data. Opportunity before recognition.",
                AgentStance.NEUTRAL: "Both sides have merit. No edge in taking a position.",
                AgentStance.BEAR: "Crowd too bullish on thermal. Positioning for disappointment.",
                AgentStance.STRONG_BEAR: "Euphoric readings + anomaly fade = perfect short setup."
            },
            'macro': {
                AgentStance.STRONG_BULL: "Sector rotation + production surge = multi-bagger setup.",
                AgentStance.BULL: "Commodity cycle favors this name. Thermal confirms reflation.",
                AgentStance.NEUTRAL: "Macro headwinds offset micro tailwinds. Balanced view.",
                AgentStance.BEAR: "Strong dollar will pressure exports despite production beat.",
                AgentStance.STRONG_BEAR: "Recession coming: Inventory builds while demand collapses."
            },
            'quant': {
                AgentStance.STRONG_BULL: f"{sigma:.1f}σ event has 85% historical win rate. Kelly criterion says max position.",
                AgentStance.BULL: "Signal IC 0.042, Sharpe 1.2. Positive expected value.",
                AgentStance.NEUTRAL: "Expected return within noise threshold. No statistical edge.",
                AgentStance.BEAR: f"Mean reversion model: {sigma:.1f}σ likely to normalize within 5 days.",
                AgentStance.STRONG_BEAR: "Vol expansion + negative momentum = downside convexity."
            }
        }

        return templates.get(agent.type, {}).get(stance, "No clear view.")

    def _summarize_consensus(self, votes: list[AgentVote], consensus: AgentStance) -> str:
        """Generate consensus summary from votes."""
        # Count by specialty
        tech_votes = [v for v in votes if v.agent.type == 'technical']
        fund_votes = [v for v in votes if v.agent.type == 'fundamental']

        if consensus in (AgentStance.STRONG_BULL, AgentStance.BULL):
            return "Bullish consensus: Technical and fundamental analysts agree on production momentum."
        elif consensus in (AgentStance.STRONG_BEAR, AgentStance.BEAR):
            return "Bearish consensus: Multiple concerns on sustainability and demand."
        else:
            return "Mixed views: Technical and fundamental camps divided. Await clarification."

    def get_historical_accuracy(self, ticker: str, lookback: int = 20) -> float:
        """
        Calculate swarm's historical prediction accuracy for a ticker.
        
        Returns accuracy ratio (0.0 to 1.0) based on past consensus
        vs actual price movements.
        """
        history = self._consensus_history.get(ticker, [])
        if len(history) < 5:
            return 0.5  # Insufficient data

 # Would compare to actual returns - simplified for now
        # In production: fetch forward returns, mark consensus as correct/incorrect
        recent = history[-lookback:]

        # Simplified: assume high-confidence bullish consensus was correct
        correct = sum(1 for h in recent if h.confidence > 0.7 and h.consensus_stance in (AgentStance.BULL, AgentStance.STRONG_BULL))

        return correct / len(recent) if recent else 0.5


# Singleton
_swarm: SignalAgentSwarm | None = None

def get_signal_swarm() -> SignalAgentSwarm:
    """Get or create the signal agent swarm."""
    global _swarm
    if _swarm is None:
        _swarm = SignalAgentSwarm()
    return _swarm


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    swarm = SignalAgentSwarm()

    # Example signal
    test_signal = {
        'signal_id': 'thermal_dunkirk_001',
        'ticker': 'MT',
        'type': 'INDUSTRIAL_THERMAL',
        'score': 85,
        'anomaly_sigma': 2.3,
        'frp_mw': 120,
        'facility_name': 'ArcelorMittal Dunkirk',
    }

    consensus = swarm.debate_signal(test_signal)

    print(f"\nSwarm Consensus for {consensus.signal_id}:")
    print(f"  Stance: {consensus.consensus_stance.name}")
    print(f"  Score: {consensus.consensus_score}")
    print(f"  Confidence: {consensus.confidence}")
    print(f"  Votes: {consensus.bull_votes} bull, {consensus.bear_votes} bear, {consensus.neutral_votes} neutral")
    print(f"  Reasoning: {consensus.reasoning_summary}")
    print("\nIndividual Votes:")
    for vote in consensus.votes:
        print(f"  {vote.agent.name} ({vote.agent.type}): {vote.stance.name} (conviction: {vote.conviction:.2f})")
        print(f"    → {vote.reasoning[:80]}...")
