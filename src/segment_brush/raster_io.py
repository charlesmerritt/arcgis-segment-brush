"""Raster I/O — reads pixels from ArcGIS raster layers into numpy arrays.

This module contains ALL arcpy-dependent raster reading logic. The segmentation
module works with pure numpy arrays and knows nothing about ArcGIS. This
separation allows testing the segmentation pipeline without an ArcGIS license.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from shapely.geometry import Polygon


@dataclass
class RasterWindow:
    """A windowed read of a raster layer."""

    pixels: NDArray[np.uint8]  # shape (rows, cols, bands)
    extent: tuple[float, float, float, float]  # (xmin, ymin, xmax, ymax) in map units
    cell_size: tuple[float, float]  # (x_size, y_size) in map units
    spatial_reference: Any  # arcpy.SpatialReference (typed as Any for test compat)
    origin: tuple[float, float]  # (x, y) of top-left corner in map units


def extract_raster_window(
    raster_layer: Any,
    extent: tuple[float, float, float, float],
    max_size: int = 4096,
) -> RasterWindow:
    """Extract a window of pixels from an ArcGIS raster layer.

    Reads only the pixels within the given extent (plus a small buffer),
    converting to a numpy array. Caps at max_size×max_size pixels.

    Parameters
    ----------
    raster_layer : arcpy raster layer
        The input raster from the map TOC.
    extent : tuple
        (xmin, ymin, xmax, ymax) in map coordinates.
    max_size : int
        Maximum dimension in pixels for the extraction window.

    Returns
    -------
    RasterWindow
        The extracted pixel data with georeferencing metadata.

    Raises
    ------
    ValueError
        If the extent is outside the raster's bounds or exceeds max_size.
    """
    raise NotImplementedError("extract_raster_window not yet implemented")


def map_coords_to_pixel(
    x: float,
    y: float,
    origin: tuple[float, float],
    cell_size: tuple[float, float],
) -> tuple[int, int]:
    """Convert map coordinates to pixel (row, col) coordinates.

    Parameters
    ----------
    x, y : float
        Map coordinates.
    origin : tuple
        (x, y) of the raster window's top-left corner.
    cell_size : tuple
        (x_size, y_size) pixel dimensions in map units.

    Returns
    -------
    tuple of (row, col)
        Pixel coordinates within the raster window.
    """
    col = int((x - origin[0]) / cell_size[0])
    row = int((origin[1] - y) / cell_size[1])
    return (row, col)


def pixel_to_map_coords(
    row: int,
    col: int,
    origin: tuple[float, float],
    cell_size: tuple[float, float],
) -> tuple[float, float]:
    """Convert pixel (row, col) coordinates to map coordinates.

    Returns the center of the pixel.

    Parameters
    ----------
    row, col : int
        Pixel coordinates.
    origin : tuple
        (x, y) of the raster window's top-left corner.
    cell_size : tuple
        (x_size, y_size) pixel dimensions in map units.

    Returns
    -------
    tuple of (x, y)
        Map coordinates at the center of the pixel.
    """
    x = origin[0] + (col + 0.5) * cell_size[0]
    y = origin[1] - (row + 0.5) * cell_size[1]
    return (x, y)


def polygon_pixels_to_map(
    polygon: Polygon,
    origin: tuple[float, float],
    cell_size: tuple[float, float],
) -> Polygon:
    """Convert a pixel-space polygon (x=col, y=row) to map coordinates.

    The segmentation pipeline produces polygons in the raster window's pixel
    space using the image convention ``x = col``, ``y = row``. The feature
    writer expects map coordinates, so each vertex must be georeferenced before
    it is written. This applies the same pixel-center convention as
    :func:`pixel_to_map_coords`, which also flips the y-axis (image rows grow
    downward, map y grows upward):

        map_x = origin_x + (col + 0.5) * cell_w
        map_y = origin_y - (row + 0.5) * cell_h

    Parameters
    ----------
    polygon : shapely.geometry.Polygon
        Polygon with vertices in pixel coordinates (x=col, y=row).
    origin : tuple
        (x, y) of the raster window's top-left corner in map units.
    cell_size : tuple
        (x_size, y_size) pixel dimensions in map units.

    Returns
    -------
    shapely.geometry.Polygon
        The polygon with vertices in map coordinates.
    """
    from shapely.affinity import affine_transform

    cell_w, cell_h = cell_size
    origin_x, origin_y = origin
    # affine_transform matrix [a, b, d, e, xoff, yoff] applies
    #   x' = a*x + b*y + xoff   (col → map_x)
    #   y' = d*x + e*y + yoff   (row → map_y, negated to flip the axis)
    matrix = [
        cell_w,
        0.0,
        0.0,
        -cell_h,
        origin_x + 0.5 * cell_w,
        origin_y - 0.5 * cell_h,
    ]
    return affine_transform(polygon, matrix)
