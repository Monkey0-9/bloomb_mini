"""
NAV Ramp-Up & Scaling Manager — Phase 12

Manages the graduated capital allocation from 10% to 100%.
Calculates fill quality metrics to detect model drift in live fills.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FillEvaluation:
    symbol: str
    expected_price: float
    actual_price: float
    slippage_bps: float


class RampManager:
    """
    Adjusts order sizes based on current soft-launch ramp stage.
    """

    def __init__(self, target_nav: float = 10_000_000.0):
        self.target_nav = target_nav
        self.current_ramp_pct = 0.10  # Start at 10% Soft Launch
        self.fill_history: list[FillEvaluation] = []

    def scale_quantity(self, theoretical_qty: int) -> int:
        """Scale orders to current launch stage allocation."""
        return int(theoretical_qty * self.current_ramp_pct)

    def record_fill_quality(self, symbol: str, expected: float, actual: float) -> None:
        """Monitor slippage vs model prediction."""
        slippage = (actual - expected) / expected * 10000
        evaluation = FillEvaluation(symbol, expected, actual, slippage)
        self.fill_history.append(evaluation)

        if abs(slippage) > 15.0:  # 15bps threshold
            logger.warning(
                f"HIGH SLIPPAGE: {symbol} | Predicted: {expected} | Actual: {actual} | Error: {slippage:.1f}bps"
            )

    def get_aggregate_slippage_error(self) -> float:
        """Average slippage error in bps across all fills."""
        if not self.fill_history:
            return 0.0
        return sum(f.slippage_bps for f in self.fill_history) / len(self.fill_history)

    def promote_ramp(self) -> None:
        """Increment ramp stage (10% -> 25% -> 50% -> 100%)."""
        if self.current_ramp_pct == 0.10:
            self.current_ramp_pct = 0.25
        elif self.current_ramp_pct == 0.25:
            self.current_ramp_pct = 0.50
        elif self.current_ramp_pct == 0.50:
            self.current_ramp_pct = 1.00
        logger.info(f"RAMP PROMOTED: Strategy now operating at {self.current_ramp_pct * 100}% NAV.")
