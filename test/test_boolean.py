"""Tests for boolean operations (union, intersect, difference,
symmetric_difference), offset, and containment checks on Polylines."""

import math

import pytest
from py_cavalier_contours import Vertex, Polyline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _total_area(polylines):
    """Sum of absolute areas of a list of polylines."""
    return sum(abs(p.area()) for p in polylines)


# ---------------------------------------------------------------------------
# Union
# ---------------------------------------------------------------------------


class TestUnion:
    def test_overlapping_squares_union_area(self, overlapping_squares):
        """Union of two 2x2 squares overlapping by 1x2 strip.
        Expected union area = 4 + 4 - 2 = 6."""
        sq_a, sq_b = overlapping_squares
        pos, neg = sq_a.union(sq_b)
        assert len(pos) >= 1
        total = _total_area(pos) - _total_area(neg)
        assert total == pytest.approx(6.0, abs=0.1)

    def test_union_no_holes(self, overlapping_squares):
        sq_a, sq_b = overlapping_squares
        _pos, neg = sq_a.union(sq_b)
        assert len(neg) == 0


# ---------------------------------------------------------------------------
# Intersect
# ---------------------------------------------------------------------------


class TestIntersect:
    def test_overlapping_squares_intersect_area(self, overlapping_squares):
        """Intersection of two overlapping 2x2 squares.
        Overlap is 1x2, area = 2."""
        sq_a, sq_b = overlapping_squares
        pos, neg = sq_a.intersect(sq_b)
        assert len(pos) >= 1
        total = _total_area(pos) - _total_area(neg)
        assert total == pytest.approx(2.0, abs=0.1)

    def test_disjoint_intersection_is_empty(self):
        left = Polyline([Vertex(0, 0), Vertex(1, 0), Vertex(1, 1), Vertex(0, 1)])
        right = Polyline([Vertex(3, 0), Vertex(4, 0), Vertex(4, 1), Vertex(3, 1)])
        assert left.intersect(right) == ([], [])


# ---------------------------------------------------------------------------
# Difference
# ---------------------------------------------------------------------------


class TestDifference:
    def test_overlapping_squares_difference_area(self, overlapping_squares):
        """A - B should have area = 4 - 2 = 2."""
        sq_a, sq_b = overlapping_squares
        pos, neg = sq_a.difference(sq_b)
        total = _total_area(pos) - _total_area(neg)
        assert total == pytest.approx(2.0, abs=0.1)

    def test_difference_is_not_symmetric(self, overlapping_squares):
        sq_a, sq_b = overlapping_squares
        pos_ab, neg_ab = sq_a.difference(sq_b)
        pos_ba, neg_ba = sq_b.difference(sq_a)
        area_ab = _total_area(pos_ab) - _total_area(neg_ab)
        area_ba = _total_area(pos_ba) - _total_area(neg_ba)
        # Both should be 2.0 but from different regions
        assert area_ab == pytest.approx(area_ba, abs=0.1)

    def test_contained_difference_creates_hole(self):
        outer = Polyline([
            Vertex(0, 0), Vertex(5, 0), Vertex(5, 5), Vertex(0, 5),
        ])
        inner = Polyline([
            Vertex(1, 1), Vertex(2, 1), Vertex(2, 2), Vertex(1, 2),
        ])

        positive, negative = outer.difference(inner)

        assert len(positive) == 1
        assert len(negative) == 1
        assert _total_area(positive) - _total_area(negative) == pytest.approx(24.0)


# ---------------------------------------------------------------------------
# Symmetric difference
# ---------------------------------------------------------------------------


