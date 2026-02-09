from __future__ import annotations
from typing import Iterable, Union, Tuple, List, Any
from collections.abc import MutableSequence, Sized
from itertools import zip_longest

from .py_cavalier_contours import lib, ffi
from .types import (
    ClosestPointResult, PointAtLengthResult, BasicIntersect,
    OverlappingIntersect, IntersectsResult,
)

class GeometryError(RuntimeError):
    pass

class Vertex:
    __slots__ = "native",

    def __init__(self, x: float = 0, y: float = 0, bulge: float = 0) -> None:
        self.native = ffi.new("cavc_vertex*")
        self.native.x = x
        self.native.y = y
        self.native.bulge = bulge

    @property
    def x(self) -> float:
        return float(self.native.x)

    @x.setter
    def x(self, value: float) -> None:
        self.native.x = value

    @property
    def y(self) -> float:
        return float(self.native.y)

    @y.setter
    def y(self, value: float) -> None:
        self.native.y = value

    @property
    def bulge(self) -> float:
        return float(self.native.bulge)

    @bulge.setter
    def bulge(self, value: float) -> None:
        self.native.bulge = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vertex):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.bulge == other.bulge

    def __str__(self) -> str:
        return f"[{self.x}, {self.y}, {self.bulge}]"

    def __repr__(self) -> str:
        return f"Vertex({self.x}, {self.y}, {self.bulge})"

    def __copy__(self) -> Vertex:
        return Vertex(self.native.x, self.native.y, self.native.bulge)

    def __deepcopy__(self, memo: Any) -> Vertex:
        return self.__copy__()


