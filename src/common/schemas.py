from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4

@dataclass
class TileMetadata:
    tile_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = ""
    acquisition_utc: datetime = field(default_factory=datetime.utcnow)
    processing_level: str = ""
    sensor_type: Literal["OPTICAL", "SAR", "THERMAL", "AIS"] = "OPTICAL"
    resolution_m: float = 10.0
    cloud_cover_pct: float | None = None
    bbox_wgs84: list[float] = field(default_factory=list)
    license_id: str = "copernicus_open"
    commercial_use_ok: bool = True
    checksum_sha256: str = ""
    preprocessing_ver: str = "0.0.0"
    ingest_timestamp_utc: datetime = field(default_factory=datetime.utcnow)
    file_path: str = ""
    location_key: str = ""

@dataclass
class QualityGateResult:
    gate_name: str
    status: Literal["PASS", "REJECT", "HOLD", "BLOCK", "QUARANTINE"]
    tile_id: str
    reason: str | None = None
    metric_value: float | None = None

@dataclass
class FeatureRecord:
    feature_id: str = field(default_factory=lambda: str(uuid4()))
    entity_id: str = ""
    feature_name: str = ""
    feature_value: float = 0.0
    event_timestamp: datetime = field(default_factory=datetime.utcnow)
    created_timestamp: datetime = field(default_factory=datetime.utcnow)
    source_tile_id: str = ""
    model_version: str = "1.0.0"
