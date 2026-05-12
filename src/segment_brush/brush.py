"""Brush stroke management — tracks painted loops on the map canvas.

Responsible for:
- Recording mouse movements as stroke paths
- Detecting loop closure (snap to anchor)
- Managing multiple painted objects in a session
- Converting screen/map coordinates to stroke pixel arrays

This module is ArcGIS-aware (uses map coordinates) but does NOT depend on arcpy
directly — it works with coordinate tuples so it can be unit tested.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

import numpy as np
from numpy.typing import NDArray


class StrokeState(Enum):
    """State of a brush stroke."""

    PAINTING = auto()  # actively being drawn
    CLOSED = auto()  # loop completed, ready for processing
    PROCESSED = auto()  # segmentation has run
    ACCEPTED = auto()  # user accepted the result
    REJECTED = auto()  # user rejected the result


@dataclass
class BrushStroke:
    """A single painted stroke representing one object boundary."""

    stroke_id: int
    points: list[tuple[float, float]] = field(default_factory=list)  # (x, y) map coords
    state: StrokeState = StrokeState.PAINTING
    brush_radius: float = 10.0  # in map units

    @property
    def anchor(self) -> tuple[float, float] | None:
        """The first point of the stroke (anchor for loop closure)."""
        return self.points[0] if self.points else None

    @property
    def is_closed(self) -> bool:
        """Whether the stroke forms a closed loop."""
        return self.state == StrokeState.CLOSED

    @property
    def extent(self) -> tuple[float, float, float, float] | None:
        """Bounding extent (xmin, ymin, xmax, ymax) of the stroke, or None if empty."""
        if not self.points:
            return None
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass
class BrushSession:
    """Manages all brush strokes in a painting session."""

    strokes: list[BrushStroke] = field(default_factory=list)
    brush_radius: float = 10.0  # current radius in map units
    snap_tolerance: float = 5.0  # in map units
    _next_id: int = 1

    def start_stroke(self, x: float, y: float) -> BrushStroke:
        """Begin a new stroke at the given map coordinates.

        Parameters
        ----------
        x, y : float
            Map coordinates of the anchor point.

        Returns
        -------
        BrushStroke
            The new stroke being painted.
        """
        stroke = BrushStroke(
            stroke_id=self._next_id,
            points=[(x, y)],
            brush_radius=self.brush_radius,
        )
        self.strokes.append(stroke)
        self._next_id += 1
        return stroke

    def add_point(self, stroke: BrushStroke, x: float, y: float) -> bool:
        """Add a point to an active stroke. Returns True if the loop closed.

        Parameters
        ----------
        stroke : BrushStroke
            The stroke being painted.
        x, y : float
            Map coordinates of the new point.

        Returns
        -------
        bool
            True if the stroke closed (snapped back to anchor), False otherwise.
        """
        if stroke.state != StrokeState.PAINTING:
            return False

        stroke.points.append((x, y))

        # Check for loop closure: is the new point within snap tolerance of anchor?
        if len(stroke.points) > 10 and stroke.anchor is not None:
            dx = x - stroke.anchor[0]
            dy = y - stroke.anchor[1]
            distance = (dx**2 + dy**2) ** 0.5
            if distance <= self.snap_tolerance:
                stroke.state = StrokeState.CLOSED
                # Close the loop by appending the anchor point
                stroke.points.append(stroke.anchor)
                return True

        return False

    def adjust_radius(self, delta: float) -> float:
        """Adjust the brush radius by a delta. Returns the new radius.

        Parameters
        ----------
        delta : float
            Change in radius (positive = bigger, negative = smaller).

        Returns
        -------
        float
            The new brush radius.
        """
        self.brush_radius = max(1.0, self.brush_radius + delta)
        return self.brush_radius

    def get_closed_strokes(self) -> list[BrushStroke]:
        """Return all strokes that are closed and ready for processing."""
        return [s for s in self.strokes if s.state == StrokeState.CLOSED]

    def get_processable_strokes(self) -> list[BrushStroke]:
        """Return all strokes ready for segmentation (closed, not yet processed)."""
        return [s for s in self.strokes if s.state == StrokeState.CLOSED]

    def to_pixel_array(
        self,
        stroke: BrushStroke,
        origin: tuple[float, float],
        cell_size: tuple[float, float],
    ) -> NDArray[np.int32]:
        """Convert a stroke's map coordinates to pixel (row, col) array.

        Parameters
        ----------
        stroke : BrushStroke
            The stroke to convert.
        origin : tuple
            (x, y) of the raster window's top-left corner.
        cell_size : tuple
            (x_size, y_size) pixel dimensions in map units.

        Returns
        -------
        ndarray, shape (N, 2)
            Pixel coordinates as (row, col) pairs.
        """
        pixels = []
        for x, y in stroke.points:
            col = int((x - origin[0]) / cell_size[0])
            row = int((origin[1] - y) / cell_size[1])
            pixels.append((row, col))
        return np.array(pixels, dtype=np.int32)

    def reset(self) -> None:
        """Clear all strokes and reset the session."""
        self.strokes.clear()
        self._next_id = 1
