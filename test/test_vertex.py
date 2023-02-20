from py_cavalier_contours import Vertex
from copy import copy, deepcopy


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


