import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    sharpe: float
    sharpe_ci_lower_95: float
    sharpe_ci_upper_95: float
    max_drawdown: float
    annualised_return: float
    hit_rate: float
    turnover_annual: float
    n_observations: int

    def validate(self):
        if self.sharpe_ci_lower_95 is None or self.sharpe_ci_upper_95 is None:
            raise ValueError("BacktestResult must include confidence intervals.")


class CostModel:
    def __init__(
        self,
        bid_ask_bps_by_mcap_tier: dict[str, float],
        commission_bps: float = 3.0,
        adtv_participation_cap: float = 0.05,
    ):
        if any(v == 0.0 for v in bid_ask_bps_by_mcap_tier.values()) and commission_bps == 0.0:
            raise ValueError(
                "Zero-cost backtest is rejected. Institutional trading always has costs."
            )
        self.bid_ask = bid_ask_bps_by_mcap_tier
        self.comm = commission_bps

    def compute_impact_bps(
        self, order_size_usd: float, adtv_usd: float, sigma_daily: float
    ) -> float:
        # Almgren-Chriss simplified
        return sigma_daily * np.sqrt(order_size_usd / adtv_usd) * 10000  # Convert to bps approx


class BacktestEngine:
    def __init__(self, cost_model: CostModel):
        self.cost_model = cost_model
        self.logger = logging.getLogger(__name__)

    def compute_sharpe_with_ci(
        self, returns: pd.Series, n_bootstrap: int = 1000, block_size_weeks: int = 13
    ) -> tuple[float, float, float]:
        """Block bootstrap for Sharpe CI."""
        sharpe = self._calc_sharpe(returns)

        boot_sharpes = []
        n = len(returns)
        for _ in range(n_bootstrap):
            # Block bootstrap logic
            indices = np.random.choice(
                n - block_size_weeks, size=n // block_size_weeks, replace=True
            )
            boot_sample = np.concatenate([returns[i : i + block_size_weeks] for i in indices])
            boot_sharpes.append(self._calc_sharpe(pd.Series(boot_sample)))

        ci_lower = float(np.percentile(boot_sharpes, 2.5))
        ci_upper = float(np.percentile(boot_sharpes, 97.5))

        return sharpe, ci_lower, ci_upper

    def _calc_sharpe(self, returns: pd.Series) -> float:
        if returns.std() == 0:
            return 0.0
        return float(returns.mean() / returns.std() * np.sqrt(252))

    def run_backtest(self, returns_series: pd.Series) -> BacktestResult:
        sharpe, low, high = self.compute_sharpe_with_ci(returns_series)

        res = BacktestResult(
            sharpe=sharpe,
            sharpe_ci_lower_95=low,
            sharpe_ci_upper_95=high,
            max_drawdown=float(
                returns_series.cumsum().max() - returns_series.cumsum().min()
            ),  # Simplified
            annualised_return=float(returns_series.mean() * 252),
            hit_rate=float((returns_series > 0).mean()),
            turnover_annual=0.5,
            n_observations=len(returns_series),
        )
        res.validate()
        return res
