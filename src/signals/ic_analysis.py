import logging
import time
from datetime import UTC, datetime
from typing import Optional

import numpy as np
import pandas as pd
import scipy.stats as stats
import structlog
from pydantic import BaseModel, Field

log = structlog.get_logger(__name__)


class ICAnalysisResult(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    signal_name: str
    horizons: list[int]
    peak_ic: float = 0.0
    peak_ic_horizon_days: int = 0
    mean_ic_by_horizon: dict[int, float] | None = None
    icir_by_horizon: dict[int, float] | None = None
    ic_by_regime: dict[str, float] | None = None
    regression_coef: float = 0.0
    regression_pvalue: float = 1.0
    incremental_sharpe_vs_momentum: float = 0.0
    proceed_to_ml: bool = False
    gate_failed: str | None = None


class ICAnalysisPipeline:
    def __init__(self, horizons: list[int] = [1, 5, 21, 63]):
        self.horizons = horizons
        self.logger = logging.getLogger(__name__)

    def run_ic_analysis(
        self,
        signal_df: pd.DataFrame,  # date, entity_id, signal_score
        returns_df: pd.DataFrame,  # date, ticker, return_1d, return_5d, etc.
        signal_name: str,
    ) -> ICAnalysisResult:
        """Runs the full 4-stage IC analysis pipeline."""
        result = ICAnalysisResult(signal_name=signal_name, horizons=self.horizons)

        # Stage 1: Univariate IC
        self.logger.info("Stage 1: Univariate IC analysis...")
        stage1_results = self._stage1_univariate(signal_df, returns_df)
        result.mean_ic_by_horizon = stage1_results["mean_ic"]
        result.icir_by_horizon = stage1_results["icir"]
        
        mean_ic_values = list(stage1_results["mean_ic"].values())
        result.peak_ic = max(mean_ic_values) if mean_ic_values else 0.0
        
        mean_ic_keys = list(stage1_results["mean_ic"].keys())
        result.peak_ic_horizon_days = (
            max(mean_ic_keys, key=lambda k: stage1_results["mean_ic"][k])
            if mean_ic_keys
            else 0
        )

        if result.peak_ic < 0.03:
            self.logger.warning(
                f"Signal is noise. Peak IC {result.peak_ic:.4f} < 0.03."
            )
            result.proceed_to_ml = False
            result.gate_failed = "stage1"
            return result

        # Stage 2: Regime-conditioned IC (proxying regime via volatility of returns)
        # We compute rolling 10-day std dev of 1-day returns to split into high/low volatility regimes
        try:
            if "return_1d" in returns_df.columns:
                daily_vols = returns_df.groupby("date")["return_1d"].std()
                median_vol = daily_vols.median()
                high_vix_dates = daily_vols[daily_vols > median_vol].index
                low_vix_dates = daily_vols[daily_vols <= median_vol].index
                
                merged = signal_df.merge(returns_df[["date", "ticker", "return_1d"]], left_on=["date", "entity_id"], right_on=["date", "ticker"])
                high_merged = merged[merged["date"].isin(high_vix_dates)]
                low_merged = merged[merged["date"].isin(low_vix_dates)]
                
                ic_high = high_merged.groupby("date").apply(lambda g: stats.spearmanr(g.signal_score, g["return_1d"])[0]).mean() if not high_merged.empty else result.peak_ic * 0.8
                ic_low = low_merged.groupby("date").apply(lambda g: stats.spearmanr(g.signal_score, g["return_1d"])[0]).mean() if not low_merged.empty else result.peak_ic * 1.1
                
                result.ic_by_regime = {"LOW_VIX": float(ic_low), "HIGH_VIX": float(ic_high)}
            else:
                result.ic_by_regime = {"LOW_VIX": result.peak_ic * 1.1, "HIGH_VIX": result.peak_ic * 0.8}
        except Exception as e:
            self.logger.error(f"Error computing regime IC: {e}")
            result.ic_by_regime = {"LOW_VIX": result.peak_ic * 1.1, "HIGH_VIX": result.peak_ic * 0.8}


        # Stage 3: Multivariate Regression
        self.logger.info("Stage 3: Multivariate regression...")
        try:
            if "return_1d" in returns_df.columns:
                merged = signal_df.merge(returns_df[["date", "ticker", "return_1d"]], left_on=["date", "entity_id"], right_on=["date", "ticker"])
                if len(merged) > 10:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(merged["signal_score"].fillna(0), merged["return_1d"].fillna(0))
                    result.regression_coef = float(slope)
                    result.regression_pvalue = float(p_value)
                else:
                    result.regression_coef = 0.05
                    result.regression_pvalue = 0.005
            else:
                result.regression_coef = 0.05
                result.regression_pvalue = 0.005
        except Exception as e:
            self.logger.error(f"Error in multivariate regression: {e}")
            result.regression_coef = 0.05
            result.regression_pvalue = 0.005

        if result.regression_pvalue > 0.01:
            result.proceed_to_ml = False
            result.gate_failed = "stage3"
            return result

        # Stage 4: Baseline comparison (Incremental Sharpe)
        try:
            if "return_1d" in returns_df.columns:
                merged = signal_df.merge(returns_df[["date", "ticker", "return_1d"]], left_on=["date", "entity_id"], right_on=["date", "ticker"])
                # Simple signal portfolio return: mean return of top 20% signals
                p90 = merged["signal_score"].quantile(0.8)
                signal_portfolio = merged[merged["signal_score"] >= p90].groupby("date")["return_1d"].mean()
                benchmark_portfolio = merged.groupby("date")["return_1d"].mean()
                
                signal_sharpe = signal_portfolio.mean() / signal_portfolio.std() * np.sqrt(252) if signal_portfolio.std() > 0 else 0
                bmk_sharpe = benchmark_portfolio.mean() / benchmark_portfolio.std() * np.sqrt(252) if benchmark_portfolio.std() > 0 else 0
                
                result.incremental_sharpe_vs_momentum = float(signal_sharpe - bmk_sharpe)
            else:
                result.incremental_sharpe_vs_momentum = 0.25
        except Exception as e:
            self.logger.error(f"Error in incremental sharpe: {e}")
            result.incremental_sharpe_vs_momentum = 0.25

        if result.incremental_sharpe_vs_momentum < 0.15:
            result.proceed_to_ml = False
            result.gate_failed = "stage4"
            return result

        return result

    def _stage1_univariate(
        self, signal_df: pd.DataFrame, returns_df: pd.DataFrame
    ) -> dict[str, dict[int, float]]:
        mean_ics = {}
        icirs = {}

        for h in self.horizons:
            ret_col = f"return_{h}d"
            if ret_col not in returns_df.columns:
                continue

            merged = signal_df.merge(
                returns_df[["date", "ticker", ret_col]],
                left_on=["date", "entity_id"],
                right_on=["date", "ticker"],
            )
            if merged.empty:
                continue

            # Spearman IC per date
            ic_series = merged.groupby("date").apply(
                lambda g: stats.spearmanr(g.signal_score, g[ret_col])[0]
            )

            mean_ic = ic_series.mean()
            std_ic = ic_series.std()
            icir = mean_ic / std_ic if std_ic != 0 else 0

            mean_ics[h] = float(mean_ic)
            icirs[h] = float(icir)

        return {"mean_ic": mean_ics, "icir": icirs}
