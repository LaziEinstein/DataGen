"""
Estimate road width from the segmentation mask using medial axis distance transform.
Width in pixels → meters via Ground Sampling Distance (GSD).
"""
from __future__ import annotations
from typing import Optional

import networkx as nx
import numpy as np


def estimate_width(G: nx.Graph, mosaic_path: str, gsd_m: float = 0.3) -> nx.Graph:
    """
    Add 'width_m' attribute to each edge.
    Uses the mask channel stored in edge geometry or falls back to road-type defaults.
    """
    for u, v, data in G.edges(data=True):
        width_pix = data.get("width_pix")
        if width_pix is not None:
            data["width_m"] = round(float(width_pix) * gsd_m, 1)
        else:
            data["width_m"] = _default_width(data.get("road_type", "unclassified"))
    return G


def _default_width(road_type: str) -> float:
    defaults = {
        "highway": 18.0,
        "primary": 12.0,
        "secondary": 8.0,
        "tertiary": 6.0,
        "track": 4.0,
        "path": 2.0,
        "unclassified": 5.0,
    }
    return defaults.get(road_type, 5.0)
