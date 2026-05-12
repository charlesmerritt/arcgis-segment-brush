# Interface Contract

> Project: arcgis-segment-brush
> Created: 2026-05-12
> Phase: project-startup

## Interface Type

**ArcGIS Pro Python Toolbox (.pyt)** with interactive map tool capability.
Shows up in the Geoprocessing pane like any native tool. The brush interaction
happens on the map canvas via arcpy's tool activation infrastructure.

## Tool Pane (Geoprocessing UI)

### Parameters
1. **Input Raster Layer** — dropdown populated from map TOC (raster layers only)
2. **Output Feature Class** — file picker, new or existing .gdb feature class
3. **Segmentation Method** — dropdown: "Watershed" (v1 only, architected for more)
4. **Smoothing Level** — slider, 0–100 (0 = raw boundary, 100 = maximum generalization)
5. **Brush Radius** — display-only, shows current radius (controlled by scroll wheel)
6. **Activate Brush** — button, enters interactive painting mode
7. **Process All** — button, runs segmentation on all closed loops
8. **Done** — button, exits tool, finalizes output

## Primary Workflow (Happy Path)

### Step 1: Setup
- User has a NAIP raster loaded in ArcGIS Pro map
- Opens Geoprocessing pane → finds "Segment Brush" toolbox → opens tool
- Selects the raster layer from dropdown
- Points output to a new or existing feature class
- Leaves segmentation method as "Watershed"
- Sets smoothing slider to taste (default: 30)
- Clicks "Activate Brush"

### Step 2: Painting
- Cursor changes to a circle brush overlaid on the map
- Scroll wheel adjusts radius — circle resizes in real time
- User clicks on the map to set an **anchor point** (shown as a colored dot)
- Drags along the approximate edge of the object (tree stand, field, etc.)
- A semi-transparent stroke trail appears behind the cursor
- When the cursor comes within **snap tolerance** of the anchor point:
  - Visual snap indicator (anchor dot highlights)
  - Releasing the mouse auto-closes the loop
  - Closed loop turns solid (different color than WIP strokes)
- User repeats for as many objects as they want
- Each closed loop is numbered on-screen ("1", "2", "3"...)

### Step 3: Processing
- User clicks "Process All"
- Progress bar appears in the tool pane
- For each closed loop (parallelizable later):
  1. Compute bounding extent of the stroke + buffer (1.5× brush radius)
  2. Extract raster pixels via arcpy.RasterToNumPyArray (windowed)
  3. Compute Sobel gradient magnitude on the RGB image
  4. Create marker array: stroke pixels = boundary markers
  5. Run watershed segmentation with edge-weighted gradient
  6. Extract the boundary that best matches the stroke path
  7. Convert contour to polygon geometry
  8. Apply smoothing per slider value
  9. Preview polygon as yellow dashed outline on map

### Step 4: Review
- All candidate polygons are shown on the map as dashed outlines
- Tool pane shows a list: "Object 1 ✓/✗", "Object 2 ✓/✗", etc.
- User clicks each to highlight it on the map
- For each polygon:
  - **Accept** (✓ or Enter) → polygon turns solid green, queued for write
  - **Reject** (✗ or Delete) → polygon removed, user can re-paint that area
  - **Refine** → user re-paints a tighter stroke, re-processes just that one
- "Accept All" convenience button for when everything looks good

### Step 5: Commit
- User clicks "Done" or all polygons are accepted
- Accepted polygons written to output feature class via arcpy.da.InsertCursor
- Each feature gets attributes:
  - `source_raster` (str): name of the input raster layer
  - `seg_method` (str): "watershed" (v1)
  - `smooth_level` (int): 0–100 value used
  - `area_sq_m` (float): geodesic area
  - `perimeter_m` (float): geodesic perimeter
  - `created_at` (str): ISO 8601 timestamp
- Feature class added to map TOC (if new)
- Tool stays open for another painting session or user closes it

## Error Cases

- **No raster layer in TOC** → tool parameter validation error, message:
  "Add a raster layer to the map before using Segment Brush"
- **Stroke not closed** → visual warning on the unclosed stroke;
  "Process All" skips unclosed strokes with a warning message
- **Raster too large for window** → cap extraction window at a configurable
  max size (e.g., 4096×4096 pixels), warn if brush area exceeds it
- **No closed loops when Process All clicked** → message:
  "Paint at least one closed boundary before processing"
- **Output FC is read-only or locked** → standard arcpy error, surfaced in tool messages
- **scikit-image not installed** → tool validation catches this at load time,
  provides install instructions

## Visual Design

- **Brush cursor**: white circle with 1px black outline, radius matches brush size
- **Anchor point**: bright magenta dot, 8px
- **WIP stroke**: semi-transparent blue, 3px dashed
- **Closed loop**: solid blue, 2px, numbered label
- **Candidate polygon (preview)**: yellow dashed outline, 2px
- **Accepted polygon**: solid green fill at 20% opacity, green outline 2px
- **Rejected polygon**: fades out with animation (or just disappears)
