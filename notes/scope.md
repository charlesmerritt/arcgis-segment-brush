# Scope

> Project: arcgis-segment-brush
> Created: 2026-05-12
> Phase: project-startup

## MVP (v1)

- Python Toolbox (.pyt) that loads in ArcGIS Pro Geoprocessing pane
- User selects an input raster layer and output feature class
- Interactive brush tool activated from the tool pane:
  - Circle brush cursor overlaid on map
  - Scroll wheel adjusts brush radius with visual feedback
  - Click to set anchor point, drag to paint along approximate edge
  - Auto-close when stroke returns within snap tolerance of anchor
  - Multiple closed loops = multiple objects (batch painting)
  - Visual states: WIP stroke (dashed), closed loop (solid)
- "Process All" button segments every painted loop at once
- Segmentation pipeline per loop:
  - Extract raster window around stroke bounding extent
  - Compute edge gradients (Sobel on RGB)
  - Watershed segmentation with stroke as boundary guide
  - Snap rough stroke to actual image edges
  - Apply smoothing (magnitude from slider, 0–100)
- Per-polygon review: accept, reject, or refine each candidate
- Accepted polygons written to file geodatabase feature class
- Metadata attributes: source_raster, seg_method, smooth_level,
  area_sq_m, perimeter_m, created_at
- Works with 3-band RGB imagery (NAIP)

## Future Vision (not building yet)

### v2 — Multi-band & Algorithm Options
- Hyperspectral / multispectral imagery support
- Band selection UI, PCA-based edge detection
- Multiple segmentation algorithms (SLIC, felzenszwalb, mean shift, quickshift)
- Interior-paint mode (flood-fill / region-growing, like Photoshop magic wand)
- Auto-process mode: close loop → segment immediately (if fast enough)

### v3 — Intelligence & Batch
- SAM (Segment Anything Model) integration for one-click segmentation
- Batch mode: paint seeds, segment all simultaneously
- Undo/redo stack for painted strokes
- Refinement mode: paint corrections on candidate boundary, re-segment
- Export to shapefile / GeoJSON / KML
- Performance profiling and GPU acceleration for large rasters
