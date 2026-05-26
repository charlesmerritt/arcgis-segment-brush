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

        return [input_raster, output_fc, seg_method, smooth_level, brush_radius]

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
        from segment_brush.segmentation import SegmentationParams, segment_stroke
        from segment_brush.raster_io import extract_raster_window
        from segment_brush.feature_output import (
            create_output_feature_class,
            write_polygon,
        )

        # 1. Read parameters
        input_raster_path = parameters[0].valueAsText
        output_fc_path = parameters[1].valueAsText
        seg_method = parameters[2].valueAsText or "Watershed"
        smooth_level = int(parameters[3].value) if parameters[3].value is not None else 50
        brush_radius = float(parameters[4].value) if parameters[4].value is not None else 10.0

        # 2. Build segmentation params
        seg_params = SegmentationParams(
            method=seg_method.lower(),
            smooth_level=smooth_level,
        )

        # 3. Get closed strokes from the active session (lazy-init if not yet set)
        global _active_session
        if _active_session is None:
            _active_session = BrushSession()
        session = _active_session

        closed_strokes = session.get_processable_strokes()
        if not closed_strokes:
            messages.addWarningMessage(
                "No closed brush strokes found. "
                "Paint at least one closed boundary before running the tool."
            )
            return

        # 4. Ensure the output feature class exists
        raster_obj = arcpy.Raster(input_raster_path)
        spatial_ref = raster_obj.spatialReference

        if not arcpy.Exists(output_fc_path):
            messages.addMessage(f"Creating output feature class: {output_fc_path}")
            create_output_feature_class(output_fc_path, spatial_ref)

        # 5. Process each closed stroke through the segmentation pipeline
        source_raster_name = os.path.basename(input_raster_path)
        polygon_count = 0

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

        messages.addMessage(
            f"Complete. {polygon_count} polygon(s) written to {output_fc_path}."
        )

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
