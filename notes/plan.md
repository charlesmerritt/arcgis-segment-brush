# Development Plan

> Project: arcgis-segment-brush
> Created: 2026-05-12
> Template: ~/templates/python/default
> Stack: Python 3.11+ / ArcPy / scikit-image / scipy / shapely / numpy

## Project Summary

An interactive paint-to-polygon segmentation tool for ArcGIS Pro that lets users
paint approximate boundaries on aerial imagery and get clean, edge-snapped polygons
automatically. Originated from a GIS professor's pain of manually digitizing
land cover boundaries. "Magic Wand for GIS" — lowest friction path from
"I see an edge" to "I have a polygon."

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   ArcGIS Pro                         │
│  ┌─────────────┐  ┌──────────────────────────────┐  │
│  │  Toolbox UI  │  │      Map Canvas              │  │
│  │  (.pyt)      │  │  ┌────────────────────────┐  │  │
│  │              │  │  │   Brush Overlay         │  │  │
│  │ [Parameters] │  │  │   (paint strokes)       │  │  │
│  │ [Process All]│  │  │   (polygon previews)    │  │  │
│  │ [Accept/Rej] │  │  └────────────────────────┘  │  │
│  └──────┬───────┘  └──────────┬───────────────────┘  │
│         │                     │                       │
│         ▼                     ▼                       │
│  ┌──────────────┐    ┌──────────────┐                │
│  │ feature_     │    │ raster_io.py │                │
│  │ output.py    │    │ (arcpy read) │                │
│  │ (arcpy write)│    └──────┬───────┘                │
│  └──────┬───────┘           │                        │
└─────────┼───────────────────┼────────────────────────┘
          │                   │
          ▼                   ▼
   ┌──────────┐      ┌───────────────┐
   │ .gdb     │      │ numpy ndarray │
   │ Feature  │      │ (rows,cols,3) │
   │ Class    │      └───────┬───────┘
   └──────────┘              │
                             ▼
                    ┌─────────────────┐
                    │ segmentation.py │  ← NO arcpy dependency
                    │                 │
                    │ 1. edge_gradient│  (scipy.ndimage.sobel)
                    │ 2. markers      │  (stroke → seed array)
                    │ 3. watershed    │  (skimage.segmentation)
                    │ 4. contour      │  (skimage.measure)
                    │ 5. smooth       │  (shapely simplify/buffer)
                    └─────────────────┘
