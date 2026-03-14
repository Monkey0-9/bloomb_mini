"""
COCO JSON Export — Phase 3.1

Export accepted annotations in COCO JSON format with tile_id FK,
class_name, bbox, segmentation_mask, annotator_ids, iou_score.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.annotate.quality import TileAnnotationResult, Annotation
from src.annotate.taxonomy import Taxonomy

logger = logging.getLogger(__name__)


class COCOExporter:
    """Export annotation results in COCO JSON format."""

    def __init__(self, taxonomy: Taxonomy) -> None:
        self._taxonomy = taxonomy

    def export(
        self,
        results: list[TileAnnotationResult],
        output_path: Path,
        dataset_name: str = "sattrade_annotations",
    ) -> dict[str, Any]:
        """
        Export accepted tiles as COCO JSON.
        
        Format:
        {
            "info": {...},
            "licenses": [...],
            "categories": [...],
            "images": [...],
            "annotations": [...]
        }
        """
        accepted = [r for r in results if r.status == "accepted"]

        coco = {
            "info": {
                "description": dataset_name,
                "version": self._taxonomy.version,
                "year": datetime.now().year,
                "contributor": "SatTrade Annotation Pipeline",
                "date_created": datetime.now(timezone.utc).isoformat(),
                "use_case": self._taxonomy.use_case.value,
            },
            "licenses": [
                {
                    "id": 1,
                    "name": "Internal Research Only",
                    "url": "",
                }
            ],
            "categories": self._taxonomy.to_coco_categories(),
            "images": [],
            "annotations": [],
        }

        annotation_id = 1
        for img_idx, result in enumerate(accepted, start=1):
            # Image entry
            coco["images"].append({
                "id": img_idx,
                "file_name": f"{result.tile_id}.tif",
                "width": 256,   # Chip size from preprocessing
                "height": 256,
                "tile_id": result.tile_id,
                "mean_iou": result.mean_iou,
                "min_pairwise_iou": result.min_pairwise_iou,
                "num_annotators": result.num_annotators,
                "adjudicated": result.adjudicated,
                "adjudicator_id": result.adjudicator_id,
            })

            # Annotation entries
            for annot in result.annotations:
                class_def = self._taxonomy.get_class_by_name(annot.class_name)
                if class_def is None:
                    logger.warning(f"Unknown class '{annot.class_name}' — skipping")
                    continue

                coco_annot: dict[str, Any] = {
                    "id": annotation_id,
                    "image_id": img_idx,
                    "category_id": class_def.class_id,
                    "bbox": list(annot.bbox),  # [x, y, w, h]
                    "area": annot.bbox[2] * annot.bbox[3],
                    "iscrowd": 0,
                    "tile_id": result.tile_id,
                    "class_name": annot.class_name,
                    "annotator_id": annot.annotator_id,
                    "iou_score": result.mean_iou,
                    "adjudicated": result.adjudicated,
                }

                if annot.segmentation_mask:
                    coco_annot["segmentation"] = annot.segmentation_mask

                coco["annotations"].append(coco_annot)
                annotation_id += 1

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(coco, f, indent=2, default=str)

        logger.info(
            f"Exported {len(coco['images'])} images, "
            f"{len(coco['annotations'])} annotations to {output_path}"
        )
        return coco

    def split_train_val(
        self,
        coco_data: dict[str, Any],
        val_fraction: float = 0.20,
        seed: int = 42,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Split COCO dataset into train and blind validation sets.
        
        The blind validation set (20%) is NEVER shown to annotators
        after labeling begins. It is used only for model evaluation.
        """
        import random
        random.seed(seed)

        images = coco_data["images"]
        random.shuffle(images)

        split_idx = int(len(images) * (1 - val_fraction))
        train_images = images[:split_idx]
        val_images = images[split_idx:]

        train_img_ids = {img["id"] for img in train_images}
        val_img_ids = {img["id"] for img in val_images}

        train_annots = [a for a in coco_data["annotations"] if a["image_id"] in train_img_ids]
        val_annots = [a for a in coco_data["annotations"] if a["image_id"] in val_img_ids]

        base = {k: v for k, v in coco_data.items() if k not in ("images", "annotations")}

        train = {**base, "images": train_images, "annotations": train_annots}
        val = {**base, "images": val_images, "annotations": val_annots}

        logger.info(f"Split: {len(train_images)} train, {len(val_images)} val (blind)")
        return train, val
