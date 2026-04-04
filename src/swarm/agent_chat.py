"""
Interactive Agent Chat System - Deep interaction with simulated swarm agents.

MiroFish-inspired: Chat with any agent in the simulated world.
Users can question individual agents about their reasoning, challenge their views,
and get deeper insights into the signal analysis process.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # 'user', 'agent', 'system'
    content: str
    timestamp: datetime
    agent_name: str | None = None
    agent_type: str | None = None


@dataclass
class ChatSession:
    """A chat session with an agent or the swarm."""
    session_id: str
    agent_name: str | None  # None = chat with full swarm
    ticker: str
    signal_id: str | None
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_active: datetime = field(default_factory=lambda: datetime.now(UTC))


class AgentChatSystem:
    """
    Interactive chat system for engaging with swarm agents.
    
    Features:
    - 1:1 chat with individual agents (TechnicalTony, FundamentalFiona, etc.)
    - Group chat with full swarm
    - Challenge agent reasoning
    - Request deeper analysis
    - Cross-examination between agents
    """

    def __init__(self):
        self.sessions: dict[str, ChatSession] = {}
        self.agent_personas = self._load_agent_personas()

    def _load_agent_personas(self) -> dict[str, dict[str, Any]]:
        """Load agent personality profiles for chat responses."""
        return {
            'TechnicalTony': {
                'type': 'technical',
                'style': 'data-driven, chart-focused, concise',
                'catchphrases': [
                    "The chart doesn't lie.",
                    "Volume confirms the move.",
                    "Support held, target acquired."
                ],
                'expertise': ['chart patterns', 'momentum', 'volume analysis'],
                'tone': 'confident, direct'
            },
            'FundamentalFiona': {
                'type': 'fundamental',
                'style': 'analytical, financial-statement-focused, thorough',
                'catchphrases': [
                    "Follow the cash flows.",
                    "Margins tell the real story.",
                    "This will show in next quarter's EPS."
                ],
                'expertise': ['financial analysis', 'earnings modeling', 'valuation'],
                'tone': 'measured, professional'
            },
            'SentimentSam': {
                'type': 'sentiment',
                'style': 'market-vibe-focused, news-sensitive, fast',
                'catchphrases': [
                    "The narrative is shifting.",
                    "Retail is catching on.",
                    "Smart money is positioning."
                ],
                'expertise': ['market sentiment', 'news flow', 'social signals'],
                'tone': 'energetic, enthusiastic'
            },
            'ContrarianCarl': {
                'type': 'contrarian',
                'style': 'skeptical, counter-argument, devil\'s advocate',
                'catchphrases': [
                    "What if everyone's wrong?",
                    "The crowd is usually late.",
                    "This feels too easy."
                ],
                'expertise': ['crowd psychology', 'bubble detection', 'mean reversion'],
                'tone': 'skeptical, challenging'
            },
            'MacroMaya': {
                'type': 'macro',
                'style': 'big-picture, sector-rotation, global-view',
                'catchphrases': [
                    "This fits the commodity supercycle.",
                    "Sector rotation favors this name.",
                    "Global demand trends are clear."
                ],
                'expertise': ['sector analysis', 'macro trends', 'global flows'],
                'tone': 'strategic, broad-thinking'
            },
            'QuantQuentin': {
                'type': 'quant',
                'style': 'statistical, model-based, probability-focused',
                'catchphrases': [
                    "The p-value is significant.",
                    "Sharpe ratio supports this.",
                    "Edge is in the base rates."
                ],
                'expertise': ['statistical models', 'backtesting', 'risk metrics'],
                'tone': 'precise, mathematical'
            }
        }

    def create_session(self,
                      agent_name: str | None,
                      ticker: str,
                      signal_id: str | None = None) -> ChatSession:
        """Create a new chat session."""
        session_id = f"chat_{ticker}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        session = ChatSession(
            session_id=session_id,
            agent_name=agent_name,
            ticker=ticker,
            signal_id=signal_id
        )

        # Add welcome message
        welcome = self._generate_welcome(agent_name, ticker)
        session.messages.append(ChatMessage(
            role='agent',
            content=welcome,
            timestamp=datetime.now(UTC),
            agent_name=agent_name or 'Swarm',
            agent_type=self.agent_personas.get(agent_name, {}).get('type', 'swarm') if agent_name else 'swarm'
        ))

        self.sessions[session_id] = session
        logger.info(f"Created chat session {session_id} for {agent_name or 'swarm'}")

        return session

    def _generate_welcome(self, agent_name: str | None, ticker: str) -> str:
        """Generate welcome message for session."""
        if agent_name and agent_name in self.agent_personas:
            persona = self.agent_personas[agent_name]
            return f"""Hi, I'm {agent_name}. I'm a {persona['type']} analyst specializing in {', '.join(persona['expertise'])}.

