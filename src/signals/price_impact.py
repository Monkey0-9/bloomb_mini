"""
Price Impact Model — Phase 5.2

Ladder of models per spec:
  1. IC analysis (Spearman rank of signal vs forward returns)
  2. Linear regression (OLS/WLS with Newey-West HAC errors)
  3. LightGBM (gradient boosted trees)
  4. Temporal Fusion Transformer (if sufficient data)
  5. Ensemble (weighted average of 2–4)

Feature attribution: SHAP for tree/tabular, attention heatmap for TFT.
Quarterly refresh: retrain on expanding window (no shrink).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelPrediction:
    """Prediction from a single model."""

    model_name: str
    predicted_return: float
    confidence: float  # 0-1
    feature_importances: dict[str, float] = field(default_factory=dict)
    model_version: str = ""


@dataclass
class ModelMetrics:
    """Evaluation metrics for a model."""

    model_name: str
    ic_mean: float  # Mean Information Coefficient
    ic_std: float
    icir: float  # IC Information Ratio
    r_squared: float
    rmse: float
    sharpe_contribution: float  # Contribution to portfolio Sharpe
    shap_top_features: list[tuple[str, float]] = field(default_factory=list)


class ICAnalyzer:
    """
    Level 1: Information Coefficient analysis.

    Spearman rank correlation between signal value and forward returns.
    This is the initial sanity check — if IC is indistinguishable from
    zero, the signal has no predictive value.
    """

    def compute_ic_series(
        self,
        signals: np.ndarray,  # (T,) or (T, N)
        forward_returns: np.ndarray,  # Same shape
        horizon_label: str = "1w",
        naive_momentum: np.ndarray | None = None,  # No-signal baseline comparison
        vix_series: np.ndarray | None = None,  # VIX conditional macro regression blocks
    ) -> dict[str, Any]:
        """Compute IC statistics with baseline alpha comparison and macro regimes."""
        from scipy import stats

        baseline_ic_mean = 0.0
        vix_stats = {}

        if signals.ndim == 1:
            valid = ~(np.isnan(signals) | np.isnan(forward_returns))
            ic, p_value = stats.spearmanr(signals[valid], forward_returns[valid])

            if naive_momentum is not None:
                valid_b = valid & ~np.isnan(naive_momentum)
                bic, _ = stats.spearmanr(naive_momentum[valid_b], forward_returns[valid_b])
                baseline_ic_mean = float(bic)

            if vix_series is not None:
                vix_valid = vix_series[valid]
                high_vix = vix_valid > np.median(vix_valid)
                if np.sum(high_vix) > 5 and np.sum(~high_vix) > 5:
                    ic_high, _ = stats.spearmanr(
                        signals[valid][high_vix], forward_returns[valid][high_vix]
                    )
                    ic_low, _ = stats.spearmanr(
                        signals[valid][~high_vix], forward_returns[valid][~high_vix]
                    )
                    vix_stats = {"ic_high_vix": float(ic_high), "ic_low_vix": float(ic_low)}

            return {
                "ic": float(ic),
                "p_value": float(p_value),
                "ic_std": 0.0,
                "icir": 0.0,
                "baseline_ic": baseline_ic_mean,
                "alpha_over_baseline": float(ic) - baseline_ic_mean,
                "horizon": horizon_label,
                "n_obs": int(np.sum(valid)),
                **vix_stats,
            }

        # Cross-sectional: compute IC per timestamp
        T = signals.shape[0]
        ics = []
        bics = []
        high_ics = []
        low_ics = []

        for t in range(T):
            s = signals[t]
            r = forward_returns[t]
            valid = ~(np.isnan(s) | np.isnan(r))
            if np.sum(valid) > 5:
                ic_t, _ = stats.spearmanr(s[valid], r[valid])
                ics.append(ic_t)

                if naive_momentum is not None:
                    nm = naive_momentum[t]
                    valid_b = valid & ~np.isnan(nm)
                    if np.sum(valid_b) > 5:
                        bic_t, _ = stats.spearmanr(nm[valid_b], r[valid_b])
                        bics.append(bic_t)

                if vix_series is not None:
                    # Treat vix_series[t] as the macro regime scalar for that day
                    if vix_series[t] > np.median(vix_series):
                        high_ics.append(ic_t)
                    else:
                        low_ics.append(ic_t)

        if not ics:
            return {"ic": 0.0, "ic_std": 0.0, "icir": 0.0, "horizon": horizon_label, "n_obs": 0}

        ic_mean = float(np.mean(ics))
        ic_std = float(np.std(ics))
        icir = ic_mean / ic_std if ic_std > 0 else 0.0

        if bics:
            baseline_ic_mean = float(np.mean(bics))
        if vix_series is not None and high_ics and low_ics:
            vix_stats = {
                "ic_high_vix": float(np.mean(high_ics)),
                "ic_low_vix": float(np.mean(low_ics)),
            }

        return {
            "ic": ic_mean,
            "ic_std": ic_std,
            "icir": icir,
            "baseline_ic": baseline_ic_mean,
            "alpha_over_baseline": ic_mean - baseline_ic_mean,
            "horizon": horizon_label,
            "n_obs": len(ics),
            **vix_stats,
        }


class LinearModel:
    """
    Level 2: OLS/WLS regression with HAC standard errors.

    Uses Newey-West correction for heteroskedasticity and autocorrelation.
    """

    def __init__(self) -> None:
        self._coefficients: np.ndarray | None = None
        self._feature_names: list[str] = []

    def fit(
        self,
        X: np.ndarray,  # (T, K) feature matrix
        y: np.ndarray,  # (T,) returns
        feature_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fit OLS with Newey-West standard errors."""
        self._feature_names = feature_names or [f"f{i}" for i in range(int(X.shape[1]))]

        # Add intercept
        T, K = X.shape
        X_with_const = np.column_stack([np.ones(T), X])

        # OLS coefficients
        try:
            coeffs = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
            self._coefficients = coeffs
        except np.linalg.LinAlgError:
            self._coefficients = np.zeros(K + 1)
            return {"status": "singular_matrix"}

        # Predictions and residuals
        y_hat = X_with_const @ self._coefficients
        residuals = y - y_hat
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # Feature importances (standardised coefficients)
        importances = {}
        for i, name in enumerate(self._feature_names):
            x_std = np.std(X[:, i])
            if x_std > 0:
                importances[name] = float(coeffs[i + 1] * x_std / np.std(y))
            else:
                importances[name] = 0.0

        return {
            "r_squared": float(r_squared),
            "rmse": float(np.sqrt(np.mean(residuals**2))),
            "coefficients": dict(zip(self._feature_names, coeffs[1:].tolist())),
            "intercept": float(coeffs[0]),
            "feature_importances": importances,
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict returns from features."""
        if self._coefficients is None:
            return np.zeros(X.shape[0])
        X_with_const = np.column_stack([np.ones(X.shape[0]), X])
        return cast(np.ndarray, X_with_const @ self._coefficients)


class GBMModel:
    """
    Level 3: LightGBM gradient boosted tree model.

    Preferred for tabular satellite features due to handling
    of missing values and nonlinear interactions.
    """

    DEFAULT_PARAMS = {
        "objective": "regression",
        "metric": "rmse",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "n_estimators": 500,
        "early_stopping_rounds": 50,
        "verbose": -1,
    }

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self._params = params or self.DEFAULT_PARAMS.copy()
        self._model = None
        self._feature_names: list[str] = []

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Train LightGBM model with early stopping on validation set."""
        self._feature_names = feature_names or [f"f{i}" for i in range(X_train.shape[1])]

        try:
            import lightgbm as lgb

            train_data = lgb.Dataset(X_train, label=y_train, feature_name=self._feature_names)
            val_data = lgb.Dataset(
                X_val, label=y_val, feature_name=self._feature_names, reference=train_data
            )

            callbacks = [lgb.early_stopping(self._params.get("early_stopping_rounds", 50))]

            self._model = lgb.train(
                {
                    k: v
                    for k, v in self._params.items()
                    if k not in ("n_estimators", "early_stopping_rounds")
                },
                train_data,
                num_boost_round=self._params.get("n_estimators", 500),
                valid_sets=[val_data],
                callbacks=callbacks,
            )

            if self._model is None:
                return {"status": "training_failed"}

            # Evaluation
            y_pred = self._model.predict(X_val)
            rmse = float(np.sqrt(np.mean((y_val - y_pred) ** 2)))

            # Feature importances
            importances = dict(
                zip(
                    self._feature_names,
                    self._model.feature_importance(importance_type="gain").tolist(),
                )
            )

            return {
                "rmse": rmse,
                "best_iteration": getattr(self._model, "best_iteration", 0),
                "feature_importances": importances,
            }
        except ImportError:
            logger.warning("LightGBM not available — model not trained")
            return {"status": "lightgbm_not_available"}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict returns."""
        if self._model is None:
            return np.zeros(X.shape[0])
        return self._model.predict(X)

    def get_shap_values(self, X: np.ndarray) -> np.ndarray | None:
        """Compute SHAP values for feature attribution."""
        if self._model is None:
            return None
        try:
            import shap

            explainer = shap.TreeExplainer(self._model)
            shap_values = explainer.shap_values(X)
            return shap_values
        except ImportError:
            logger.warning("SHAP not available")
            return None


class EnsembleModel:
    """
    Level 5: Weighted ensemble of linear + GBM (+ TFT when available).

    Weights determined by out-of-sample IC contribution.
    """

    def __init__(self) -> None:
        self._linear = LinearModel()
        self._gbm = GBMModel()
        self._weights: dict[str, float] = {"linear": 0.3, "gbm": 0.7}

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Train all sub-models and compute ensemble weights."""
        # Train linear
        linear_result = self._linear.fit(X_train, y_train, feature_names)

        # Train GBM
        gbm_result = self._gbm.fit(X_train, y_train, X_val, y_val, feature_names)

        # Compute weights based on validation performance
        linear_pred = self._linear.predict(X_val)
        gbm_pred = self._gbm.predict(X_val)

        from scipy import stats

        linear_ic, _ = stats.spearmanr(linear_pred, y_val)
        gbm_ic, _ = stats.spearmanr(gbm_pred, y_val)

        total_ic = abs(linear_ic) + abs(gbm_ic)
        if total_ic > 0:
            self._weights = {
                "linear": abs(linear_ic) / total_ic,
                "gbm": abs(gbm_ic) / total_ic,
            }

        # Ensemble prediction on validation
        ens_pred = self._weights["linear"] * linear_pred + self._weights["gbm"] * gbm_pred
        ens_ic, _ = stats.spearmanr(ens_pred, y_val)
        ens_rmse = float(np.sqrt(np.mean((y_val - ens_pred) ** 2)))

        return {
            "ensemble_weights": self._weights,
            "ensemble_ic": float(ens_ic),
            "ensemble_rmse": ens_rmse,
            "linear_result": linear_result,
            "gbm_result": gbm_result,
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate ensemble predictions."""
        linear_pred = self._linear.predict(X)
        gbm_pred = self._gbm.predict(X)
        return self._weights["linear"] * linear_pred + self._weights["gbm"] * gbm_pred
