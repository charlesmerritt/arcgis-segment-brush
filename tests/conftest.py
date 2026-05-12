"""Shared test fixtures for arcgis-segment-brush.

NOTE: arcpy is NOT available outside ArcGIS Pro. All tests that touch
arcpy-dependent modules must mock it. The core segmentation and brush
modules are designed to be testable without arcpy.
"""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """A 100×100 RGB image with a clear square object in the center.

    The center 40×40 pixels are bright (200, 200, 200),
    the background is dark (50, 50, 50). This creates obvious edges
    for testing segmentation.
    """
    img = np.full((100, 100, 3), 50, dtype=np.uint8)
    img[30:70, 30:70, :] = 200
    return img


@pytest.fixture
def sample_stroke_around_square() -> np.ndarray:
    """A brush stroke (pixel coords) that approximately traces the center square.

    The stroke follows a rough path around the 30:70 square in the sample image,
    with some imprecision (as a real user would paint).
    """
    # Approximate path around the square, slightly offset (simulating human painting)
    points = []
    # Top edge (row ~28, cols 28→72)
    for col in range(28, 73, 2):
        points.append((28, col))
    # Right edge (col ~72, rows 28→72)
    for row in range(28, 73, 2):
        points.append((row, 72))
    # Bottom edge (row ~72, cols 72→28)
    for col in range(72, 27, -2):
        points.append((72, col))
    # Left edge (col ~28, rows 72→28)
    for row in range(72, 27, -2):
        points.append((row, 28))
    # Close the loop
    points.append((28, 28))

    return np.array(points, dtype=np.int32)
