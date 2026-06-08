"""Sun glint correction for shallow-water Sentinel-2 imagery.

Implements the NIR-based deglinting of Hedley, Harborne & Mumby (2005),
"Simple and robust removal of sun glint for mapping shallow-water benthos",
International Journal of Remote Sensing 26(10): 2107-2112.
"""
from __future__ import annotations
import numpy as np


def deglint_band(
    visible: np.ndarray,
    nir: np.ndarray,
    deepwater_mask: np.ndarray,
) -> np.ndarray:
    """Remove sun glint from a single visible band.

    Parameters
    ----------
    visible : 2-D reflectance array for the visible band to correct.
    nir     : 2-D NIR reflectance array (same grid).
    deepwater_mask : boolean array selecting optically deep water pixels used to
        fit the glint regression. Over deep water any signal correlated with NIR
        is assumed to be glint.

    Returns
    -------
    Corrected visible band, glint removed, clipped at 0.
    """
    sample_vis = visible[deepwater_mask]
    sample_nir = nir[deepwater_mask]
    if sample_vis.size < 50:
        raise ValueError("Deep-water sample too small to fit a glint regression.")

    # slope of visible-vs-NIR over deep water = glint contamination factor
    slope = np.polyfit(sample_nir, sample_vis, 1)[0]
    min_nir = float(np.nanmin(sample_nir))

    corrected = visible - slope * (nir - min_nir)
    return np.clip(corrected, 0.0, None)


def deglint_scene(scene: dict, deepwater_mask: np.ndarray) -> dict:
    """Apply :func:`deglint_band` to blue, green and red bands of a loaded scene."""
    out = dict(scene)
    for name in ("blue", "green", "red"):
        out[name] = deglint_band(scene[name], scene["nir"], deepwater_mask)
    return out
