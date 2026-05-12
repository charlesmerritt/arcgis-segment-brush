"""Tests for the segmentation pipeline.

These tests verify the segmentation module's interface contract.
Currently tests that stubs exist and are callable; as implementations
land, these will test actual algorithm behavior.
"""

from __future__ import annotations

import numpy as np
import pytest

from segment_brush.segmentation import (
    SegmentationParams,
    SegmentationResult,
    compute_edge_gradient,
    extract_boundary_polygon,
    run_watershed,
    segment_stroke,
    smooth_polygon,
    stroke_to_markers,
)


class TestSegmentationParams:
    """Test SegmentationParams defaults and construction."""

    def test_defaults(self) -> None:
        params = SegmentationParams()
        assert params.method == "watershed"
        assert params.smooth_level == 30
        assert params.snap_tolerance_px == 5
        assert params.gradient_sigma == 1.0

    def test_custom_values(self) -> None:
        params = SegmentationParams(method="slic", smooth_level=80)
        assert params.method == "slic"
        assert params.smooth_level == 80


class TestComputeEdgeGradient:
    """Test compute_edge_gradient stub."""

    def test_raises_not_implemented(self, sample_rgb_image: np.ndarray) -> None:
        with pytest.raises(NotImplementedError):
            compute_edge_gradient(sample_rgb_image)


class TestStrokeToMarkers:
    """Test stroke_to_markers stub."""

    def test_raises_not_implemented(
        self, sample_stroke_around_square: np.ndarray
    ) -> None:
        with pytest.raises(NotImplementedError):
            stroke_to_markers(sample_stroke_around_square, (100, 100), brush_radius=3)


class TestRunWatershed:
    """Test run_watershed stub."""

    def test_raises_not_implemented(self) -> None:
        gradient = np.zeros((100, 100), dtype=np.float64)
        markers = np.zeros((100, 100), dtype=np.int32)
        with pytest.raises(NotImplementedError):
            run_watershed(gradient, markers)


class TestExtractBoundaryPolygon:
    """Test extract_boundary_polygon stub."""

    def test_raises_not_implemented(self) -> None:
        labels = np.zeros((100, 100), dtype=np.int32)
        with pytest.raises(NotImplementedError):
            extract_boundary_polygon(labels)


class TestSmoothPolygon:
    """Test smooth_polygon stub."""

    def test_raises_not_implemented(self) -> None:
        # We can't create a real Polygon without importing shapely in the test,
        # but the function should fail before it even uses the polygon.
        with pytest.raises((NotImplementedError, TypeError)):
            smooth_polygon(None, smooth_level=50)  # type: ignore[arg-type]


class TestSegmentStroke:
    """Test the full pipeline entry point stub."""

    def test_raises_not_implemented(
        self,
        sample_rgb_image: np.ndarray,
        sample_stroke_around_square: np.ndarray,
    ) -> None:
        with pytest.raises(NotImplementedError):
            segment_stroke(
                raster_window=sample_rgb_image,
                stroke_pixels=sample_stroke_around_square,
                brush_radius=3,
            )
