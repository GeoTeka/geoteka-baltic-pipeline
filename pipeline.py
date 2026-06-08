"""Command-line entry point: Sentinel-2 scene dir -> vegetation GeoJSON.

Usage:
    python -m src.pipeline /path/to/S2_scene.SAFE outputs/katthammarsvik_veg.geojson
"""
from __future__ import annotations
import sys
from . import io_s2, deglint, classify


def run(scene_dir: str, out_geojson: str,
        ndwi_thresh: float = 0.0, ndvi_thresh: float = 0.10):
    scene = io_s2.load_scene(scene_dir)
    deep = classify.deepwater_mask(scene["green"], scene["nir"], scene["valid"])
    scene = deglint.deglint_scene(scene, deep)
    water = classify.water_mask(scene["green"], scene["nir"], scene["valid"], ndwi_thresh)
    classes = classify.classify_vegetation(scene, water, ndvi_thresh)
    gdf = classify.to_geojson(classes, scene["profile"], out_geojson)
    print(f"Wrote {len(gdf)} polygons to {out_geojson} ({classify.SWEREF99_TM})")
    return gdf


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
