"""Feature class output — writes polygons to ArcGIS geodatabase feature classes.

Contains ALL arcpy-dependent feature writing logic. Accepts shapely Polygons
in map coordinates and writes them to a file geodatabase feature class with
metadata attributes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shapely.geometry import Polygon


# Schema for the output feature class
OUTPUT_FIELDS = [
    ("source_raster", "TEXT", 255),
    ("seg_method", "TEXT", 50),
    ("smooth_level", "SHORT", None),
    ("area_sq_m", "DOUBLE", None),
    ("perimeter_m", "DOUBLE", None),
    ("created_at", "TEXT", 30),
]


def create_output_feature_class(
    output_path: str,
    spatial_reference: Any,
) -> str:
    """Create a new polygon feature class with the segment brush schema.

    Parameters
    ----------
    output_path : str
        Full path to the output feature class (e.g., "C:/data/results.gdb/segments").
    spatial_reference : arcpy.SpatialReference
        The coordinate system for the feature class.

    Returns
    -------
    str
        Path to the created feature class.
    """
    raise NotImplementedError("create_output_feature_class not yet implemented")


def write_polygon(
    output_path: str,
    polygon: Polygon,
    spatial_reference: Any,
    source_raster: str,
    seg_method: str,
    smooth_level: int,
) -> int:
    """Write a single polygon to the output feature class.

    Converts the shapely Polygon (in map coordinates) to an arcpy Polygon
    geometry and inserts it with metadata attributes.

    Parameters
    ----------
    output_path : str
        Path to the output feature class.
    polygon : shapely.geometry.Polygon
        The polygon in map coordinates.
    spatial_reference : arcpy.SpatialReference
        Coordinate system.
    source_raster : str
        Name of the source raster layer.
    seg_method : str
        Segmentation method used.
    smooth_level : int
        Smoothing level (0–100).

    Returns
    -------
    int
        The ObjectID of the inserted feature.
    """
    raise NotImplementedError("write_polygon not yet implemented")


def shapely_to_arcpy_polygon(
    polygon: Polygon,
    spatial_reference: Any,
) -> Any:
    """Convert a shapely Polygon to an arcpy Polygon geometry.

    Parameters
    ----------
    polygon : shapely.geometry.Polygon
        Input polygon with coordinates in map units.
    spatial_reference : arcpy.SpatialReference
        Target coordinate system.

    Returns
    -------
    arcpy.Polygon
        ArcPy polygon geometry.
    """
    raise NotImplementedError("shapely_to_arcpy_polygon not yet implemented")


def compute_geodesic_measurements(
    polygon: Polygon,
    spatial_reference: Any,
) -> tuple[float, float]:
    """Compute geodesic area and perimeter for a polygon.

    Parameters
    ----------
    polygon : shapely.geometry.Polygon
        The polygon in map coordinates.
    spatial_reference : arcpy.SpatialReference
        Coordinate system (needed for geodesic computation).

    Returns
    -------
    tuple of (area_sq_m, perimeter_m)
        Geodesic area in square meters and perimeter in meters.
    """
    raise NotImplementedError("compute_geodesic_measurements not yet implemented")


def get_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()