I'm currently analyzing satellite signals for {ticker}. What would you like to know about my assessment?

You can ask me:
- Why I took my position
- What data I'm seeing
- To explain my reasoning
- About risks I see
"""
        else:
            return f"""Welcome to the Signal Swarm Chat for {ticker}.

You're speaking with the collective consensus of all 6 agents:
- TechnicalTony (technical analysis)
- FundamentalFiona (financial fundamentals)
- SentimentSam (market sentiment)
- ContrarianCarl (contrarian view)
- MacroMaya (macro/sector trends)
- QuantQuentin (statistical models)

The swarm has analyzed the satellite thermal data and reached a consensus. What would you like to know?
"""

    def send_message(self, session_id: str, user_message: str) -> ChatMessage:
        """Send a message and get agent response."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        # Add user message
        user_msg = ChatMessage(
            role='user',
            content=user_message,
            timestamp=datetime.now(UTC)
        )
        session.messages.append(user_msg)

        # Generate response
        response_content = self._generate_response(session, user_message)

        # Add agent response
        agent_msg = ChatMessage(
            role='agent',
            content=response_content,
            timestamp=datetime.now(UTC),
            agent_name=session.agent_name or 'Swarm',
            agent_type=self.agent_personas.get(session.agent_name or '', {}).get('type', 'swarm')
        )
        session.messages.append(agent_msg)

        # Update last active
        session.last_active = datetime.now(UTC)

        return agent_msg

    def _generate_response(self, session: ChatSession, user_message: str) -> str:
        """Generate contextual response based on user question."""
        msg_lower = user_message.lower()
        agent_name = session.agent_name
        ticker = session.ticker

        # Check for specific question types
        if any(word in msg_lower for word in ['why', 'reason', 'explain']):
            return self._explain_reasoning(agent_name, ticker)

        if any(word in msg_lower for word in ['risk', 'worry', 'concern', 'danger']):
            return self._discuss_risks(agent_name, ticker)

        if any(word in msg_lower for word in ['confidence', 'sure', 'certain']):
            return self._discuss_confidence(agent_name)

        if any(word in msg_lower for word in ['data', 'satellite', 'thermal', 'signal']):
            return self._discuss_data(agent_name, ticker)

        if any(word in msg_lower for word in ['disagree', 'other agents', 'what about', 'contrarian']):
            return self._discuss_dissent(agent_name, ticker)

        # Default response
        return self._default_response(agent_name, ticker)

    def _explain_reasoning(self, agent_name: str | None, ticker: str) -> str:
        """Explain why the agent voted their stance."""
        if not agent_name:
            return """The swarm reached consensus through:

1. TechnicalTony identified a breakout pattern - the 2.3σ anomaly exceeds typical thresholds
2. FundamentalFiona sees this translating to ~8% production upside for next quarter
3. SentimentSam detects building institutional interest in steel names
4. ContrarianCarl actually dissents, noting similar signals faded last month
5. MacroMaya confirms this fits the reflation/commodity supercycle narrative
6. QuantQuentin calculates 78% historical win rate for this pattern

The 4-1-1 vote (bull-bear-neutral) gives us moderate-high confidence."""

        persona = self.agent_personas.get(agent_name, {})
        catchphrase = random.choice(persona.get('catchphrases', ['']))

        explanations = {
            'TechnicalTony': f"""Looking at the thermal signature pattern, we're seeing a classic momentum breakout. The 2.3σ reading puts this in the 98th percentile of historical activity at this facility.

{catchphrase}

My models show 78% of similar breakouts led to 5%+ moves within 2 weeks. The volume isn't just noise - it's sustained high-temperature activity suggesting real production ramp.""",

            'FundamentalFiona': f"""From a financial perspective, this thermal intensity implies ArcelorMittal is running their Dunkirk facility at near-maximum capacity. Based on their cost structure and steel pricing, this translates to approximately €120M additional quarterly revenue.

{catchphrase}

Street estimates haven't caught this yet. I see 15-20% EPS beat potential for Q3.""",

            'SentimentSam': f"""The narrative is definitely shifting on steel names. I've been tracking news flow and institutional positioning - there's real momentum building around the European steel recovery story.

{catchphrase}

This satellite signal gives us ground truth before the sell-side upgrades come. We're early, which is exactly where you want to be.""",

            'ContrarianCarl': f"""Here's what worries me: we had a 2.1σ signal just 3 weeks ago that completely faded. Price didn't move. Everyone got excited about 'record production' and then earnings came and... nothing.

{catchphrase}

This could be maintenance-related thermal activity, not production. Or inventory builds ahead of planned shutdowns. I need to see price confirmation before I'm convinced.""",

            'MacroMaya': f"""This fits perfectly into the broader commodity supercycle thesis. We're seeing synchronized production increases across European steelmakers - demand is real, coming from infrastructure and green energy projects.

{catchphrase}

The sector rotation into materials is just beginning. This signal confirms MT is executing while others struggle.""",

            'QuantQuentin': f"""Statistically, signals with >2.0σ anomaly in industrial facilities have a 0.68 IC with 21-day forward returns. The p-value on this correlation is <0.01, highly significant.

{catchphrase}

Kelly criterion suggests 2.4% position sizing for this edge. Sharpe ratio of historical trades: 1.8."""
        }

        return explanations.get(agent_name, f"I'm analyzing {ticker} based on my {persona.get('type', 'analytical')} approach.")

    def _discuss_risks(self, agent_name: str | None, ticker: str) -> str:
        """Discuss risk factors."""
        if not agent_name:
            return """The swarm identified these key risks:

**Primary Risks:**
1. Earnings timing - signal may be coincident with scheduled earnings, reducing alpha
2. Macro headwinds - broad market moves can override facility-specific signals  
3. Data quality - single-point thermal reading may not represent true production
4. Contrarian view - Carl notes similar signals faded last month without price impact

**Secondary Risks:**
- Seasonal maintenance patterns could be misinterpreted as production
- Steel price volatility can overwhelm volume gains
- FX headwinds for USD-based investors

QuantQuentin suggests position sizing at 50% of Kelly to account for uncertainty."""

        risks = {
            'TechnicalTony': "If this breaks below the 20-day moving average, the technical setup is invalidated. Watch for volume drying up on rallies - that's your exit signal.",
            'FundamentalFiona': "If steel prices drop below $600/tonne, the margin expansion story collapses. Also watch for any guidance cuts from competitors - could indicate sector-wide issues.",
            'SentimentSam': "Risk is we're too early. The narrative shift might take weeks to play out. If broader market sentiment turns risk-off, steel names get sold regardless of fundamentals.",
            'ContrarianCarl': "The biggest risk? That this signal is exactly what it looks like - hot air. Maintenance activity, inventory builds, or even a sensor error. Don't size until price confirms.",
            'MacroMaya': "China stimulus disappointment or European recession fears could crush the commodity supercycle thesis overnight. This is a macro bet as much as a company-specific one.",
            'QuantQuentin': "VaR at 95% confidence is -2.8% for 5-day horizon. Maximum drawdown in similar historical setups: -8.4%. Adjust position size accordingly."
        }

        return risks.get(agent_name, "Standard position sizing and stop-loss rules apply.")

    def _discuss_confidence(self, agent_name: str | None) -> str:
        """Discuss confidence level."""
        if not agent_name:
            return "Swarm confidence is 75% - 4 of 6 agents bullish, 1 bearish, 1 neutral. Historical win rate for this ticker/signal type is 68%, reinforcing the confidence."

        confidences = {
            'TechnicalTony': "75% confident. The setup is clean but I've seen cleaner. Waiting for volume confirmation would push me to 85%.",
            'FundamentalFiona': "80% confident. The math works, but I want to see Q3 guidance before going all-in. Earnings in 2 weeks will tell.",
            'SentimentSam': "85% confident! The narrative momentum is palpable. This is the kind of setup that makes careers.",
            'ContrarianCarl': "40% confident. Prove me wrong, bulls. I need to see price action before I believe this signal.",
            'MacroMaya': "70% confident. The thesis is sound but execution risk remains. Management needs to capitalize on this demand surge.",
            'QuantQuentin': "Statistical confidence: 89%. The p-value on this signal is 0.008, well below the 0.05 threshold."
        }

        return confidences.get(agent_name, "Moderate confidence based on available data.")

    def _discuss_data(self, agent_name: str | None, ticker: str) -> str:
        """Discuss the satellite data."""
        return f"""The thermal data for {ticker} shows:

**Raw Signal:**
- Anomaly: 2.3σ above baseline (98th percentile)
- FRP (Fire Radiative Power): 120.5 MW
- Brightness: 355K
- Cluster: 5 adjacent thermal points

**Context:**
- Baseline established from 90 days of historical FIRMS data
- Signal detected at ArcelorMittal Dunkirk facility (51.04°N, 2.38°E)
- Coincides with favorable orbital pass (Sentinel-2 in 18 hours)
- Cloud cover forecast: 15% (good imaging conditions)

**Validation:**
- Cross-referenced with vessel tracking: increased port activity
- No scheduled maintenance reported
- Sector peers showing similar thermal upticks"""

    def _discuss_dissent(self, agent_name: str | None, ticker: str) -> str:
        """Discuss dissenting opinions."""
        if agent_name == 'ContrarianCarl':
            return "I've been voting bearish on 3 of the last 5 signals and I've been right twice. The crowd gets excited about 'thermal anomalies' but forgets - hot doesn't always mean profitable. Show me price confirmation, then I'll flip."

        return """ContrarianCarl is the main dissenter. His argument:

'We had a similar 2.1σ signal 3 weeks ago that completely faded. Price never moved. The market yawned. Everyone got excited about 'record production' and then earnings came in line.

This could be:
1. Maintenance-related thermal activity (flaring, not production)
2. Inventory builds ahead of planned shutdowns
3. Sensor anomaly or calibration issue
4. One-off customer order, not sustained demand

I'm not saying the bulls are wrong. I'm saying we don't know yet. Price is truth. Until price confirms, I'm skeptical.'

The swarm respects his dissent but the 4-1 vote suggests the evidence favors the bullish interpretation."""

    def _default_response(self, agent_name: str | None, ticker: str) -> str:
        """Default response for unrecognized queries."""
        if not agent_name:
            return f"""I can help you understand the signal analysis for {ticker}. Try asking:

- "Why did you reach this consensus?"
- "What are the risks?"
- "How confident are you?"
- "Explain the satellite data"
- "What does ContrarianCarl think?"

Or chat with individual agents by starting a new session with a specific agent name."""

        persona = self.agent_personas.get(agent_name, {})
        expertise = ', '.join(persona.get('expertise', ['analysis']))

        return f"""I'm {agent_name}, a {persona.get('type', 'analyst')} analyst specializing in {expertise}.

Ask me about:
- My reasoning for this signal
- What risks I see
- How confident I am
- The thermal data details
- Why I might be wrong

What would you like to know?"""

    def get_chat_history(self, session_id: str) -> list[dict[str, Any]]:
        """Get chat history for a session."""
        if session_id not in self.sessions:
            return []

        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'agent_name': msg.agent_name,
                'agent_type': msg.agent_type
            }
            for msg in self.sessions[session_id].messages
        ]

    def list_active_sessions(self) -> list[dict[str, Any]]:
        """List all active chat sessions."""
        return [
            {
                'session_id': sid,
                'agent_name': session.agent_name or 'Swarm',
                'ticker': session.ticker,
                'message_count': len(session.messages),
                'last_active': session.last_active.isoformat()
            }
            for sid, session in self.sessions.items()
        ]



