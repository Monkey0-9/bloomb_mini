"""
Object Detection — Phase 4.1

Architecture: YOLOv8-L (fast inference) or Detectron2 Mask R-CNN
Backbone: pre-trained on xView / DOTA — fine-tune, never train from scratch
Augmentation: flips, rotations (0/90/180/270), colour jitter, Gaussian noise, MixUp
Evaluation: mAP@0.5, mAP@0.5:0.95, per-class PR curve, confusion matrix
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single object detection result."""
    class_name: str
    class_id: int
    confidence: float
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    mask: Optional[np.ndarray] = None  # Instance segmentation mask


@dataclass
class DetectionResult:
    """Detection results for a single chip."""
    chip_id: str
    tile_id: str
    detections: list[Detection] = field(default_factory=list)
    model_version: str = ""
    inference_time_ms: float = 0.0

    def count_by_class(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for d in self.detections:
            counts[d.class_name] = counts.get(d.class_name, 0) + 1
        return counts


@dataclass
class DetectorMetrics:
    """Model evaluation metrics (on blind validation set ONLY)."""
    map_50: float = 0.0           # mAP @ IoU=0.50
    map_50_95: float = 0.0       # mAP @ IoU=0.50:0.95
    per_class_ap: dict[str, float] = field(default_factory=dict)
    confusion_matrix: Optional[np.ndarray] = None
    inference_fps: float = 0.0
    model_version: str = ""


@dataclass
class AugmentationConfig:
    """Satellite-specific augmentation configuration."""
    horizontal_flip: bool = True
    vertical_flip: bool = True
    rotations: list[int] = field(default_factory=lambda: [0, 90, 180, 270])  # Nadir only
    color_jitter: float = 0.2
    gaussian_noise_std: float = 0.01
    mixup_alpha: float = 0.3
    mosaic: bool = True
    scale_range: tuple[float, float] = (0.5, 1.5)


class SatelliteObjectDetector:
    """
    YOLOv8-based object detector for satellite imagery.
    
    Spec requirements:
    - Pre-trained on xView/DOTA, fine-tuned on our annotations
    - Must beat naive pixel-count baseline before deployment
    - SHAP/attribution not applicable to detector; use per-class AP
    """

    DEFAULT_CONFIDENCE_THRESHOLD = 0.25
    DEFAULT_NMS_IOU_THRESHOLD = 0.45

    def __init__(
        self,
        model_path: Optional[Path] = None,
        model_variant: str = "yolov8l",
        device: str = "cuda",
    ) -> None:
        self._model_path = model_path
        self._model_variant = model_variant
        self._device = device
        self._model = None
        self._model_version = "0.0.0"

    def load_model(self, weights_path: Optional[Path] = None) -> None:
        """Load YOLOv8 model with pretrained or fine-tuned weights."""
        try:
            from ultralytics import YOLO

            if weights_path and weights_path.exists():
                self._model = YOLO(str(weights_path))
                logger.info(f"Loaded fine-tuned model from {weights_path}")
            else:
                # Load pretrained YOLOv8-L
                self._model = YOLO(f"{self._model_variant}.pt")
                logger.info(f"Loaded pretrained {self._model_variant}")
        except ImportError:
            logger.warning("ultralytics not available — using mock detector")
            self._model = None

    def train(
        self,
        train_data_yaml: Path,
        epochs: int = 100,
        batch_size: int = 16,
        imgsz: int = 256,
        augmentation: Optional[AugmentationConfig] = None,
        project: str = "runs/detect",
        name: str = "sattrade_train",
    ) -> dict[str, Any]:
        """
        Fine-tune detector on satellite annotation dataset.
        
        Never trains from scratch on < 50k samples — always uses
        pretrained backbone.
        """
        aug = augmentation or AugmentationConfig()

        if self._model is None:
            self.load_model()

        if self._model is None:
            logger.error("No model loaded — cannot train")
            return {"status": "error", "reason": "model_not_loaded"}

        results = self._model.train(
            data=str(train_data_yaml),
            epochs=epochs,
            batch=batch_size,
            imgsz=imgsz,
            device=self._device,
            project=project,
            name=name,
            # Satellite-specific augmentations
            flipud=0.5 if aug.vertical_flip else 0.0,
            fliplr=0.5 if aug.horizontal_flip else 0.0,
            degrees=0.0,  # Use discrete rotations only
            hsv_h=aug.color_jitter * 0.05,
            hsv_s=aug.color_jitter * 0.35,
            hsv_v=aug.color_jitter * 0.20,
            mixup=aug.mixup_alpha,
            mosaic=1.0 if aug.mosaic else 0.0,
            scale=aug.scale_range[1] - 1.0,
            # Pretrained backbone
            pretrained=True,
        )

        return {
            "status": "complete",
            "project": project,
            "name": name,
            "epochs": epochs,
        }

    def predict(
        self,
        chip: np.ndarray,
        chip_id: str,
        tile_id: str,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        nms_iou_threshold: float = DEFAULT_NMS_IOU_THRESHOLD,
    ) -> DetectionResult:
        """Run inference on a single 256×256 chip."""
        import time
        start = time.time()

        if self._model is None:
            return DetectionResult(
                chip_id=chip_id, tile_id=tile_id,
                model_version=self._model_version,
            )

        results = self._model.predict(
            chip,
            conf=confidence_threshold,
            iou=nms_iou_threshold,
            device=self._device,
            verbose=False,
        )

        detections = []
        for r in results:
            boxes = r.boxes
            for i in range(len(boxes)):
                det = Detection(
                    class_name=r.names[int(boxes.cls[i])],
                    class_id=int(boxes.cls[i]),
                    confidence=float(boxes.conf[i]),
                    bbox=tuple(float(x) for x in boxes.xyxy[i]),
                )
                detections.append(det)

        elapsed_ms = (time.time() - start) * 1000
        return DetectionResult(
            chip_id=chip_id,
            tile_id=tile_id,
            detections=detections,
            model_version=self._model_version,
            inference_time_ms=elapsed_ms,
        )

    def predict_batch(
        self,
        chips: list[np.ndarray],
        chip_ids: list[str],
        tile_id: str,
    ) -> list[DetectionResult]:
        """Batch inference on multiple chips."""
        return [
            self.predict(chip, chip_id, tile_id)
            for chip, chip_id in zip(chips, chip_ids)
        ]

    def evaluate(
        self,
        val_data_yaml: Path,
    ) -> DetectorMetrics:
        """
        Evaluate on the held-out blind validation set ONLY.
        
        Computes mAP@0.5, mAP@0.5:0.95, per-class AP, confusion matrix.
        """
        if self._model is None:
            return DetectorMetrics()

        results = self._model.val(data=str(val_data_yaml), device=self._device)

        metrics = DetectorMetrics(
            map_50=float(results.box.map50),
            map_50_95=float(results.box.map),
            model_version=self._model_version,
        )

        # Per-class AP
        for i, name in enumerate(results.names.values()):
            metrics.per_class_ap[name] = float(results.box.ap50[i])

        return metrics


class PixelCountBaseline:
    """
    Naive pixel-count classifier baseline.
    
    Per spec: detector must beat this baseline before deployment.
    Counts pixels matching spectral signatures for each class.
    """

    def __init__(self, thresholds: Optional[dict[str, tuple[float, float]]] = None) -> None:
        self._thresholds = thresholds or {}

    def count(self, chip: np.ndarray, class_name: str) -> int:
        """Count pixels matching a class signature."""
        if class_name not in self._thresholds:
            return 0

        low, high = self._thresholds[class_name]
        if chip.ndim == 3:
            gray = np.mean(chip, axis=2)
        else:
            gray = chip

        mask = (gray >= low) & (gray <= high)
        return int(np.sum(mask))
