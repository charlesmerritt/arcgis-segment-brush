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

# Smoothing magnitudes (in pixel units) at smooth_level == 100. Scaled linearly
# down to 0 at smooth_level == 0. Kept modest so smoothing generalizes without
# destroying the segmented shape.
_MAX_SIMPLIFY_PX = 5.0
_MAX_BUFFER_PX = 2.5


@dataclass
class SegmentationParams:
    """Parameters controlling the segmentation pipeline."""

    method: str = "watershed"
    smooth_level: int = 30  # 0–100
    snap_tolerance_px: int = 5
    gradient_sigma: float = 1.0
    tolerance: int = 30  # 0–100, fuzzy-select color similarity (magic-wand knob)


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
    if smooth_level <= 0:
        return polygon

    level = min(100, smooth_level) / 100.0

    # Douglas-Peucker simplification: drop vertices within tolerance of the
    # line they sit on. Tolerance is in pixel units (polygons are in pixel
    # space at this stage), scaled by the smoothing level.
    simplify_tol = level * _MAX_SIMPLIFY_PX
    smoothed = polygon.simplify(simplify_tol, preserve_topology=True)

    # Rounded-corner smoothing: dilate then erode by the same amount so the
    # overall area is preserved but sharp jaggies are rounded off.
    buffer_dist = level * _MAX_BUFFER_PX
    if buffer_dist > 0:
        smoothed = smoothed.buffer(buffer_dist).buffer(-buffer_dist)

    # Buffer ops can yield an empty or non-polygon result on degenerate input;
    # fall back to the pre-buffer geometry rather than returning garbage.
    if smoothed.is_empty or smoothed.geom_type != "Polygon":
        return polygon
    return smoothed


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


# ---------------------------------------------------------------------------
# Fuzzy select (magic wand) — seed-based region growing.
#
# Unlike the stroke-based watershed pipeline above, this path emulates
# Photoshop's magic wand: the user drops a seed point on an object and the
# region grows outward from it by color similarity, bounded by a tolerance.
# It needs only a seed pixel (from ArcGIS's native sketch tool) rather than a
# painted loop, so it works from a pure Python toolbox with no .NET add-in.
# ---------------------------------------------------------------------------


def flood_fill_from_seed(
    raster_window: NDArray[np.uint8],
    seed_px: tuple[int, int],
    tolerance: int,
    connectivity: int = 1,
) -> NDArray[np.bool_]:
    """Grow a region from a seed pixel by color similarity (magic-wand fill).

    Computes each pixel's Euclidean color distance from the seed pixel, then
    flood-fills the contiguous region whose distance stays within ``tolerance``.
    This is the region-growing core of a fuzzy-select / magic-wand tool.

    Parameters
    ----------
    raster_window : ndarray, shape (rows, cols) or (rows, cols, bands)
        The image pixels. RGB for v1, arbitrary bands for v2.
    seed_px : tuple of (row, col)
        Pixel the region grows from — where the user clicked.
    tolerance : int
        Fuzziness, 0–100. 0 selects only pixels identical to the seed; 100
        selects everything reachable. Maps linearly onto the color-distance
        range ``[0, sqrt(bands) * 255]``.
    connectivity : int
        Pixel connectivity for the flood (1 = 4-connected, 2 = 8-connected).

    Returns
    -------
    ndarray of bool, shape (rows, cols)
        True for pixels in the selected region.

    Raises
    ------
    ValueError
        If the seed pixel falls outside the raster window.
    """
    from skimage.segmentation import flood

    img = raster_window.astype(np.float64)
    if img.ndim == 2:
        img = img[:, :, np.newaxis]

    rows, cols, bands = img.shape
    row, col = int(seed_px[0]), int(seed_px[1])
    if not (0 <= row < rows and 0 <= col < cols):
        raise ValueError(
            f"seed pixel {seed_px!r} is outside the {rows}x{cols} raster window"
        )

    # Scalar "distance from the seed color" field. The seed sits at 0, so
    # flooding this field with an absolute tolerance grows the region by how
    # far each pixel's color drifts from the seed's — the magic-wand rule.
    seed_color = img[row, col, :]
    distance = np.sqrt(((img - seed_color) ** 2).sum(axis=2))

    max_distance = np.sqrt(bands) * 255.0
    tol = max(0, min(100, tolerance)) / 100.0 * max_distance

    return flood(distance, (row, col), connectivity=connectivity, tolerance=tol)


