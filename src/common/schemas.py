import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Literal
from uuid import uuid4


class IngestStatus(str, Enum):
    RECEIVED = "RECEIVED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class ProcessingLevel(str, Enum):
    L1C = "L1C"
    L2A = "L2A"
    L2_LST = "L2_LST"

class SensorType(str, Enum):
    OPTICAL = "OPTICAL"
    SAR = "SAR"
    THERMAL = "THERMAL"
    AIS = "AIS"

@dataclass
class TileMetadata:
    tile_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = ""
    acquisition_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    processing_level: ProcessingLevel = ProcessingLevel.L2A
    sensor_type: SensorType = SensorType.OPTICAL
    resolution_m: float = 10.0
    cloud_cover_pct: float | None = None
    bbox_wgs84: list[float] = field(default_factory=list)
    license_id: str = "copernicus_open"
    commercial_use_ok: bool = True
    checksum_sha256: str = ""
    preprocessing_ver: str = "0.0.0"
    ingest_timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
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
    event_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    source_tile_id: str = ""
    model_version: str = "1.0.0"

@dataclass
class BoundingBox:
    west: float
    south: float
    east: float
    north: float

@dataclass
class IngestEvent:
    tile_id: str = ""
    status: IngestStatus = IngestStatus.RECEIVED
    reason_if_not_accepted: str | None = None
    ingest_timestamp_utc: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SignalRecord:
    signal_id: str = field(default_factory=lambda: str(uuid4()))
    entity_id: str = ""
    score: float = 0.5
    status: Literal["BULLISH", "BEARISH", "NEUTRAL"] = "NEUTRAL"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: float = 0.0

@dataclass
class FeatureVector:
    entity_id: str
    timestamp: datetime
    features: dict[str, float]
