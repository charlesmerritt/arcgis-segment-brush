"""Tests for the segmentation pipeline.

These tests verify the segmentation module's interface contract.
Currently tests that stubs exist and are callable; as implementations
land, these will test actual algorithm behavior.
"""

from __future__ import annotations

import numpy as np
import pytest
from shapely.geometry import Polygon

from segment_brush.segmentation import (
    SegmentationParams,
    compute_edge_gradient,
    extract_boundary_polygon,
    flood_fill_from_seed,
    mask_to_polygon,
    run_watershed,
    segment_from_seed,
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
    """Test smooth_polygon (implemented — pure shapely, no arcpy)."""

    @staticmethod
    def _jagged_square() -> Polygon:
        # A square whose edges have a small saw-tooth jitter to smooth away.
        pts = []
        for col in range(0, 40, 2):
            pts.append((col, 1 if col % 4 == 0 else -1))
        for row in range(0, 40, 2):
            pts.append((40 + (1 if row % 4 == 0 else -1), row))
        for col in range(40, 0, -2):
            pts.append((col, 40 + (1 if col % 4 == 0 else -1)))
        for row in range(40, 0, -2):
            pts.append((1 if row % 4 == 0 else -1, row))
        return Polygon(pts)

    def test_zero_level_is_identity(self) -> None:
        poly = self._jagged_square()
        assert smooth_polygon(poly, 0).equals(poly)

    def test_smoothing_reduces_vertex_count(self) -> None:
        poly = self._jagged_square()
        smoothed = smooth_polygon(poly, 100)
        assert smoothed.geom_type == "Polygon"
        assert not smoothed.is_empty
        assert len(smoothed.exterior.coords) < len(poly.exterior.coords)

    def test_higher_level_smooths_more(self) -> None:
        poly = self._jagged_square()
        light = len(smooth_polygon(poly, 20).exterior.coords)
        heavy = len(smooth_polygon(poly, 100).exterior.coords)
        assert heavy <= light


class TestSegmentStroke:
    """Test the full watershed pipeline entry point stub."""

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


# The seed sits inside the bright 30:70 square of ``sample_rgb_image``.
_SEED = (50, 50)


class TestFloodFillFromSeed:
    """Test the magic-wand region-growing fill (implemented — no arcpy)."""

    def test_selects_the_object_containing_the_seed(
        self, sample_rgb_image: np.ndarray
    ) -> None:
        mask = flood_fill_from_seed(sample_rgb_image, _SEED, tolerance=30)
        # The whole bright square should be selected...
        assert mask[30:70, 30:70].all()
        # ...and none of the dark background.
        assert not mask[:30, :].any()
        assert not mask[70:, :].any()

    def test_seed_pixel_is_always_selected(self, sample_rgb_image: np.ndarray) -> None:
        mask = flood_fill_from_seed(sample_rgb_image, _SEED, tolerance=0)
        assert mask[_SEED]

    def test_higher_tolerance_selects_at_least_as_much(
        self, sample_rgb_image: np.ndarray
    ) -> None:
        low = flood_fill_from_seed(sample_rgb_image, _SEED, tolerance=10).sum()
        high = flood_fill_from_seed(sample_rgb_image, _SEED, tolerance=90).sum()
        assert high >= low

    def test_max_tolerance_floods_everything_contiguous(
        self, sample_rgb_image: np.ndarray
    ) -> None:
        mask = flood_fill_from_seed(sample_rgb_image, _SEED, tolerance=100)
        assert mask.all()

    def test_seed_out_of_bounds_raises(self, sample_rgb_image: np.ndarray) -> None:
        with pytest.raises(ValueError, match="outside"):
            flood_fill_from_seed(sample_rgb_image, (999, 999), tolerance=30)

    def test_works_on_single_band_image(self) -> None:
        img = np.full((20, 20), 50, dtype=np.uint8)
        img[5:15, 5:15] = 200
        mask = flood_fill_from_seed(img, (10, 10), tolerance=20)
        assert mask[5:15, 5:15].all()
        assert not mask[0, 0]


class TestMaskToPolygon:
    """Test boundary tracing from a region mask."""

    def test_traces_a_square_region(self) -> None:
        mask = np.zeros((100, 100), dtype=bool)
        mask[30:70, 30:70] = True
        poly = mask_to_polygon(mask)
        assert poly.geom_type == "Polygon"
        assert not poly.is_empty
        # Area should be close to the 40x40 = 1600 px region.
        assert poly.area == pytest.approx(1600, rel=0.15)

    def test_polygon_uses_col_x_row_y_convention(self) -> None:
        # A wide, short region: bounds must be wider in x than in y.
        mask = np.zeros((50, 100), dtype=bool)
        mask[20:30, 10:90] = True
        minx, miny, maxx, maxy = mask_to_polygon(mask).bounds
        assert (maxx - minx) > (maxy - miny)

    def test_empty_mask_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            mask_to_polygon(np.zeros((10, 10), dtype=bool))


class TestSegmentFromSeed:
    """Test the full fuzzy-select pipeline entry point (implemented)."""

    def test_produces_polygon_of_the_seeded_object(
        self, sample_rgb_image: np.ndarray
    ) -> None:
        result = segment_from_seed(sample_rgb_image, _SEED, tolerance=30)
        assert result.method == "fuzzy_select"
        assert result.polygon.geom_type == "Polygon"
        assert result.polygon.area == pytest.approx(1600, rel=0.2)

    def test_crisp_edge_yields_high_confidence(
        self, sample_rgb_image: np.ndarray
    ) -> None:
        result = segment_from_seed(sample_rgb_image, _SEED, tolerance=30)
        assert 0.0 < result.confidence <= 1.0

    def test_tolerance_falls_back_to_params(self, sample_rgb_image: np.ndarray) -> None:
        params = SegmentationParams(method="fuzzy_select", tolerance=30)
        result = segment_from_seed(sample_rgb_image, _SEED, params=params)
        assert result.polygon.area == pytest.approx(1600, rel=0.2)

    def test_smoothing_is_applied(self, sample_rgb_image: np.ndarray) -> None:
        raw = segment_from_seed(
            sample_rgb_image, _SEED, params=SegmentationParams(smooth_level=0)
        )
        smoothed = segment_from_seed(
            sample_rgb_image, _SEED, params=SegmentationParams(smooth_level=100)
        )
        assert len(smoothed.polygon.exterior.coords) <= len(raw.polygon.exterior.coords)
