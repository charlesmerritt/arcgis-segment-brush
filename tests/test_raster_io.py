"""Tests for raster I/O module.

Tests coordinate conversion (no arcpy needed) and verifies stubs exist
for arcpy-dependent functions.
"""

from __future__ import annotations

import pytest

from segment_brush.raster_io import (
    extract_raster_window,
    map_coords_to_pixel,
    pixel_to_map_coords,
)


class TestCoordinateConversion:
    """Test pixel ↔ map coordinate conversion — pure math, no arcpy."""

    def test_map_to_pixel_basic(self) -> None:
        origin = (100.0, 200.0)  # top-left (x, y)
        cell_size = (1.0, 1.0)

        row, col = map_coords_to_pixel(105.0, 195.0, origin, cell_size)
        assert col == 5
        assert row == 5

    def test_map_to_pixel_fractional(self) -> None:
        origin = (0.0, 100.0)
        cell_size = (0.5, 0.5)

        row, col = map_coords_to_pixel(1.25, 98.75, origin, cell_size)
        assert col == 2  # int(1.25 / 0.5) = 2
        assert row == 2  # int((100.0 - 98.75) / 0.5) = 2

    def test_pixel_to_map_basic(self) -> None:
        origin = (100.0, 200.0)
        cell_size = (1.0, 1.0)

        x, y = pixel_to_map_coords(5, 5, origin, cell_size)
        assert x == 105.5  # center of pixel
        assert y == 194.5  # center of pixel

    def test_round_trip(self) -> None:
        """Converting map→pixel→map should return approximately the original."""
        origin = (500.0, 1000.0)
        cell_size = (0.3, 0.3)

        original_x, original_y = 501.5, 998.2
        row, col = map_coords_to_pixel(original_x, original_y, origin, cell_size)
        recovered_x, recovered_y = pixel_to_map_coords(row, col, origin, cell_size)

        # Should be within one cell_size of original (pixel center snapping)
        assert abs(recovered_x - original_x) < cell_size[0]
        assert abs(recovered_y - original_y) < cell_size[1]


class TestExtractRasterWindow:
    """Test extract_raster_window stub."""

    def test_raises_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError):
            extract_raster_window(
                raster_layer=None,
                extent=(0.0, 0.0, 100.0, 100.0),
            )
