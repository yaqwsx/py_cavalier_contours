import pytest
from py_cavalier_contours import Vertex, Polyline


@pytest.fixture
def unit_square():
    """Closed CCW unit square: (0,0)-(1,0)-(1,1)-(0,1)."""
    return Polyline([
        Vertex(0, 0),
        Vertex(1, 0),
        Vertex(1, 1),
        Vertex(0, 1),
    ], closed=True)


@pytest.fixture
def unit_circle():
    """Closed circle approximated as two arc segments with radius 1 centered
    at the origin.  Vertex(1,0,1) -> Vertex(-1,0,1) traces the full circle."""
    return Polyline([
        Vertex(1, 0, 1),
        Vertex(-1, 0, 1),
    ], closed=True)


@pytest.fixture
def overlapping_squares():
    """Two closed CCW squares that overlap by half their area.

    square_a: (0,0)-(2,0)-(2,2)-(0,2)   area = 4
    square_b: (1,0)-(3,0)-(3,2)-(1,2)   area = 4
    overlap region: x in [1,2], y in [0,2]  area = 2
    union area: 4 + 4 - 2 = 6
    """
    square_a = Polyline([
        Vertex(0, 0),
        Vertex(2, 0),
        Vertex(2, 2),
        Vertex(0, 2),
    ], closed=True)
    square_b = Polyline([
        Vertex(1, 0),
        Vertex(3, 0),
        Vertex(3, 2),
        Vertex(1, 2),
    ], closed=True)
    return square_a, square_b
