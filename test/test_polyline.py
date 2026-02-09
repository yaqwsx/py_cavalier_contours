"""Tests for Polyline construction, sequence protocol, geometry queries, and
transforms."""

import math
from copy import copy, deepcopy

import pytest
from py_cavalier_contours import Vertex, Polyline, GeometryError


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_empty_polyline(self):
        p = Polyline()
        assert len(p) == 0
        assert p.closed is True  # default

    def test_empty_open_polyline(self):
        p = Polyline([], closed=False)
        assert len(p) == 0
        assert p.closed is False

    def test_from_vertices_closed(self, unit_square):
        assert len(unit_square) == 4
        assert unit_square.closed is True

    def test_from_vertices_open(self):
        p = Polyline([Vertex(0, 0), Vertex(1, 0)], closed=False)
        assert len(p) == 2
        assert p.closed is False

    def test_toggle_closed(self, unit_square):
        unit_square.closed = False
        assert unit_square.closed is False
        unit_square.closed = True
        assert unit_square.closed is True


# ---------------------------------------------------------------------------
# Sequence protocol
# ---------------------------------------------------------------------------


class TestSequenceProtocol:
    def test_len(self, unit_square):
        assert len(unit_square) == 4

    def test_getitem_positive(self, unit_square):
        v = unit_square[0]
        assert v.x == pytest.approx(0)
        assert v.y == pytest.approx(0)

    def test_getitem_negative(self, unit_square):
        v = unit_square[-1]
        assert v.x == pytest.approx(0)
        assert v.y == pytest.approx(1)

    def test_getitem_out_of_range(self, unit_square):
        with pytest.raises(IndexError):
            unit_square[10]

    def test_setitem(self, unit_square):
        unit_square[0] = Vertex(5, 5, 0)
        v = unit_square[0]
        assert v.x == pytest.approx(5)
        assert v.y == pytest.approx(5)

    def test_setitem_type_error(self, unit_square):
        with pytest.raises(TypeError):
            unit_square[0] = (1, 2, 3)

    def test_delitem(self, unit_square):
        del unit_square[0]
        assert len(unit_square) == 3
        # The former index-1 vertex should now be at index 0
        v = unit_square[0]
        assert v.x == pytest.approx(1)
        assert v.y == pytest.approx(0)

    def test_delitem_negative(self, unit_square):
        del unit_square[-1]
        assert len(unit_square) == 3

    def test_append(self):
        p = Polyline()
        p.append(Vertex(10, 20))
        assert len(p) == 1
        v = p[0]
        assert v.x == pytest.approx(10)
        assert v.y == pytest.approx(20)

    def test_iteration(self, unit_square):
        coords = [(v.x, v.y) for v in unit_square]
        assert coords == [
            pytest.approx((0, 0)),
            pytest.approx((1, 0)),
            pytest.approx((1, 1)),
            pytest.approx((0, 1)),
        ]

    def test_slice_getitem_not_supported(self, unit_square):
        with pytest.raises(NotImplementedError):
            unit_square[0:2]

    def test_add_polylines(self, unit_square):
        extra = Polyline([Vertex(9, 9)])
        combined = unit_square + extra
        assert len(combined) == 5
        assert combined[-1].x == pytest.approx(9)

    def test_iadd_polylines(self):
        p = Polyline([Vertex(0, 0)])
        p += [Vertex(1, 1)]
        assert len(p) == 2


# ---------------------------------------------------------------------------
# Copy / deepcopy
# ---------------------------------------------------------------------------


class TestCopy:
    def test_copy_produces_equal_polyline(self, unit_square):
        p2 = copy(unit_square)
        assert len(p2) == len(unit_square)
        for v1, v2 in zip(unit_square, p2):
            assert v1.x == pytest.approx(v2.x)
            assert v1.y == pytest.approx(v2.y)
            assert v1.bulge == pytest.approx(v2.bulge)

    def test_copy_independent_via_delete(self, unit_square):
        """Verify copy independence by deleting from original."""
        p2 = copy(unit_square)
        del unit_square[-1]
        assert len(unit_square) == 3
        assert len(p2) == 4

    def test_deepcopy_produces_equal_polyline(self, unit_square):
        p2 = deepcopy(unit_square)
        assert len(p2) == len(unit_square)
        for v1, v2 in zip(unit_square, p2):
            assert v1.x == pytest.approx(v2.x)
            assert v1.y == pytest.approx(v2.y)

    def test_deepcopy_independent_via_delete(self, unit_square):
        p2 = deepcopy(unit_square)
        del unit_square[-1]
        assert len(unit_square) == 3
        assert len(p2) == 4


# ---------------------------------------------------------------------------
# Geometric properties
# ---------------------------------------------------------------------------


class TestLength:
    def test_unit_square_perimeter(self, unit_square):
        assert unit_square.length() == pytest.approx(4.0)

    def test_open_segment_length(self):
        seg = Polyline([Vertex(0, 0), Vertex(3, 4)], closed=False)
        assert seg.length() == pytest.approx(5.0)


class TestArea:
    def test_unit_square_area(self, unit_square):
        assert unit_square.area() == pytest.approx(1.0)

    def test_area_sign_flips_with_reverse(self, unit_square):
        original_area = unit_square.area()
        unit_square.reverse()
        assert unit_square.area() == pytest.approx(-original_area)

    def test_circle_area(self, unit_circle):
        assert unit_circle.area() == pytest.approx(math.pi, abs=1e-4)


