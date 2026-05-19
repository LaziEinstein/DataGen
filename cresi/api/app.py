"""
DataGen API — FastAPI application.
Entry point: uvicorn cresi.api.app:app --reload
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from .models import JobRequest, JobResponse, JobStatusResponse, JobStatus
from .tasks import run_pipeline_task
from .store import job_store

app = FastAPI(
    title="DataGen Road Extraction API",
    description="AOI-driven satellite road extraction and inventory generation",
    version="0.1.0",
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "datagen-api"}


@app.post("/jobs", response_model=JobResponse, status_code=202)
def submit_job(request: JobRequest) -> JobResponse:
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    aoi_coords = request.aoi.geometry.coordinates
    area_km2 = _estimate_area_km2(aoi_coords)
    estimated_tiles = max(1, int(area_km2 / 0.09))  # ~300m tiles

    job_store[job_id] = {
        "status": JobStatus.queued,
        "progress_pct": 0.0,
        "current_step": "queued",
        "error": None,
        "created_at": now,
        "updated_at": now,
        "request": request.model_dump(),
        "result_path": None,
    }

    run_pipeline_task.delay(job_id, request.model_dump())

    return JobResponse(
        job_id=job_id,
        status=JobStatus.queued,
        aoi_area_km2=round(area_km2, 2),
        estimated_tiles=estimated_tiles,
        message="Job queued. Poll /jobs/{job_id} for status.",
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress_pct=job["progress_pct"],
        current_step=job["current_step"],
        error=job.get("error"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@app.get("/jobs/{job_id}/results")
def get_job_results(job_id: str) -> Any:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != JobStatus.complete:
        raise HTTPException(status_code=409, detail=f"Job not complete: {job['status']}")
    result_path = job.get("result_path")
    if not result_path:
        raise HTTPException(status_code=500, detail="Result path missing")
    import json, pathlib
    return JSONResponse(content=json.loads(pathlib.Path(result_path).read_text()))


@app.delete("/jobs/{job_id}", status_code=204)
def cancel_job(job_id: str) -> None:
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    job_store[job_id]["status"] = JobStatus.failed
    job_store[job_id]["error"] = "Cancelled by user"


def _estimate_area_km2(coordinates: Any) -> float:
    """Rough bounding-box area estimate from polygon coordinates."""
    try:
        ring = coordinates[0]
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]
        lon_span = (max(lons) - min(lons)) * 111.32 * abs((max(lats) + min(lats)) / 2 * 0.01745)
        lat_span = (max(lats) - min(lats)) * 110.574
        return lon_span * lat_span
    except Exception:
        return 0.0
