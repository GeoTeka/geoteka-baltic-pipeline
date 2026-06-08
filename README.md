# Katthammarsvik Coastal Vegetation Mapping

Automated Sentinel-2 pipeline for mapping submerged and coastal vegetation in
turbid, carbonate-rich Baltic waters around Katthammarsvik, Gotland. Built as part of
my final thesis project (YH Mätningsteknik/Geodesi, Hermods, 2026) in collaboration
with Länsstyrelsen i Gotlands län.

The hard part on Gotland's east coast is the water: high calcareous sediment load and
strong sun glint corrupt the optical signal, which is exactly what makes naive
classification fail. This pipeline corrects for sun glint, masks land and deep water,
classifies vegetation, and exports clean vector layers in **SWEREF 99 TM (EPSG:3006)**
ready for QGIS.

## What it does

```
Sentinel-2 L2A scene
        |
        v
1. Load bands + scene mask (SCL)              io_s2.py
        |
        v
2. Sun glint correction (Hedley et al. 2005)  deglint.py
        |
        v
3. Water / land masking (NDWI)                classify.py
        |
        v
4. Vegetation classification (NDVI)           classify.py
        |
        v
5. Vectorise -> GeoJSON in EPSG:3006          classify.py
```

End-to-end run: `katthammarsvik_pipeline.ipynb`.

## Method notes

**Sun glint correction.** NIR-based deglinting of Hedley, Harborne & Mumby (2005). For
each visible band a linear regression is fit between NIR and the visible band over a
sampled deep-water region; the glint component is subtracted per pixel:

```
R_corrected = R_visible - slope * (R_NIR - min_NIR_deepwater)
```

This is the standard, defensible approach for shallow-water optical work and the
correction described in the thesis.

**Classification.** Water is separated from land with NDWI (McFeeters); vegetation
within the water/coastal mask is flagged with an NDVI threshold. Thresholds are
exposed as parameters: they are scene-dependent and must be tuned, not trusted blindly.

**Coordinate system.** All outputs in EPSG:3006 (SWEREF 99 TM), the Swedish national
grid, so layers drop straight into a Lantmateriet-aligned QGIS project.

## Run it

```bash
pip install -r requirements.txt
jupyter lab katthammarsvik_pipeline.ipynb
```

Point the notebook at a Sentinel-2 L2A scene covering Katthammarsvik (download from the
Copernicus Data Space Ecosystem; raster data is not committed).

## Limitations / honesty

- Thresholds are empirical and tuned for this site; they will not transfer unchanged.
- Validation against field/ground-truth points is partial: a thesis-scale result, not
  an operational product.
- Atmospheric correction relies on the Sen2Cor L2A product, not a custom model.

## Author

Emma Kathleen Larsen — Visby, Gotland — emma@geoteka.se
