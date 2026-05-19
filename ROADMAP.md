# DataGen Product Roadmap

> Road Dataset Generation & Road Inventory Creation from Satellite Imagery  
> Status: Phase 1 — In Progress  
> Last updated: 2026-05-19

---

## Vision
A self-service tool that accepts an area of interest (AOI) polygon, fetches satellite imagery, extracts road networks and inventory attributes, and delivers structured GeoJSON road data to a connected backend — filling gaps where OSM coverage is absent or unreliable.

---

## Phase 1 — Foundation
**Target: Weeks 1–3**

### Goals
- Wrap CRESI pipeline in a callable API
- Enable AOI-driven tile fetching from satellite imagery
- Produce GeoJSON output from pipeline results

### Deliverables
- [ ] `cresi/api/app.py` — FastAPI application with job endpoints
- [ ] `cresi/api/models.py` — Pydantic request/response models
- [ ] `cresi/api/tasks.py` — Celery task definitions
- [ ] `cresi/ingest/aoi.py` — AOI polygon → mercator tile grid
- [ ] `cresi/ingest/imagery.py` — Pluggable imagery tile fetcher (ESRI default)
- [ ] `cresi/ingest/mosaic.py` — Tile assembly and reprojection
- [ ] `cresi/export/geojson.py` — NetworkX graph → GeoJSON FeatureCollection
- [ ] `docker-compose.yml` — API + Celery worker + Redis + Flower monitor
- [ ] `requirements-product.txt` — Product layer dependencies
- [ ] Fix JSON syntax error in `cresi/configs/sn5_baseline.json`

### API Endpoints (Phase 1)
```
POST /jobs           Submit AOI, returns job_id
GET  /jobs/{id}      Job status + progress
GET  /jobs/{id}/results  GeoJSON FeatureCollection
DELETE /jobs/{id}    Cancel job
GET  /health         Health check
```

---

## Phase 2 — Road Attribute Enrichment
**Target: Weeks 4–5**

### Goals
- Extract full road inventory attributes beyond geometry and speed
- Map CRESI segmentation output to road taxonomy
- Estimate road width and surface condition

### Deliverables
- [ ] `cresi/enrich/road_type.py` — Speed-bin to road type mapper
  - Bins → highway / primary / secondary / tertiary / track / path
- [ ] `cresi/enrich/width.py` — Mask-based road width estimator
  - Medial axis distance transform → pixel width → meters (via GSD)
- [ ] `cresi/enrich/surface.py` — Surface condition heuristic v1
  - High speed + wide → paved; low speed + narrow → unpaved/track
- [ ] `cresi/enrich/confidence.py` — Per-edge extraction confidence score
- [ ] Updated GeoJSON schema with all inventory fields

### Road Inventory GeoJSON Schema (target)
```json
{
  "type": "Feature",
  "geometry": { "type": "LineString", "coordinates": [...] },
  "properties": {
    "road_type": "secondary",
    "surface": "paved",
    "width_m": 7.2,
    "speed_mph": 45,
    "travel_time_s": 12.4,
    "length_m": 154.0,
    "confidence": 0.87,
    "source": "satellite",
    "imagery_date": "2025-11",
    "model_version": "cresi-sn5-v1"
  }
}
```

---

## Phase 3 — OSM Integration & Gap Detection
**Target: Weeks 5–6**

### Goals
- Compare CRESI output against OSM road network
- Flag roads present in satellite imagery but absent from OSM
- Merge data sources intelligently

### Deliverables
- [ ] `cresi/osm_merge/fetch.py` — OSM road network fetch for AOI (via Overpass)
- [ ] `cresi/osm_merge/diff.py` — Spatial diff: CRESI vs OSM (15m buffer threshold)
- [ ] `cresi/osm_merge/merge.py` — Merge strategy:
  - `source: "osm"` — road only in OSM
  - `source: "satellite"` — road only in CRESI output (OSM gap)
  - `source: "merged"` — road in both; CRESI attributes applied to OSM geometry
- [ ] OSM gap report: count and geometry of unmapped roads per AOI

---

## Phase 4 — Backend Integration
**Target: Week 7**

### Goals
- Push results to existing data collection REST API
- Handle authentication and retry logic
- Support webhook callbacks on job completion

### Deliverables
- [ ] `cresi/backend/connector.py` — REST API push client
- [ ] `cresi/backend/auth.py` — Auth handler (API key / OAuth2)
- [ ] `cresi/backend/schema.py` — Transform DataGen GeoJSON to backend schema
- [ ] Job config: `backend_url`, `backend_auth` fields in job request
- [ ] Webhook: `POST callback_url` when job completes

---

## Phase 5 — Production Hardening
**Target: Weeks 8–10**

### Goals
- Make the system robust for arbitrary AOI sizes and geographies
- Add monitoring, logging, and rate limiting
- Imagery provider failover

### Deliverables
- [ ] Tile-level retry and partial failure handling
- [ ] AOI size validation and auto-split for large areas
- [ ] Prometheus metrics + Grafana dashboard
- [ ] Structured JSON logging throughout pipeline
- [ ] Imagery provider failover chain (ESRI → Bing → Planet)
- [ ] Rate limiting on API endpoints
- [ ] Result caching: skip re-inference for recently processed AOIs

---

## Phase 6 — Model Improvement (v2)
**Target: Months 3–4**

### Goals
- Improve detection in OSM-gap regions (often rural, low-contrast)
- Add proper surface condition classifier
- Support multi-resolution inputs

### Deliverables
- [ ] Fine-tune CRESI model on Planet NICFI imagery (10m→3m fusion)
- [ ] Surface condition binary classifier (paved / unpaved) using auxiliary bands
- [ ] Sentinel-2 10m fallback model for coarse network detection
- [ ] Active learning loop: flag low-confidence edges for human review

---

## Imagery Provider Roadmap

| Phase | Provider | Resolution | Cost | Use case |
|-------|----------|------------|------|----------|
| 1–2 | ESRI World Imagery | 0.3–0.5m urban | Free | Bootstrap, testing |
| 2–3 | Planet NICFI | 4.77m | Free (tropics) | Developing nation coverage |
| 3+ | Maxar SecureWatch | 0.3m | Commercial | Production high-res |
| 3+ | Bing Maps | 0.3–0.5m | Free (research) | Fallback |

---

## Known Technical Debt (inherited from CRESI)
- `sn5_baseline.json` has a JSON syntax error (line 6, colon in key name)
- Some scripts still have `python2` shebangs
- `nx.connected_component_subgraphs()` removed in NetworkX 2.4+ (already patched)
- `skimage.imsave` deprecated (already patched)
- No test suite

---

## Milestones

| Milestone | Target date | Status |
|-----------|-------------|--------|
| Phase 1 complete | Week 3 | In progress |
| First end-to-end AOI → GeoJSON run | Week 3 | Pending |
| Phase 2 attribute enrichment | Week 5 | Planned |
| OSM gap detection live | Week 6 | Planned |
| Backend connected | Week 7 | Planned |
| First production AOI processed | Week 8 | Planned |
| v2 model training begins | Month 3 | Planned |