class TestWindingNumber:
    def test_inside_unit_square(self, unit_square):
        wn = unit_square.winding_number(0.5, 0.5)
        assert wn != 0

    def test_outside_unit_square(self, unit_square):
        wn = unit_square.winding_number(5.0, 5.0)
        assert wn == 0


class TestBoundingBox:
    def test_unit_square_bbox(self, unit_square):
        minx, miny, maxx, maxy = unit_square.bounding_box()
        assert minx == pytest.approx(0)
        assert miny == pytest.approx(0)
        assert maxx == pytest.approx(1)
        assert maxy == pytest.approx(1)

    def test_empty_raises(self):
        p = Polyline()
        with pytest.raises(GeometryError):
            p.bounding_box()


class TestOrientation:
    def test_ccw_square(self, unit_square):
        assert unit_square.orientation == "ccw"

    def test_cw_after_reverse(self, unit_square):
        unit_square.reverse()
        assert unit_square.orientation == "cw"

    def test_open_polyline(self):
        p = Polyline([Vertex(0, 0), Vertex(1, 0)], closed=False)
        assert p.orientation == "open"


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------


class TestTransforms:
    def test_scale(self, unit_square):
        unit_square.scale(2.0)
        minx, miny, maxx, maxy = unit_square.bounding_box()
        assert minx == pytest.approx(0)
        assert miny == pytest.approx(0)
        assert maxx == pytest.approx(2)
        assert maxy == pytest.approx(2)

    def test_translate(self, unit_square):
        unit_square.translate(10, 20)
        minx, miny, maxx, maxy = unit_square.bounding_box()
        assert minx == pytest.approx(10)
        assert miny == pytest.approx(20)
        assert maxx == pytest.approx(11)
        assert maxy == pytest.approx(21)


# ---------------------------------------------------------------------------
# Vertex cleanup
# ---------------------------------------------------------------------------


class TestVertexCleanup:
    def test_remove_repeated(self):
        p = Polyline([
            Vertex(0, 0), Vertex(0, 0), Vertex(1, 0), Vertex(1, 1),
        ], closed=True)
        p.remove_repeated()
        assert len(p) == 3

    def test_remove_redundant_collinear(self):
        """Three collinear points on a line should reduce to two."""
        p = Polyline([
            Vertex(0, 0), Vertex(0.5, 0), Vertex(1, 0),
            Vertex(1, 1), Vertex(0, 1),
        ], closed=True)
        original_len = len(p)
        p.remove_redundant()
        assert len(p) < original_len


# ---------------------------------------------------------------------------
# Closest point / point at length
# ---------------------------------------------------------------------------


class TestClosestPoint:
    def test_point_outside_square(self, unit_square):
        result = unit_square.closest_point(2.0, 0.5)
        assert result.x == pytest.approx(1.0)
        assert result.y == pytest.approx(0.5)
        assert result.distance == pytest.approx(1.0)

    def test_closest_point_on_vertex(self, unit_square):
        result = unit_square.closest_point(-1, 0)
        assert result.x == pytest.approx(0)
        assert result.y == pytest.approx(0)
        assert result.distance == pytest.approx(1.0)


class TestPointAtLength:
    def test_midpoint_of_first_edge(self, unit_square):
        result = unit_square.point_at_length(0.5)
        assert result.x == pytest.approx(0.5)
        assert result.y == pytest.approx(0)
        assert result.seg_index == 0

    def test_beyond_total_raises(self, unit_square):
        with pytest.raises(GeometryError):
            unit_square.point_at_length(100.0)


# ---------------------------------------------------------------------------
# Self-intersection
# ---------------------------------------------------------------------------


class TestSelfIntersect:
    def test_simple_square_no_self_intersect(self, unit_square):
        assert unit_square.has_self_intersect() is False


# ---------------------------------------------------------------------------
# to_lines
# ---------------------------------------------------------------------------


class TestToLines:
    def test_circle_to_lines_all_zero_bulge(self, unit_circle):
        lines = unit_circle.to_lines()
        assert len(lines) > 2  # should have many segments
        for v in lines:
            assert v.bulge == pytest.approx(0)

    def test_to_lines_preserves_closed(self, unit_circle):
        lines = unit_circle.to_lines()
        assert lines.closed is True


# ---------------------------------------------------------------------------
# find_intersects
# ---------------------------------------------------------------------------


class TestFindIntersects:
    def test_two_crossing_segments(self):
        """An X-cross of two open segments should produce one basic
        intersection at the crossing point."""
        seg1 = Polyline([Vertex(0, 0), Vertex(2, 2)], closed=False)
        seg2 = Polyline([Vertex(0, 2), Vertex(2, 0)], closed=False)
        result = seg1.find_intersects(seg2)
        assert len(result.basic) == 1
        pt = result.basic[0]
        assert pt.x == pytest.approx(1.0)
        assert pt.y == pytest.approx(1.0)
        assert len(result.overlapping) == 0

    def test_no_intersection_parallel(self):
        seg1 = Polyline([Vertex(0, 0), Vertex(1, 0)], closed=False)
        seg2 = Polyline([Vertex(0, 1), Vertex(1, 1)], closed=False)
        result = seg1.find_intersects(seg2)
        assert len(result.basic) == 0
        assert len(result.overlapping) == 0