def mask_to_polygon(mask: NDArray[np.bool_]) -> Polygon:
    """Trace the boundary of a boolean region mask into a shapely Polygon.

    Extracts the longest contour of the mask (the outer boundary of the
    selected region) and returns it as a polygon in pixel coordinates, using
    the image convention ``x = col``, ``y = row``.

    Parameters
    ----------
    mask : ndarray of bool, shape (rows, cols)
        The selected region (e.g. from :func:`flood_fill_from_seed`).

    Returns
    -------
    shapely.geometry.Polygon
        Boundary polygon in pixel coordinates.

    Raises
    ------
    ValueError
        If the mask is empty (no region to trace).
    """
    from shapely.geometry import Polygon
    from skimage.measure import find_contours

    if not mask.any():
        raise ValueError("mask is empty; no boundary to extract")

    # Pad by one pixel so regions touching the window edge still produce a
    # closed contour; subtract the pad offset when converting back.
    padded = np.pad(mask.astype(np.float64), 1)
    contours = find_contours(padded, 0.5)
    if not contours:
        raise ValueError("mask has no traceable boundary")

    # The longest contour is the outer boundary of the largest component.
    contour = max(contours, key=len)
    coords = [(col - 1.0, row - 1.0) for row, col in contour]
    return Polygon(coords)


def _boundary_confidence(
    raster_window: NDArray[np.uint8],
    mask: NDArray[np.bool_],
) -> float:
    """Estimate how crisp the selected region's edge is, in [0, 1].

    Measures the mean image gradient along the mask boundary relative to the
    maximum possible gradient. A high value means the fill stopped at a strong
    color discontinuity (a real edge); a low value means it petered out in a
    smooth gradient and the boundary is less trustworthy.
    """
    from scipy import ndimage

    img = raster_window.astype(np.float64)
    gray = img.mean(axis=2) if img.ndim == 3 else img

    boundary = mask ^ ndimage.binary_erosion(mask)
    if not boundary.any():
        return 0.0

    grad = np.hypot(ndimage.sobel(gray, axis=0), ndimage.sobel(gray, axis=1))
    # sobel's peak response for an ideal 0→255 step is 4 * 255.
    return float(min(1.0, grad[boundary].mean() / (4.0 * 255.0)))


def segment_from_seed(
    raster_window: NDArray[np.uint8],
    seed_px: tuple[int, int],
    tolerance: int | None = None,
    params: SegmentationParams | None = None,
) -> SegmentationResult:
    """Full fuzzy-select pipeline for a single seed point (magic wand).

    This is the seed-based counterpart to :func:`segment_stroke`. Given a
    raster window and a seed pixel, it grows a region by color similarity,
    traces its boundary, and smooths it into a polygon.

    Pipeline:
    1. flood_fill_from_seed → boolean region mask
    2. mask_to_polygon → raw boundary polygon
    3. smooth_polygon → final polygon

    Parameters
    ----------
    raster_window : ndarray, shape (rows, cols, bands)
        Pixel data extracted around the seed.
    seed_px : tuple of (row, col)
        The seed pixel — where the user clicked.
    tolerance : int, optional
        Fuzziness 0–100. Falls back to ``params.tolerance`` if not given.
    params : SegmentationParams, optional
        Algorithm parameters. Uses defaults if not provided.

    Returns
    -------
    SegmentationResult
        The refined polygon and metadata.

    Raises
    ------
    ValueError
        If the flood fill produces an empty region.
    """
    if params is None:
        params = SegmentationParams(method="fuzzy_select")
    if tolerance is None:
        tolerance = params.tolerance

    mask = flood_fill_from_seed(raster_window, seed_px, tolerance)
    polygon = mask_to_polygon(mask)
    polygon = smooth_polygon(polygon, params.smooth_level)
    confidence = _boundary_confidence(raster_window, mask)

    return SegmentationResult(
        polygon=polygon,
        confidence=confidence,
        method="fuzzy_select",
    )
