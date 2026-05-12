"""ArcGIS Segment Brush — Python Toolbox.

This .pyt file is the entry point that ArcGIS Pro loads. It defines the
toolbox and its tools, which appear in the Geoprocessing pane.

To install: copy this toolbox folder to a location, then in ArcGIS Pro:
  Geoprocessing pane → Toolboxes → Add Toolbox → select SegmentBrush.pyt
"""

from __future__ import annotations

import os
import sys

# Add the project's src/ directory to the Python path so we can import
# the segment_brush package. This handles the case where the toolbox
# is loaded from its installed location.
_toolbox_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(os.path.dirname(_toolbox_dir), "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


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
        # NOTE: arcpy.Parameter is only available inside ArcGIS Pro.
        # This method is called by the GP framework at tool load time.
        # For testing, see tests/test_toolbox.py which mocks arcpy.
        raise NotImplementedError(
            "getParameterInfo not yet implemented — "
            "requires arcpy.Parameter which is only available in ArcGIS Pro"
        )
        # Planned parameters:
        # 0: input_raster (GPRasterLayer) — raster layer from map TOC
        # 1: output_fc (DEFeatureClass) — output polygon feature class
        # 2: seg_method (GPString) — segmentation method dropdown
        # 3: smooth_level (GPLong) — smoothing slider 0–100
        # 4: brush_radius (GPDouble) — display-only, current brush radius

    def isLicensed(self) -> bool:
        """Check whether the tool is licensed to execute.

        We require:
        - Spatial Analyst OR Image Analyst (for raster access)
        - scikit-image installed in the Python environment
        """
        raise NotImplementedError("isLicensed not yet implemented")

    def updateParameters(self, parameters: list) -> None:
        """Modify parameter values and properties.

        Called whenever a parameter is changed in the tool dialog.
        Used for dynamic validation (e.g., populate method dropdown).
        """
        raise NotImplementedError("updateParameters not yet implemented")

    def updateMessages(self, parameters: list) -> None:
        """Modify messages for each parameter.

        Called after updateParameters. Used to add warnings/errors
        (e.g., "scikit-image not installed").
        """
        raise NotImplementedError("updateMessages not yet implemented")

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
        raise NotImplementedError("execute not yet implemented")

    def postExecute(self, parameters: list) -> None:
        """Post-execution cleanup.

        Add the output feature class to the map TOC if it's new.
        """
        raise NotImplementedError("postExecute not yet implemented")