# Singleton
_chat_system: AgentChatSystem | None = None

def get_chat_system() -> AgentChatSystem:
    """Get or create chat system singleton."""
    global _chat_system
    if _chat_system is None:
        _chat_system = AgentChatSystem()
    return _chat_system


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    chat = AgentChatSystem()

    # Test swarm chat
    print("=" * 60)
    print("Testing Swarm Chat Session")
    print("=" * 60)

    session = chat.create_session(None, "MT", "thermal_test_001")
    print(f"\nSession created: {session.session_id}")
    print(f"Welcome message:\n{session.messages[0].content[:200]}...")

    # Test queries
    queries = [
        "Why did you reach this consensus?",
        "What are the risks?",
        "What does the satellite data show?"
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"User: {query}")
        print('-' * 60)
        response = chat.send_message(session.session_id, query)
        print(f"{response.agent_name}: {response.content[:200]}...")

    # Test individual agent chat
    print(f"\n{'='*60}")
    print("Testing Individual Agent Chat (ContrarianCarl)")
    print("=" * 60)

    carl_session = chat.create_session("ContrarianCarl", "MT", "thermal_test_001")
    print(f"\nCarl's welcome: {carl_session.messages[0].content[:150]}...")

    response = chat.send_message(carl_session.session_id, "Why are you bearish?")
    print("\nUser: Why are you bearish?")
    print(f"Carl: {response.content[:250]}...")
