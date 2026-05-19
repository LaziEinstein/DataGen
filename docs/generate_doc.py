"""Run this script once to generate the Word documentation file."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

def add_heading(doc, text, level=1, color=None):
    h = doc.add_heading(text, level=level)
    if color:
        for run in h.runs:
            run.font.color.rgb = RGBColor(*color)
    return h

def add_table_row(table, cells, bold_first=False):
    row = table.add_row()
    for i, (cell, text) in enumerate(zip(row.cells, cells)):
        cell.text = text
        if bold_first and i == 0:
            cell.paragraphs[0].runs[0].bold = True
    return row

doc = Document()

# ── Title page ──────────────────────────────────────────────────────────────
doc.add_paragraph()
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("DataGen")
run.bold = True
run.font.size = Pt(36)
run.font.color.rgb = RGBColor(0x1A, 0x73, 0xE8)

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = subtitle.add_run("Road Dataset Generation & Road Inventory Creation\nfrom Satellite Imagery")
run2.font.size = Pt(16)
run2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

doc.add_paragraph()
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run(f"Preliminary Design Document  ·  CONFIDENTIAL\n")
meta.add_run(f"Version 0.1  ·  {datetime.date.today().strftime('%B %Y')}")
meta.runs[-1].font.color.rgb = RGBColor(0x88, 0x88, 0x88)

doc.add_page_break()

# ── 1. Executive Summary ────────────────────────────────────────────────────
add_heading(doc, "1. Executive Summary")
doc.add_paragraph(
    "DataGen is a road dataset generation and road inventory creation tool built on top of "
    "CRESI (City-scale Road Extraction from Satellite Imagery). It addresses a fundamental "
    "limitation of data collection systems that depend on OpenStreetMap (OSM): in rural, "
    "conflict-affected, and rapidly-developing areas, OSM road coverage is sparse, outdated, "
    "or entirely absent."
)
doc.add_paragraph(
    "DataGen accepts an area of interest (AOI) polygon, fetches satellite imagery, runs a "
    "deep-learning road extraction pipeline, enriches the output with road inventory "
    "attributes (road type, width, surface condition, speed), and delivers structured GeoJSON "
    "to a connected data collection backend. Where OSM data exists it is merged and used to "
    "cross-validate; where it is absent the satellite-derived data stands alone, flagged for "
    "downstream review."
)

# ── 2. Problem Statement ────────────────────────────────────────────────────
add_heading(doc, "2. Problem Statement")
doc.add_paragraph(
    "The existing data collection tool operates on OSM datasets. This introduces three "
    "compounding problems:"
)
problems = [
    ("Coverage gaps", "Large geographies — particularly rural Africa, South Asia, and conflict zones — have little to no road data in OSM."),
    ("Data staleness", "OSM edits in low-activity regions can be years out of date, missing new roads, road closures, or changed classifications."),
    ("Attribute incompleteness", "Even where OSM roads exist, attributes like surface condition, width, and accurate speed limits are frequently missing."),
]
for title_text, detail in problems:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(title_text + ": ")
    run.bold = True
    p.add_run(detail)

doc.add_paragraph(
    "DataGen solves these gaps by treating satellite imagery as the ground truth and OSM "
    "as a supplementary, cross-validation source rather than the primary data input."
)

# ── 3. Solution Architecture ────────────────────────────────────────────────
add_heading(doc, "3. Solution Architecture")
doc.add_paragraph("The system is composed of six layers:")

layers = [
    ("1", "Product API", "FastAPI REST endpoints for AOI submission, job status polling, and GeoJSON result retrieval."),
    ("2", "Job Queue", "Celery + Redis async task queue for long-running inference jobs. Flower UI for monitoring."),
    ("3", "Imagery Ingest", "AOI → tile grid (mercantile). Pluggable tile fetcher: ESRI World Imagery (default), Bing, Planet NICFI, Maxar."),
    ("4", "CRESI Pipeline", "Existing research pipeline: inference (ResNet34 U-Net), skeletonization, graph extraction, speed inference."),
    ("5", "Attribute Enrichment", "Road type (speed-bin taxonomy), width (mask distance transform), surface condition (heuristic v1)."),
    ("6", "OSM Merge & Export", "Spatial diff against OSM, gap tagging, GeoJSON FeatureCollection export, backend API push."),
]

table = doc.add_table(rows=1, cols=3)
table.style = "Table Grid"
hdr = table.rows[0].cells
hdr[0].text = "#"
hdr[1].text = "Layer"
hdr[2].text = "Description"
for cell in hdr:
    cell.paragraphs[0].runs[0].bold = True

for row_data in layers:
    row = table.add_row()
    for cell, text in zip(row.cells, row_data):
        cell.text = text

doc.add_paragraph()

# ── 4. Pipeline Detail ──────────────────────────────────────────────────────
add_heading(doc, "4. Pipeline Detail")

add_heading(doc, "4.1  AOI Ingestion", level=2)
doc.add_paragraph(
    "The user submits a GeoJSON Feature with a Polygon geometry. The ingest layer converts "
    "this to a Web Mercator tile grid at zoom level 18 (~0.6m/px native resolution). Tiles "
    "are fetched in parallel from the configured imagery provider, assembled into a single "
    "georeferenced GeoTIFF mosaic using rasterio, and reprojected to match the CRESI model's "
    "expected input format (8-bit RGB, 0.3m GSD target)."
)

add_heading(doc, "4.2  CRESI Inference Pipeline", level=2)
doc.add_paragraph(
    "The assembled mosaic is sliced into overlapping 512×512 chips and fed through the "
    "trained ResNet34 U-Net segmentation model. The model outputs an 8-class probability "
    "map where each class corresponds to a speed bin. Predictions are stitched, "
    "skeletonized (04_skeletonize.py), converted to a NetworkX road graph "
    "(05_wkt_to_G.py), and annotated with travel time and speed estimates "
    "(06_infer_speed.py)."
)

add_heading(doc, "4.3  Road Attribute Enrichment", level=2)
attrs = [
    ("Road type", "Speed bin → taxonomy: highway (>65 mph), primary (50–65), secondary (35–50), tertiary (25–35), track (15–25), path (<15)."),
    ("Road width", "Medial axis distance transform on the segmentation mask yields pixel width. Multiplied by GSD (0.3 m/px default) gives width in metres. Defaults to road-type average when mask data is absent."),
    ("Surface condition", "Heuristic v1: high speed + wide → paved; low speed + narrow → unpaved. A supervised ML classifier is planned for Phase 6 using labelled ground-truth samples."),
    ("Confidence score", "Per-edge mean model output probability across the mask pixels contributing to that edge."),
]
for attr, desc in attrs:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(attr + ": ")
    run.bold = True
    p.add_run(desc)

add_heading(doc, "4.4  OSM Merge & Gap Detection", level=2)
doc.add_paragraph(
    "After enrichment, the CRESI output is spatially compared against the OSM road network "
    "fetched via the Overpass API (osmnx) for the same AOI. A 15-metre buffer threshold "
    "determines whether a CRESI-detected edge has a corresponding OSM road:"
)
sources = [
    ("satellite", "Edge detected by CRESI with no OSM counterpart within 15 m. Flagged osm_gap: true."),
    ("merged", "Edge present in both CRESI and OSM. CRESI attributes applied to OSM geometry."),
    ("osm", "Road present in OSM but not detected by CRESI (e.g. below imagery resolution, occluded)."),
]
for src, desc in sources:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(f'source: "{src}": ')
    run.bold = True
    p.add_run(desc)

# ── 5. API Reference ────────────────────────────────────────────────────────
add_heading(doc, "5. API Reference (Phase 1)")

endpoints = [
    ("POST /jobs", "Submit a new job. Body: AOI GeoJSON, imagery provider, options. Returns: job_id, estimated tiles, queue status."),
    ("GET /jobs/{id}", "Poll job status. Returns: status enum, progress %, current step, error (if failed)."),
    ("GET /jobs/{id}/results", "Retrieve completed GeoJSON FeatureCollection. Returns 409 if job not yet complete."),
    ("DELETE /jobs/{id}", "Cancel a running job."),
    ("GET /health", "Service health check."),
]

table2 = doc.add_table(rows=1, cols=2)
table2.style = "Table Grid"
hdr2 = table2.rows[0].cells
hdr2[0].text = "Endpoint"
hdr2[1].text = "Description"
for cell in hdr2:
    cell.paragraphs[0].runs[0].bold = True
for ep, desc in endpoints:
    row = table2.add_row()
    row.cells[0].text = ep
    row.cells[1].text = desc

doc.add_paragraph()

# ── 6. Road Inventory GeoJSON Schema ───────────────────────────────────────
add_heading(doc, "6. Road Inventory GeoJSON Schema")
doc.add_paragraph("Each road feature in the output FeatureCollection carries the following properties:")

schema_fields = [
    ("road_type", "string", "highway / primary / secondary / tertiary / track / path / unclassified"),
    ("surface", "string", "paved / unpaved"),
    ("width_m", "float", "Estimated road width in metres"),
    ("speed_mph", "float", "Inferred speed limit in mph"),
    ("travel_time_s", "float", "Edge traversal time in seconds"),
    ("length_m", "float", "Edge length in metres"),
    ("confidence", "float", "Model confidence 0–1"),
    ("source", "string", "satellite / merged / osm"),
    ("osm_gap", "boolean", "True if no OSM road found within 15 m buffer"),
    ("imagery_date", "string", "YYYY-MM of imagery used"),
    ("model_version", "string", "Model identifier, e.g. cresi-sn5-v1"),
]

table3 = doc.add_table(rows=1, cols=3)
table3.style = "Table Grid"
h3 = table3.rows[0].cells
h3[0].text = "Field"
h3[1].text = "Type"
h3[2].text = "Notes"
for cell in h3:
    cell.paragraphs[0].runs[0].bold = True
for field, ftype, notes in schema_fields:
    row = table3.add_row()
    row.cells[0].text = field
    row.cells[1].text = ftype
    row.cells[2].text = notes

doc.add_paragraph()

# ── 7. Imagery Provider Strategy ───────────────────────────────────────────
add_heading(doc, "7. Imagery Provider Strategy")

imagery_rows = [
    ("ESRI World Imagery", "0.3–0.5 m urban", "Free", "Phase 1–2 bootstrap and testing"),
    ("Bing Maps", "0.3–0.5 m", "Free (research)", "Fallback provider"),
    ("Planet NICFI", "4.77 m", "Free (tropics)", "Developing nation coverage, Phase 3+"),
    ("Maxar SecureWatch", "0.3 m", "Commercial", "Production high-resolution, Phase 3+"),
]

table4 = doc.add_table(rows=1, cols=4)
table4.style = "Table Grid"
h4 = table4.rows[0].cells
for cell, txt in zip(h4, ["Provider", "Resolution", "Cost", "Use case"]):
    cell.text = txt
    cell.paragraphs[0].runs[0].bold = True
for row_data in imagery_rows:
    row = table4.add_row()
    for cell, text in zip(row.cells, row_data):
        cell.text = text

doc.add_paragraph()

# ── 8. Technology Stack ─────────────────────────────────────────────────────
add_heading(doc, "8. Technology Stack")

stack = [
    ("API framework", "FastAPI + Uvicorn"),
    ("Task queue", "Celery 5 + Redis 7"),
    ("Queue monitor", "Flower"),
    ("Deep learning", "PyTorch (existing CRESI model: ResNet34 U-Net)"),
    ("Graph processing", "NetworkX"),
    ("Spatial operations", "Shapely, rasterio, GDAL"),
    ("OSM integration", "osmnx + Overpass API"),
    ("Tile math", "mercantile"),
    ("Data validation", "Pydantic v2"),
    ("Containerisation", "Docker + Docker Compose"),
    ("Geo output format", "GeoJSON (RFC 7946)"),
]

table5 = doc.add_table(rows=1, cols=2)
table5.style = "Table Grid"
h5 = table5.rows[0].cells
h5[0].text = "Component"
h5[1].text = "Technology"
for cell in h5:
    cell.paragraphs[0].runs[0].bold = True
for comp, tech in stack:
    row = table5.add_row()
    row.cells[0].text = comp
    row.cells[1].text = tech

doc.add_paragraph()

# ── 9. Phased Roadmap Summary ───────────────────────────────────────────────
add_heading(doc, "9. Phased Roadmap Summary")

phases = [
    ("Phase 1 — Foundation", "Weeks 1–3", "FastAPI + Celery, AOI tile ingestion, GeoJSON export, Docker Compose"),
    ("Phase 2 — Enrichment", "Weeks 4–5", "Road type, width, surface condition attributes"),
    ("Phase 3 — OSM Integration", "Weeks 5–6", "OSM diff, gap detection, merged output"),
    ("Phase 4 — Backend Integration", "Week 7", "Push connector to existing data collection API"),
    ("Phase 5 — Production Hardening", "Weeks 8–10", "Monitoring, retry logic, AOI size limits, caching"),
    ("Phase 6 — Model Improvement", "Months 3–4", "Retrain on Planet NICFI, surface classifier, Sentinel-2 fallback"),
]

table6 = doc.add_table(rows=1, cols=3)
table6.style = "Table Grid"
h6 = table6.rows[0].cells
for cell, txt in zip(h6, ["Phase", "Target", "Key deliverables"]):
    cell.text = txt
    cell.paragraphs[0].runs[0].bold = True
for row_data in phases:
    row = table6.add_row()
    for cell, text in zip(row.cells, row_data):
        cell.text = text

doc.add_paragraph()

# ── 10. Known Risks & Mitigations ──────────────────────────────────────────
add_heading(doc, "10. Known Risks & Mitigations")

risks = [
    ("Imagery TOS", "ESRI/Bing tiles carry usage restrictions for commercial products.",
     "Evaluate Planet NICFI and Maxar for production; keep provider layer pluggable."),
    ("Model resolution mismatch", "CRESI trained at 0.3 m GSD; lower-res imagery degrades detection accuracy.",
     "Validate with ESRI tiles first; plan Sentinel-2 fallback model for Phase 6."),
    ("Surface condition accuracy", "Heuristic v1 will misclassify edge cases (e.g. paved rural tracks).",
     "Log and flag low-confidence edges; add ML classifier in Phase 6 with ground-truth labels."),
    ("Large AOI performance", "City-scale AOIs can produce thousands of tiles and hours of inference.",
     "Auto-split large AOIs; add tile-level result caching; expose progress streaming."),
    ("OSM licence", "ODbL licence on OSM data may require share-alike on derived products.",
     "Legal review required before shipping merged OSM+satellite output to commercial clients."),
]

table7 = doc.add_table(rows=1, cols=3)
table7.style = "Table Grid"
h7 = table7.rows[0].cells
for cell, txt in zip(h7, ["Risk", "Description", "Mitigation"]):
    cell.text = txt
    cell.paragraphs[0].runs[0].bold = True
for risk, desc, mit in risks:
    row = table7.add_row()
    row.cells[0].text = risk
    row.cells[1].text = desc
    row.cells[2].text = mit

doc.add_paragraph()

# ── 11. Next Immediate Steps ────────────────────────────────────────────────
add_heading(doc, "11. Next Immediate Steps")
steps = [
    "Fix JSON syntax error in cresi/configs/sn5_baseline.json (colon inside key name on line 6).",
    "Wire CRESI pipeline steps 02–06 into the Celery task (_run_cresi placeholder in tasks.py).",
    "Validate ESRI tile fetch → mosaic → CRESI inference on a small test AOI (≤1 km²).",
    "Confirm backend API schema with the data collection team and implement schema transform in cresi/backend/connector.py.",
    "Conduct legal review of ESRI tile TOS and OSM ODbL share-alike implications.",
    "Set repository to private on GitHub (see Section 12).",
]
for step in steps:
    doc.add_paragraph(step, style="List Number")

# ── 12. Repository Privacy ──────────────────────────────────────────────────
add_heading(doc, "12. Repository Privacy")
doc.add_paragraph(
    "The repository (lazieinstein/datagen) is currently a public fork. To restrict visibility:"
)
priv_steps = [
    "Navigate to https://github.com/lazieinstein/datagen/settings",
    'Scroll to the "Danger Zone" section at the bottom of the General settings page.',
    'Click "Change repository visibility" → select "Make private" → confirm.',
    "This action is only available to repository owners and organisation admins.",
    "Note: forking history is retained internally; GitHub does not notify the upstream repository of the visibility change.",
]
for s in priv_steps:
    doc.add_paragraph(s, style="List Number")

doc.add_paragraph()
footer = doc.add_paragraph()
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.add_run(
    f"DataGen Preliminary Design Document  ·  CONFIDENTIAL  ·  {datetime.date.today().strftime('%B %Y')}"
).font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)

doc.save("docs/DataGen_Preliminary_Documentation.docx")
print("Generated: docs/DataGen_Preliminary_Documentation.docx")
