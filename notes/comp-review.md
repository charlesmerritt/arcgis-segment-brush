# Competitive Review

> Project: arcgis-segment-brush
> Created: 2026-05-12
> Search tools used: context7 (arcgis-python-api), training knowledge

## Open Source Alternatives

### Raster Vision (azavea/raster-vision)
- **URL:** https://github.com/azavea/raster-vision
- **What it does well:** Full pipeline for training CV models on satellite/aerial
  imagery. Supports chip classification, object detection, semantic segmentation.
  Well-maintained, PyTorch-based.
- **Gaps:** Requires training data and model training. Not interactive — it's a
  batch processing framework. No ArcGIS integration. Overkill for "grab that one
  tree stand."
- **What we learn:** Their semantic segmentation pipeline architecture is well
  designed. Their chip-based windowed reading approach is similar to ours.

### Segment Anything Model (Meta AI / segment-anything)
- **URL:** https://github.com/facebookresearch/segment-anything
- **What it does well:** One-click or box-prompt segmentation of arbitrary objects.
  State-of-the-art zero-shot segmentation. Works on any image.
- **Gaps:** Requires GPU, large model download (~2.5GB), not integrated with GIS
  workflows. No ArcGIS Pro integration. Returns masks not polygons. No geodatabase
  output, no coordinate system awareness.
- **What we learn:** SAM is the v3 vision — if we architect the segmentation step
  as a pluggable interface, SAM becomes a backend option later.

### QGIS Semi-Automatic Classification Plugin (SCP)
- **URL:** https://fromgistors.blogspot.com/p/semi-automatic-classification-plugin.html
- **What it does well:** Free, open source, integrated into QGIS. Supports
  supervised classification with ROI drawing. Band math, spectral signatures.
- **Gaps:** Classification-based (whole image into classes), not object-based
  interactive segmentation. QGIS-only. Workflow is "train a classifier" not
  "paint a boundary and snap it."
- **What we learn:** Their ROI drawing UX is relevant — how they handle training
  area selection on the map canvas.

### scikit-image interactive segmentation examples
- **URL:** https://scikit-image.org/docs/stable/auto_examples/segmentation/
- **What it does well:** Excellent algorithm implementations (watershed, SLIC,
  felzenszwalb, random walker). Well-documented. Fast.
- **Gaps:** Library, not a tool. No GIS integration. No map canvas interaction.
  You have to write the glue code yourself.
- **What we learn:** This IS our segmentation backend. We're building the GIS
  glue layer on top of scikit-image.

## Commercial Products

### ArcGIS Pro Image Classification Wizard
- **URL:** Built into ArcGIS Pro (Image Analyst extension)
- **Pricing:** Included with Image Analyst license (~$X,XXX/year)
- **Strengths:** Native ArcGIS integration. Supports supervised and unsupervised
  classification. Deep learning integration with ArcGIS-trained models.
- **Gaps:** Training-sample workflow — you define training areas, train a
  classifier, classify the whole image, then convert to polygons. It's a
  multi-step, whole-image process. Not interactive object-level segmentation.
  Requires Image Analyst extension license.
- **Differentiation:** We're "paint one object → get one polygon" vs their
  "train a model → classify everything." Completely different use case.

### Trimble eCognition
- **URL:** https://geospatial.trimble.com/en/products/software/trimble-ecognition
- **Pricing:** ~$10K+ license
- **Strengths:** Industry standard for object-based image analysis (OBIA).
  Powerful rule-based segmentation. Multi-scale segmentation.
- **Gaps:** Expensive. Steep learning curve. Separate application (not in ArcGIS).
  Batch-oriented, not interactive paint-to-polygon.
- **Differentiation:** eCognition is the "enterprise OBIA platform." We're the
  "quick interactive tool for when you just need to grab some polygons." Different
  market entirely — a professor doesn't need eCognition to digitize a property.

### Photoshop / GIMP Magic Wand + Georeferencing
- **Strengths:** Intuitive UX that people understand. The mental model we're borrowing.
- **Gaps:** Not GIS-aware. No coordinate systems. No geodatabase output. You'd have
  to export, georeference, trace, import — absurd workflow.
- **What we learn:** The UX paradigm. "Paint near an edge, computer finds it."

## Market Summary

The GIS image segmentation space is split between **heavy enterprise tools**
(eCognition, ArcGIS Image Classification) that require training data and batch
workflows, and **research ML frameworks** (Raster Vision, SAM) that require
Python expertise and GPU resources. Nothing fills the gap of a **simple,
interactive, paint-to-polygon tool** that lives natively in ArcGIS Pro.

The closest analogy is Photoshop's magic wand — everyone understands the
interaction model, but nobody has brought it to GIS with coordinate-system-aware
polygon output. That's the opportunity.

Our angle: **lowest possible friction from "I see an edge" to "I have a polygon."**
No training data. No classification. No separate application. Paint, snap, done.
