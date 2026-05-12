"""Segmentation pipeline — the core algorithm.

Takes a raster window (numpy array) and a brush stroke (list of pixel coords),
returns a refined polygon boundary snapped to image edges.

Architecture note: this module has NO arcpy dependency. It works entirely with
numpy arrays and shapely geometries. The arcpy layer lives in raster_io.py and
toolbox/. This separation allows testing without an ArcGIS Pro license.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from shapely.geometry import Polygon


@dataclass
class SegmentationParams:
    """Parameters controlling the segmentation pipeline."""

    method: str = "watershed"
    smooth_level: int = 30  # 0–100
    snap_tolerance_px: int = 5
    gradient_sigma: float = 1.0


@dataclass
class SegmentationResult:
    """Result of segmenting a single painted loop."""

    polygon: Polygon  # refined boundary in pixel coordinates
    confidence: float  # 0.0–1.0, how well the stroke matched an edge
    method: str  # which algorithm produced this


def compute_edge_gradient(
    raster_window: NDArray[np.uint8],
    sigma: float = 1.0,
) -> NDArray[np.float64]:
    """Compute edge gradient magnitude from an RGB raster window.

    Uses Sobel filters on each band, then takes the maximum gradient
    across bands. This gives a single-channel edge strength map.

    Parameters
    ----------
    raster_window : ndarray, shape (rows, cols, bands)
        The image pixels. RGB for v1, arbitrary bands for v2.
    sigma : float
        Gaussian smoothing sigma applied before edge detection.

    Returns
    -------
    ndarray, shape (rows, cols)
        Edge gradient magnitude, normalized to [0, 1].
    """
    raise NotImplementedError("compute_edge_gradient not yet implemented")


def stroke_to_markers(
    stroke_pixels: NDArray[np.int32],
    image_shape: tuple[int, int],
    brush_radius: int,
) -> NDArray[np.int32]:
    """Convert a brush stroke (closed loop) into a marker array for watershed.

    The stroke defines the approximate boundary. We create a marker array where:
    - Pixels along the stroke (dilated by brush_radius) = boundary marker (1)
    - Pixels clearly inside the stroke = interior marker (2)
    - Pixels clearly outside = exterior marker (3)
    - Ambiguous pixels = 0 (to be determined by watershed)

    Parameters
    ----------
    stroke_pixels : ndarray, shape (N, 2)
        Ordered (row, col) pixel coordinates of the brush stroke path.
    image_shape : tuple of (rows, cols)
        Shape of the raster window.
    brush_radius : int
        Radius of the brush in pixels.

    Returns
    -------
    ndarray, shape (rows, cols)
        Marker array for watershed segmentation.
    """
    raise NotImplementedError("stroke_to_markers not yet implemented")


def run_watershed(
    gradient: NDArray[np.float64],
    markers: NDArray[np.int32],
) -> NDArray[np.int32]:
    """Run watershed segmentation on the edge gradient with the given markers.

    Parameters
    ----------
    gradient : ndarray, shape (rows, cols)
        Edge gradient magnitude (higher = stronger edge).
    markers : ndarray, shape (rows, cols)
        Seed markers: 0 = unknown, 1 = boundary, 2 = interior, 3 = exterior.

    Returns
    -------
    ndarray, shape (rows, cols)
        Label array where each pixel is assigned to a region.
    """
    raise NotImplementedError("run_watershed not yet implemented")


def extract_boundary_polygon(
    labels: NDArray[np.int32],
    interior_label: int = 2,
) -> Polygon:
    """Extract the boundary of the interior region as a shapely Polygon.

    Parameters
    ----------
    labels : ndarray, shape (rows, cols)
        Label array from watershed.
    interior_label : int
        Which label represents the interior region.

    Returns
    -------
    shapely.geometry.Polygon
        The boundary polygon in pixel coordinates.
    """
    raise NotImplementedError("extract_boundary_polygon not yet implemented")


def smooth_polygon(
    polygon: Polygon,
    smooth_level: int,
) -> Polygon:
    """Apply smoothing to a polygon.

    Combines Douglas-Peucker simplification with buffer-based smoothing.
    The smooth_level (0–100) controls magnitude:
    - 0: no smoothing (raw boundary from segmentation)
    - 50: moderate generalization
    - 100: maximum smoothing (very simplified shape)

    Parameters
    ----------
    polygon : shapely.geometry.Polygon
        Input polygon in pixel coordinates.
    smooth_level : int
        Smoothing magnitude, 0–100.

    Returns
    -------
    shapely.geometry.Polygon
        Smoothed polygon.
    """
    raise NotImplementedError("smooth_polygon not yet implemented")


def segment_stroke(
    raster_window: NDArray[np.uint8],
    stroke_pixels: NDArray[np.int32],
    brush_radius: int,
    params: SegmentationParams | None = None,
) -> SegmentationResult:
    """Full segmentation pipeline for a single painted stroke.

    This is the main entry point. Takes a raster window and a brush stroke,
    returns a refined polygon boundary.

    Pipeline:
    1. compute_edge_gradient → edge strength map
    2. stroke_to_markers → seed markers from brush stroke
    3. run_watershed → label array
    4. extract_boundary_polygon → raw polygon
    5. smooth_polygon → final polygon

    Parameters
    ----------
    raster_window : ndarray, shape (rows, cols, bands)
        Pixel data extracted around the stroke.
    stroke_pixels : ndarray, shape (N, 2)
        Ordered (row, col) coordinates of the closed brush stroke.
    brush_radius : int
        Brush radius in pixels.
    params : SegmentationParams, optional
        Algorithm parameters. Uses defaults if not provided.

    Returns
    -------
    SegmentationResult
        The refined polygon and metadata.
    """
    raise NotImplementedError("segment_stroke not yet implemented")
