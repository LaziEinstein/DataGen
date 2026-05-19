"""
Map CRESI 8-class speed-bin output to road type taxonomy.
Speed bins (mph): 0, 10, 20, 30, 40, 50, 60, 70+
"""
from __future__ import annotations
import networkx as nx

SPEED_TO_ROAD_TYPE = {
    (0, 15): "path",
    (15, 25): "track",
    (25, 35): "tertiary",
    (35, 50): "secondary",
    (50, 65): "primary",
    (65, 1000): "highway",
}


def classify_road_type(G: nx.Graph) -> nx.Graph:
    """Add 'road_type' attribute to each edge based on inferred speed."""
    for u, v, data in G.edges(data=True):
        speed = data.get("inferred_speed_mph") or data.get("speed_mph") or 0
        data["road_type"] = _speed_to_type(float(speed))
    return G


def _speed_to_type(speed_mph: float) -> str:
    for (low, high), road_type in SPEED_TO_ROAD_TYPE.items():
        if low <= speed_mph < high:
            return road_type
    return "unclassified"
