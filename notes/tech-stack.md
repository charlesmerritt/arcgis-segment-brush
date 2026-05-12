# Tech Stack

> Project: arcgis-segment-brush
> Created: 2026-05-12
> Phase: project-startup

## Runtime Environment

- **ArcGIS Pro 3.x** — host application (provides arcpy, map canvas, GP framework)
- **Python 3.11+** — ArcGIS Pro's bundled Python (via conda env `arcgispro-py3`)
- **Note:** ArcGIS Pro ships its own Python; we can pip-install into it but must
  respect its constraints (no conflicting numpy versions, etc.)

## Core Dependencies

| Package | Role | Rationale |
|---------|------|-----------|
| **arcpy** | Raster I/O, map interaction, feature class output | Ships with ArcGIS Pro, required for native integration |
| **numpy** | Array math, raster↔array conversion | Ships with ArcGIS Pro |
| **scipy** | Edge detection (Sobel/Canny gradients), morphological ops | Likely ships with ArcGIS Pro; lightweight |
| **scikit-image** | Segmentation algorithms (watershed, SLIC, felzenszwalb) | The workhorse — pip install into ArcGIS Pro env |
| **shapely** | Polygon smoothing (simplify, buffer ops) | pip install; may already be present via arcgis package |

## Development Dependencies

| Package | Role |
|---------|------|
| **uv** | Package management (for dev environment outside ArcGIS) |
| **ruff** | Linting + formatting |
| **ty** | Type checking |
| **pytest** | Testing (unit tests run outside ArcGIS with mocked arcpy) |

## Architecture Decisions

### Why scikit-image over arcpy's built-in segmentation?
ArcPy's Segment Mean Shift is a whole-image GP tool — it's slow, not interactive,
and returns a raster not a polygon. scikit-image gives us fine-grained control:
we extract a small window of pixels, run watershed with custom markers derived
from the user's brush stroke, and get contours back in milliseconds.

### Why a Python Toolbox (.pyt) and not an Add-In?
- Python Toolboxes are pure Python — no C#, no ArcGIS Pro SDK, no Visual Studio
- They show up natively in the Geoprocessing pane
- They support `updateParameters` and `updateMessages` for dynamic UI
- The interactive map component will use arcpy's tool infrastructure
- Much lower maintenance burden than a compiled add-in

### Raster Pipeline
```
ArcGIS Raster Layer
  → arcpy.RasterToNumPyArray (windowed read around brush extent)
  → numpy ndarray (rows, cols, 3) for RGB
  → scipy.ndimage.sobel → edge gradient magnitude
  → skimage.segmentation.watershed (brush stroke as markers)
  → contour extraction → shapely Polygon
  → smoothing (Douglas-Peucker + buffer)
  → arcpy.da.InsertCursor → feature class
```

This pipeline is designed so that replacing `3` with `N` bands is a v2 change
localized to the edge gradient computation step.
