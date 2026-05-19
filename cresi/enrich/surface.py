"""
Heuristic v1 surface condition estimator.
High speed + wide → paved; low speed + narrow → unpaved/track.
A proper ML classifier is planned for Phase 6.
"""
from __future__ import annotations
import networkx as nx


def estimate_surface(G: nx.Graph) -> nx.Graph:
    """Add 'surface' attribute to each edge."""
    for u, v, data in G.edges(data=True):
        data["surface"] = _classify_surface(
            road_type=data.get("road_type", "unclassified"),
            speed_mph=data.get("inferred_speed_mph") or 0,
            width_m=data.get("width_m") or 5.0,
        )
    return G


def _classify_surface(road_type: str, speed_mph: float, width_m: float) -> str:
    if road_type in ("highway", "primary"):
        return "paved"
    if road_type == "secondary" and speed_mph >= 40:
        return "paved"
    if road_type in ("track", "path"):
        return "unpaved"
    if speed_mph < 25 or width_m < 4.0:
        return "unpaved"
    return "paved"
