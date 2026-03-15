"""
Regime Analysis — Phase 6.4

Level 4 validation: analyse signal performance across market regimes.
Ensures the signal is not just a bull/bear market proxy.

Regimes:
  - VIX regime: low (<15), medium (15-25), high (>25), crisis (>35)
  - Market regime: bull (>0% trailing 63d), bear (<0%)
  - Sector rotation: cyclical vs defensive leadership
  - Rate regime: hiking, cutting, holding
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


class VIXRegime:
    LOW = "low_vol"  # VIX < 15
    MEDIUM = "medium_vol"  # 15 ≤ VIX < 25
    HIGH = "high_vol"  # 25 ≤ VIX < 35
    CRISIS = "crisis"  # VIX ≥ 35


class MarketRegime:
    BULL = "bull"  # trailing 63d return ≥ 0
    BEAR = "bear"  # trailing 63d return < 0


class RateRegime:
    HIKING = "hiking"
    CUTTING = "cutting"
    HOLDING = "holding"


class SectorRegime:
    CYCLICAL = "cyclical"
    DEFENSIVE = "defensive"


@dataclass
class RegimePerformance:
    """Performance metrics within a specific market regime."""

    regime_name: str
    regime_value: str
    n_observations: int
    sharpe_ratio: float
    annualised_return: float
    ic_mean: float
    max_drawdown: float
    hit_rate: float
    pct_of_total: float  # % of time spent in this regime


@dataclass
class RegimeAnalysisResult:
    """Complete regime analysis across all regime dimensions."""

    vix_performance: list[RegimePerformance] = field(default_factory=list)
    market_performance: list[RegimePerformance] = field(default_factory=list)
    rate_performance: list[RegimePerformance] = field(default_factory=list)
    sector_performance: list[RegimePerformance] = field(default_factory=list)
    regime_stability: float = 0.0  # Std of Sharpe across regimes (lower = better)
    regime_dependent: bool = False  # True if signal only works in one regime
    warnings: list[str] = field(default_factory=list)


class RegimeAnalyzer:
    """
    Analyse signal performance across market regimes.

    If a signal only works in one regime (e.g., only in bull markets),
    it is flagged as REGIME_DEPENDENT — likely a market beta exposure,
    not genuine alpha.
    """

    REGIME_DEPENDENT_THRESHOLD = 0.3  # Max allowable Sharpe std across regimes

    def analyse(
        self,
        portfolio_returns: np.ndarray,  # (T,)
        vix_levels: np.ndarray | None = None,
        market_returns_63d: np.ndarray | None = None,
        rate_diff: np.ndarray | None = None,
        cyclical_relative_perf: np.ndarray | None = None,
        signals: np.ndarray | None = None,
        asset_returns: np.ndarray | None = None,
    ) -> RegimeAnalysisResult:
        """Run full regime analysis."""
        result = RegimeAnalysisResult()

        # VIX regime analysis
        if vix_levels is not None:
            vix_regimes = self._classify_vix(vix_levels)
            result.vix_performance = self._compute_regime_performance(
                portfolio_returns,
                vix_regimes,
                "VIX",
                signals,
                asset_returns,
            )

        # Market regime analysis
        if market_returns_63d is not None:
            market_regimes = self._classify_market(market_returns_63d)
            result.market_performance = self._compute_regime_performance(
                portfolio_returns,
                market_regimes,
                "Market",
                signals,
                asset_returns,
            )

        # Rate regime analysis
        if rate_diff is not None:
            rate_regimes = self._classify_rates(rate_diff)
            result.rate_performance = self._compute_regime_performance(
                portfolio_returns,
                rate_regimes,
                "Rates",
                signals,
                asset_returns,
            )

        # Sector rotation analysis
        if cyclical_relative_perf is not None:
            sector_regimes = self._classify_sectors(cyclical_relative_perf)
            result.sector_performance = self._compute_regime_performance(
                portfolio_returns,
                sector_regimes,
                "Sectors",
                signals,
                asset_returns,
            )

        # Stability assessment
        all_rp = (
            result.vix_performance
            + result.market_performance
            + result.rate_performance
            + result.sector_performance
        )
        all_sharpes = [rp.sharpe_ratio for rp in all_rp if rp.n_observations > 10]
        if all_sharpes:
            result.regime_stability = float(np.std(all_sharpes))
            result.regime_dependent = result.regime_stability > self.REGIME_DEPENDENT_THRESHOLD

            if result.regime_dependent:
                warning = (
                    f"REGIME DEPENDENT: Sharpe std across regimes = "
                    f"{result.regime_stability:.3f} > {self.REGIME_DEPENDENT_THRESHOLD}. "
                    f"Signal may be a disguised market beta exposure."
                )
                result.warnings.append(warning)
                logger.warning(warning)

        return result

    def _classify_vix(self, vix: np.ndarray) -> np.ndarray:
        """Classify VIX levels into regime labels."""
        regimes = np.empty(len(vix), dtype=object)
        regimes[vix < 15] = VIXRegime.LOW
        regimes[(vix >= 15) & (vix < 25)] = VIXRegime.MEDIUM
        regimes[(vix >= 25) & (vix < 35)] = VIXRegime.HIGH
        regimes[vix >= 35] = VIXRegime.CRISIS
        return regimes

    def _classify_market(self, trailing_returns: np.ndarray) -> np.ndarray:
        """Classify market regime from trailing 63-day returns."""
        regimes = np.empty(len(trailing_returns), dtype=object)
        regimes[trailing_returns >= 0] = MarketRegime.BULL
        regimes[trailing_returns < 0] = MarketRegime.BEAR
        return regimes

    def _classify_rates(self, rate_diff: np.ndarray) -> np.ndarray:
        """Classify rate regime from basis point changes."""
        regimes = np.empty(len(rate_diff), dtype=object)
        regimes[rate_diff > 10] = RateRegime.HIKING
        regimes[rate_diff < -10] = RateRegime.CUTTING
        regimes[(rate_diff >= -10) & (rate_diff <= 10)] = RateRegime.HOLDING
        return regimes

    def _classify_sectors(self, cyclical_relative_perf: np.ndarray) -> np.ndarray:
        """Classify sector leadership from cyclical vs defensive relative returns."""
        regimes = np.empty(len(cyclical_relative_perf), dtype=object)
        regimes[cyclical_relative_perf >= 0] = SectorRegime.CYCLICAL
        regimes[cyclical_relative_perf < 0] = SectorRegime.DEFENSIVE
        return regimes

    def _compute_regime_performance(
        self,
        returns: np.ndarray,
        regimes: np.ndarray,
        dimension_name: str,
        signals: np.ndarray | None = None,
        asset_returns: np.ndarray | None = None,
    ) -> list[RegimePerformance]:
        """Compute performance metrics for each regime level."""
        unique_regimes = [r for r in np.unique(regimes) if r is not None]
        performance = []
        total = len(returns)

        for regime in unique_regimes:
            mask = regimes == regime
            regime_returns = returns[mask]
            n = len(regime_returns)

            if n < 5:
                continue

            mean_ret = float(np.mean(regime_returns))
            std_ret = float(np.std(regime_returns, ddof=1))
            sharpe = mean_ret / std_ret * np.sqrt(52) if std_ret > 0 else 0

            # Max drawdown
            cum = np.cumprod(1 + regime_returns)
            peak = np.maximum.accumulate(cum)
            dd = (peak - cum) / peak
            max_dd = float(np.max(dd)) * 100

            # Hit rate
            hit_rate = float(np.mean(regime_returns > 0)) * 100

            # IC in this regime
            ic_mean = 0.0
            if signals is not None and asset_returns is not None:
                from scipy import stats

                regime_signals = signals[mask]
                regime_asset_returns = asset_returns[mask]
                ics = []
                for t in range(len(regime_signals)):
                    if regime_signals.ndim > 1 and regime_asset_returns.ndim > 1:
                        s = regime_signals[t]
                        r = regime_asset_returns[t]
                        valid = ~(np.isnan(s) | np.isnan(r))
                        if np.sum(valid) > 3:
                            ic, _ = stats.spearmanr(s[valid], r[valid])
                            ics.append(ic)
                ic_mean = float(np.mean(ics)) if ics else 0

            performance.append(
                RegimePerformance(
                    regime_name=dimension_name,
                    regime_value=str(regime),
                    n_observations=n,
                    sharpe_ratio=sharpe,
                    annualised_return=mean_ret * 52,
                    ic_mean=ic_mean,
                    max_drawdown=max_dd,
                    hit_rate=hit_rate,
                    pct_of_total=n / total * 100,
                )
            )

        return performance
