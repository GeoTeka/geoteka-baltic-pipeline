"""Loading Sentinel-2 L2A bands and the scene classification (SCL) mask."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling

# Sentinel-2 L2A band file suffixes (10 m unless noted)
BANDS = {
    "B02": "blue",
    "B03": "green",
    "B04": "red",
    "B08": "nir",
}

# SCL classes we treat as invalid (clouds, shadows, snow, saturated, no-data)
SCL_INVALID = {0, 1, 3, 8, 9, 10, 11}


def _find_band(scene_dir: Path, band: str) -> Path:
    matches = list(scene_dir.rglob(f"*_{band}_10m.jp2")) or list(
        scene_dir.rglob(f"*{band}*.jp2")
    )
    if not matches:
        raise FileNotFoundError(f"Band {band} not found under {scene_dir}")
    return matches[0]


def load_scene(scene_dir: str | Path) -> dict:
    """Load blue/green/red/nir as float reflectance plus profile and valid mask.

    Returns a dict with band arrays (0-1 reflectance), the rasterio profile of the
    red band (reference grid), and a boolean ``valid`` mask from the SCL layer.
    """
    scene_dir = Path(scene_dir)
    out: dict = {}
    ref_profile = None
    for band, name in BANDS.items():
        with rasterio.open(_find_band(scene_dir, band)) as ds:
            arr = ds.read(1).astype("float32") / 10000.0  # L2A scale factor
            out[name] = arr
            if band == "B04":
                ref_profile = ds.profile

    out["profile"] = ref_profile
    out["valid"] = _load_valid_mask(scene_dir, out["red"].shape)
    return out


def _load_valid_mask(scene_dir: Path, shape) -> np.ndarray:
    """Boolean mask of usable pixels from the 20 m SCL band, resampled to 10 m."""
    scl = list(scene_dir.rglob("*_SCL_20m.jp2")) or list(scene_dir.rglob("*SCL*.jp2"))
    if not scl:
        # No SCL available: treat everything as valid, let later masks handle it.
        return np.ones(shape, dtype=bool)
    with rasterio.open(scl[0]) as ds:
        scl_arr = ds.read(1, out_shape=shape, resampling=Resampling.nearest)
    return ~np.isin(scl_arr, list(SCL_INVALID))
