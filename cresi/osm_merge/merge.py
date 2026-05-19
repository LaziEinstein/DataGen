"""
Compare CRESI GeoJSON output against OSM road network for an AOI.
Tags each feature with source: 'satellite' | 'osm' | 'merged'.
Flags roads in CRESI output absent from OSM as osm_gap: true.
"""
from __future__ import annotations
from typing import Any, Dict

OSM_BUFFER_M = 15.0


def merge_with_osm(geojson: Dict[str, Any], aoi_geometry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch OSM roads for the AOI and merge with CRESI features.
    Requires osmnx and shapely.
    """
    try:
        import osmnx as ox
        from shapely.geometry import shape, LineString
        from shapely.ops import unary_union
    except ImportError:
        raise ImportError("osmnx and shapely are required for OSM merging")

    aoi_shape = shape(aoi_geometry)
    osm_graph = ox.graph_from_polygon(aoi_shape, network_type="all")
    osm_edges = ox.graph_to_gdfs(osm_graph, nodes=False)

    osm_union = unary_union(osm_edges.geometry.values)

    for feature in geojson["features"]:
        geom = shape(feature["geometry"])
        buffered = geom.buffer(_buffer_degrees(OSM_BUFFER_M, aoi_shape.centroid.y))
        in_osm = osm_union.intersects(buffered)
        feature["properties"]["osm_gap"] = not in_osm
        if not in_osm:
            feature["properties"]["source"] = "satellite"
        else:
            feature["properties"]["source"] = "merged"

    osm_features = _osm_only_features(osm_edges, geojson)
    geojson["features"].extend(osm_features)

    return geojson


def _buffer_degrees(meters: float, lat: float) -> float:
    """Convert a metre buffer to approximate degrees at given latitude."""
    import math
    return meters / (111320 * math.cos(math.radians(lat)))


def _osm_only_features(osm_edges: Any, cresi_geojson: Dict[str, Any]) -> list:
    """Return OSM roads not represented in the CRESI output."""
    from shapely.geometry import shape
    from shapely.ops import unary_union

    if not cresi_geojson["features"]:
        return []

    cresi_union = unary_union([
        shape(f["geometry"]) for f in cresi_geojson["features"]
        if f["geometry"]["type"] == "LineString"
    ])

    osm_only = []
    for _, row in osm_edges.iterrows():
        if not cresi_union.buffer(0.0001).intersects(row.geometry):
            osm_only.append({
                "type": "Feature",
                "geometry": row.geometry.__geo_interface__,
                "properties": {
                    "road_type": row.get("highway", "unclassified"),
                    "source": "osm",
                    "osm_gap": False,
                    "name": row.get("name"),
                    "speed_mph": row.get("maxspeed"),
                },
            })
    return osm_only
