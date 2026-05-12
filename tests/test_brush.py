"""Tests for the brush stroke management module.

These tests verify brush session logic — no arcpy dependency needed.
"""

from __future__ import annotations

import numpy as np
import pytest

from segment_brush.brush import BrushSession, BrushStroke, StrokeState


class TestBrushStroke:
    """Test BrushStroke data class."""

    def test_anchor_empty(self) -> None:
        stroke = BrushStroke(stroke_id=1)
        assert stroke.anchor is None

    def test_anchor_with_points(self) -> None:
        stroke = BrushStroke(stroke_id=1, points=[(10.0, 20.0), (11.0, 21.0)])
        assert stroke.anchor == (10.0, 20.0)

    def test_is_closed_default(self) -> None:
        stroke = BrushStroke(stroke_id=1)
        assert not stroke.is_closed

    def test_extent_empty(self) -> None:
        stroke = BrushStroke(stroke_id=1)
        assert stroke.extent is None

    def test_extent_computed(self) -> None:
        stroke = BrushStroke(
            stroke_id=1,
            points=[(0.0, 0.0), (10.0, 5.0), (5.0, 10.0)],
        )
        assert stroke.extent == (0.0, 0.0, 10.0, 10.0)


class TestBrushSession:
    """Test BrushSession — the core painting session manager."""

    def test_start_stroke(self) -> None:
        session = BrushSession()
        stroke = session.start_stroke(100.0, 200.0)

        assert stroke.stroke_id == 1
        assert stroke.anchor == (100.0, 200.0)
        assert stroke.state == StrokeState.PAINTING
        assert len(session.strokes) == 1

    def test_multiple_strokes_get_unique_ids(self) -> None:
        session = BrushSession()
        s1 = session.start_stroke(0.0, 0.0)
        s2 = session.start_stroke(10.0, 10.0)

        assert s1.stroke_id == 1
        assert s2.stroke_id == 2

    def test_add_point(self) -> None:
        session = BrushSession()
        stroke = session.start_stroke(0.0, 0.0)

        closed = session.add_point(stroke, 5.0, 0.0)
        assert not closed
        assert len(stroke.points) == 2

    def test_loop_closure(self) -> None:
        session = BrushSession(snap_tolerance=5.0)
        stroke = session.start_stroke(0.0, 0.0)

        # Paint a path that eventually comes back near the anchor
        # Need > 10 points before closure detection kicks in
        for i in range(1, 15):
            session.add_point(stroke, float(i), float(i % 5))

        # Now come back near (0, 0)
        closed = session.add_point(stroke, 1.0, 0.5)
        assert closed
        assert stroke.state == StrokeState.CLOSED
        assert stroke.is_closed

    def test_no_early_closure(self) -> None:
        """Stroke shouldn't close if fewer than 10 points, even if near anchor."""
        session = BrushSession(snap_tolerance=100.0)  # very generous tolerance
        stroke = session.start_stroke(0.0, 0.0)

        # Add only a few points near the anchor
        for i in range(1, 5):
            closed = session.add_point(stroke, 0.1 * i, 0.1 * i)
            assert not closed

    def test_adjust_radius(self) -> None:
        session = BrushSession(brush_radius=10.0)

        new_radius = session.adjust_radius(5.0)
        assert new_radius == 15.0

        new_radius = session.adjust_radius(-20.0)
        assert new_radius == 1.0  # clamped to minimum of 1.0

    def test_get_closed_strokes(self) -> None:
        session = BrushSession()
        s1 = session.start_stroke(0.0, 0.0)
        s1.state = StrokeState.CLOSED  # force closed for test

        s2 = session.start_stroke(10.0, 10.0)
        # s2 still PAINTING

        closed = session.get_closed_strokes()
        assert len(closed) == 1
        assert closed[0].stroke_id == 1

    def test_to_pixel_array(self) -> None:
        session = BrushSession()
        stroke = session.start_stroke(100.0, 200.0)
        session.add_point(stroke, 101.0, 199.0)

        origin = (99.0, 201.0)  # top-left corner
        cell_size = (1.0, 1.0)

        pixels = session.to_pixel_array(stroke, origin, cell_size)

        assert pixels.dtype == np.int32
        assert pixels.shape == (2, 2)
        # (100 - 99) / 1 = col 1, (201 - 200) / 1 = row 1
        assert pixels[0, 0] == 1  # row
        assert pixels[0, 1] == 1  # col

    def test_reset(self) -> None:
        session = BrushSession()
        session.start_stroke(0.0, 0.0)
        session.start_stroke(10.0, 10.0)

        session.reset()
        assert len(session.strokes) == 0
        # Next stroke should get id 1 again
        stroke = session.start_stroke(5.0, 5.0)
        assert stroke.stroke_id == 1
