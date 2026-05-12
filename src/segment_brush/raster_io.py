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