class Polyline(MutableSequence[Vertex]):
    __slots__ = "native",

    def __init__(self, vertices: Iterable[Vertex] = [], closed: bool = True ) -> None:
        p_native = ffi.new("cavc_pline**")
        dummy_data = ffi.new("cavc_vertex*", None)
        lib.cavc_pline_create(dummy_data, 0, closed, p_native)
        self.native = p_native[0]

        if isinstance(vertices, Sized):
            lib.cavc_pline_reserve(self.native, len(vertices))
        for v in vertices:
            lib.cavc_pline_add(self.native, v.x, v.y, v.bulge)

    def __del__(self) -> None:
        lib.cavc_pline_f(self.native)

    def __str__(self) -> str:
        return f"Polyline({', '.join([str(x) for x in self])})"

    def __repr__(self) -> str:
        return f"Polyline({', '.join([str(x) for x in self])})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Iterable):
            return NotImplemented
        return all(l == r for l, r in zip_longest(self, other))

    def _ensure_in_range(self, i: int) -> int:
        if i < 0:
                i = len(self) + i
        if i < 0 or i >= len(self):
            raise IndexError()
        return i

    def __getitem__(self, i: Union[int, slice]) -> Any: # Union[Vertex, Polyline]
        if isinstance(i, slice):
            raise NotImplementedError("Slices are not supported for getitem")
        else:
            i = self._ensure_in_range(i)
            v = Vertex()
            lib.cavc_pline_get_vertex(self.native, i, v.native)
            return v

    def __setitem__(self, i: Union[int, slice], item: Union[Vertex, Iterable[Vertex]]) -> None:
        if isinstance(i, slice):
            raise NotImplementedError("Slices are not supported for for setitem")
        else:
            i = self._ensure_in_range(i)
            if not isinstance(item, Vertex):
                raise TypeError("Polyline can only contain vertices")
            lib.cavc_pline_set_vertex(self.native, i, item.native[0])

    def __delitem__(self, i: Union[int, slice]) -> None:
        if isinstance(i, slice):
            raise NotImplementedError("Slices are not supported for for setitem")
        else:
            i = self._ensure_in_range(i)
            lib.cavc_pline_remove(self.native, i)

    def __add__(self, other: Union[Polyline, Iterable[Vertex]]) -> Polyline:
        pline = self.__copy__()
        pline += other
        return pline

    def __radd__(self, other: Union[Polyline, Iterable[Vertex]]) -> Polyline:
        p = Polyline()
        for v in other:
            p.append(v)
        for v in self:
            p.append(v)
        return p

    def __iadd__(self, other: Union[Polyline, Iterable[Vertex]]) -> Polyline:
        for v in other:
            self.append(v)
        return self

    def __len__(self) -> int:
        psize = ffi.new("uint32_t*")
        lib.cavc_pline_get_vertex_count(self.native, psize)
        return int(psize[0])

    def __copy__(self) -> Polyline:
        pline = self.__class__.__new__(self.__class__)

        p_native = ffi.new("cavc_pline**")
        lib.cavc_pline_clone(self.native, p_native)
        pline.native = p_native[0]

        return pline

    def __deepcopy__(self, memo: Any) -> Polyline:
        return self.__copy__()

    def length(self) -> float:
        """
        Return length of the polyline
        """
        l = ffi.new("double*")
        lib.cavc_pline_eval_path_length(self.native, l)
        return float(l[0])

    def area(self) -> float:
        """
        Return area of the polyline
        """
        a = ffi.new("double*")
        lib.cavc_pline_eval_area(self.native, a)
        return float(a[0])

    def winding_number(self, x: float, y: float) -> int:
        """
        Return winding number of a point relative to the polyline.
        Non-zero means the point is inside.
        """
        wn = ffi.new("int32_t*")
        lib.cavc_pline_eval_wn(self.native, x, y, wn)
        return int(wn[0])

    def reverse(self) -> None:
        """
        Reverse the direction
        """
        lib.cavc_pline_invert_direction(self.native)

    def scale(self, factor: float) -> None:
        """
        Scale the polyline around [0, 0]
        """
        lib.cavc_pline_scale(self.native, factor)

    def translate(self, x: float, y: float) -> None:
        """
        Translate the polyline
        """
        lib.cavc_pline_translate(self.native, x, y)

    def remove_repeated(self, eps: float = 1e-5) -> None:
        """
        Remove repeated vertices
        """
        lib.cavc_pline_remove_repeat_pos(self.native, eps)

    def remove_redundant(self, eps: float = 1e-5) -> None:
        """
        Remove redundant vertices.

        Redundant vertexes can arise with multiple vertexes on top of each
        other, along a straight line, or forming a concentric arc with sweep
        angle less than or equal to PI.
        """
        lib.cavc_pline_remove_redundant(self.native, eps)

    def clear(self) -> None:
        """
        Clear all polygons
        """
        lib.cavc_pline_clear(self.native)

    def append(self, v: Vertex) -> None:
        """
        Append a vertex to the end of the list
        """
        lib.cavc_pline_add(self.native, v.x, v.y, v.bulge)

    def insert(self, index: int, v: Vertex) -> None:
        """
        Insert a vertex at given index
        """
        raise NotImplementedError("insert is not yet supported")

    def reserve(self, additional: int) -> None:
        """
        Reserve space for additional vertices in the underlying storage
        """
        lib.cavc_pline_reserve(self.native, additional)

    def bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Compute bounding box and return it as (minx, miny, maxx, maxy)
        """
        minx = ffi.new("double*")
        miny = ffi.new("double*")
        maxx = ffi.new("double*")
        maxy = ffi.new("double*")
        retval = lib.cavc_pline_eval_extents(self.native, minx, miny, maxx, maxy)
        if retval == 2:
            raise GeometryError("Cannot evaluate bounding box on less than 1 vertice")
        return minx[0], miny[0], maxx[0], maxy[0]

    @property
    def closed(self) -> bool:
        c = ffi.new("uint8_t*")
        lib.cavc_pline_get_is_closed(self.native, c)
        return bool(c[0])

    @closed.setter
    def closed(self, value: bool) -> None:
        lib.cavc_pline_set_is_closed(self.native, value)

    @staticmethod
    def _pythonizePlist(list_handle: Any) -> List[Polyline]:
        """
        Given a cavc_pline* handle, turn it into a Python list of Polylines and
        free the original native list.
        """
        count = ffi.new("uint32_t*")
        lib.cavc_plinelist_get_count(list_handle, count)
        result: List[Polyline] = []
        for i in range(count[0]):
            p_native = ffi.new("cavc_pline **")
            lib.cavc_plinelist_take(list_handle, i, p_native)
            polyline = Polyline.__new__(Polyline)
            polyline.native = p_native[0]
            result.append(polyline)
        lib.cavc_plinelist_f(list_handle)
        return result


    def offset(self, distance: float, handle_self_intersects: bool = True,
        pos_equal_eps: float = 1e-5, slice_join_eps: float = 1e-5,
        offset_dist_eps: float = 1e-5) -> List[Polyline]:
        """
        Compute offset.
        """
        options = ffi.new("cavc_pline_parallel_offset_o*")
        lib.cavc_pline_parallel_offset_o_init(options)
        options.pos_equal_eps = pos_equal_eps
        options.slice_join_eps = slice_join_eps
        options.offset_dist_eps = offset_dist_eps
        options.handle_self_intersects = handle_self_intersects

        result = ffi.new("cavc_plinelist**")
        lib.cavc_pline_parallel_offset(self.native, distance, options, result)
        return Polyline._pythonizePlist(result[0])

    def _bool_op(self, other: Polyline, op: int,
                 pos_equal_eps: float) -> Tuple[List[Polyline], List[Polyline]]:
        options = ffi.new("cavc_pline_boolean_o*")
        lib.cavc_pline_boolean_o_init(options)
        options.pos_equal_eps = pos_equal_eps

        pos_result = ffi.new("cavc_plinelist**")
        neg_result = ffi.new("cavc_plinelist**")
        lib.cavc_pline_boolean(self.native, other.native, op, options, pos_result, neg_result)
        return Polyline._pythonizePlist(pos_result[0]), Polyline._pythonizePlist(neg_result[0])

    def union(self, other: Polyline,
              pos_equal_eps: float = 1e-5) -> Tuple[List[Polyline], List[Polyline]]:
        """
        Return union of two polylines. Returns a tuple of (positive polylines,
        negative polylines) where positive are outlines and negative are holes.
        """
        return self._bool_op(other, 0, pos_equal_eps)

    def intersect(self, other: Polyline,
              pos_equal_eps: float = 1e-5) -> Tuple[List[Polyline], List[Polyline]]:
        """
        Return intersection of two polylines. Returns a tuple of (positive
        polylines, negative polylines).
        """
        return self._bool_op(other, 1, pos_equal_eps)

    def difference(self, other: Polyline,
              pos_equal_eps: float = 1e-5) -> Tuple[List[Polyline], List[Polyline]]:
        """
        Return difference self - other. Returns a tuple of (positive polylines,
        negative polylines).
        """
        return self._bool_op(other, 2, pos_equal_eps)

    def symmetric_difference(self, other: Polyline,
              pos_equal_eps: float = 1e-5) -> Tuple[List[Polyline], List[Polyline]]:
        """
        Return symmetric difference. Returns a tuple of (positive polylines,
        negative polylines).
        """
        return self._bool_op(other, 3, pos_equal_eps)

    def has_self_intersect(self, pos_equal_eps: float = 1e-5) -> bool:
        """
        Check if the polyline has any self-intersections.
        """
        options = ffi.new("cavc_pline_self_intersect_o*")
        lib.cavc_pline_self_intersect_o_init(options)
        options.pos_equal_eps = pos_equal_eps

        result = ffi.new("uint8_t*")
        lib.cavc_pline_scan_for_self_intersect(self.native, options, result)
        return bool(result[0])

    _CONTAINS_RESULTS = {
        0: "invalid",
        1: "pline1_inside_pline2",
        2: "pline2_inside_pline1",
        3: "disjoint",
        4: "intersected",
    }

    def contains(self, other: Polyline, pos_equal_eps: float = 1e-5) -> str:
        """
        Test the containment relationship between this polyline and another.

        Returns one of:
        - "pline1_inside_pline2": self is inside other
        - "pline2_inside_pline1": other is inside self
        - "disjoint": no overlap
        - "intersected": polylines intersect
        - "invalid": invalid input
        """
        options = ffi.new("cavc_pline_contains_o*")
        lib.cavc_pline_contains_o_init(options)
        options.pos_equal_eps = pos_equal_eps

        result = ffi.new("uint32_t*")
        lib.cavc_pline_contains(self.native, other.native, options, result)
        return self._CONTAINS_RESULTS.get(result[0], "unknown")

    @property
    def orientation(self) -> str:
        """
        Get the orientation of the polyline.

        Returns "open", "cw" (clockwise), or "ccw" (counter-clockwise).
        """
        o = ffi.new("uint32_t*")
        lib.cavc_pline_orientation(self.native, o)
        return {0: "open", 1: "cw", 2: "ccw"}.get(o[0], "unknown")

    def closest_point(self, x: float, y: float,
                      pos_equal_eps: float = 1e-5) -> ClosestPointResult:
        """
        Find the closest point on this polyline to the given point.

        Returns a ClosestPointResult with seg_index, x, y, distance.
        Raises GeometryError if the polyline has no segments.
        """
        seg_idx = ffi.new("uint32_t*")
        cx = ffi.new("double*")
        cy = ffi.new("double*")
        dist = ffi.new("double*")
        ret = lib.cavc_pline_closest_point(
            self.native, x, y, pos_equal_eps, seg_idx, cx, cy, dist)
        if ret == 2:
            raise GeometryError("Polyline has no segments")
        return ClosestPointResult(
            seg_index=int(seg_idx[0]), x=float(cx[0]),
            y=float(cy[0]), distance=float(dist[0]))

    def point_at_length(self, target_length: float) -> PointAtLengthResult:
        """
        Find the point at a given path length along the polyline.

        Raises GeometryError if the target length exceeds the total path length.
        """
        seg_idx = ffi.new("uint32_t*")
        px = ffi.new("double*")
        py = ffi.new("double*")
        ret = lib.cavc_pline_find_point_at_path_length(
            self.native, target_length, seg_idx, px, py)
        if ret == 2:
            raise GeometryError(
                "Target length exceeds total path length or polyline is empty")
        return PointAtLengthResult(
            seg_index=int(seg_idx[0]), x=float(px[0]), y=float(py[0]))

    def to_lines(self, error_distance: float = 0.01) -> Polyline:
        """
        Convert all arc segments to approximate line segments.

        Returns a new Polyline with all bulge values equal to zero.
        """
        result = ffi.new("cavc_pline**")
        lib.cavc_pline_arcs_to_approx_lines(self.native, error_distance, result)
        pline = Polyline.__new__(Polyline)
        pline.native = result[0]
        return pline

    def rotate_start(self, index: int, x: float, y: float,
                     pos_equal_eps: float = 1e-5) -> None:
        """
        Rotate the start of a closed polyline to a new index and split point.

        Modifies the polyline in place.
        Raises GeometryError if the polyline is open or the operation fails.
        """
        ret = lib.cavc_pline_rotate_start(
            self.native, index, x, y, pos_equal_eps)
        if ret == 2:
            raise GeometryError(
                "Cannot rotate start: polyline may be open or index invalid")

    def find_intersects(self, other: Polyline,
                        pos_equal_eps: float = 1e-5) -> IntersectsResult:
        """
        Find all intersections between this polyline and another.

        Returns an IntersectsResult containing basic and overlapping intersections.
        """
        result_ptr = ffi.new("cavc_intersects_result**")
        lib.cavc_pline_find_intersects(
            self.native, other.native, pos_equal_eps, result_ptr)
        result_handle = result_ptr[0]

        # Extract basic intersections
        basic_count = ffi.new("uint32_t*")
        lib.cavc_intersects_result_get_basic_count(result_handle, basic_count)
        basic_list = []
        intr = ffi.new("cavc_basic_intersect*")
        for i in range(basic_count[0]):
            lib.cavc_intersects_result_get_basic(result_handle, i, intr)
            basic_list.append(BasicIntersect(
                seg_index1=int(intr.start_index1),
                seg_index2=int(intr.start_index2),
                x=float(intr.point_x), y=float(intr.point_y)))

        # Extract overlapping intersections
        overlap_count = ffi.new("uint32_t*")
        lib.cavc_intersects_result_get_overlapping_count(
            result_handle, overlap_count)
        overlap_list = []
        ointr = ffi.new("cavc_overlapping_intersect*")
        for i in range(overlap_count[0]):
            lib.cavc_intersects_result_get_overlapping(
                result_handle, i, ointr)
            overlap_list.append(OverlappingIntersect(
                seg_index1=int(ointr.start_index1),
                seg_index2=int(ointr.start_index2),
                x1=float(ointr.point1_x), y1=float(ointr.point1_y),
                x2=float(ointr.point2_x), y2=float(ointr.point2_y)))

        # Free the native result
        lib.cavc_intersects_result_f(result_handle)

        return IntersectsResult(basic=basic_list, overlapping=overlap_list)
