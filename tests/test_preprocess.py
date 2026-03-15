import numpy as np
import pytest
import tempfile
from pathlib import Path


def test_dos_not_in_optical_source():
    """DOS (Dark Object Subtraction) is forbidden. If this test fails, remove DOS."""
    source = Path("src/preprocess/optical.py").read_text(encoding="utf-8")
    assert "dark_object" not in source.lower(), (
        "DOS method found in optical.py -- remove it. Use py6S only."
    )
    assert "def DOS" not in source, "DOS function found -- remove it."


def test_correction_output_range(monkeypatch):
    """Surface reflectance must be in [0.0, 1.0] for all pixels."""
    pytest.importorskip("rasterio")
    pytest.importorskip("Py6S")
    import rasterio
    from rasterio.transform import from_bounds
    from src.preprocess.optical import correct_atmospheric_6s
    import Py6S

    # Mock Py6S execution so it doesn't need the Fortran binary
    def mock_run(self):
        self.outputs = type('Outputs', (), {'coef_xa': 0.002, 'coef_xb': 0.01, 'coef_xc': 0.05})()
    monkeypatch.setattr(Py6S.SixS, "run", mock_run)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = f"{tmpdir}/test_input.tif"
        output_path = f"{tmpdir}/test_output_sr.tif"

        data = np.random.randint(0, 3000, (6, 64, 64), dtype=np.uint16)
        transform = from_bounds(3.9, 51.85, 4.6, 52.05, 64, 64)
        with rasterio.open(input_path, "w", driver="GTiff", height=64, width=64,
                           count=6, dtype="uint16",
                           crs="EPSG:4326", transform=transform) as dst:
            dst.write(data)

        result = correct_atmospheric_6s(
            input_path, output_path, tile_id="test-tile-001"
        )

        with rasterio.open(output_path) as src:
            for band_idx in range(1, src.count + 1):
                band_data = src.read(band_idx)
                assert band_data.min() >= 0.0, (
                    f"Band {band_idx} has negative reflectance: {band_data.min()}"
                )
                assert band_data.max() <= 1.0, (
                    f"Band {band_idx} exceeds 1.0 reflectance: {band_data.max()}"
                )


def test_correction_output_shape_matches_input(monkeypatch):
    pytest.importorskip("rasterio")
    pytest.importorskip("Py6S")
    import rasterio
    from rasterio.transform import from_bounds
    from src.preprocess.optical import correct_atmospheric_6s
    import Py6S

    def mock_run(self):
        self.outputs = type('Outputs', (), {'coef_xa': 0.002, 'coef_xb': 0.01, 'coef_xc': 0.05})()
    monkeypatch.setattr(Py6S.SixS, "run", mock_run)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = f"{tmpdir}/test_input.tif"
        output_path = f"{tmpdir}/test_output_sr.tif"

        data = np.random.randint(500, 2000, (6, 128, 128), dtype=np.uint16)
        transform = from_bounds(3.9, 51.85, 4.6, 52.05, 128, 128)
        with rasterio.open(input_path, "w", driver="GTiff", height=128, width=128,
                           count=6, dtype="uint16",
                           crs="EPSG:4326", transform=transform) as dst:
            dst.write(data)

        correct_atmospheric_6s(input_path, output_path, tile_id="shape-test")

        with rasterio.open(input_path) as src_in, \
             rasterio.open(output_path) as src_out:
            assert src_in.height == src_out.height
            assert src_in.width == src_out.width


def test_ndvi_range_is_valid():
    pytest.importorskip("rasterio")
    import rasterio
    from rasterio.transform import from_bounds
    from src.preprocess.optical import compute_ndvi

    with tempfile.TemporaryDirectory() as tmpdir:
        sr_path = f"{tmpdir}/test_sr.tif"
        sr_data = np.random.uniform(0.0, 0.8, (6, 64, 64)).astype(np.float32)
        transform = from_bounds(3.9, 51.85, 4.6, 52.05, 64, 64)
        with rasterio.open(sr_path, "w", driver="GTiff", height=64, width=64,
                           count=6, dtype="float32",
                           crs="EPSG:4326", transform=transform) as dst:
            dst.write(sr_data)

        ndvi = compute_ndvi(sr_path)
        assert ndvi.min() >= -1.0, f"NDVI below -1.0: {ndvi.min()}"
        assert ndvi.max() <= 1.0, f"NDVI above 1.0: {ndvi.max()}"
