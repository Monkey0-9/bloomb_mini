"""
Temporal Fusion Transformer — Phase 5.3

Level 4 model for multi-horizon forecasting when sufficient data exists.
TFT uses variable selection networks, multi-head attention, and gating
to model complex temporal relationships.

Only deployed if:
  - Training data > 2,000 samples (per entity)
  - Walk-forward OOS IC exceeds GBM by > 0.01
  - Attention heatmap is interpretable (manual review)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TFTConfig:
    """Temporal Fusion Transformer configuration."""

    # Architecture
    hidden_size: int = 64
    num_attention_heads: int = 4
    num_encoder_layers: int = 2
    num_decoder_layers: int = 2
    dropout: float = 0.1

    # Training
    learning_rate: float = 1e-3
    batch_size: int = 64
    epochs: int = 100
    early_stopping_patience: int = 10

    # Data
    input_sequence_length: int = 52  # 52 weeks lookback
    forecast_horizon: int = 4  # 4 weeks ahead
    known_categoricals: list[str] = field(
        default_factory=lambda: ["port_id", "day_of_week", "month"]
    )
    # "time_since_last_obs" explicitly models irregular satellite acquisition steps
    known_reals: list[str] = field(default_factory=lambda: ["time_since_last_obs"])
    target: str = "forward_return"

    # Minimum data requirements
    min_samples_per_entity: int = 2000


@dataclass
class TFTPrediction:
    """TFT model prediction output."""

    entity_id: str
    predictions: dict[int, float]  # horizon → predicted value
    prediction_intervals: dict[int, tuple[float, float]]  # horizon → (lower, upper)
    attention_weights: np.ndarray | None = None  # Interpretability
    variable_selection_weights: dict[str, float] | None = None
    model_version: str = ""


class TemporalFusionTransformerModel:
    """
    TFT model wrapper for multi-horizon signal forecasting.

    In production: uses PyTorch Forecasting's TemporalFusionTransformer.
    For development: implements core TFT architecture.
    """

    def __init__(self, config: TFTConfig | None = None) -> None:
        self._config = config or TFTConfig()
        self._model = None
        self._model_version = "0.1.0"

    def check_data_sufficiency(self, n_samples: int) -> bool:
        """Check if enough data exists to train TFT (min 2k samples)."""
        if n_samples < self._config.min_samples_per_entity:
            logger.warning(
                f"Insufficient data for TFT: {n_samples} samples "
                f"< {self._config.min_samples_per_entity} minimum"
            )
            return False
        return True

    def build_model(self) -> None:
        """Build TFT model architecture."""
        try:
            import torch
            import torch.nn as nn

            class GatedResidualNetwork(nn.Module):
                """Variable selection / gating mechanism."""

                def __init__(
                    self, input_size: int, hidden_size: int, output_size: int, dropout: float = 0.1
                ):
                    super().__init__()
                    self.fc1 = nn.Linear(input_size, hidden_size)
                    self.elu = nn.ELU()
                    self.fc2 = nn.Linear(hidden_size, output_size)
                    self.gate = nn.Linear(hidden_size, output_size)
                    self.sigmoid = nn.Sigmoid()
                    self.dropout = nn.Dropout(dropout)
                    self.layer_norm = nn.LayerNorm(output_size)
                    self.skip = (
                        nn.Linear(input_size, output_size)
                        if input_size != output_size
                        else nn.Identity()
                    )

                def forward(self, x: torch.Tensor) -> torch.Tensor:
                    h = self.elu(self.fc1(x))
                    h = self.dropout(h)
                    output = self.fc2(h)
                    gate = self.sigmoid(self.gate(h))
                    gated = gate * output
                    skip = self.skip(x)
                    return self.layer_norm(gated + skip)

            class VariableSelectionNetwork(nn.Module):
                """Learn to select important features."""

                def __init__(self, n_features: int, hidden_size: int, dropout: float = 0.1):
                    super().__init__()
                    self.grns = nn.ModuleList(
                        [
                            GatedResidualNetwork(1, hidden_size, hidden_size, dropout)
                            for _ in range(n_features)
                        ]
                    )
                    self.softmax_grn = GatedResidualNetwork(
                        n_features * hidden_size, hidden_size, n_features, dropout
                    )
                    self.softmax = nn.Softmax(dim=-1)

                def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
                    # x: (batch, time, features)
                    processed = []
                    for i, grn in enumerate(self.grns):
                        processed.append(grn(x[:, :, i : i + 1]))
                    processed = torch.stack(processed, dim=-1)  # (batch, time, hidden, n_features)

                    # Variable selection weights
                    flat = processed.reshape(x.shape[0], x.shape[1], -1)
                    weights = self.softmax(self.softmax_grn(flat))

                    # Weighted sum
                    selected = (processed * weights.unsqueeze(2)).sum(dim=-1)
                    return selected, weights

            class TFTModel(nn.Module):
                """Core TFT architecture."""

                def __init__(self, config: TFTConfig, n_features: int):
                    super().__init__()
                    self.config = config
                    self.vsn = VariableSelectionNetwork(
                        n_features, config.hidden_size, config.dropout
                    )
                    self.encoder = nn.LSTM(
                        config.hidden_size,
                        config.hidden_size,
                        num_layers=config.num_encoder_layers,
                        batch_first=True,
                        dropout=config.dropout,
                    )
                    self.attention = nn.MultiheadAttention(
                        config.hidden_size,
                        config.num_attention_heads,
                        dropout=config.dropout,
                        batch_first=True,
                    )
                    self.output_grn = GatedResidualNetwork(
                        config.hidden_size,
                        config.hidden_size,
                        1,
                        config.dropout,
                    )
                    # Quantile outputs for prediction intervals
                    self.quantile_heads = nn.ModuleList(
                        [nn.Linear(1, 1) for _ in [0.10, 0.50, 0.90]]
                    )

                def forward(
                    self, x: torch.Tensor
                ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
                    selected, var_weights = self.vsn(x)
                    encoded, _ = self.encoder(selected)
                    attended, attention_weights = self.attention(encoded, encoded, encoded)
                    output = self.output_grn(attended[:, -1:, :])

                    quantiles = torch.cat([qh(output) for qh in self.quantile_heads], dim=-1)

                    return quantiles, attention_weights, var_weights

            n_features = len(self._config.known_reals) + len(self._config.known_categoricals)
            n_features = max(n_features, 10)
            self._model = TFTModel(self._config, n_features)
            logger.info(
                f"Built TFT model: {sum(p.numel() for p in self._model.parameters())} parameters"
            )

        except ImportError:
            logger.warning("PyTorch not available — TFT model not built")

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> dict[str, Any]:
        """Train TFT model with quantile loss."""
        if not self.check_data_sufficiency(len(X_train)):
            return {"status": "insufficient_data"}

        if self._model is None:
            self.build_model()
            if self._model is None:
                return {"status": "model_build_failed"}

        try:
            import torch
            import torch.optim as optim

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = self._model.to(device)

            optimizer = optim.Adam(self._model.parameters(), lr=self._config.learning_rate)
            best_val_loss = float("inf")
            patience_counter = 0

            for epoch in range(self._config.epochs):
                self._model.train()

                # Mini-batch training
                indices = np.random.permutation(len(X_train))
                epoch_loss = 0.0
                n_batches = 0

                for i in range(0, len(indices), self._config.batch_size):
                    batch_idx = indices[i : i + self._config.batch_size]
                    x_batch = torch.from_numpy(X_train[batch_idx]).float().to(device)
                    y_batch = torch.from_numpy(y_train[batch_idx]).float().to(device)

                    if x_batch.dim() == 2:
                        x_batch = x_batch.unsqueeze(1)  # Add time dim

                    optimizer.zero_grad()
                    quantiles, _, _ = self._model(x_batch)
                    loss = self._quantile_loss(quantiles.squeeze(), y_batch)
                    loss.backward()
                    optimizer.step()

                    epoch_loss += loss.item()
                    n_batches += 1

                # Validation
                self._model.eval()
                with torch.no_grad():
                    x_val_t = torch.from_numpy(X_val).float().to(device)
                    y_val_t = torch.from_numpy(y_val).float().to(device)
                    if x_val_t.dim() == 2:
                        x_val_t = x_val_t.unsqueeze(1)
                    val_q, _, _ = self._model(x_val_t)
                    val_loss = self._quantile_loss(val_q.squeeze(), y_val_t).item()

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self._config.early_stopping_patience:
                        logger.info(f"Early stopping at epoch {epoch}")
                        break

            return {
                "status": "trained",
                "best_val_loss": best_val_loss,
                "epochs_trained": epoch + 1,
            }

        except Exception as e:
            logger.error(f"TFT training failed: {e}")
            return {"status": "training_failed", "error": str(e)}

    def predict(self, X: np.ndarray) -> list[TFTPrediction]:
        """Generate multi-horizon predictions with intervals."""
        if self._model is None:
            return []

        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model.eval()

        with torch.no_grad():
            x_t = torch.from_numpy(X).float().to(device)
            if x_t.dim() == 2:
                x_t = x_t.unsqueeze(1)
            quantiles, attention, var_weights = self._model(x_t)

        predictions = []
        for i in range(len(X)):
            q = quantiles[i].cpu().numpy().flatten()
            pred = TFTPrediction(
                entity_id=f"entity_{i}",
                predictions={1: float(q[1]) if len(q) > 1 else float(q[0])},
                prediction_intervals={
                    # Explicit 80% Confidence Interval using 10th and 90th percentiles
                    1: (float(q[0]), float(q[2]) if len(q) > 2 else float(q[0]))
                },
                attention_weights=attention[i].cpu().numpy() if attention is not None else None,
                model_version=self._model_version,
            )
            predictions.append(pred)

        return predictions

    @staticmethod
    def _quantile_loss(
        predictions: Any, targets: Any, quantiles: list[float] = [0.10, 0.50, 0.90]
    ) -> Any:
        """Compute combined quantile loss."""
        import torch

        losses = []
        for i, q in enumerate(quantiles):
            if predictions.dim() == 1:
                pred = predictions
            else:
                pred = predictions[:, i] if predictions.shape[-1] > i else predictions[:, -1]
            errors = targets - pred
            losses.append(torch.max((q - 1) * errors, q * errors).mean())
        return sum(losses) / len(losses)
