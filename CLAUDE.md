# DataGen — CRESI Road Extraction Product

## Project Purpose
This repository is a fork of CRESI (City-scale Road Extraction from Satellite Imagery) being developed into a production road dataset generation and road inventory creation tool. The goal is to supplement and improve upon OSM data coverage using satellite imagery as input.

## Architecture Overview
The product wraps the existing CRESI research pipeline with:
- A REST API (FastAPI) for AOI-based job submission
- An async job queue (Celery + Redis) for long-running inference
- A pluggable imagery ingestion layer (ESRI/Bing/Planet tiles)
- Road attribute enrichment (type, width, surface condition)
- OSM comparison and gap-fill merge layer
- GeoJSON export connector to an existing data collection backend

## Repository Structure
```
cresi/
├── 00_gen_folds.py … 08_plot_graph_plus_im.py  # Original CRESI pipeline scripts
├── api/          # FastAPI app, Celery tasks, Pydantic models
├── ingest/       # AOI tiling, imagery fetching, mosaicking
├── enrich/       # Road attribute enrichment (type, width, surface)
├── export/       # NetworkX graph → GeoJSON converter
├── osm_merge/    # OSM comparison, gap detection, merge
├── backend/      # Connector to existing data collection REST API
├── configs/      # JSON config files
├── data_prep/    # Original CRESI data prep scripts
├── net/          # Deep learning model (U-Net, ResNet34)
├── utils/        # Graph tools, APLS scoring, GDAL helpers
docker/
docs/             # Design documents and roadmap
notebooks/        # Tutorial notebooks
results/          # Weights and sample outputs
```

## Development Branch
Active development: `claude/map-repo-status-Ca1xG`

## Key Design Decisions
- CRESI model trained at 0.3m GSD — target imagery should match this resolution
- Default imagery source: ESRI World Imagery tiles (free, global, no API key)
- Road type derived from CRESI 8-class speed-bin output
- Road width estimated via medial axis distance transform on segmentation mask
- Surface condition: heuristic v1 (speed + width proxy), ML classifier planned for v2
- OSM merge uses 15m buffer threshold for gap detection
- All pipeline runs are async jobs; results delivered as GeoJSON FeatureCollection

## Running the Pipeline
See `cresi/train.sh` and `cresi/test.sh` for the original pipeline.
New API entrypoint: `cresi/api/app.py` (FastAPI, run with uvicorn)

## Environment
- Docker: `docker/gpu/Dockerfile` (GPU inference) or `docker/cpu/Dockerfile`
- Full stack: `docker-compose.yml` (API + Celery + Redis + Flower)
- Python deps: `requirements-product.txt` (product layer additions)

## Config File Notes
`cresi/configs/sn5_baseline.json` has a syntax error on line 6:
`"speed_conversion_file:"` — colon is inside the key name, will fail JSON parse.
Fix: rename key to `"speed_conversion_file"`.

## Status
- Phase 1 (Foundation): In progress
- Phase 2 (Enrichment): Planned
- Phase 3 (Backend Integration): Planned
See `ROADMAP.md` for full timeline.
