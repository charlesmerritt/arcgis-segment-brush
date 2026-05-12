# ArcGIS Segment Brush — Idea

> Project: arcgis-segment-brush
> Created: 2026-05-12
> Phase: project-startup

## Core Idea

An interactive "Magic Wand for GIS" tool that runs natively inside ArcGIS Pro.
The user paints approximate boundaries around objects in aerial/satellite imagery,
and segmentation algorithms snap the rough sketch onto the actual edges in the
image, producing clean polygons automatically.

The pain point: a GIS professor was spending hours manually digitizing a property
by hand-tracing each patch of trees, each field, each land cover boundary.
The computer can *see* those edges — it just needs to be told where to look.

### How it works

1. **Paint** — User activates a brush tool, paints closed loops along the
   approximate edges of objects they want to delineate. Scroll wheel adjusts
   brush radius. Multiple objects can be painted before processing.
2. **Segment** — On "Process All", the algorithm extracts raster pixels around
   each painted stroke, computes edge gradients, and snaps the rough stroke
   onto the real image edges using watershed segmentation.
3. **Refine** — Each candidate polygon is previewed. The user accepts, rejects,
   or re-paints for refinement on a per-polygon basis.
4. **Smooth** — A slider controls polygon smoothing magnitude (Douglas-Peucker
   simplification / buffer smoothing) applied before final output.
5. **Output** — Accepted polygons are written to a geodatabase feature class
   with metadata attributes.

## Target Users

### Primary: GIS professor + grad students
- Research workflows at a university
- Delineating land cover features (tree canopy, wetlands, impervious surfaces,
  agricultural fields) from NAIP imagery for publications and grants
- Need precision and repeatability
- Comfortable with ArcGIS Pro, not necessarily with Python scripting

### Secondary: Undergrad GIS students
- Learning remote sensing and spatial analysis
- Need intuitive tools that don't require coding
- If the tool works well, it becomes a teaching instrument in GIS courses

## Current Alternatives

**Manual polygon tracing with ArcGIS Pro Edit tools.** This is the primary pain
point. The professor was literally hand-tracing every tree stand and field
boundary on a property — obvious edges the computer should be able to find.

Other existing approaches and why they fall short:
- **Raster to Polygon GP tool** — requires reclassification first, whole-image,
  can't target individual objects
- **ISO Cluster Unsupervised Classification** — whole-image, produces thematic
  classes not individual object polygons
- **Segment Mean Shift GP tool** — slow, whole-image, not interactive
- **Image Classification Wizard** — training-sample based, overkill for
  "I just want to grab that one tree stand"

The gap: no tool lets you interactively point at a thing in imagery and get
a clean polygon of just that thing.
