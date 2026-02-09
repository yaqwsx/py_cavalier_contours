"""Tests for the Shape class -- construction, polyline extraction, offset,
and repr."""

import pytest
from py_cavalier_contours import Vertex, Polyline, Shape


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ccw_square(x, y, size):
    """Return a closed CCW square at (x, y) with the given side length."""
    return Polyline([
        Vertex(x, y),
        Vertex(x + size, y),
        Vertex(x + size, y + size),
        Vertex(x, y + size),
    ], closed=True)


def _make_cw_square(x, y, size):
    """Return a closed CW square (reversed winding) at (x, y)."""
    return Polyline([
        Vertex(x, y),
        Vertex(x, y + size),
        Vertex(x + size, y + size),
        Vertex(x + size, y),
    ], closed=True)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_from_single_ccw_polyline(self, unit_square):
        shape = Shape([unit_square])
        ccw = shape.ccw_polylines
        cw = shape.cw_polylines
        assert len(ccw) == 1
        assert len(cw) == 0

    def test_from_outer_and_hole(self):
        outer = _make_ccw_square(0, 0, 10)
        hole = _make_cw_square(2, 2, 3)
        shape = Shape([outer, hole])
        assert len(shape.ccw_polylines) == 1
        assert len(shape.cw_polylines) == 1

    def test_ccw_polylines_are_closed(self, unit_square):
        shape = Shape([unit_square])
        for p in shape.ccw_polylines:
            assert p.closed is True

    def test_cw_polylines_are_closed(self):
        outer = _make_ccw_square(0, 0, 10)
        hole = _make_cw_square(2, 2, 3)
        shape = Shape([outer, hole])
        for p in shape.cw_polylines:
            assert p.closed is True


# ---------------------------------------------------------------------------
# Polyline extraction preserves geometry
# ---------------------------------------------------------------------------


class TestPolylineExtraction:
    def test_ccw_area_positive(self, unit_square):
        shape = Shape([unit_square])
        ccw = shape.ccw_polylines
        assert len(ccw) == 1
        assert ccw[0].area() == pytest.approx(1.0, abs=0.01)

    def test_cw_area_negative(self):
        outer = _make_ccw_square(0, 0, 10)
        hole = _make_cw_square(2, 2, 3)
        shape = Shape([outer, hole])
        cw = shape.cw_polylines
        assert len(cw) == 1
        # CW polylines have negative signed area
        assert cw[0].area() < 0


# ---------------------------------------------------------------------------
# Offset
# ---------------------------------------------------------------------------


class TestOffset:
    def test_outward_offset_increases_area(self):
        """For a CCW shape, a negative offset distance expands outward."""
        big = _make_ccw_square(0, 0, 10)
        shape = Shape([big])
        offset_shape = shape.offset(-1.0)
        ccw = offset_shape.ccw_polylines
        assert len(ccw) >= 1
        offset_area = sum(abs(p.area()) for p in ccw)
        assert offset_area > abs(big.area())

    def test_inward_offset_decreases_area(self):
        """For a CCW shape, a positive offset distance shrinks inward."""
        big = _make_ccw_square(0, 0, 10)
        shape = Shape([big])
        offset_shape = shape.offset(1.0)
        ccw = offset_shape.ccw_polylines
        assert len(ccw) >= 1
        offset_area = sum(abs(p.area()) for p in ccw)
        assert offset_area < abs(big.area())


# ---------------------------------------------------------------------------
# repr
# ---------------------------------------------------------------------------


class TestRepr:
    def test_repr_single_outer(self, unit_square):
        shape = Shape([unit_square])
        r = repr(shape)
        assert "Shape" in r
        assert "outer=1" in r
        assert "holes=0" in r

    def test_repr_outer_and_hole(self):
        outer = _make_ccw_square(0, 0, 10)
        hole = _make_cw_square(2, 2, 3)
        shape = Shape([outer, hole])
        r = repr(shape)
        assert "outer=1" in r
        assert "holes=1" in r
