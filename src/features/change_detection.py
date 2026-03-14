"""
Change Detection — Phase 4.2

Method: Siamese U-Net or ChangeFormer on bi-temporal chip pairs.
Output: change mask + change magnitude raster.
Use-cases: construction starts, crop phenology, vessel presence delta.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ChangeDetectionResult:
    """Result of change detection between two temporal observations."""
    tile_id: str
    date_before: str
    date_after: str
    change_mask: Optional[np.ndarray] = None  # Binary mask (H×W)
    change_magnitude: Optional[np.ndarray] = None  # Magnitude raster (H×W)
    change_pct: float = 0.0  # % of pixels changed
    model_version: str = ""
    processing_time_ms: float = 0.0

    def get_change_summary(self) -> dict[str, Any]:
        return {
            "tile_id": self.tile_id,
            "period": f"{self.date_before} → {self.date_after}",
            "change_pct": self.change_pct,
            "model_version": self.model_version,
        }


class SiameseUNet:
    """
    Siamese U-Net for bi-temporal change detection.
    
    Architecture: two-stream encoder sharing weights, with difference
    features concatenated in the decoder. Produces binary change mask
    and continuous change magnitude.
    
    Pre-trained on satellite change detection benchmarks (LEVIR-CD, S2Looking).
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        device: str = "cuda",
        input_size: int = 256,
    ) -> None:
        self._model_path = model_path
        self._device = device
        self._input_size = input_size
        self._model = None
        self._model_version = "0.1.0"

    def load_model(self) -> None:
        """Load Siamese U-Net model."""
        try:
            import torch
            import torch.nn as nn

            if self._model_path and self._model_path.exists():
                self._model = torch.load(str(self._model_path), map_location=self._device)
                logger.info(f"Loaded change detection model from {self._model_path}")
            else:
                self._model = self._build_model()
                logger.info("Built Siamese U-Net from scratch (needs training)")
        except ImportError:
            logger.warning("PyTorch not available — using mock change detector")

    def _build_model(self) -> Any:
        """Build Siamese U-Net architecture."""
        import torch
        import torch.nn as nn

        class EncoderBlock(nn.Module):
            def __init__(self, in_c: int, out_c: int):
                super().__init__()
                self.conv = nn.Sequential(
                    nn.Conv2d(in_c, out_c, 3, padding=1),
                    nn.BatchNorm2d(out_c),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(out_c, out_c, 3, padding=1),
                    nn.BatchNorm2d(out_c),
                    nn.ReLU(inplace=True),
                )
                self.pool = nn.MaxPool2d(2)

            def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
                features = self.conv(x)
                pooled = self.pool(features)
                return features, pooled

        class DecoderBlock(nn.Module):
            def __init__(self, in_c: int, out_c: int):
                super().__init__()
                self.up = nn.ConvTranspose2d(in_c, out_c, 2, stride=2)
                self.conv = nn.Sequential(
                    nn.Conv2d(out_c * 3, out_c, 3, padding=1),  # skip + diff
                    nn.BatchNorm2d(out_c),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(out_c, out_c, 3, padding=1),
                    nn.BatchNorm2d(out_c),
                    nn.ReLU(inplace=True),
                )

            def forward(self, x: torch.Tensor, skip1: torch.Tensor, skip2: torch.Tensor) -> torch.Tensor:
                x = self.up(x)
                diff = torch.abs(skip1 - skip2)
                x = torch.cat([x, skip1, diff], dim=1)
                return self.conv(x)

        class SiameseUNetModel(nn.Module):
            def __init__(self, in_channels: int = 4):
                super().__init__()
                self.enc1 = EncoderBlock(in_channels, 64)
                self.enc2 = EncoderBlock(64, 128)
                self.enc3 = EncoderBlock(128, 256)
                self.enc4 = EncoderBlock(256, 512)
                self.bottleneck = nn.Sequential(
                    nn.Conv2d(512, 1024, 3, padding=1),
                    nn.BatchNorm2d(1024),
                    nn.ReLU(inplace=True),
                )
                self.dec4 = DecoderBlock(1024, 512)
                self.dec3 = DecoderBlock(512, 256)
                self.dec2 = DecoderBlock(256, 128)
                self.dec1 = DecoderBlock(128, 64)
                self.change_head = nn.Conv2d(64, 1, 1)  # Binary change mask
                self.magnitude_head = nn.Conv2d(64, 1, 1)  # Change magnitude

            def forward_encoder(self, x: torch.Tensor) -> tuple:
                f1, x = self.enc1(x)
                f2, x = self.enc2(x)
                f3, x = self.enc3(x)
                f4, x = self.enc4(x)
                b = self.bottleneck(x)
                return f1, f2, f3, f4, b

            def forward(self, img_before: torch.Tensor, img_after: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
                f1a, f2a, f3a, f4a, ba = self.forward_encoder(img_before)
                f1b, f2b, f3b, f4b, bb = self.forward_encoder(img_after)
                diff_b = torch.abs(ba - bb)
                x = self.dec4(diff_b, f4a, f4b)
                x = self.dec3(x, f3a, f3b)
                x = self.dec2(x, f2a, f2b)
                x = self.dec1(x, f1a, f1b)
                change_mask = torch.sigmoid(self.change_head(x))
                magnitude = torch.relu(self.magnitude_head(x))
                return change_mask, magnitude

        model = SiameseUNetModel()
        return model.to(self._device) if self._device != "cpu" else model

    def detect_change(
        self,
        chip_before: np.ndarray,
        chip_after: np.ndarray,
        tile_id: str,
        date_before: str,
        date_after: str,
        threshold: float = 0.5,
    ) -> ChangeDetectionResult:
        """
        Detect changes between two temporal chips.
        
        Returns binary change mask and continuous magnitude raster.
        """
        import time
        start = time.time()

        if self._model is None:
            # Fallback: simple difference-based change detection
            return self._simple_change_detection(
                chip_before, chip_after, tile_id, date_before, date_after, threshold
            )

        import torch

        # Prepare tensors
        t_before = torch.from_numpy(chip_before).float().unsqueeze(0)
        t_after = torch.from_numpy(chip_after).float().unsqueeze(0)

        if t_before.dim() == 3:
            t_before = t_before.unsqueeze(0)
            t_after = t_after.unsqueeze(0)

        # Channel-first format
        if t_before.shape[-1] in (3, 4):
            t_before = t_before.permute(0, 3, 1, 2)
            t_after = t_after.permute(0, 3, 1, 2)

        with torch.no_grad():
            change_prob, magnitude = self._model(t_before, t_after)

        change_mask = (change_prob.squeeze().cpu().numpy() > threshold).astype(np.uint8)
        magnitude_map = magnitude.squeeze().cpu().numpy()
        change_pct = float(np.mean(change_mask)) * 100

        elapsed_ms = (time.time() - start) * 1000

        return ChangeDetectionResult(
            tile_id=tile_id,
            date_before=date_before,
            date_after=date_after,
            change_mask=change_mask,
            change_magnitude=magnitude_map,
            change_pct=change_pct,
            model_version=self._model_version,
            processing_time_ms=elapsed_ms,
        )

    def _simple_change_detection(
        self,
        before: np.ndarray,
        after: np.ndarray,
        tile_id: str,
        date_before: str,
        date_after: str,
        threshold: float = 0.5,
    ) -> ChangeDetectionResult:
        """Simple difference-based fallback when model is unavailable."""
        if before.ndim == 3:
            diff = np.mean(np.abs(after.astype(float) - before.astype(float)), axis=2)
        else:
            diff = np.abs(after.astype(float) - before.astype(float))

        # Normalise to 0-1
        if diff.max() > 0:
            diff_norm = diff / diff.max()
        else:
            diff_norm = diff

        change_mask = (diff_norm > threshold).astype(np.uint8)
        change_pct = float(np.mean(change_mask)) * 100

        return ChangeDetectionResult(
            tile_id=tile_id,
            date_before=date_before,
            date_after=date_after,
            change_mask=change_mask,
            change_magnitude=diff_norm,
            change_pct=change_pct,
            model_version="simple_diff_v0",
        )
