"""Tests for feature output module.

Tests utility functions (no arcpy needed) and verifies stubs exist
for arcpy-dependent functions.
"""

from __future__ import annotations

import pytest

from segment_brush.feature_output import (
    OUTPUT_FIELDS,
    create_output_feature_class,
    get_timestamp,
    write_polygon,
)


class TestOutputSchema:
    """Verify the output feature class schema is well-defined."""

    def test_has_required_fields(self) -> None:
        field_names = [f[0] for f in OUTPUT_FIELDS]
        assert "source_raster" in field_names
        assert "seg_method" in field_names
        assert "smooth_level" in field_names
        assert "area_sq_m" in field_names
        assert "perimeter_m" in field_names
        assert "created_at" in field_names

    def test_field_count(self) -> None:
        assert len(OUTPUT_FIELDS) == 6


class TestGetTimestamp:
    """Test the timestamp utility."""

    def test_returns_iso_format(self) -> None:
        ts = get_timestamp()
        # Should be a valid ISO 8601 string with timezone
        assert "T" in ts
        assert "+" in ts or "Z" in ts or ts.endswith("+00:00")

    def test_returns_string(self) -> None:
        assert isinstance(get_timestamp(), str)


class TestArcpyStubs:
    """Verify arcpy-dependent functions exist and raise NotImplementedError."""

    def test_create_output_feature_class(self) -> None:
        with pytest.raises(NotImplementedError):
            create_output_feature_class("test.gdb/test", spatial_reference=None)

    def test_write_polygon(self) -> None:
        with pytest.raises(NotImplementedError):
            write_polygon(
                output_path="test.gdb/test",
                polygon=None,  # type: ignore[arg-type]
                spatial_reference=None,
                source_raster="test_raster",
                seg_method="watershed",
                smooth_level=30,
            )
