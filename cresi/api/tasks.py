"""
Celery task definitions for the DataGen pipeline.
Each task step updates job_store so the API can report progress.
"""
from __future__ import annotations
import json
import logging
import pathlib
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict

from celery import Celery

from .store import job_store
from .models import JobStatus

logger = logging.getLogger(__name__)

celery_app = Celery(
    "datagen",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)


def _update(job_id: str, status: JobStatus, pct: float, step: str) -> None:
    if job_id in job_store:
        job_store[job_id].update({
            "status": status,
            "progress_pct": pct,
            "current_step": step,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })


@celery_app.task(bind=True, name="datagen.run_pipeline")
def run_pipeline_task(self, job_id: str, request: Dict[str, Any]) -> None:
    try:
        from cresi.ingest.aoi import aoi_to_tile_grid
        from cresi.ingest.imagery import fetch_tiles
        from cresi.ingest.mosaic import mosaic_tiles
        from cresi.enrich.road_type import classify_road_type
        from cresi.enrich.width import estimate_width
        from cresi.enrich.surface import estimate_surface
        from cresi.export.geojson import graph_to_geojson
        from cresi.osm_merge.merge import merge_with_osm

        aoi = request["aoi"]
        provider = request.get("imagery_provider", "esri")
        merge_osm = request.get("merge_osm", True)

        _update(job_id, JobStatus.fetching_imagery, 5.0, "computing tile grid")
        tiles = aoi_to_tile_grid(aoi["geometry"]["coordinates"][0], zoom=18)

        _update(job_id, JobStatus.fetching_imagery, 15.0, f"fetching {len(tiles)} imagery tiles")
        tile_paths = fetch_tiles(tiles, provider=provider)

        _update(job_id, JobStatus.fetching_imagery, 30.0, "mosaicking tiles")
        mosaic_path = mosaic_tiles(tile_paths)

        _update(job_id, JobStatus.running_inference, 40.0, "running CRESI inference")
        graph = _run_cresi(mosaic_path, job_id, request.get("config_overrides") or {})

        _update(job_id, JobStatus.enriching, 70.0, "enriching road attributes")
        graph = classify_road_type(graph)
        graph = estimate_width(graph, mosaic_path)
        graph = estimate_surface(graph)

        _update(job_id, JobStatus.enriching, 80.0, "exporting GeoJSON")
        geojson = graph_to_geojson(graph, imagery_date=request.get("imagery_date"))

        if merge_osm:
            _update(job_id, JobStatus.merging_osm, 88.0, "merging with OSM")
            geojson = merge_with_osm(geojson, aoi["geometry"])

        result_dir = pathlib.Path(tempfile.mkdtemp(prefix=f"datagen_{job_id}_"))
        result_path = result_dir / "result.geojson"
        result_path.write_text(json.dumps(geojson, indent=2))

        if job_id in job_store:
            job_store[job_id]["result_path"] = str(result_path)

        if request.get("push_to_backend") and request.get("callback_url"):
            from cresi.backend.connector import push_results
            push_results(str(result_path), request["callback_url"])

        _update(job_id, JobStatus.complete, 100.0, "complete")

    except Exception as exc:
        logger.exception("Pipeline failed for job %s", job_id)
        if job_id in job_store:
            job_store[job_id].update({
                "status": JobStatus.failed,
                "error": str(exc),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        raise


def _run_cresi(mosaic_path: str, job_id: str, overrides: Dict[str, Any]) -> Any:
    """Invoke the CRESI research pipeline steps 02–06 programmatically."""
    raise NotImplementedError(
        "CRESI pipeline integration pending — implement in Phase 1 sprint 2"
    )
