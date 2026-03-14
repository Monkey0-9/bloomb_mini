"""
Data schemas for the SatTrade tile catalog.

Every tile entering the data lake MUST conform to TileMetadata.
These schemas are the single source of truth — never bypass them
to ingest data without validation.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class SensorType(str, Enum):
    OPTICAL = "optical"
    SAR = "sar"
    THERMAL = "thermal"
    AIS = "ais"
    RF = "rf"


class ProcessingLevel(str, Enum):
    RAW = "raw"
    L1C = "L1C"       # Top of atmosphere reflectance
    L2A = "L2A"       # Surface reflectance (atmospherically corrected)
    L1_GRD = "L1_GRD"  # SAR ground range detected
    L2_LST = "L2_LST"  # Land surface temperature


class IngestStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    DUPLICATE = "DUPLICATE"


class BoundingBox(BaseModel):
    """WGS84 bounding box (west, south, east, north)."""
    west: float = Field(..., ge=-180, le=180)
    south: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    north: float = Field(..., ge=-90, le=90)

    @model_validator(mode="after")
    def validate_bounds(self) -> "BoundingBox":
        if self.south >= self.north:
            raise ValueError(f"south ({self.south}) must be < north ({self.north})")
        return self


class TileMetadata(BaseModel):
    """
    Mandatory metadata for every tile in the data lake.
    
    Per spec: tile_id, source, acquisition_utc, cloud_cover_pct, sensor_type,
    resolution_m, bounding_box_wgs84, license_id, commercial_use_permitted,
    processing_level, checksum_sha256
    """
    tile_id: str = Field(..., min_length=1, description="Unique tile identifier")
    source: str = Field(..., min_length=1, description="Data provider (e.g., 'sentinel-2', 'planet')")
    acquisition_utc: datetime = Field(..., description="Image acquisition timestamp (UTC)")
    cloud_cover_pct: float = Field(..., ge=0, le=100, description="Cloud cover percentage")
    sensor_type: SensorType
    resolution_m: float = Field(..., gt=0, description="Spatial resolution in meters")
    bounding_box_wgs84: BoundingBox
    license_id: str = Field(..., min_length=1, description="FK to data licensing audit")
    commercial_use_permitted: bool
    processing_level: ProcessingLevel
    checksum_sha256: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash of raw file")

    # Optional enrichment fields
    preprocessing_version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    parent_tile_ids: list[str] = Field(default_factory=list, description="Source tiles for derived products")
    rejection_reason: Optional[str] = None
    ingest_timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("acquisition_utc")
    @classmethod
    def validate_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("acquisition_utc must be timezone-aware (UTC)")
        return v

    @field_validator("checksum_sha256")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("checksum_sha256 must be a valid hex string")
        return v.lower()


class IngestEvent(BaseModel):
    """Output schema for the data ingestor agent."""
    tile_id: str
    status: IngestStatus
    reason_if_not_accepted: Optional[str] = None
    ingest_timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QualityCheckResult(BaseModel):
    """Result of a single quality gate check."""
    check_name: str
    passed: bool
    value: Optional[float] = None
    threshold: Optional[float] = None
    message: str = ""


class SignalRecord(BaseModel):
    """
    Feature store record for a scored signal.
    
    Every record is point-in-time correct — feature_timestamp is the timestamp
    at which this feature WOULD HAVE BEEN AVAILABLE, not the event timestamp.
    """
    entity_id: str = Field(..., description="Facility or port identifier")
    feature_timestamp: datetime = Field(..., description="Point-in-time availability (NOT event time)")
    signal_name: str
    signal_value: float
    confidence: float = Field(..., ge=0, le=1)
    source_tile_ids: list[str] = Field(default_factory=list)
    model_version: str
    feature_hash: str = Field(..., description="Content-addressed hash of feature inputs")
    staleness_seconds: int = Field(0, ge=0, description="Time since last raw data update")
    causation_weight: float = Field(0.0, ge=0, le=1, description="Confidence in facility->ticker mapping")
    ticker_mapped: bool = False

    @field_validator("feature_timestamp")
    @classmethod
    def validate_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("feature_timestamp must be timezone-aware (UTC)")
        return v


class AuditLogEntry(BaseModel):
    """
    Immutable audit log entry for every signal, order, fill, and risk check.
    Written to append-only store (QLDB or equivalent).
    Retention: 7 years.
    """
    event_id: str
    event_type: str  # signal_generated, order_submitted, fill_received, risk_check, kill_switch
    timestamp_utc: datetime
    asset_id: str
    signal_value: Optional[float] = None
    signal_age_seconds: Optional[int] = None
    order_id: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    risk_check_results: list[QualityCheckResult] = Field(default_factory=list)
    model_version: str = ""
    feature_hash: str = ""
    feature_lineage_hashes: dict[str, str] = Field(default_factory=dict, description="Map of feature names to their respective hashes")
    operator_id: str = "system"
    regulatory_jurisdiction: str = Field("INTERNAL_RESEARCH", description="ISO 3166-1 alpha-2 or internal label")
    compliance_check_id: Optional[str] = Field(None, description="FK to regulatory review case")
    audit_approval_timestamp: Optional[datetime] = None


def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file (streaming, memory-efficient)."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
