from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ImageryProvider(str, Enum):
    esri = "esri"
    bing = "bing"
    planet_nicfi = "planet_nicfi"
    maxar = "maxar"


class JobStatus(str, Enum):
    queued = "queued"
    fetching_imagery = "fetching_imagery"
    running_inference = "running_inference"
    enriching = "enriching"
    merging_osm = "merging_osm"
    complete = "complete"
    failed = "failed"


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: List[Any]


class AOIFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry


class JobRequest(BaseModel):
    aoi: AOIFeature = Field(..., description="AOI polygon as a GeoJSON Feature")
    imagery_provider: ImageryProvider = ImageryProvider.esri
    imagery_date: Optional[str] = Field(None, description="YYYY-MM preferred date, best-available used if absent")
    merge_osm: bool = Field(True, description="Compare output against OSM and tag gaps")
    push_to_backend: bool = Field(False, description="Push results to configured backend API on completion")
    callback_url: Optional[str] = Field(None, description="Webhook URL called when job completes")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="Override cresi config keys")


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    aoi_area_km2: float
    estimated_tiles: int
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress_pct: float
    current_step: str
    error: Optional[str] = None
    created_at: str
    updated_at: str


class RoadFeatureProperties(BaseModel):
    road_type: Optional[str] = None
    surface: Optional[str] = None
    width_m: Optional[float] = None
    speed_mph: Optional[float] = None
    travel_time_s: Optional[float] = None
    length_m: Optional[float] = None
    confidence: Optional[float] = None
    source: str = "satellite"
    imagery_date: Optional[str] = None
    model_version: str = "cresi-sn5-v1"
    osm_gap: bool = False
