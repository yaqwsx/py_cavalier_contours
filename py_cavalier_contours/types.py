from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ClosestPointResult:
    """Result of a closest point query on a polyline."""
    seg_index: int
    x: float
    y: float
    distance: float


@dataclass(frozen=True)
class PointAtLengthResult:
    """Result of finding a point at a given path length on a polyline."""
    seg_index: int
    x: float
    y: float


@dataclass(frozen=True)
class BasicIntersect:
    """A basic (single point) intersection between two polyline segments."""
    seg_index1: int
    seg_index2: int
    x: float
    y: float


@dataclass(frozen=True)
class OverlappingIntersect:
    """An overlapping intersection between two polyline segments."""
    seg_index1: int
    seg_index2: int
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class IntersectsResult:
    """Collection of intersections found between two polylines."""
    basic: List[BasicIntersect]
    overlapping: List[OverlappingIntersect]
