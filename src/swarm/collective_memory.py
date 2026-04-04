"""
Collective Memory System - Historical signal-market pattern learning.

Inspired by MiroFish collective memory:
- Stores historical satellite signals and their market outcomes
- Learns patterns: which signals predict which movements
- Provides similarity matching for new signals vs historical ones
- Improves prediction accuracy over time through experience
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SignalMemory:
    """A single signal memory with its market outcome."""
    signal_id: str
    timestamp: datetime
    ticker: str
    facility_name: str
    signal_type: str  # 'thermal', 'vessel', 'geopolitical'

    # Signal characteristics
    anomaly_sigma: float
    signal_score: float
    direction: str

    # Market outcome (recorded after prediction period)
    entry_price: float | None = None
    exit_price: float | None = None
    forward_return_1d: float | None = None
    forward_return_5d: float | None = None
    forward_return_21d: float | None = None

    # Prediction accuracy
    prediction_correct: bool | None = None  # Did signal direction match return?
    confidence_score: float = 0.0

    # Context
    market_regime: str = 'unknown'  # 'bull', 'bear', 'range'
    sector_trend: str = 'neutral'
    similar_signals: list[str] = field(default_factory=list)


@dataclass
class Pattern:
    """A learned pattern from multiple similar signals."""
    pattern_id: str
    ticker: str
    signal_type: str

    # Pattern characteristics
    avg_sigma_range: tuple[float, float]  # Min/max anomaly sigma
    avg_score_range: tuple[float, float]
    typical_direction: str

    # Outcome statistics
    n_occurrences: int
    win_rate: float  # % of times prediction was correct
    avg_return_5d: float
    avg_return_21d: float
    sharpe_ratio: float

    # Confidence metrics
    confidence_trend: str  # 'improving', 'stable', 'degrading'
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


class CollectiveMemory:
    """
    Collective memory system for signal-market pattern learning.
    
    Stores:
    - Every signal detected and its eventual market outcome
    - Patterns of which signal types predict which movements
    - Similarity scores for new signals vs historical ones
    
    Enables:
    - "This thermal signal at ArcelorMittal previously led to +5% moves"
    - Win rate calculations per facility/ticker
    - Confidence adjustment based on historical accuracy
    """

    def __init__(self, max_memories: int = 10000):
        self.memories: dict[str, SignalMemory] = {}  # signal_id -> memory
        self.ticker_memories: dict[str, list[str]] = defaultdict(list)  # ticker -> signal_ids
        self.patterns: dict[str, Pattern] = {}  # pattern_id -> pattern
        self.max_memories = max_memories

    def store_signal(self, memory: SignalMemory) -> None:
        """
        Store a new signal in collective memory.
        
        Called when a signal is first detected (before outcome known).
        """
        self.memories[memory.signal_id] = memory
        self.ticker_memories[memory.ticker].append(memory.signal_id)

        # Prune old memories if needed
        if len(self.memories) > self.max_memories:
            self._prune_old_memories()

        logger.info(f"Stored signal memory: {memory.signal_id} for {memory.ticker}")

    def update_outcome(self,
                      signal_id: str,
                      forward_return_1d: float | None = None,
                      forward_return_5d: float | None = None,
                      forward_return_21d: float | None = None) -> None:
        """
        Update a signal memory with its actual market outcome.
        
        Called after prediction period has elapsed.
        """
        if signal_id not in self.memories:
            logger.warning(f"Cannot update unknown signal: {signal_id}")
            return

        memory = self.memories[signal_id]

        if forward_return_1d is not None:
            memory.forward_return_1d = forward_return_1d
        if forward_return_5d is not None:
            memory.forward_return_5d = forward_return_5d
        if forward_return_21d is not None:
            memory.forward_return_21d = forward_return_21d

        # Determine if prediction was correct
        if memory.forward_return_5d is not None:
            predicted_bullish = memory.direction in ('BULLISH', 'STRONG_BULL')
            actual_bullish = memory.forward_return_5d > 0
            memory.prediction_correct = (predicted_bullish == actual_bullish)

        # Update patterns
        self._update_patterns(memory)

        logger.info(
            f"Updated outcome for {signal_id}: 5d return={forward_return_5d}, "
            f"correct={memory.prediction_correct}"
        )

    def find_similar_signals(self,
                            ticker: str,
                            signal_type: str,
                            anomaly_sigma: float,
                            n_results: int = 5) -> list[SignalMemory]:
        """
        Find historical signals similar to given characteristics.
        
        Uses similarity scoring based on:
        - Same ticker
        - Same signal type
        - Similar anomaly sigma
        """
        candidates = []

        for signal_id in self.ticker_memories.get(ticker, []):
            memory = self.memories.get(signal_id)
            if not memory or memory.signal_type != signal_type:
                continue

            # Calculate similarity score
            sigma_diff = abs(memory.anomaly_sigma - anomaly_sigma)
            if sigma_diff > 2.0:  # Too dissimilar
                continue

            # Score: closer sigma = higher similarity
            similarity = 1.0 / (1.0 + sigma_diff)

            if memory.prediction_correct is not None:
                candidates.append((similarity, memory))

        # Sort by similarity
        candidates.sort(key=lambda x: x[0], reverse=True)

        return [m for _, m in candidates[:n_results]]

    def get_win_rate(self,
                    ticker: str,
                    signal_type: str | None = None,
                    lookback_days: int = 90) -> float:
        """
        Calculate win rate for a ticker/signal type combination.
        
        Win rate = % of predictions that matched actual direction.
        """
        cutoff = datetime.now(UTC) - timedelta(days=lookback_days)

        relevant = []
        for signal_id in self.ticker_memories.get(ticker, []):
            memory = self.memories.get(signal_id)
            if not memory:
                continue
            if memory.timestamp < cutoff:
                continue
            if signal_type and memory.signal_type != signal_type:
                continue
            if memory.prediction_correct is None:
                continue

            relevant.append(memory)

        if not relevant:
            return 0.5  # No data = coin flip

        wins = sum(1 for m in relevant if m.prediction_correct)
        return wins / len(relevant)

    def get_expected_return(self,
                           ticker: str,
                           signal_type: str,
                           anomaly_sigma: float,
                           horizon_days: int = 5) -> tuple[float, float]:
        """
        Get expected return and confidence based on similar historical signals.
        
        Returns:
            (expected_return, confidence) tuple
        """
        similar = self.find_similar_signals(ticker, signal_type, anomaly_sigma, n_results=20)

        if len(similar) < 5:
            return 0.0, 0.0  # Insufficient data

        # Get returns for requested horizon
        returns = []
        for m in similar:
            if horizon_days <= 1 and m.forward_return_1d is not None:
                returns.append(m.forward_return_1d)
            elif horizon_days <= 5 and m.forward_return_5d is not None:
                returns.append(m.forward_return_5d)
            elif m.forward_return_21d is not None:
                returns.append(m.forward_return_21d)

        if not returns:
            return 0.0, 0.0

        expected_return = np.mean(returns)
        # Confidence based on consistency and sample size
        std = np.std(returns) if len(returns) > 1 else 1.0
        consistency = 1.0 / (1.0 + std)
        sample_confidence = min(1.0, len(returns) / 20)
        confidence = consistency * sample_confidence

        return round(expected_return, 4), round(confidence, 2)

    def _update_patterns(self, memory: SignalMemory) -> None:
        """Update learned patterns based on new outcome data."""
        # Create pattern key
        pattern_key = f"{memory.ticker}_{memory.signal_type}"

        # Find or create pattern
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = Pattern(
                pattern_id=pattern_key,
                ticker=memory.ticker,
                signal_type=memory.signal_type,
                avg_sigma_range=(memory.anomaly_sigma, memory.anomaly_sigma),
                avg_score_range=(memory.signal_score, memory.signal_score),
                typical_direction=memory.direction,
                n_occurrences=0,
                win_rate=0.0,
                avg_return_5d=0.0,
                avg_return_21d=0.0,
                sharpe_ratio=0.0,
                confidence_trend='stable'
            )

        pattern = self.patterns[pattern_key]

        # Update statistics
        old_n = pattern.n_occurrences
        pattern.n_occurrences += 1
        new_n = pattern.n_occurrences

        # Update ranges
        pattern.avg_sigma_range = (
            min(pattern.avg_sigma_range[0], memory.anomaly_sigma),
            max(pattern.avg_sigma_range[1], memory.anomaly_sigma)
        )

        # Update win rate
        if memory.prediction_correct is not None:
            pattern.win_rate = (pattern.win_rate * old_n + (1.0 if memory.prediction_correct else 0.0)) / new_n

        # Update returns
        if memory.forward_return_5d is not None:
            pattern.avg_return_5d = (pattern.avg_return_5d * old_n + memory.forward_return_5d) / new_n
        if memory.forward_return_21d is not None:
            pattern.avg_return_21d = (pattern.avg_return_21d * old_n + memory.forward_return_21d) / new_n

        pattern.last_updated = datetime.now(UTC)

    def _prune_old_memories(self) -> None:
        """Remove oldest memories to stay under limit."""
        sorted_memories = sorted(
            self.memories.items(),
            key=lambda x: x[1].timestamp
        )

        # Remove oldest 10%
        to_remove = int(self.max_memories * 0.1)
        for signal_id, _ in sorted_memories[:to_remove]:
            del self.memories[signal_id]
            # Clean up from ticker index
            for ticker, ids in self.ticker_memories.items():
                if signal_id in ids:
                    self.ticker_memories[ticker].remove(signal_id)

        logger.info(f"Pruned {to_remove} old memories")

    def get_insight_report(self, ticker: str) -> dict[str, Any]:
        """
        Generate insight report for a ticker based on collective memory.
        
        Returns:
            Dict with win rates, patterns, and recommendations
        """
        # Get all memories for this ticker
        signal_ids = self.ticker_memories.get(ticker, [])
        memories = [self.memories[sid] for sid in signal_ids if sid in self.memories]

        if not memories:
            return {'error': f'No memory for {ticker}'}

        # Calculate statistics by signal type
        stats_by_type = defaultdict(lambda: {'count': 0, 'wins': 0, 'avg_return': 0.0})

        for m in memories:
            if m.prediction_correct is None:
                continue

            s = stats_by_type[m.signal_type]
            s['count'] += 1
            if m.prediction_correct:
                s['wins'] += 1
            if m.forward_return_5d:
                s['avg_return'] = (s['avg_return'] * (s['count'] - 1) + m.forward_return_5d) / s['count']

        # Get patterns
        patterns = [
            p for p in self.patterns.values()
            if p.ticker == ticker
        ]

        # Overall win rate
        total_wins = sum(s['wins'] for s in stats_by_type.values())
        total_count = sum(s['count'] for s in stats_by_type.values())
        overall_win_rate = total_wins / total_count if total_count > 0 else 0.5

        return {
            'ticker': ticker,
            'total_signals': len(memories),
            'overall_win_rate': round(overall_win_rate, 2),
            'by_signal_type': dict(stats_by_type),
            'learned_patterns': [
                {
                    'type': p.signal_type,
                    'win_rate': round(p.win_rate, 2),
                    'avg_return_5d': round(p.avg_return_5d, 4),
                    'n_occurrences': p.n_occurrences
                }
                for p in sorted(patterns, key=lambda x: x.win_rate, reverse=True)
            ],
            'recommendation': self._generate_recommendation(overall_win_rate, stats_by_type)
        }

    def _generate_recommendation(self,
                                win_rate: float,
                                stats: dict[str, Any]) -> str:
        """Generate human-readable recommendation."""
        if win_rate > 0.65:
            return f"Strong historical edge ({win_rate:.0%} win rate). Satellite signals for this ticker have been reliable predictors."
        elif win_rate > 0.55:
            return f"Moderate edge ({win_rate:.0%} win rate). Signals work but require confirmation."
        elif win_rate > 0.45:
            return f"No clear edge ({win_rate:.0%} win rate). Signal noise roughly equals signal."
        else:
            return f"Poor track record ({win_rate:.0%} win rate). Consider fading or ignoring signals."

    def save(self, filepath: str) -> None:
        """Save memory to JSON file."""
        data = {
            'memories': [
                {
                    'signal_id': m.signal_id,
                    'timestamp': m.timestamp.isoformat(),
                    'ticker': m.ticker,
                    'facility_name': m.facility_name,
                    'signal_type': m.signal_type,
                    'anomaly_sigma': m.anomaly_sigma,
                    'signal_score': m.signal_score,
                    'direction': m.direction,
                    'forward_return_5d': m.forward_return_5d,
                    'forward_return_21d': m.forward_return_21d,
                    'prediction_correct': m.prediction_correct
                }
                for m in self.memories.values()
            ],
            'patterns': [
                {
                    'pattern_id': p.pattern_id,
                    'ticker': p.ticker,
                    'signal_type': p.signal_type,
                    'win_rate': p.win_rate,
                    'avg_return_5d': p.avg_return_5d,
                    'n_occurrences': p.n_occurrences
                }
                for p in self.patterns.values()
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(self.memories)} memories to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> CollectiveMemory:
        """Load memory from JSON file."""
        with open(filepath) as f:
            data = json.load(f)

        memory = cls()

        for m in data.get('memories', []):
            sm = SignalMemory(
                signal_id=m['signal_id'],
                timestamp=datetime.fromisoformat(m['timestamp']),
                ticker=m['ticker'],
                facility_name=m['facility_name'],
                signal_type=m['signal_type'],
                anomaly_sigma=m['anomaly_sigma'],
                signal_score=m['signal_score'],
                direction=m['direction'],
                forward_return_5d=m.get('forward_return_5d'),
                forward_return_21d=m.get('forward_return_21d'),
                prediction_correct=m.get('prediction_correct')
            )
            memory.memories[sm.signal_id] = sm
            memory.ticker_memories[sm.ticker].append(sm.signal_id)

        for p in data.get('patterns', []):
            pattern = Pattern(
                pattern_id=p['pattern_id'],
                ticker=p['ticker'],
                signal_type=p['signal_type'],
                avg_sigma_range=(0, 0),
                avg_score_range=(0, 0),
                typical_direction='NEUTRAL',
                n_occurrences=p.get('n_occurrences', 0),
                win_rate=p.get('win_rate', 0),
                avg_return_5d=p.get('avg_return_5d', 0),
                avg_return_21d=0,
                sharpe_ratio=0
            )
            memory.patterns[pattern.pattern_id] = pattern

        logger.info(f"Loaded {len(memory.memories)} memories from {filepath}")
        return memory


# Singleton
_memory: CollectiveMemory | None = None

def get_collective_memory() -> CollectiveMemory:
    """Get or create the collective memory."""
    global _memory
    if _memory is None:
        _memory = CollectiveMemory()
    return _memory


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    memory = CollectiveMemory()

    # Simulate storing some historical signals
    test_signals = [
        SignalMemory(
            signal_id='thermal_mt_001',
            timestamp=datetime.now(UTC) - timedelta(days=30),
            ticker='MT',
            facility_name='ArcelorMittal Dunkirk',
            signal_type='thermal',
            anomaly_sigma=2.1,
            signal_score=85,
            direction='BULLISH',
            forward_return_5d=0.032,
            forward_return_21d=0.058,
            prediction_correct=True
        ),
        SignalMemory(
            signal_id='thermal_mt_002',
            timestamp=datetime.now(UTC) - timedelta(days=15),
            ticker='MT',
            facility_name='ArcelorMittal Dunkirk',
            signal_type='thermal',
            anomaly_sigma=1.8,
            signal_score=78,
            direction='BULLISH',
            forward_return_5d=0.015,
            forward_return_21d=0.042,
            prediction_correct=True
        ),
        SignalMemory(
            signal_id='thermal_mt_003',
            timestamp=datetime.now(UTC) - timedelta(days=5),
            ticker='MT',
            facility_name='ArcelorMittal Dunkirk',
            signal_type='thermal',
            anomaly_sigma=2.3,
            signal_score=88,
            direction='BULLISH',
            prediction_correct=None  # Not yet resolved
        )
    ]

    for sig in test_signals:
        memory.store_signal(sig)

    # Get insight report
    print("\nCollective Memory Insight Report:")
    print("=" * 60)

    report = memory.get_insight_report('MT')
    print(f"\nTicker: {report['ticker']}")
    print(f"Total Signals: {report['total_signals']}")
    print(f"Overall Win Rate: {report['overall_win_rate']:.0%}")
    print(f"\nRecommendation: {report['recommendation']}")

    # Find similar signals
    print("\nSimilar Signals (sigma=2.0):")
    similar = memory.find_similar_signals('MT', 'thermal', 2.0)
    for s in similar:
        print(f"  {s.signal_id}: σ={s.anomaly_sigma}, return={s.forward_return_5d}, correct={s.prediction_correct}")

    # Get expected return
    expected, conf = memory.get_expected_return('MT', 'thermal', 2.0, horizon_days=5)
    print(f"\nExpected 5-day return for new σ=2.0 signal: {expected:.2%} (confidence: {conf:.0%})")