class TestSymmetricDifference:
    def test_symmetric_difference_area_and_commutativity(self):
        """XOR keeps both non-overlapping portions, independent of order."""
        sq_a = Polyline([
            Vertex(0, 0), Vertex(3, 0), Vertex(3, 3), Vertex(0, 3),
        ], closed=True)
        sq_b = Polyline([
            Vertex(1, 1), Vertex(4, 1), Vertex(4, 4), Vertex(1, 4),
        ], closed=True)
        pos_ab, neg_ab = sq_a.symmetric_difference(sq_b)
        pos_ba, neg_ba = sq_b.symmetric_difference(sq_a)
        area_ab = _total_area(pos_ab) - _total_area(neg_ab)
        area_ba = _total_area(pos_ba) - _total_area(neg_ba)

        # Each square has area 9 and the overlap has area 4:
        # XOR = 9 + 9 - 2 * 4 = 10.
        assert area_ab == pytest.approx(10.0)
        assert area_ba == pytest.approx(10.0)
        assert len(pos_ab) == 2
        assert all(len(polyline) > 0 for polyline in pos_ab)

    def test_symmetric_difference_disjoint(self):
        """Symmetric difference of disjoint squares should return all area."""
        sq_a = Polyline([
            Vertex(0, 0), Vertex(1, 0), Vertex(1, 1), Vertex(0, 1),
        ], closed=True)
        sq_b = Polyline([
            Vertex(5, 5), Vertex(6, 5), Vertex(6, 6), Vertex(5, 6),
        ], closed=True)
        pos, neg = sq_a.symmetric_difference(sq_b)
        total = _total_area(pos) - _total_area(neg)
        assert total == pytest.approx(2.0)
        assert len(pos) == 2


# ---------------------------------------------------------------------------
# Offset
# ---------------------------------------------------------------------------


class TestOffset:
    def test_outward_offset_increases_area(self):
        """For a CCW polyline, a negative offset distance expands outward."""
        sq = Polyline([
            Vertex(0, 0), Vertex(10, 0), Vertex(10, 10), Vertex(0, 10),
        ], closed=True)
        original_area = abs(sq.area())
        results = sq.offset(-1.0)
        assert len(results) >= 1
        offset_area = sum(abs(r.area()) for r in results)
        assert offset_area > original_area

    def test_inward_offset_decreases_area(self):
        """For a CCW polyline, a positive offset distance shrinks inward."""
        big = Polyline([
            Vertex(0, 0), Vertex(10, 0), Vertex(10, 10), Vertex(0, 10),
        ], closed=True)
        original_area = abs(big.area())
        results = big.offset(1.0)
        assert len(results) >= 1
        offset_area = sum(abs(r.area()) for r in results)
        assert offset_area < original_area

    def test_large_inward_offset_vanishes(self, unit_square):
        """An inward offset bigger than half the smallest dimension should
        produce no output polylines (the shape collapses).
        For CCW, positive distance = inward."""
        results = unit_square.offset(1.0)
        assert len(results) == 0

    @pytest.mark.xfail(
        strict=True,
        reason="fixed after 0.7.0 on upstream master by cavalier_contours PR #81",
    )
    def test_repeat_position_offset_stays_finite(self):
        polyline = Polyline([
            Vertex(0, 0), Vertex(20, 0), Vertex(20, 0),
            Vertex(20, 10), Vertex(0, 10),
        ])

        results = polyline.offset(-2.0)

        assert len(results) == 1
        assert len(results[0]) == 8
        assert math.isfinite(results[0].area())
        assert math.isfinite(results[0].length())
        assert results[0].area() == pytest.approx(332.566370614359)


# ---------------------------------------------------------------------------
# Contains
# ---------------------------------------------------------------------------


class TestContains:
    def test_small_inside_big(self):
        big = Polyline([
            Vertex(0, 0), Vertex(10, 0), Vertex(10, 10), Vertex(0, 10),
        ], closed=True)
        small = Polyline([
            Vertex(2, 2), Vertex(3, 2), Vertex(3, 3), Vertex(2, 3),
        ], closed=True)
        assert big.contains(small) == "pline2_inside_pline1"

    def test_disjoint_squares(self):
        sq1 = Polyline([
            Vertex(0, 0), Vertex(1, 0), Vertex(1, 1), Vertex(0, 1),
        ], closed=True)
        sq2 = Polyline([
            Vertex(5, 5), Vertex(6, 5), Vertex(6, 6), Vertex(5, 6),
        ], closed=True)
        assert sq1.contains(sq2) == "disjoint"

    def test_intersected(self, overlapping_squares):
        sq_a, sq_b = overlapping_squares
        assert sq_a.contains(sq_b) == "intersected"
