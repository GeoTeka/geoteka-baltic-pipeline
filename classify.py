"""Indices, masking, vegetation classification and vectorisation to GeoJSON."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import rasterio
from rasterio import features
import geopandas as gpd
from shapely.geometry import shape

SWEREF99_TM = "EPSG:3006"


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """McFeeters NDWI; high over water."""
    return _norm_diff(green, nir)


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """NDVI; high over vegetation."""
    return _norm_diff(nir, red)


def _norm_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = a + b
    out = np.where(denom == 0, 0.0, (a - b) / denom)
    return out.astype("float32")


def water_mask(green, nir, valid, ndwi_thresh: float = 0.0) -> np.ndarray:
    """Boolean water mask: NDWI above threshold and pixel flagged valid."""
    return (ndwi(green, nir) > ndwi_thresh) & valid


def deepwater_mask(green, nir, valid, ndwi_thresh: float = 0.3) -> np.ndarray:
    """Conservative optically-deep-water mask used to fit the glint regression."""
    return (ndwi(green, nir) > ndwi_thresh) & valid


def classify_vegetation(
    scene: dict,
    water: np.ndarray,
    ndvi_thresh: float = 0.10,
) -> np.ndarray:
    """Return uint8 raster: 1 = vegetation, 2 = bare/open water, 0 = not classified."""
    veg = ndvi(scene["nir"], scene["red"]) > ndvi_thresh
    out = np.zeros(scene["red"].shape, dtype="uint8")
    out[water & ~veg] = 2
    out[water & veg] = 1
    return out


def to_geojson(
    classes: np.ndarray,
    profile: dict,
    out_path: str | Path,
    keep: tuple[int, ...] = (1, 2),
    min_pixels: int = 10,
) -> gpd.GeoDataFrame:
    """Vectorise a class raster and write GeoJSON in SWEREF 99 TM (EPSG:3006)."""
    transform = profile["transform"]
    src_crs = profile["crs"]
    pixel_area = abs(transform.a * transform.e)

    labels = {1: "vegetation", 2: "open_water"}
    geoms, recs = [], []
    for geom, val in features.shapes(classes, mask=np.isin(classes, keep), transform=transform):
        val = int(val)
        poly = shape(geom)
        if poly.area < min_pixels * pixel_area:
            continue
        geoms.append(poly)
        recs.append({"class_id": val, "class": labels.get(val, str(val))})

    gdf = gpd.GeoDataFrame(recs, geometry=geoms, crs=src_crs).to_crs(SWEREF99_TM)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GeoJSON")
    return gdf
