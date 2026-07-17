"""Tests for the Shape class -- construction, polyline extraction, offset,
and repr."""

import math
from copy import copy, deepcopy

import pytest
from py_cavalier_contours import Vertex, Polyline, Shape, GeometryError


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

    def test_accepts_generator_without_partial_construction_failure(self):
        shape = Shape(p for p in [_make_ccw_square(0, 0, 2)])
        assert len(shape.ccw_polylines) == 1

    def test_rejects_open_polyline(self):
        open_polyline = Polyline(
            [Vertex(0, 0), Vertex(1, 0)], closed=False)
        with pytest.raises(ValueError, match="closed polylines"):
            Shape([open_polyline])

    def test_rejects_non_polyline(self):
        with pytest.raises(TypeError, match="only contain Polylines"):
            Shape([object()])

    def test_rejects_non_iterable(self):
        with pytest.raises(TypeError, match="iterable"):
            Shape(42)

    def test_rejects_single_vertex_boundary(self):
        with pytest.raises(ValueError, match="at least two vertices"):
            Shape([Polyline([Vertex(0, 0)])])

    def test_rejects_closed_native_object(self, unit_square):
        unit_square.close()
        with pytest.raises(GeometryError, match="released Polyline"):
            Shape([unit_square])

    def test_close_is_idempotent_and_context_manager_closes(self, unit_square):
        with Shape([unit_square]) as shape:
            assert len(shape.ccw_polylines) == 1
        with pytest.raises(GeometryError, match="native status"):
            repr(shape)
        shape.close()
        with pytest.raises(GeometryError, match="closed"):
            with shape:
                pass


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

    @pytest.mark.parametrize("copier", [copy, deepcopy])
    def test_copy_preserves_outer_and_hole(self, copier):
        shape = Shape([
            _make_ccw_square(0, 0, 10),
            _make_cw_square(2, 2, 3),
        ])

        duplicate = copier(shape)

        assert len(duplicate.ccw_polylines) == 1
        assert len(duplicate.cw_polylines) == 1
        assert repr(duplicate) == "Shape(outer=1, holes=1)"


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

    @pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
    def test_rejects_non_finite_offset(self, unit_square, value):
        shape = Shape([unit_square])
        with pytest.raises(ValueError, match="finite"):
            shape.offset(value)

    def test_rejects_non_positive_tolerance(self, unit_square):
        shape = Shape([unit_square])
        with pytest.raises(ValueError, match="greater than zero"):
            shape.offset(1, pos_equal_eps=0)


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
