import math
from copy import copy, deepcopy

import pytest

from py_cavalier_contours import Vertex


def test_vertex_attributes():
    p1 = Vertex()

    assert p1.x == 0
    assert p1.y == 0
    assert p1.bulge == 0

    p1.x = 42
    assert p1.x == 42
    assert p1.y == 0
    assert p1.bulge == 0

    p1.y = 13
    assert p1.x == 42
    assert p1.y == 13
    assert p1.bulge == 0

    p1.bulge = 1
    assert p1.x == 42
    assert p1.y == 13
    assert p1.bulge == 1

    p1.x += 10
    assert p1.x == 52
    assert p1.y == 13
    assert p1.bulge == 1

def test_vertex_copy():
    p1 = Vertex()
    p2 = copy(p1)
    p1.x = 15
    assert p1.x == 15
    assert p2.x == 0

    p3 = deepcopy(p2)
    p3.x = 42

    assert p1.x == 15
    assert p2.x == 0
    assert p3.x == 42


def test_vertex_string_equality_and_repr():
    vertex = Vertex(1, 2, 0.5)

    assert str(vertex) == "[1.0, 2.0, 0.5]"
    assert repr(vertex) == "Vertex(1.0, 2.0, 0.5)"
    assert vertex == Vertex(1, 2, 0.5)
    assert vertex != Vertex(1, 2, 0)
    assert vertex != (1, 2, 0.5)


@pytest.mark.parametrize("attribute", ["x", "y", "bulge"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_vertex_setters_reject_non_finite_values(attribute, value):
    vertex = Vertex()

    with pytest.raises(ValueError, match="finite"):
        setattr(vertex, attribute, value)


def test_vertex_rejects_non_numeric_value():
    with pytest.raises(TypeError, match="real number"):
        Vertex("not-a-number", 0)

