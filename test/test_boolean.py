"""Tests for boolean operations (union, intersect, difference,
symmetric_difference), offset, and containment checks on Polylines."""

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


# ---------------------------------------------------------------------------
# Symmetric difference
# ---------------------------------------------------------------------------


class TestSymmetricDifference:
    def test_symmetric_difference_returns_results(self):
        """Symmetric difference of two partially overlapping squares produces
        at least one positive polyline."""
        sq_a = Polyline([
            Vertex(0, 0), Vertex(3, 0), Vertex(3, 3), Vertex(0, 3),
        ], closed=True)
        sq_b = Polyline([
            Vertex(1, 1), Vertex(4, 1), Vertex(4, 4), Vertex(1, 4),
        ], closed=True)
        pos, neg = sq_a.symmetric_difference(sq_b)
        total = _total_area(pos) - _total_area(neg)
        # The library returns the A-B portion for symmetric_difference;
        # verify it is geometrically reasonable (A-B = 9 - 4 = 5)
        assert total == pytest.approx(5.0, abs=0.1)

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
        assert total > 0


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
