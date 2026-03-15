import hashlib
import sqlite3
from pathlib import Path

from src.common.schemas import QualityGateResult, TileMetadata


def gate_cloud_cover(m: TileMetadata) -> QualityGateResult:
    if m.cloud_cover_pct is None:
        return QualityGateResult("cloud_cover", "REJECT", m.tile_id,
                                 "cloud_cover_pct is null — cannot assess quality")
    if m.cloud_cover_pct > 30.0:
        return QualityGateResult("cloud_cover", "REJECT", m.tile_id,
                                 f"Cloud {m.cloud_cover_pct:.1f}% > 30% threshold",
                                 m.cloud_cover_pct)
    return QualityGateResult("cloud_cover", "PASS", m.tile_id,
                             metric_value=m.cloud_cover_pct)


def gate_schema(m: TileMetadata) -> QualityGateResult:
    required = {
        "tile_id": m.tile_id, "source": m.source,
        "processing_level": m.processing_level, "sensor_type": m.sensor_type,
        "bbox_wgs84": m.bbox_wgs84, "license_id": m.license_id,
        "checksum_sha256": m.checksum_sha256, "file_path": m.file_path,
    }
    for field_name, value in required.items():
        if not value:
            return QualityGateResult("schema", "REJECT", m.tile_id,
                                     f"Required field '{field_name}' is empty or null")
    return QualityGateResult("schema", "PASS", m.tile_id)


def gate_checksum(tile_id: str, file_path: str,
                  stored_checksum: str) -> QualityGateResult:
    if not Path(file_path).exists():
        return QualityGateResult("checksum", "REJECT", tile_id,
                                 f"File not found: {file_path}")
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    computed = h.hexdigest()
    if computed != stored_checksum:
        return QualityGateResult("checksum", "QUARANTINE", tile_id,
                                 f"Checksum mismatch. Stored: {stored_checksum[:16]}"
                                 f"... Computed: {computed[:16]}...")
    return QualityGateResult("checksum", "PASS", tile_id)


def gate_license(m: TileMetadata, catalog_db: str = "data/catalog.db") -> QualityGateResult:
    if not m.commercial_use_ok:
        with sqlite3.connect(catalog_db) as conn:
            conn.execute(
                "INSERT INTO compliance_log (tile_id, event, timestamp, reason) "
                "VALUES (?, 'LICENSE_BLOCK', datetime('now'), ?)",
                (m.tile_id, f"license_id={m.license_id} has commercial_use_ok=False"),
            )
            conn.commit()
        return QualityGateResult("license", "BLOCK", m.tile_id,
                                 f"License {m.license_id}: commercial use not permitted")
    return QualityGateResult("license", "PASS", m.tile_id)


def gate_duplicate(m: TileMetadata, catalog_db: str = "data/catalog.db") -> QualityGateResult:
    try:
        with sqlite3.connect(catalog_db) as conn:
            row = conn.execute(
                """SELECT tile_id FROM tiles
                   WHERE tile_id != ?
                   AND ABS(JULIANDAY(acquisition_utc) -
                           JULIANDAY(?)) < 0.000694
                   LIMIT 1""",
                (m.tile_id, m.acquisition_utc.isoformat()),
            ).fetchone()
        if row:
            return QualityGateResult("duplicate", "REJECT", m.tile_id,
                                     f"Duplicate of existing tile {row[0]}")
    except sqlite3.OperationalError:
        pass
    return QualityGateResult("duplicate", "PASS", m.tile_id)


def gate_geolocation(m: TileMetadata) -> QualityGateResult:
    if len(m.bbox_wgs84) != 4:
        return QualityGateResult("geolocation", "REJECT", m.tile_id,
                                 "bbox_wgs84 must have exactly 4 values")
    min_lon, min_lat, max_lon, max_lat = m.bbox_wgs84
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        return QualityGateResult("geolocation", "REJECT", m.tile_id,
                                 f"Longitude out of range: {min_lon}, {max_lon}")
    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        return QualityGateResult("geolocation", "REJECT", m.tile_id,
                                 f"Latitude out of range: {min_lat}, {max_lat}")
    return QualityGateResult("geolocation", "PASS", m.tile_id)


def run_all_gates(m: TileMetadata, catalog_db: str = "data/catalog.db") -> QualityGateResult:
    for gate_fn in [
        lambda: gate_schema(m),
        lambda: gate_geolocation(m),
        lambda: gate_license(m, catalog_db),
        lambda: gate_cloud_cover(m),
        lambda: gate_duplicate(m, catalog_db),
        lambda: gate_checksum(m.tile_id, m.file_path, m.checksum_sha256),
    ]:
        result = gate_fn()
        if result.status != "PASS":
            return result
    return QualityGateResult("all_gates", "PASS", m.tile_id)
