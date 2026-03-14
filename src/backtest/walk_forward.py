"""
Walk-Forward Validator — Phase 6.1

Level 1 validation: expanding window, 52-week steps, 12-week OOS.
Ensures model performance is evaluated in a realistic, non-leaking manner.

Walk-forward protocol:
  1. Train on [start, start + 52w]
  2. Test on [start + 52w, start + 64w]
  3. Expand window: Train on [start, start + 104w]
  4. Test on [start + 104w, start + 116w]
  5. Repeat until holdout boundary
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardFold:
    """A single fold in the walk-forward validation."""
    fold_id: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_size: int
    test_size: int
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class WalkForwardResult:
    """Complete walk-forward validation result."""
    folds: list[WalkForwardFold] = field(default_factory=list)
    oos_sharpe_mean: float = 0.0
    oos_sharpe_std: float = 0.0
    oos_ic_mean: float = 0.0
    oos_ic_std: float = 0.0
    degradation_ratio: float = 0.0  # OOS Sharpe / IS Sharpe
    passed: bool = False
    fail_reason: Optional[str] = None


class WalkForwardValidator:
    """
    Walk-forward validation with expanding window.
    
    The last line of defence before backtesting:
    if walk-forward OOS Sharpe < 0.5, do NOT proceed to full backtest.
    """

    MIN_OOS_SHARPE = 0.5  # Below this → INSUFFICIENT_SIGNAL
    TRAIN_STEP_WEEKS = 52
    OOS_WINDOW_WEEKS = 12
    MAX_DEGRADATION_RATIO = 0.5  # OOS should be at least 50% of IS

    def __init__(
        self,
        holdout_start: datetime,
        min_train_weeks: int = 52,
    ) -> None:
        self._holdout_start = holdout_start
        self._min_train_weeks = min_train_weeks

    def generate_folds(
        self,
        dates: list[datetime],
    ) -> list[WalkForwardFold]:
        """Generate walk-forward fold boundaries."""
        folds = []
        fold_id = 0

        dates_sorted = sorted(dates)
        start = dates_sorted[0]

        while True:
            train_end = start + timedelta(weeks=self.TRAIN_STEP_WEEKS * (fold_id + 1))
            test_start = train_end
            test_end = test_start + timedelta(weeks=self.OOS_WINDOW_WEEKS)

            # Stop before holdout
            if test_end > self._holdout_start:
                break

            # Count samples in each window
            train_dates = [d for d in dates_sorted if start <= d < train_end]
            test_dates = [d for d in dates_sorted if test_start <= d < test_end]

            if len(train_dates) < self._min_train_weeks and fold_id == 0:
                logger.warning(f"Insufficient training data for fold {fold_id}")
                break

            if not test_dates:
                break

            folds.append(WalkForwardFold(
                fold_id=fold_id,
                train_start=start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                train_size=len(train_dates),
                test_size=len(test_dates),
            ))

            fold_id += 1

        logger.info(f"Generated {len(folds)} walk-forward folds")
        return folds

    def run(
        self,
        signals: np.ndarray,
        returns: np.ndarray,
        dates: list[datetime],
        train_and_predict_fn: Callable,
    ) -> WalkForwardResult:
        """
        Run full walk-forward validation.
        
        Args:
            signals: (T, N) signal matrix
            returns: (T, N) return matrix
            dates: list of date labels
            train_and_predict_fn: function(X_train, y_train, X_test) → predictions
        """
        folds = self.generate_folds(dates)
        if not folds:
            return WalkForwardResult(
                passed=False,
                fail_reason="Cannot generate any folds — insufficient data",
            )

        oos_sharpes = []
        is_sharpes = []
        oos_ics = []

        for fold in folds:
            # Get train/test indices
            train_mask = np.array([fold.train_start <= d < fold.train_end for d in dates])
            test_mask = np.array([fold.test_start <= d < fold.test_end for d in dates])

            X_train = signals[train_mask]
            y_train = returns[train_mask]
            X_test = signals[test_mask]
            y_test = returns[test_mask]

            # Train model and get predictions
            try:
                predictions = train_and_predict_fn(X_train, y_train, X_test)
            except Exception as e:
                logger.warning(f"Fold {fold.fold_id} failed: {e}")
                continue

            # Compute metrics
            is_sharpe = self._compute_sharpe(y_train.mean(axis=1) if y_train.ndim > 1 else y_train)
            oos_sharpe = self._compute_sharpe(predictions if predictions.ndim == 1 else predictions.mean(axis=1))

            from scipy import stats
            if X_test.ndim > 1 and y_test.ndim > 1:
                ics = []
                for t in range(len(X_test)):
                    valid = ~(np.isnan(X_test[t]) | np.isnan(y_test[t]))
                    if np.sum(valid) > 3:
                        ic, _ = stats.spearmanr(X_test[t][valid], y_test[t][valid])
                        ics.append(ic)
                oos_ic = float(np.mean(ics)) if ics else 0
            else:
                oos_ic = 0

            fold.metrics = {
                "is_sharpe": is_sharpe,
                "oos_sharpe": oos_sharpe,
                "oos_ic": oos_ic,
            }

            oos_sharpes.append(oos_sharpe)
            is_sharpes.append(is_sharpe)
            oos_ics.append(oos_ic)

        if not oos_sharpes:
            return WalkForwardResult(
                folds=folds,
                passed=False,
                fail_reason="No valid folds completed",
            )

        result = WalkForwardResult(
            folds=folds,
            oos_sharpe_mean=float(np.mean(oos_sharpes)),
            oos_sharpe_std=float(np.std(oos_sharpes)),
            oos_ic_mean=float(np.mean(oos_ics)),
            oos_ic_std=float(np.std(oos_ics)),
        )

        # Degradation check
        avg_is = float(np.mean(is_sharpes)) if is_sharpes else 0
        result.degradation_ratio = result.oos_sharpe_mean / avg_is if avg_is > 0 else 0

        # Pass/fail
        if result.oos_sharpe_mean < self.MIN_OOS_SHARPE:
            result.passed = False
            result.fail_reason = (
                f"INSUFFICIENT_SIGNAL: OOS Sharpe {result.oos_sharpe_mean:.3f} "
                f"< {self.MIN_OOS_SHARPE} threshold"
            )
            logger.warning(result.fail_reason)
        elif result.degradation_ratio < self.MAX_DEGRADATION_RATIO:
            result.passed = False
            result.fail_reason = (
                f"SEVERE OVERFIT: OOS/IS ratio {result.degradation_ratio:.2f} "
                f"< {self.MAX_DEGRADATION_RATIO} — model degrades too much"
            )
            logger.warning(result.fail_reason)
        else:
            result.passed = True
            logger.info(
                f"Walk-forward PASSED: OOS Sharpe {result.oos_sharpe_mean:.3f} ± "
                f"{result.oos_sharpe_std:.3f}, degradation ratio {result.degradation_ratio:.2f}"
            )

        return result

    @staticmethod
    def _compute_sharpe(returns: np.ndarray) -> float:
        """Annualised Sharpe from weekly returns."""
        if len(returns) < 2:
            return 0.0
        std = np.std(returns, ddof=1)
        if std < 1e-10:
            return 0.0
        return float(np.mean(returns) / std * np.sqrt(52))
