"""
Push DataGen GeoJSON results to the connected data collection backend REST API.
"""
from __future__ import annotations
import json
import pathlib
import time
from typing import Optional

import requests


def push_results(
    result_path: str,
    backend_url: str,
    api_key: Optional[str] = None,
    max_retries: int = 4,
) -> None:
    """POST GeoJSON FeatureCollection to the backend API."""
    geojson = json.loads(pathlib.Path(result_path).read_text())
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    for attempt in range(max_retries):
        try:
            resp = requests.post(backend_url, json=geojson, headers=headers, timeout=30)
            resp.raise_for_status()
            return
        except requests.RequestException as exc:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Backend push failed after {max_retries} attempts: {exc}") from exc
            time.sleep(2 ** attempt)
