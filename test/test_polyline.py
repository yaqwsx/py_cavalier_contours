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

    def test_constructor_rejects_non_vertex_elements(self):
        with pytest.raises(TypeError, match="only contain vertices"):
            Polyline([(0, 0, 0)])

    @pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
    def test_constructor_rejects_non_finite_vertex_coordinates(self, value):
        with pytest.raises(ValueError, match="finite"):
            Vertex(value, 0)


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

    def test_append_rejects_non_vertex(self):
        with pytest.raises(TypeError, match="only contain vertices"):
            Polyline().append((10, 20, 0))

    @pytest.mark.parametrize(
        ("index", "expected_x"),
        [
            (0, [9, 0, 1, 2]),
            (1, [0, 9, 1, 2]),
            (99, [0, 1, 2, 9]),
            (-99, [9, 0, 1, 2]),
        ],
    )
    def test_insert_matches_mutable_sequence_semantics(self, index, expected_x):
        p = Polyline([Vertex(0, 0), Vertex(1, 0), Vertex(2, 0)])
        p.insert(index, Vertex(9, 0))
        assert [v.x for v in p] == expected_x

    def test_insert_rejects_non_vertex(self):
        with pytest.raises(TypeError, match="only contain vertices"):
            Polyline().insert(0, (1, 2, 3))

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

    def test_slice_assignment_and_deletion_not_supported(self, unit_square):
        with pytest.raises(NotImplementedError):
            unit_square[0:2] = [Vertex(2, 2)]
        with pytest.raises(NotImplementedError):
            del unit_square[0:2]

    def test_non_integer_index_rejected(self, unit_square):
        with pytest.raises(TypeError, match="indices must be integers"):
            unit_square["0"]

    def test_add_polylines(self, unit_square):
        extra = Polyline([Vertex(9, 9)])
        combined = unit_square + extra
        assert len(combined) == 5
        assert combined[-1].x == pytest.approx(9)

    def test_iadd_polylines(self):
        p = Polyline([Vertex(0, 0)])
        p += [Vertex(1, 1)]
        assert len(p) == 2

    def test_radd_vertices(self, unit_square):
        combined = [Vertex(-1, -1)] + unit_square
        assert [(v.x, v.y) for v in list(combined)[:2]] == [(-1, -1), (0, 0)]

    def test_equality_detects_extra_none_item(self):
        p = Polyline([Vertex(1, 2)])
        assert p != [Vertex(1, 2), None]
        assert Polyline() != [None]

    def test_close_is_idempotent_and_context_manager_closes(self):
        with Polyline([Vertex(0, 0)]) as p:
            assert len(p) == 1
        with pytest.raises(GeometryError, match="native status"):
            len(p)
        p.close()

        with pytest.raises(GeometryError, match="closed"):
            with p:
                pass


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

    @pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
    def test_transforms_reject_non_finite_values(self, unit_square, value):
        with pytest.raises(ValueError, match="finite"):
            unit_square.scale(value)
        with pytest.raises(ValueError, match="finite"):
            unit_square.translate(value, 0)


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

    def test_clear_and_reserve(self, unit_square):
        unit_square.reserve(10)
        unit_square.clear()
        assert len(unit_square) == 0

    @pytest.mark.parametrize("value, exception", [(-1, ValueError), (1.5, TypeError)])
    def test_reserve_rejects_invalid_capacity(self, unit_square, value, exception):
        with pytest.raises(exception):
            unit_square.reserve(value)


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

    @pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
    def test_rejects_non_finite_query(self, unit_square, value):
        with pytest.raises(ValueError, match="finite"):
            unit_square.closest_point(value, 0)

    def test_rejects_non_positive_epsilon(self, unit_square):
        with pytest.raises(ValueError, match="greater than zero"):
            unit_square.closest_point(0, 0, pos_equal_eps=0)

    def test_empty_polyline_raises(self):
        with pytest.raises(GeometryError, match="no segments"):
            Polyline().closest_point(0, 0)


class TestPointAtLength:
    def test_midpoint_of_first_edge(self, unit_square):
        result = unit_square.point_at_length(0.5)
        assert result.x == pytest.approx(0.5)
        assert result.y == pytest.approx(0)
        assert result.seg_index == 0

    def test_beyond_total_raises(self, unit_square):
        with pytest.raises(GeometryError):
            unit_square.point_at_length(100.0)

    def test_empty_raises_without_returning_fabricated_point(self):
        with pytest.raises(GeometryError, match="empty"):
            Polyline().point_at_length(0)

    def test_negative_length_rejected(self, unit_square):
        with pytest.raises(ValueError, match="non-negative"):
            unit_square.point_at_length(-1)

    @pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
    def test_non_finite_length_rejected(self, unit_square, value):
        with pytest.raises(ValueError, match="finite"):
            unit_square.point_at_length(value)


# ---------------------------------------------------------------------------
# Self-intersection
# ---------------------------------------------------------------------------


class TestSelfIntersect:
    def test_simple_square_no_self_intersect(self, unit_square):
        assert unit_square.has_self_intersect() is False

    def test_bow_tie_has_self_intersection(self):
        bow_tie = Polyline([
            Vertex(0, 0), Vertex(2, 2), Vertex(0, 2), Vertex(2, 0),
        ])
        assert bow_tie.has_self_intersect() is True

    def test_nan_epsilon_rejected(self, unit_square):
        with pytest.raises(ValueError, match="finite"):
            unit_square.has_self_intersect(math.nan)


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

    @pytest.mark.parametrize("value", [0, -1, math.nan, math.inf])
    def test_invalid_error_distance_rejected(self, unit_circle, value):
        with pytest.raises(ValueError):
            unit_circle.to_lines(value)


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

    def test_overlapping_collinear_segments(self):
        first = Polyline([Vertex(0, 0), Vertex(3, 0)], closed=False)
        second = Polyline([Vertex(1, 0), Vertex(2, 0)], closed=False)

        result = first.find_intersects(second)

        assert len(result.basic) == 0
        assert len(result.overlapping) == 1
        overlap = result.overlapping[0]
        assert {(overlap.x1, overlap.y1), (overlap.x2, overlap.y2)} == {
            (1.0, 0.0), (2.0, 0.0),
        }

    def test_rejects_non_polyline(self, unit_square):
        with pytest.raises(TypeError, match="other must be a Polyline"):
            unit_square.find_intersects(object())


class TestRotateStart:
    def test_rotates_closed_polyline_to_existing_vertex(self, unit_square):
        unit_square.rotate_start(2, 1, 1)
        assert (unit_square[0].x, unit_square[0].y) == pytest.approx((1, 1))
        assert unit_square.area() == pytest.approx(1.0)

    def test_rejects_open_polyline(self):
        open_polyline = Polyline(
            [Vertex(0, 0), Vertex(1, 0), Vertex(2, 0)], closed=False)
        with pytest.raises(GeometryError, match="Cannot rotate start"):
            open_polyline.rotate_start(1, 1, 0)


class TestBinaryArgumentValidation:
    @pytest.mark.parametrize(
        "method",
        ["union", "intersect", "difference", "symmetric_difference", "contains"],
    )
    def test_binary_operations_reject_non_polyline(self, unit_square, method):
        with pytest.raises(TypeError, match="other must be a Polyline"):
            getattr(unit_square, method)(object())
