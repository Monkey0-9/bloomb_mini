import hashlib
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.common.schemas import TileMetadata
from src.ingest.quality_gates import (
    gate_checksum, gate_cloud_cover, gate_geolocation,
    gate_license, gate_schema, run_all_gates,
)


def make_tile(**kwargs) -> TileMetadata:
    defaults = dict(
        tile_id="test-tile-001",
        source="sentinel2",
        acquisition_utc=datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc),
        processing_level="L2A",
        sensor_type="OPTICAL",
        resolution_m=10.0,
        cloud_cover_pct=12.0,
        bbox_wgs84=[3.9, 51.85, 4.6, 52.05],
        license_id="copernicus_open",
        commercial_use_ok=True,
        checksum_sha256="abc123" * 10,
        preprocessing_ver="0.0.0",
        ingest_timestamp_utc=datetime.utcnow(),
        file_path="/tmp/test_tile.tif",
        location_key="rotterdam",
    )
    defaults.update(kwargs)
    return TileMetadata(**defaults)


def test_gate_cloud_rejects_high_cloud():
    result = gate_cloud_cover(make_tile(cloud_cover_pct=45.0))
    assert result.status == "REJECT"
    assert result.metric_value == 45.0


def test_gate_cloud_rejects_null_cloud():
    result = gate_cloud_cover(make_tile(cloud_cover_pct=None))
    assert result.status == "REJECT"
    assert "null" in result.reason.lower()


def test_gate_cloud_passes_low_cloud():
    result = gate_cloud_cover(make_tile(cloud_cover_pct=12.0))
    assert result.status == "PASS"


def test_gate_license_blocks_noncommercial():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = f"{tmpdir}/catalog.db"
        with sqlite3.connect(db) as conn:
            conn.execute(
                "CREATE TABLE compliance_log "
                "(id INTEGER PRIMARY KEY, tile_id TEXT, event TEXT, "
                "timestamp TEXT, reason TEXT)"
            )
            conn.commit()
        result = gate_license(make_tile(commercial_use_ok=False), db)
        assert result.status == "BLOCK"
        with sqlite3.connect(db) as conn:
            row = conn.execute(
                "SELECT * FROM compliance_log WHERE tile_id='test-tile-001'"
            ).fetchone()
        assert row is not None, "Compliance log must record blocked tiles"


def test_gate_checksum_quarantines_corrupted_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as f:
        f.write(b"original content")
        path = f.name
    correct_hash = hashlib.sha256(b"original content").hexdigest()
    wrong_hash = hashlib.sha256(b"different content").hexdigest()
    result = gate_checksum("test-tile-001", path, wrong_hash)
    assert result.status == "QUARANTINE"
    Path(path).unlink(missing_ok=True)


def test_gate_checksum_passes_valid_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as f:
        f.write(b"valid satellite data")
        path = f.name
    correct_hash = hashlib.sha256(b"valid satellite data").hexdigest()
    result = gate_checksum("test-tile-001", path, correct_hash)
    assert result.status == "PASS"
    Path(path).unlink(missing_ok=True)


def test_gate_schema_rejects_empty_tile_id():
    result = gate_schema(make_tile(tile_id=""))
    assert result.status == "REJECT"
    assert "tile_id" in result.reason


def test_gate_geolocation_rejects_invalid_coords():
    result = gate_geolocation(make_tile(bbox_wgs84=[-200.0, 51.85, 4.6, 52.05]))
    assert result.status == "REJECT"


def test_gate_geolocation_passes_valid_coords():
    result = gate_geolocation(make_tile(bbox_wgs84=[3.9, 51.85, 4.6, 52.05]))
    assert result.status == "PASS"
