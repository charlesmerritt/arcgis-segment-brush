# ArcGIS Segment Brush

Interactive paint-to-polygon segmentation tool for ArcGIS Pro.

**Paint approximate boundaries on aerial imagery → get clean, edge-snapped polygons automatically.**

Think Photoshop's Magic Wand, but for GIS — with coordinate-system-aware polygon output
written directly to a geodatabase feature class.

## How It Works

1. **Paint** — Activate the brush tool, paint closed loops along the approximate edges
   of objects (tree stands, fields, buildings, wetlands) in your imagery
2. **Segment** — Hit "Process All" and the algorithm snaps your rough strokes onto the
   actual image edges using watershed segmentation
3. **Review** — Accept, reject, or refine each candidate polygon individually
4. **Output** — Accepted polygons are written to a feature class with metadata

## Quick Start

### Prerequisites

- ArcGIS Pro 3.x with a Spatial Analyst or Image Analyst license
- Python 3.11+ (ArcGIS Pro's bundled environment)

### Install

```bash
# Clone the repository
git clone https://github.com/charlesmerritt/arcgis-segment-brush.git
cd arcgis-segment-brush

# Install dependencies into ArcGIS Pro's Python environment
# (activate the arcgispro-py3 conda env first)
pip install scikit-image shapely

# Or for development:
uv sync --group dev --group test
```

### Add the Toolbox to ArcGIS Pro

1. Open ArcGIS Pro
2. In the **Geoprocessing** pane → click **Toolboxes** → **Add Toolbox**
3. Navigate to `toolbox/SegmentBrush.pyt`
4. The **Segment Brush** tool appears under the new toolbox

### Use

1. Load a NAIP or other RGB raster into your map
2. Open the **Segment Brush** tool from the Geoprocessing pane
3. Select your raster layer and output feature class
4. Click **Activate Brush** and start painting boundaries
5. Click **Process All** when ready

## Development

```bash
make install    # Install all dependencies
make test       # Run tests
make lint       # Run linters
make format     # Run formatters
make typecheck  # Run type checker
make all        # Run everything
```

## Architecture

```
src/segment_brush/
├── __init__.py          # Package root
├── segmentation.py      # Core algorithm (no arcpy dependency)
├── raster_io.py         # ArcGIS raster → numpy array
├── brush.py             # Brush stroke management
└── feature_output.py    # Polygon → geodatabase feature class

toolbox/
└── SegmentBrush.pyt     # ArcGIS Pro Python Toolbox entry point
```

Key design principle: **the segmentation pipeline has zero arcpy dependency**.
It works entirely with numpy arrays and shapely geometries. The arcpy layer
is isolated in `raster_io.py`, `feature_output.py`, and the `.pyt` toolbox.
This allows testing the core algorithm without an ArcGIS Pro license.

## License

MIT
