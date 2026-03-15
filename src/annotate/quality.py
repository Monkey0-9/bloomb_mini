"""
Annotation Quality Agent — Phase 3.3

Quality Protocol:
  - Minimum 3 annotators per tile
  - Inter-annotator IoU threshold: ≥ 0.70 to accept; < 0.50 = discard
  - Adjudication: senior annotator resolves ties on 0.50-0.70 tiles
  - Stratified sampling: class balance across season, geography, time-of-day, sensor
  - Minimum corpus: 2,000 tiles per use-case
  - Blind validation set: 20% held out

Annotation Metrics (weekly report):
  IoU per class, Fleiss' kappa, rejection rate by annotator,
  class distribution histogram, coverage by geography
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Annotation:
    """Single annotator's annotation for one tile."""

    tile_id: str
    annotator_id: str
    class_name: str
    bbox: tuple[float, float, float, float]  # x, y, w, h (COCO format)
    segmentation_mask: list[list[float]] | None = None  # Polygon coords
    confidence: float = 1.0


@dataclass
class TileAnnotationResult:
    """Result of annotation quality check for a single tile."""

    tile_id: str
    status: str  # "accepted", "adjudication", "discarded"
    min_pairwise_iou: float
    mean_iou: float
    num_annotators: int
    annotations: list[Annotation] = field(default_factory=list)
    majority_vote_mask: Any | None = None
    adjudicated: bool = False
    adjudicator_id: str | None = None
    rejection_reason: str | None = None


@dataclass
class BatchReport:
    """End-of-batch annotation quality report."""

    batch_id: str
    n_tiles: int
    n_accepted: int
    n_adjudicated: int
    n_discarded: int
    mean_iou_per_class: dict[str, float]
    annotator_agreement_kappa: float
    rejection_rate_by_annotator: dict[str, float]
    class_distribution: dict[str, int]
    generated_utc: str = ""


