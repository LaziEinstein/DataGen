"""
AOI polygon → mercator tile grid.
Uses the mercantile library for tile math.
"""
from __future__ import annotations
from typing import List, Tuple

import mercantile

Tile = mercantile.Tile
Coord = Tuple[float, float]


def aoi_to_tile_grid(ring: List[Coord], zoom: int = 18) -> List[Tile]:
    """
    Convert a polygon ring (list of [lon, lat] pairs) to a list of
    Web Mercator tiles at the given zoom level that cover the polygon.
    """
    lons = [pt[0] for pt in ring]
    lats = [pt[1] for pt in ring]
    west, south, east, north = min(lons), min(lats), max(lons), max(lats)
    tiles = list(mercantile.tiles(west, south, east, north, zooms=zoom))
    return tiles


def tile_count_estimate(ring: List[Coord], zoom: int = 18) -> int:
    return len(aoi_to_tile_grid(ring, zoom))
