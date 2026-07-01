"""ArcGIS Segment Brush — Python Toolbox.

This .pyt file is the entry point that ArcGIS Pro loads. It defines the
toolbox and its tools, which appear in the Geoprocessing pane.

To install: copy this toolbox folder to a location, then in ArcGIS Pro:
  Geoprocessing pane → Toolboxes → Add Toolbox → select SegmentBrush.pyt
"""

from __future__ import annotations

import os
import sys

import arcpy

# Add the project's src/ directory to the Python path so we can import
# the segment_brush package. This handles the case where the toolbox
# is loaded from its installed location.
_toolbox_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(os.path.dirname(_toolbox_dir), "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Module-level brush session — populated by the interactive brush component
# (to be implemented in M3). execute() processes whatever closed strokes
# are present here. Reset between tool runs via postExecute.
_active_session = None  # BrushSession | None

# Read-window sizing (in pixels) for the adaptive fuzzy-select seed fill. The
# window starts at the initial size and doubles until the filled region no
# longer touches the window edge (the whole object is contained) or the max is
# reached. A magic-wand fill has no predetermined size, so this avoids both
# reading huge windows for small objects and clipping large ones.
_SEED_INITIAL_WINDOW_PX = 512
_SEED_MAX_WINDOW_PX = 8192


class Toolbox:
    """ArcGIS Segment Brush Toolbox."""

    def __init__(self) -> None:
        self.label = "Segment Brush"
        self.alias = "segmentbrush"
        self.tools = [SegmentBrushTool]


class SegmentBrushTool:
    """Interactive paint-to-polygon segmentation tool.

    Allows the user to paint approximate boundaries on imagery,
    then uses segmentation algorithms to snap the boundary to
    actual image edges and produce clean polygon features.
    """

    def __init__(self) -> None:
        self.label = "Segment Brush"
        self.description = (
            "Paint approximate boundaries on imagery and automatically "
            "generate clean polygons snapped to image edges using "
            "segmentation algorithms."
        )
        self.canRunInBackground = False
        self.category = "Image Segmentation"

    def getParameterInfo(self) -> list:
        """Define tool parameters.

        Returns
        -------
        list of arcpy.Parameter
            The tool's parameter definitions.
        """

        # 0: input_raster (GPRasterLayer) — raster layer from map TOC
        input_raster = arcpy.Parameter(
            displayName="Input Raster",
            name="input_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input",
        )

        # 1: output_fc (DEFeatureClass) — output polygon feature class
        output_fc = arcpy.Parameter(
            displayName="Output Feature Class",
            name="output_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output",
        )

        # 2: seg_method (GPString) — segmentation method dropdown
        seg_method = arcpy.Parameter(
            displayName="Segmentation Method",
            name="seg_method",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        seg_method.filter.type = "ValueList"
        seg_method.filter.list = ["Watershed", "SLIC", "Felzenszwalb", "Quickshift"]
        seg_method.value = "Watershed"

        # 3: smooth_level (GPLong) — smoothing slider 0–100
        smooth_level = arcpy.Parameter(
            displayName="Smooth Level",
            name="smooth_level",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input",
        )
        smooth_level.filter.type = "Range"
        smooth_level.filter.list = [0, 100]
        smooth_level.value = 50

        # 4: brush_radius (GPDouble) — display-only, current brush radius
        brush_radius = arcpy.Parameter(
            displayName="Brush Radius",
            name="brush_radius",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input",
        )
        brush_radius.value = 10.0

        # 5: seed_points (GPFeatureRecordSetLayer) — interactive "magic wand"
        # seeds. A Feature Set gives us ArcGIS Pro's *native* sketch tool on the
        # map canvas from pure Python — no .NET SDK add-in required. Each point
        # the user drops is a seed for fuzzy-select region growing. This is the
        # low-friction path to Photoshop magic-wand behavior inside a .pyt.
        seed_points = arcpy.Parameter(
            displayName="Seed Points (Magic Wand)",
            name="seed_points",
            datatype="GPFeatureRecordSetLayer",
            parameterType="Optional",
            direction="Input",
        )
        seed_points.filter.list = ["Point"]

        # 6: tolerance (GPLong) — fuzziness slider 0–100 (the magic-wand knob).
        # Distinct from smooth_level: tolerance controls how far the region
        # grows by color similarity; smooth_level controls boundary smoothing.
        tolerance = arcpy.Parameter(
            displayName="Fuzziness / Tolerance",
            name="tolerance",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input",
        )
        tolerance.filter.type = "Range"
        tolerance.filter.list = [0, 100]
        tolerance.value = 30

        return [
            input_raster,
            output_fc,
            seg_method,
            smooth_level,
            brush_radius,
            seed_points,
            tolerance,
        ]

    def isLicensed(self) -> bool:
        """Check whether the tool is licensed to execute.

        We require:
        - Spatial Analyst OR Image Analyst (for raster access)
        - scikit-image installed in the Python environment
        """
        try:
            import arcpy
            has_extension = (
                arcpy.CheckExtension("Spatial") == "Available"
                or arcpy.CheckExtension("ImageAnalyst") == "Available"
            )
        except Exception:
            has_extension = False

        try:
            import skimage  # noqa: F401
            has_skimage = True
        except ImportError:
            has_skimage = False

        return has_extension and has_skimage

    def updateParameters(self, parameters: list) -> None:
        """Modify parameter values and properties.

        Called whenever a parameter is changed in the tool dialog.
        Used for dynamic validation (e.g., populate method dropdown).
        """

        input_raster = parameters[0]
        output_fc = parameters[1]

        # Auto-populate output_fc when the user picks a raster but hasn't set an output yet
        if input_raster.altered and not output_fc.altered:
            raster_path = input_raster.valueAsText
            if raster_path:
                base_name = os.path.splitext(os.path.basename(raster_path))[0]
                workspace = arcpy.env.workspace or os.path.dirname(raster_path)
                output_fc.value = os.path.join(workspace, base_name + "_segments")

    def updateMessages(self, parameters: list) -> None:
        """Modify messages for each parameter.

        Called after updateParameters. Used to add warnings/errors
        (e.g., "scikit-image not installed").
        """

        input_raster = parameters[0]

        # Surface a hard error if scikit-image is not installed
        try:
            import skimage  # noqa: F401
        except ImportError:
            input_raster.setErrorMessage(
                "scikit-image is not installed in this Python environment. "
                "Run: pip install scikit-image"
            )
            return

        # Warn if neither required extension is licensed
        has_extension = (
            arcpy.CheckExtension("Spatial") == "Available"
            or arcpy.CheckExtension("ImageAnalyst") == "Available"
        )
        if not has_extension:
            input_raster.setWarningMessage(
                "Neither Spatial Analyst nor Image Analyst extension is available. "
                "Raster access may fail at execution."
            )

    def execute(self, parameters: list, messages: object) -> None:
        """Run the tool.

        This is the main execution method. In v1, it orchestrates:
        1. Read parameters
        2. Initialize the brush session
        3. Enter interactive painting mode (map tool activation)
        4. On "Process All": run segmentation pipeline for each closed stroke
        5. Display previews for review
        6. Write accepted polygons to the output feature class

        NOTE: The interactive brush component (mouse events on the map canvas)
        requires ArcGIS Pro's CIM/tool infrastructure. The exact mechanism
        (arcpy.mapping tool activation vs CIM tool definition) will be
        determined during M1 implementation.
        """
        from segment_brush.brush import BrushSession, StrokeState
        from segment_brush.feature_output import (
            create_output_feature_class,
            write_polygon,
        )
        from segment_brush.raster_io import extract_raster_window, map_coords_to_pixel
        from segment_brush.segmentation import (
            SegmentationParams,
            segment_from_seed_adaptive,
            segment_stroke,
        )

        # 1. Read parameters
        input_raster_path = parameters[0].valueAsText
        output_fc_path = parameters[1].valueAsText
        seg_method = parameters[2].valueAsText or "Watershed"
        smooth_level = int(parameters[3].value) if parameters[3].value is not None else 50
        brush_radius = float(parameters[4].value) if parameters[4].value is not None else 10.0
        seed_points = parameters[5].value
        tolerance = int(parameters[6].value) if parameters[6].value is not None else 30

        # 2. Build segmentation params (shared by both input modes)
        seg_params = SegmentationParams(
            method=seg_method.lower(),
            smooth_level=smooth_level,
            tolerance=tolerance,
        )

        # 3. Gather inputs. Two modes are supported:
        #    - Painted strokes (watershed) from the interactive brush add-in.
        #    - Seed points (fuzzy select / magic wand) from the native sketch.
        global _active_session
        if _active_session is None:
            _active_session = BrushSession()
        session = _active_session
        closed_strokes = session.get_processable_strokes()
        seed_coords = self._read_seed_points(seed_points)

        if not closed_strokes and not seed_coords:
            messages.addWarningMessage(
                "No inputs found. Either paint a closed boundary with the brush "
                "or drop one or more Seed Points before running the tool."
            )
            return

        # 4. Ensure the output feature class exists
        raster_obj = arcpy.Raster(input_raster_path)
        spatial_ref = raster_obj.spatialReference

        if not arcpy.Exists(output_fc_path):
            messages.addMessage(f"Creating output feature class: {output_fc_path}")
            create_output_feature_class(output_fc_path, spatial_ref)

        source_raster_name = os.path.basename(input_raster_path)
        polygon_count = 0

        # 5a. Process each closed stroke through the watershed pipeline
        for i, stroke in enumerate(closed_strokes, start=1):
            messages.addMessage(f"Processing stroke {i} of {len(closed_strokes)}...")

            extent = stroke.extent
            if extent is None:
                messages.addWarningMessage(f"Stroke {i} has no points — skipping.")
                continue

            # Extract the raster window clipped to the stroke's bounding extent
            raster_window = extract_raster_window(raster_obj, extent)

            # Convert stroke map coords → pixel (row, col) coords
            stroke_pixels = session.to_pixel_array(
                stroke, raster_window.origin, raster_window.cell_size
            )
            brush_radius_px = max(1, int(brush_radius / raster_window.cell_size[0]))

            # Run the full segmentation pipeline for this stroke
            result = segment_stroke(
                raster_window.pixels, stroke_pixels, brush_radius_px, seg_params
            )

            # Write the refined polygon to the output feature class
            write_polygon(
                output_fc_path,
                result.polygon,
                raster_window.spatial_reference,
                source_raster=source_raster_name,
                seg_method=seg_method,
                smooth_level=smooth_level,
            )

            stroke.state = StrokeState.PROCESSED
            polygon_count += 1
            messages.addMessage(
                f"  \u2192 Polygon {polygon_count} written "
                f"(confidence: {result.confidence:.2f})"
            )

        # 5b. Process each seed point through the adaptive fuzzy-select pipeline.
        # The read window grows around the seed until the filled region is fully
        # contained (or the max window is hit), so large objects aren't clipped
        # and small ones don't pay for an oversized read.
        for i, (seed_x, seed_y) in enumerate(seed_coords, start=1):
            messages.addMessage(
                f"Processing seed {i} of {len(seed_coords)} "
                f"(tolerance={tolerance})..."
            )

            provider = self._make_seed_window_provider(
                raster_obj,
                seed_x,
                seed_y,
                extract_raster_window,
                map_coords_to_pixel,
            )

            try:
                result, window = segment_from_seed_adaptive(
                    provider,
                    tolerance,
                    seg_params,
                    initial_window_px=_SEED_INITIAL_WINDOW_PX,
                    max_window_px=_SEED_MAX_WINDOW_PX,
                )
            except ValueError as exc:
                messages.addWarningMessage(f"  Seed {i} produced no region: {exc}")
                continue

            if result.clipped:
                messages.addWarningMessage(
                    f"  Seed {i}: region still reached the "
                    f"{_SEED_MAX_WINDOW_PX}px window edge \u2014 the polygon may be "
                    "clipped. Try a lower tolerance or a more central seed."
                )

            write_polygon(
                output_fc_path,
                result.polygon,
                window.spatial_reference,
                source_raster=source_raster_name,
                seg_method="fuzzy_select",
                smooth_level=smooth_level,
            )

            polygon_count += 1
            messages.addMessage(
                f"  \u2192 Polygon {polygon_count} written "
                f"(confidence: {result.confidence:.2f})"
            )

        messages.addMessage(
            f"Complete. {polygon_count} polygon(s) written to {output_fc_path}."
        )

    @staticmethod
    def _read_seed_points(seed_points: object) -> list:
        """Extract (x, y) map coordinates from the seed-point Feature Set.

        Returns an empty list when no seeds were sketched. Kept separate from
        execute() so the arcpy cursor access is isolated and easy to follow.
        """
        if not seed_points:
            return []
        coords = []
        with arcpy.da.SearchCursor(seed_points, ["SHAPE@XY"]) as cursor:
            for (xy,) in cursor:
                if xy is not None:
                    coords.append((float(xy[0]), float(xy[1])))
        return coords

    @staticmethod
    def _make_seed_window_provider(
        raster_obj: object,
        seed_x: float,
        seed_y: float,
        extract_raster_window: object,
        map_coords_to_pixel: object,
    ) -> object:
        """Build the window provider the adaptive fuzzy-select driver calls.

        Returns a callable ``provider(window_px) -> (window, seed_px)`` that
        reads a ``window_px``-sided raster window centered on the seed and maps
        the seed's map coordinates to a pixel within it. This is where the arcpy
        raster read lives; the driver in ``segmentation`` stays arcpy-free.
        """
        cell_w = raster_obj.meanCellWidth
        cell_h = raster_obj.meanCellHeight

        def provider(window_px: int) -> tuple:
            half_w = (window_px / 2) * cell_w
            half_h = (window_px / 2) * cell_h
            extent = (
                seed_x - half_w,
                seed_y - half_h,
                seed_x + half_w,
                seed_y + half_h,
            )
            window = extract_raster_window(raster_obj, extent, max_size=window_px)
            seed_px = map_coords_to_pixel(
                seed_x, seed_y, window.origin, window.cell_size
            )
            return window, seed_px

        return provider

    def postExecute(self, parameters: list) -> None:
        """Post-execution cleanup.

        Add the output feature class to the map TOC if it's new.
        """
        output_fc_path = parameters[1].valueAsText
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            active_map = aprx.activeMap
            if active_map is not None and not any(
                lyr.dataSource == output_fc_path
                for lyr in active_map.listLayers()
                if hasattr(lyr, "dataSource")
            ):
                active_map.addDataFromPath(output_fc_path)
        except Exception:
            pass  # Not running inside an active ArcGIS Pro session
