"""
Assemble downloaded tile images into a single georeferenced mosaic (GeoTIFF).
Requires rasterio and mercantile.
"""
from __future__ import annotations
import pathlib
import tempfile
from typing import List

import mercantile
import numpy as np


def mosaic_tiles(tile_paths: List[str], output_path: str = "") -> str:
    """
    Merge tile PNGs into a single GeoTIFF with Web Mercator projection.
    Returns path to the output GeoTIFF.
    """
    try:
        import rasterio
        from rasterio.merge import merge
        from rasterio.transform import from_bounds
        from rasterio.crs import CRS
    except ImportError:
        raise ImportError("rasterio is required for mosaicking — pip install rasterio")

    if not output_path:
        output_path = str(pathlib.Path(tempfile.mkdtemp()) / "mosaic.tif")

    datasets = [rasterio.open(p) for p in tile_paths]
    mosaic_arr, mosaic_transform = merge(datasets)
    for ds in datasets:
        ds.close()

    meta = datasets[0].meta.copy()
    meta.update({
        "driver": "GTiff",
        "height": mosaic_arr.shape[1],
        "width": mosaic_arr.shape[2],
        "transform": mosaic_transform,
        "crs": CRS.from_epsg(3857),
    })
    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(mosaic_arr)

    return output_path
