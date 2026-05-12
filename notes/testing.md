# Testing Strategy

> Project: arcgis-segment-brush
> Created: 2026-05-12

## Current Coverage

- 34 tests covering interface skeleton
- All stubs verified as importable and callable
- Brush session logic fully tested (start, paint, close, reset, coordinate conversion)
- Coordinate conversion (map↔pixel) tested with round-trip verification
- Feature class schema verified
- Test runner: pytest

## Testing Patterns

- Tests mirror source structure: `tests/test_<module>.py`
- Fixtures in `tests/conftest.py` (sample RGB image, sample brush stroke)
- **No arcpy in tests** — the core segmentation and brush modules are arcpy-free
  by design. Arcpy-dependent modules (raster_io, feature_output) have stubs
  verified as raising NotImplementedError.
- When implementations land, real segmentation tests will use the synthetic
  fixtures (100×100 image with a clear square object, stroke that traces it)

## Two-Tier Testing

### Tier 1: Unit tests (run anywhere, no ArcGIS license)
- Segmentation pipeline (numpy + scikit-image + shapely)
- Brush session management
- Coordinate conversion
- Polygon smoothing
- Run with `make test` on any machine

### Tier 2: Integration tests (require ArcGIS Pro)
- Raster window extraction via arcpy
- Feature class creation and writing
- Toolbox parameter validation
- These will be marked with `@pytest.mark.arcgis` and skipped when arcpy
  is not available

## Regression Prevention

These tests exist to prevent:
- Breaking the public interface contract (function signatures)
- Removing or renaming segmentation pipeline steps
- Breaking brush session logic (loop closure, coordinate conversion)
- Schema changes to the output feature class without updating tests

## Next Steps

- Add algorithm tests as segmentation functions are implemented
- Add integration tests with `@pytest.mark.arcgis` for ArcGIS-dependent code
- Add property-based tests for coordinate conversion edge cases
- Add visual regression tests (save expected polygon output, compare)