```

## Milestones

### M1: Core Segmentation Pipeline (Week 1–2)
**Goal:** Given a numpy array and a stroke, produce a refined polygon.
No ArcGIS integration yet — just the algorithm working in isolation.

- [ ] `compute_edge_gradient` — Sobel on RGB, max across bands, normalize
- [ ] `stroke_to_markers` — dilate stroke into boundary markers, flood-fill
      interior/exterior markers, leave ambiguous pixels as 0
- [ ] `run_watershed` — call `skimage.segmentation.watershed` with edge gradient
      and markers
- [ ] `extract_boundary_polygon` — `skimage.measure.find_contours` → shapely Polygon
- [ ] `smooth_polygon` — Douglas-Peucker + buffer smoothing scaled by smooth_level
- [ ] `segment_stroke` — wire the full pipeline together
- [ ] Tests: synthetic image with known edges, verify polygon matches expected shape
- [ ] Tests: edge cases (tiny objects, objects at image border, no clear edge)
- [ ] Benchmark: time the pipeline on 512×512 and 2048×2048 windows

### M2: Brush Session & Coordinate System (Week 2–3)
**Goal:** Full brush session management and coordinate conversion between
map space and pixel space. Still no ArcGIS UI, but all the logic is testable.

- [ ] Brush session refinements: handle edge cases (re-opening a closed stroke,
      deleting individual strokes, stroke selection)
- [ ] `raster_io.extract_raster_window` — arcpy.RasterToNumPyArray with extent
      clipping, band selection, projection handling
- [ ] Map-to-pixel batch conversion for strokes (with buffered extent)
- [ ] `feature_output.create_output_feature_class` — arcpy.CreateFeatureclass
      with schema
- [ ] `feature_output.write_polygon` — shapely → arcpy.Polygon → InsertCursor
- [ ] `feature_output.compute_geodesic_measurements` — area/perimeter in meters
- [ ] Integration tests (marked `@pytest.mark.arcgis`, skipped without license)

### M3: ArcGIS Pro Toolbox Integration (Week 3–4)
**Goal:** The tool works end-to-end inside ArcGIS Pro. User can paint and
get polygons.

- [ ] `SegmentBrushTool.getParameterInfo` — define all GP parameters
- [ ] `SegmentBrushTool.isLicensed` — check for extensions and scikit-image
- [ ] `SegmentBrushTool.updateParameters` — dynamic parameter behavior
- [ ] `SegmentBrushTool.updateMessages` — validation warnings
- [ ] `SegmentBrushTool.execute` — orchestrate the full workflow
- [ ] Interactive brush activation — research and implement the map tool
      mechanism (CIM tool definition vs arcpy.mapping tool vs pythonaddins approach)
- [ ] Brush overlay rendering (circle cursor, stroke trails, closed loop display)
- [ ] Scroll wheel → radius adjustment binding
- [ ] "Process All" → batch segmentation → preview overlay
- [ ] Accept/reject per polygon in the tool pane
- [ ] Output FC added to map TOC

### M4: Polish & Release Prep (Week 4–5)
**Goal:** Ready for the professor to use.

- [ ] Error messages are helpful and specific
- [ ] Progress reporting during batch segmentation
- [ ] Handle edge cases: raster with nodata, very large brush areas, projected
      vs geographic coordinate systems
- [ ] Performance optimization: profile and optimize the hot path
- [ ] Documentation: full README with screenshots, installation guide,
      usage examples
- [ ] User guide: step-by-step walkthrough with annotated screenshots
- [ ] CI/CD: GitHub Actions runs lint + typecheck + tests on every push
- [ ] CHANGELOG entries for all milestones
- [ ] Package: instructions for installing into ArcGIS Pro's Python env

## Testing Strategy

- Each milestone adds tests for its features before moving on
- M1: pure algorithm tests with synthetic images (no arcpy)
- M2: coordinate conversion + arcpy integration tests
- M3: toolbox parameter validation tests
- M4: end-to-end workflow tests in ArcGIS Pro
- Target: full coverage of the segmentation pipeline, meaningful coverage
  of ArcGIS integration points

## Technical Debt Budget

- Track debt in GitHub issues with `tech-debt` label
- Address debt items during milestone transitions, not mid-milestone
- Acceptable debt: placeholder UI elements, hardcoded defaults
- Unacceptable debt: missing error handling in segmentation pipeline,
  untested coordinate conversions, broken ArcGIS integration

## Open Questions

- **Map tool mechanism:** How exactly does ArcGIS Pro allow a Python Toolbox
  to capture mouse events on the map canvas? Options: CIM tool definition,
  tool activation via arcpy, or a hybrid with a Python add-in for the
  interactive component and a .pyt for the GP interface. Needs research in M3.
- **Performance:** Will watershed on a 2048×2048 window be fast enough for
  interactive use? M1 benchmarking will answer this. If too slow, consider
  downsampling the raster window before segmentation.
- **ArcGIS Pro version compatibility:** Tested on 3.x. How far back can we
  support? arcpy API changes between versions may affect raster reading.

## Competitive Positioning

Nothing fills the gap of a simple, interactive, paint-to-polygon tool native
to ArcGIS Pro. Enterprise tools (eCognition) are expensive and batch-oriented.
ArcGIS's own classification tools require training data. We're the lowest-friction
path from "I see a boundary" to "I have a polygon in my geodatabase."
