"""
Convert a CRESI NetworkX graph to a GeoJSON FeatureCollection.
Handles both pixel-coordinate and geo-coordinate geometries.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

import networkx as nx


def graph_to_geojson(
    G: nx.Graph,
    imagery_date: Optional[str] = None,
    model_version: str = "cresi-sn5-v1",
) -> Dict[str, Any]:
    """Return a GeoJSON FeatureCollection from a CRESI graph."""
    features = []
    seen = set()

    for u, v, data in G.edges(data=True):
        edge_key = (min(u, v), max(u, v))
        if edge_key in seen:
            continue
        seen.add(edge_key)

        geom = _extract_geometry(data)
        if geom is None:
            continue

        props = {
            "road_type": data.get("road_type"),
            "surface": data.get("surface"),
            "width_m": data.get("width_m"),
            "speed_mph": data.get("inferred_speed_mph") or data.get("speed_mph"),
            "travel_time_s": data.get("travel_time_s"),
            "length_m": data.get("length") or data.get("length_m"),
            "confidence": data.get("confidence"),
            "source": data.get("source", "satellite"),
            "imagery_date": imagery_date,
            "model_version": model_version,
            "osm_gap": data.get("osm_gap", False),
        }

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {k: v for k, v in props.items() if v is not None},
        })

    return {"type": "FeatureCollection", "features": features}


def _extract_geometry(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract a GeoJSON LineString geometry from edge data."""
    geom_geo = data.get("geometry_geo") or data.get("geometry_wgs84")
    if geom_geo is not None:
        if hasattr(geom_geo, "__geo_interface__"):
            return dict(geom_geo.__geo_interface__)
        return geom_geo

    geom_pix = data.get("geometry_pix")
    if geom_pix is not None:
        # pixel coords fallback — caller should reproject before export
        if hasattr(geom_pix, "coords"):
            coords = list(geom_pix.coords)
            return {"type": "LineString", "coordinates": coords}

    return None
