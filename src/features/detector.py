from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

# Mocking ultralytics for setup if not installed
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


@dataclass
class DetectionResult:
    tile_id: str
    detection_timestamp: datetime
    model_version: str
    class_counts: dict[str, int]
    confidence_scores: dict[str, float]
    bounding_boxes: list[dict[str, Any]]
    processing_seconds: float


class Detector:
    def __init__(self, model_weights: str = "yolov8l.pt"):
        self.model_version = "1.0.0"
        if YOLO:
            self.model = YOLO(model_weights)
        else:
            self.model = None
            logger.warning(
                "ultralytics not installed. detector will run in simulation mode if forced."
            )

    def detect_objects(
        self,
        tile_path: str,
        tile_id: str,
        confidence_threshold: float = 0.40,
    ) -> DetectionResult:
        if not self.model:
            # For "Top 1% Global", we should raise or provide real counts if we have a small internal model
            # But here we'll assume we can run inference if the lib is there.
            raise ImportError("ultralytics/YOLO required for Step 4")

        start_time = datetime.now()
        results = self.model.predict(tile_path, conf=confidence_threshold)

        class_counts = {"vessel_at_berth": 0, "vessel_moving": 0, "crane_active": 0, "truck": 0}
        conf_sum = {"vessel_at_berth": 0.0, "vessel_moving": 0.0, "crane_active": 0.0, "truck": 0.0}
        bboxes = []

        # xView class mapping (simplification for this step)
        # 21: cargo ship, 23: container ship, 73: crane, 9: truck
        XVIEW_MAP = {21: "vessel", 23: "vessel", 73: "crane_active", 9: "truck"}

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                if cls_id in XVIEW_MAP:
                    mapped_cls = XVIEW_MAP[cls_id]

                    if mapped_cls == "vessel":
                        # Simplistic logic: if near edge or specific orientation, call it moving?
                        # Real requirement: "vessel_at_berth" if speed < 1 knot (requires AIS fusion later)
                        # For Step 4 solo, we'll label as at_berth by default or check area
                        mapped_cls = "vessel_at_berth"

                    class_counts[mapped_cls] += 1
                    conf_sum[mapped_cls] += conf
                    bboxes.append(
                        {"class": mapped_cls, "confidence": conf, "bbox": box.xyxy[0].tolist()}
                    )

        conf_avg = {
            k: (conf_sum[k] / class_counts[k] if class_counts[k] > 0 else 0.0) for k in class_counts
        }

        proc_time = (datetime.now() - start_time).total_seconds()

        return DetectionResult(
            tile_id=tile_id,
            detection_timestamp=datetime.now(UTC),
            model_version=self.model_version,
            class_counts=class_counts,
            confidence_scores=conf_avg,
            bounding_boxes=bboxes,
            processing_seconds=proc_time,
        )


def tile_to_feature_records(
    result: DetectionResult,
    entity_id: str,
    event_timestamp: datetime,
    processing_lag_seconds: int,
) -> list[Any]:  # List[FeatureRecord]
    import uuid

    from src.features.feature_store import FeatureRecord

    created_ts = event_timestamp + timedelta(seconds=processing_lag_seconds)
    records = []

    for cls_name, count in result.class_counts.items():
        records.append(
            FeatureRecord(
                feature_id=str(uuid.uuid4()),
                entity_id=entity_id,
                feature_name=f"{cls_name}_count",
                feature_value=float(count),
                event_timestamp=event_timestamp,
                created_timestamp=created_ts,
                source_tile_id=result.tile_id,
                model_version=result.model_version,
            )
        )
    return records