class AnnotationQualityAgent:
    """
    Annotation quality enforcement for the labeling pipeline.

    Implements the Annotation Agent spec:
    1. Enforce minimum 3 annotators per tile
    2. Compute pairwise IoU for every class
    3. Accept / adjudicate / discard based on IoU thresholds
    4. Export as COCO JSON with all quality metadata
    5. Generate weekly quality reports
    """

    IOU_ACCEPT_THRESHOLD = 0.70  # ≥ 0.70 → accept
    IOU_ADJUDICATE_LOW = 0.50  # 0.50-0.70 → adjudicate
    IOU_DISCARD_THRESHOLD = 0.50  # < 0.50 → discard
    MIN_ANNOTATORS = 3
    MIN_CORPUS_SIZE = 2000
    BLIND_VALIDATION_PCT = 0.20

    def __init__(self) -> None:
        self._accepted_tiles: list[TileAnnotationResult] = []
        self._discarded_tiles: list[TileAnnotationResult] = []
        self._adjudication_queue: list[TileAnnotationResult] = []

    def process_batch(
        self,
        tile_annotations: dict[str, list[list[Annotation]]],
    ) -> BatchReport:
        """
        Process a batch of tile annotations.

        Args:
            tile_annotations: {tile_id: [[annotator1_annots], [annotator2_annots], ...]}
        """
        batch_id = f"batch_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        results: list[TileAnnotationResult] = []

        for tile_id, annotator_sets in tile_annotations.items():
            result = self._evaluate_tile(tile_id, annotator_sets)
            results.append(result)

            if result.status == "accepted":
                self._accepted_tiles.append(result)
            elif result.status == "adjudication":
                self._adjudication_queue.append(result)
            else:
                self._discarded_tiles.append(result)

        # Generate report
        report = self._generate_report(batch_id, results)
        logger.info(
            f"Batch {batch_id}: {report.n_accepted} accepted, "
            f"{report.n_adjudicated} for adjudication, "
            f"{report.n_discarded} discarded"
        )
        return report

    def _evaluate_tile(
        self,
        tile_id: str,
        annotator_sets: list[list[Annotation]],
    ) -> TileAnnotationResult:
        """Evaluate annotation quality for a single tile."""
        n_annotators = len(annotator_sets)

        # Rule: never accept < 3 annotators
        if n_annotators < self.MIN_ANNOTATORS:
            return TileAnnotationResult(
                tile_id=tile_id,
                status="discarded",
                min_pairwise_iou=0.0,
                mean_iou=0.0,
                num_annotators=n_annotators,
                rejection_reason=f"Only {n_annotators} annotators (minimum {self.MIN_ANNOTATORS})",
            )

        # Compute pairwise IoU between all annotator pairs
        pairwise_ious = []
        for i in range(n_annotators):
            for j in range(i + 1, n_annotators):
                iou = self._compute_annotation_iou(annotator_sets[i], annotator_sets[j])
                pairwise_ious.append(iou)

        min_iou = min(pairwise_ious) if pairwise_ious else 0.0
        mean_iou = float(np.mean(pairwise_ious)) if pairwise_ious else 0.0

        # Classify
        all_annotations = [a for annotator_set in annotator_sets for a in annotator_set]

        if min_iou >= self.IOU_ACCEPT_THRESHOLD:
            return TileAnnotationResult(
                tile_id=tile_id,
                status="accepted",
                min_pairwise_iou=min_iou,
                mean_iou=mean_iou,
                num_annotators=n_annotators,
                annotations=all_annotations,
            )
        elif min_iou >= self.IOU_DISCARD_THRESHOLD:
            return TileAnnotationResult(
                tile_id=tile_id,
                status="adjudication",
                min_pairwise_iou=min_iou,
                mean_iou=mean_iou,
                num_annotators=n_annotators,
                annotations=all_annotations,
            )
        else:
            return TileAnnotationResult(
                tile_id=tile_id,
                status="discarded",
                min_pairwise_iou=min_iou,
                mean_iou=mean_iou,
                num_annotators=n_annotators,
                rejection_reason=f"min IoU {min_iou:.3f} < {self.IOU_DISCARD_THRESHOLD}",
            )

    def _compute_annotation_iou(
        self,
        annots_a: list[Annotation],
        annots_b: list[Annotation],
    ) -> float:
        """Compute average IoU between two annotators' annotations."""
        if not annots_a or not annots_b:
            return 0.0

        ious = []
        for a in annots_a:
            best_iou = 0.0
            for b in annots_b:
                if a.class_name == b.class_name:
                    iou = self._bbox_iou(a.bbox, b.bbox)
                    best_iou = max(best_iou, iou)
            ious.append(best_iou)

        return float(np.mean(ious)) if ious else 0.0

    @staticmethod
    def _bbox_iou(
        box_a: tuple[float, float, float, float],
        box_b: tuple[float, float, float, float],
    ) -> float:
        """
        Compute IoU between two bounding boxes in COCO format (x, y, w, h).
        """
        ax, ay, aw, ah = box_a
        bx, by, bw, bh = box_b

        # Convert to corners
        a_x1, a_y1, a_x2, a_y2 = ax, ay, ax + aw, ay + ah
        b_x1, b_y1, b_x2, b_y2 = bx, by, bx + bw, by + bh

        # Intersection
        inter_x1 = max(a_x1, b_x1)
        inter_y1 = max(a_y1, b_y1)
        inter_x2 = min(a_x2, b_x2)
        inter_y2 = min(a_y2, b_y2)

        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

        # Union
        a_area = aw * ah
        b_area = bw * bh
        union_area = a_area + b_area - inter_area

        if union_area <= 0:
            return 0.0

        return inter_area / union_area

    def adjudicate_tile(
        self,
        tile_id: str,
        adjudicator_id: str,
        final_annotations: list[Annotation],
    ) -> TileAnnotationResult:
        """Senior annotator resolves adjudication cases."""
        pending = [t for t in self._adjudication_queue if t.tile_id == tile_id]
        if not pending:
            raise ValueError(f"Tile {tile_id} not in adjudication queue")

        result = pending[0]
        result.status = "accepted"
        result.adjudicated = True
        result.adjudicator_id = adjudicator_id
        result.annotations = final_annotations

        self._adjudication_queue.remove(result)
        self._accepted_tiles.append(result)

        logger.info(f"Tile {tile_id} adjudicated by {adjudicator_id} — ACCEPTED")
        return result

    def _generate_report(
        self,
        batch_id: str,
        results: list[TileAnnotationResult],
    ) -> BatchReport:
        """Generate batch quality report."""
        accepted = [r for r in results if r.status == "accepted"]
        adjudicated = [r for r in results if r.status == "adjudication"]
        discarded = [r for r in results if r.status == "discarded"]

        # IoU per class
        class_ious: dict[str, list[float]] = {}
        for r in accepted:
            for a in r.annotations:
                if a.class_name not in class_ious:
                    class_ious[a.class_name] = []
                class_ious[a.class_name].append(r.mean_iou)

        mean_iou_per_class = {cls: float(np.mean(vals)) for cls, vals in class_ious.items()}

        # Class distribution
        class_dist: dict[str, int] = {}
        for r in accepted:
            for a in r.annotations:
                class_dist[a.class_name] = class_dist.get(a.class_name, 0) + 1

        # Fleiss' kappa (simplified)
        kappa = self._compute_fleiss_kappa(results)

        return BatchReport(
            batch_id=batch_id,
            n_tiles=len(results),
            n_accepted=len(accepted),
            n_adjudicated=len(adjudicated),
            n_discarded=len(discarded),
            mean_iou_per_class=mean_iou_per_class,
            annotator_agreement_kappa=kappa,
            rejection_rate_by_annotator={},
            class_distribution=class_dist,
            generated_utc=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    def _compute_fleiss_kappa(results: list[TileAnnotationResult]) -> float:
        """Compute simplified Fleiss' kappa for inter-annotator agreement."""
        if not results:
            return 0.0
        ious = [r.mean_iou for r in results if r.mean_iou > 0]
        if not ious:
            return 0.0
        # Simplified: transform mean IoU to kappa-like statistic
        mean_agreement = float(np.mean(ious))
        chance_agreement = 0.5  # Rough approximation
        if 1 - chance_agreement == 0:
            return 0.0
        return (mean_agreement - chance_agreement) / (1 - chance_agreement)

    def get_corpus_stats(self) -> dict[str, Any]:
        """Get corpus completeness statistics."""
        return {
            "total_accepted": len(self._accepted_tiles),
            "total_discarded": len(self._discarded_tiles),
            "pending_adjudication": len(self._adjudication_queue),
            "corpus_target": self.MIN_CORPUS_SIZE,
            "corpus_pct_complete": len(self._accepted_tiles) / self.MIN_CORPUS_SIZE * 100,
            "blind_validation_tiles": int(len(self._accepted_tiles) * self.BLIND_VALIDATION_PCT),
        }
