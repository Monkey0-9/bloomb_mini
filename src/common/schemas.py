import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

class IngestStatus(str, Enum):
    # Expanded combined statuses based on specs
    RECEIVED = "RECEIVED"
    ACCEPTED = "ACCEPTED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    QUARANTINE = "QUARANTINE"

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
class BoundingBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

@dataclass
class TileMetadata:
    tile_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = ""
    acquisition_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_level: ProcessingLevel = ProcessingLevel.L2A
    sensor_type: SensorType = SensorType.OPTICAL
    resolution_m: float = 10.0
    cloud_cover_pct: float | None = None
    bbox_wgs84: list[float] = field(default_factory=list)
    license_id: str = "copernicus_open"
    commercial_use_ok: bool = True
    checksum_sha256: str = ""
    preprocessing_ver: str = "0.0.0"
    ingest_timestamp_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
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
    event_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_tile_id: str = ""
    model_version: str = "1.0.0"

@dataclass
class IngestEvent:
    tile_id: str = ""
    source: str = ""
    sensor_type: str = ""
    bbox: list[float] = field(default_factory=list)
    acquisition_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: IngestStatus = IngestStatus.RECEIVED
    reason_if_not_accepted: str | None = None
    ingest_timestamp_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class SignalRecord:
    signal_id: str = field(default_factory=lambda: str(uuid4()))
    signal_name: str = ""
    entity_id: str = ""
    score: float = 0.5
    direction: Literal["BULLISH", "BEARISH", "NEUTRAL"] = "NEUTRAL"
    ic: float = 0.0
    icir: float = 0.0
    status: Literal["BULLISH", "BEARISH", "NEUTRAL"] = "NEUTRAL"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 0.0

@dataclass
class PortfolioPosition:
    position_id: str = field(default_factory=lambda: str(uuid4()))
    ticker: str = ""
    quantity: float = 0.0
    entry_price: float = 0.0
    notional_usd: float = 0.0

@dataclass
class FeatureVector:
    entity_id: str
    timestamp: datetime
    features: dict[str, float]
