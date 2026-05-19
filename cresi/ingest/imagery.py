"""
Pluggable satellite imagery tile fetcher.
Supported providers: esri, bing, planet_nicfi, maxar.
"""
from __future__ import annotations
import os
import time
import pathlib
import tempfile
from typing import List, Optional

import mercantile
import requests

TILE_URLS = {
    "esri": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "bing": "https://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1",
}

Tile = mercantile.Tile


def fetch_tiles(
    tiles: List[Tile],
    provider: str = "esri",
    output_dir: Optional[str] = None,
    api_key: Optional[str] = None,
    max_retries: int = 3,
) -> List[str]:
    """
    Fetch imagery tiles and save to disk. Returns list of file paths.
    """
    out = pathlib.Path(output_dir or tempfile.mkdtemp(prefix="datagen_tiles_"))
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    session = requests.Session()

    for tile in tiles:
        dest = out / f"{tile.z}_{tile.x}_{tile.y}.png"
        if dest.exists():
            paths.append(str(dest))
            continue
        url = _build_url(tile, provider, api_key)
        _download(session, url, dest, max_retries)
        paths.append(str(dest))

    return paths


def _build_url(tile: Tile, provider: str, api_key: Optional[str]) -> str:
    if provider == "esri":
        return TILE_URLS["esri"].format(z=tile.z, x=tile.x, y=tile.y)
    if provider == "bing":
        quadkey = mercantile.quadkey(tile)
        return TILE_URLS["bing"].format(q=quadkey)
    if provider == "planet_nicfi":
        if not api_key:
            raise ValueError("Planet NICFI requires an API key")
        # Placeholder — Planet tile endpoint requires subscription mosaic ID
        raise NotImplementedError("Planet NICFI integration pending")
    if provider == "maxar":
        raise NotImplementedError("Maxar integration pending")
    raise ValueError(f"Unknown provider: {provider}")


def _download(session: requests.Session, url: str, dest: pathlib.Path, retries: int) -> None:
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            return
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
