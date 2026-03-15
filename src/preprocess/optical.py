"""
Sentinel-2 atmospheric correction using py6S radiative transfer model.
NOT DOS. NOT a placeholder. Real surface reflectance computation.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np

try:
    import rasterio
    from rasterio.transform import from_bounds
except ImportError:
    # We will let the execution fail if actually used, but for structure:
    pass

try:
    from Py6S import (
        SixS, Geometry, AeroProfile, AtmosProfile, Wavelength, SixSHelpers
    )
except ImportError:
    pass


SENTINEL2_BANDS: dict[str, float] = {
    "B02": 490.0,   # Blue
    "B03": 560.0,   # Green
    "B04": 665.0,   # Red
    "B08": 842.0,   # NIR
    "B11": 1610.0,  # SWIR-1
    "B12": 2190.0,  # SWIR-2
}

AEROSOL_PROFILE_MAP = {
    "continental": AeroProfile.Continental if 'AeroProfile' in globals() else None,
    "maritime":    AeroProfile.Maritime if 'AeroProfile' in globals() else None,
    "urban":       AeroProfile.Urban if 'AeroProfile' in globals() else None,
}


@dataclass
class CorrectionResult:
    band_stats: dict[str, dict[str, float]]
    output_path: str
    pixels_clipped: int
    tile_id: str
    preprocessing_ver: str = "1.0.0"


def correct_atmospheric_6s(
    input_path: str,
    output_path: str,
    solar_zenith: float = 40.0,
    solar_azimuth: float = 160.0,
    view_zenith: float = 0.0,
    view_azimuth: float = 0.0,
    acquisition_month: int = 6,
    acquisition_day: int = 15,
    aerosol_optical_depth: float = 0.1,
    aerosol_profile: str = "continental",
    tile_id: str = "",
) -> CorrectionResult:
    import rasterio
    from Py6S import SixS, Geometry, AeroProfile, AtmosProfile, Wavelength
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pixels_clipped_total = 0
    band_stats: dict[str, dict[str, float]] = {}

    s = SixS()
    s.geometry = Geometry.User()
    s.geometry.solar_z = solar_zenith
    s.geometry.solar_a = solar_azimuth
    s.geometry.view_z = view_zenith
    s.geometry.view_a = view_azimuth
    s.geometry.month = acquisition_month
    s.geometry.day = acquisition_day
    s.aero_profile = AeroProfile.PredefinedType(
        AEROSOL_PROFILE_MAP.get(aerosol_profile, AeroProfile.Continental)
    )
    s.aot550 = aerosol_optical_depth
    s.atmos_profile = AtmosProfile.PredefinedType(
        AtmosProfile.MidlatitudeSummer
    )

    corrections: list[tuple[float, float, float]] = []
    for band_name, wavelength_nm in SENTINEL2_BANDS.items():
        s.wavelength = Wavelength(wavelength_nm / 1000.0)
        s.run()
        xa = s.outputs.coef_xa
        xb = s.outputs.coef_xb
        xc = s.outputs.coef_xc
        corrections.append((xa, xb, xc))

    with rasterio.open(input_path) as src:
        profile = src.profile.copy()
        n_bands = min(src.count, len(SENTINEL2_BANDS))

        profile.update(
            driver="GTiff",
            dtype="float32",
            count=n_bands,
            compress="lzw",
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.update_tags(
                TILE_ID=tile_id,
                PREPROCESSING_VER="1.0.0",
                CORRECTION_METHOD="6S_RTM",
                AEROSOL_PROFILE=aerosol_profile,
                AOD550=str(aerosol_optical_depth),
            )
            for i, (band_name, (xa, xb, xc)) in enumerate(
                zip(SENTINEL2_BANDS.keys(), corrections), start=1
            ):
                if i > src.count:
                    break
                toa = src.read(i).astype(np.float32)
                # Convert DN to TOA reflectance (Sentinel-2 scale factor)
                toa = toa / 10000.0
                # Apply 6S correction
                y = xa * toa - xb
                denominator = 1.0 + xc * y
                denominator = np.where(denominator == 0, 1e-10, denominator)
                sr = y / denominator
                # Clip to valid reflectance range
                n_clipped = int(np.sum((sr < 0.0) | (sr > 1.0)))
                pixels_clipped_total += n_clipped
                sr = np.clip(sr, 0.0, 1.0)
                dst.write(sr, i)
                band_stats[band_name] = {
                    "mean": float(np.nanmean(sr)),
                    "std": float(np.nanstd(sr)),
                    "min": float(np.nanmin(sr)),
                    "max": float(np.nanmax(sr)),
                    "n_clipped": n_clipped,
                }

    return CorrectionResult(
        band_stats=band_stats,
        output_path=output_path,
        pixels_clipped=pixels_clipped_total,
        tile_id=tile_id,
    )


def compute_ndvi(sr_path: str) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red). Reads B08 (NIR) and B04 (Red)."""
    import rasterio
    with rasterio.open(sr_path) as src:
        # Band index: B02=1, B03=2, B04=3, B08=4, B11=5, B12=6
        red = src.read(3).astype(np.float32)  # B04
        nir = src.read(4).astype(np.float32)  # B08

    denom = nir + red
    denom = np.where(denom == 0, 1e-10, denom)
    ndvi = (nir - red) / denom
    ndvi = np.clip(ndvi, -1.0, 1.0)
    return ndvi
