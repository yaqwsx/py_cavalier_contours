from __future__ import annotations
from typing import Iterable, Union, Tuple, List, Any
from collections.abc import MutableSequence, Sized
from itertools import zip_longest
import math
import operator

from .py_cavalier_contours import lib, ffi  # type: ignore[import-not-found,attr-defined]
from .types import (
    ClosestPointResult, PointAtLengthResult, BasicIntersect,
    OverlappingIntersect, IntersectsResult,
)

class GeometryError(RuntimeError):
    pass


def _check_status(status: int, operation: str) -> None:
    """Turn every native failure into a deterministic Python exception."""
    if status != 0:
        raise GeometryError(f"{operation} failed (native status {status})")


def _check_handle(handle: Any, operation: str) -> None:
    if handle == ffi.NULL:
        raise GeometryError(f"{operation} failed (native result was null)")


def _finite_float(value: float, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a real number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive_float(value: float, name: str) -> float:
    result = _finite_float(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return result


def _vertex(value: Any) -> Vertex:
    if not isinstance(value, Vertex):
        raise TypeError("Polyline can only contain vertices")
    return value

class Vertex:
    __slots__ = "native",

    def __init__(self, x: float = 0, y: float = 0, bulge: float = 0) -> None:
        self.native = ffi.new("cavc_vertex*")
        self.native.x = _finite_float(x, "x")
        self.native.y = _finite_float(y, "y")
        self.native.bulge = _finite_float(bulge, "bulge")

    @property
    def x(self) -> float:
        return float(self.native.x)

    @x.setter
    def x(self, value: float) -> None:
        self.native.x = _finite_float(value, "x")

    @property
    def y(self) -> float:
        return float(self.native.y)

    @y.setter
    def y(self, value: float) -> None:
        self.native.y = _finite_float(value, "y")

    @property
    def bulge(self) -> float:
        return float(self.native.bulge)

    @bulge.setter
    def bulge(self, value: float) -> None:
        self.native.bulge = _finite_float(value, "bulge")

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

    def __init__(self, vertices: Iterable[Vertex] = (), closed: bool = True) -> None:
        self.native = ffi.NULL
        p_native = ffi.new("cavc_pline**")
        status = lib.cavc_pline_create(ffi.NULL, 0, closed, p_native)
        _check_status(status, "create polyline")
        _check_handle(p_native[0], "create polyline")
        self.native = p_native[0]

        try:
            if isinstance(vertices, Sized):
                status = lib.cavc_pline_reserve(self.native, len(vertices))
                _check_status(status, "reserve polyline storage")
            for value in vertices:
                v = _vertex(value)
                status = lib.cavc_pline_add(self.native, v.x, v.y, v.bulge)
                _check_status(status, "append polyline vertex")
        except BaseException:
            self.close()
            raise

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            # Destructors must remain safe during partial construction and
            # interpreter shutdown.
            pass

    def close(self) -> None:
        """Release the native polyline. Calling this more than once is safe."""
        native = getattr(self, "native", ffi.NULL)
        if native != ffi.NULL:
            lib.cavc_pline_f(native)
            self.native = ffi.NULL

    def __enter__(self) -> Polyline:
        if self.native == ffi.NULL:
            raise GeometryError("Polyline is closed")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def __str__(self) -> str:
        return f"Polyline({', '.join([str(x) for x in self])})"

    def __repr__(self) -> str:
        return f"Polyline({', '.join([str(x) for x in self])})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Iterable):
            return NotImplemented
        sentinel = object()
        return all(
            left is not sentinel and right is not sentinel and left == right
            for left, right in zip_longest(self, other, fillvalue=sentinel)
        )

    def _ensure_in_range(self, i: int) -> int:
        try:
            i = operator.index(i)
        except TypeError as exc:
            raise TypeError("Polyline indices must be integers") from exc
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
            status = lib.cavc_pline_get_vertex(self.native, i, v.native)
            _check_status(status, "get polyline vertex")
            return v

    def __setitem__(self, i: Union[int, slice], item: Union[Vertex, Iterable[Vertex]]) -> None:
        if isinstance(i, slice):
            raise NotImplementedError("Slices are not supported for for setitem")
        else:
            i = self._ensure_in_range(i)
            item = _vertex(item)
            status = lib.cavc_pline_set_vertex(self.native, i, item.native[0])
            _check_status(status, "set polyline vertex")

    def __delitem__(self, i: Union[int, slice]) -> None:
        if isinstance(i, slice):
            raise NotImplementedError("Slices are not supported for for setitem")
        else:
            i = self._ensure_in_range(i)
            status = lib.cavc_pline_remove(self.native, i)
            _check_status(status, "remove polyline vertex")

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
        status = lib.cavc_pline_get_vertex_count(self.native, psize)
        _check_status(status, "get polyline vertex count")
        return int(psize[0])

    def __copy__(self) -> Polyline:
        pline = self.__class__.__new__(self.__class__)

        p_native = ffi.new("cavc_pline**")
        status = lib.cavc_pline_clone(self.native, p_native)
        _check_status(status, "clone polyline")
        _check_handle(p_native[0], "clone polyline")
        pline.native = p_native[0]

        return pline

    def __deepcopy__(self, memo: Any) -> Polyline:
        return self.__copy__()

    def length(self) -> float:
        """
        Return length of the polyline
        """
        length = ffi.new("double*")
        status = lib.cavc_pline_eval_path_length(self.native, length)
        _check_status(status, "evaluate polyline length")
        return float(length[0])

    def area(self) -> float:
        """
        Return area of the polyline
        """
        a = ffi.new("double*")
        status = lib.cavc_pline_eval_area(self.native, a)
        _check_status(status, "evaluate polyline area")
        return float(a[0])

    def winding_number(self, x: float, y: float) -> int:
        """
        Return winding number of a point relative to the polyline.
        Non-zero means the point is inside.
        """
        wn = ffi.new("int32_t*")
        x = _finite_float(x, "x")
        y = _finite_float(y, "y")
        status = lib.cavc_pline_eval_wn(self.native, x, y, wn)
        _check_status(status, "evaluate winding number")
        return int(wn[0])

    def reverse(self) -> None:
        """
        Reverse the direction
        """
        status = lib.cavc_pline_invert_direction(self.native)
        _check_status(status, "reverse polyline")

    def scale(self, factor: float) -> None:
        """
        Scale the polyline around [0, 0]
        """
        factor = _finite_float(factor, "factor")
        status = lib.cavc_pline_scale(self.native, factor)
        _check_status(status, "scale polyline")

    def translate(self, x: float, y: float) -> None:
        """
        Translate the polyline
        """
        x = _finite_float(x, "x")
        y = _finite_float(y, "y")
        status = lib.cavc_pline_translate(self.native, x, y)
        _check_status(status, "translate polyline")

    def remove_repeated(self, eps: float = 1e-5) -> None:
        """
        Remove repeated vertices
        """
        eps = _positive_float(eps, "eps")
        status = lib.cavc_pline_remove_repeat_pos(self.native, eps)
        _check_status(status, "remove repeated vertices")

    def remove_redundant(self, eps: float = 1e-5) -> None:
        """
        Remove redundant vertices.

        Redundant vertexes can arise with multiple vertexes on top of each
        other, along a straight line, or forming a concentric arc with sweep
        angle less than or equal to PI.
        """
        eps = _positive_float(eps, "eps")
        status = lib.cavc_pline_remove_redundant(self.native, eps)
        _check_status(status, "remove redundant vertices")

    def clear(self) -> None:
        """
        Clear all polygons
        """
        status = lib.cavc_pline_clear(self.native)
        _check_status(status, "clear polyline")

    def append(self, v: Vertex) -> None:
        """
        Append a vertex to the end of the list
        """
        v = _vertex(v)
        status = lib.cavc_pline_add(self.native, v.x, v.y, v.bulge)
        _check_status(status, "append polyline vertex")

    def insert(self, index: int, v: Vertex) -> None:
        """
        Insert a vertex at given index
        """
        v = _vertex(v)
        try:
            index = operator.index(index)
        except TypeError as exc:
            raise TypeError("Polyline indices must be integers") from exc

        size = len(self)
        if index < 0:
            index = max(0, size + index)
        elif index > size:
            index = size

        if index == size:
            self.append(v)
            return

        # The native API has no insertion primitive. Preserve strong exception
        # safety by keeping a native clone until the shift completes.
        backup = self.__copy__()
        try:
            self.append(self[-1])
            for position in range(size - 1, index, -1):
                self[position] = self[position - 1]
            self[index] = v
        except BaseException:
            modified_native = self.native
            self.native = backup.native
            backup.native = modified_native
            backup.close()
            raise
        else:
            backup.close()

    def reserve(self, additional: int) -> None:
        """
        Reserve space for additional vertices in the underlying storage
        """
        try:
            additional = operator.index(additional)
        except TypeError as exc:
            raise TypeError("additional must be an integer") from exc
        if additional < 0:
            raise ValueError("additional must be non-negative")
        status = lib.cavc_pline_reserve(self.native, additional)
        _check_status(status, "reserve polyline storage")

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
            raise GeometryError("Cannot evaluate bounding box with fewer than 2 vertices")
        _check_status(retval, "evaluate polyline bounding box")
        return minx[0], miny[0], maxx[0], maxy[0]

    @property
    def closed(self) -> bool:
        c = ffi.new("uint8_t*")
        status = lib.cavc_pline_get_is_closed(self.native, c)
        _check_status(status, "get polyline closed state")
        return bool(c[0])

    @closed.setter
    def closed(self, value: bool) -> None:
        status = lib.cavc_pline_set_is_closed(self.native, value)
        _check_status(status, "set polyline closed state")

    @staticmethod
    def _pythonizePlist(list_handle: Any) -> List[Polyline]:
        """
        Given a cavc_pline* handle, turn it into a Python list of Polylines and
        free the original native list.
        """
        _check_handle(list_handle, "read polyline list")
        count = ffi.new("uint32_t*")
        result: List[Polyline] = []
        try:
            status = lib.cavc_plinelist_get_count(list_handle, count)
            _check_status(status, "get polyline list count")
            # Taking an item shrinks the native list. Always take index zero;
            # increasing indexes would skip elements and eventually wrap NULL.
            for _ in range(count[0]):
                p_native = ffi.new("cavc_pline **")
                status = lib.cavc_plinelist_take(list_handle, 0, p_native)
                _check_status(status, "take polyline from list")
                _check_handle(p_native[0], "take polyline from list")
                polyline = Polyline.__new__(Polyline)
                polyline.native = p_native[0]
                result.append(polyline)
            return result
        except BaseException:
            for polyline in result:
                polyline.close()
            raise
        finally:
            lib.cavc_plinelist_f(list_handle)


    def offset(self, distance: float, handle_self_intersects: bool = True,
        pos_equal_eps: float = 1e-5, slice_join_eps: float = 1e-5,
        offset_dist_eps: float = 1e-5) -> List[Polyline]:
        """
        Compute offset.
        """
        distance = _finite_float(distance, "distance")
        pos_equal_eps = _positive_float(pos_equal_eps, "pos_equal_eps")
        slice_join_eps = _positive_float(slice_join_eps, "slice_join_eps")
        offset_dist_eps = _positive_float(offset_dist_eps, "offset_dist_eps")
        options = ffi.new("cavc_pline_parallel_offset_o*")
        status = lib.cavc_pline_parallel_offset_o_init(options)
        _check_status(status, "initialize polyline offset options")
        options.pos_equal_eps = pos_equal_eps
        options.slice_join_eps = slice_join_eps
        options.offset_dist_eps = offset_dist_eps
        options.handle_self_intersects = handle_self_intersects

        result = ffi.new("cavc_plinelist**")
        status = lib.cavc_pline_parallel_offset(
            self.native, distance, options, result)
        _check_status(status, "offset polyline")
        _check_handle(result[0], "offset polyline")
        return Polyline._pythonizePlist(result[0])

    def _bool_op(self, other: Polyline, op: int,
                 pos_equal_eps: float) -> Tuple[List[Polyline], List[Polyline]]:
        if not isinstance(other, Polyline):
            raise TypeError("other must be a Polyline")
        pos_equal_eps = _positive_float(pos_equal_eps, "pos_equal_eps")
        options = ffi.new("cavc_pline_boolean_o*")
        status = lib.cavc_pline_boolean_o_init(options)
        _check_status(status, "initialize polyline boolean options")
        options.pos_equal_eps = pos_equal_eps

        pos_result = ffi.new("cavc_plinelist**")
        neg_result = ffi.new("cavc_plinelist**")
        status = lib.cavc_pline_boolean(
            self.native, other.native, op, options, pos_result, neg_result)
        _check_status(status, "perform polyline boolean operation")
        pos_handle = pos_result[0]
        neg_handle = neg_result[0]
        pos: List[Polyline] = []
        try:
            _check_handle(pos_handle, "perform polyline boolean operation")
            _check_handle(neg_handle, "perform polyline boolean operation")
            # _pythonizePlist always consumes its handle, including on error.
            transferred = pos_handle
            pos_handle = ffi.NULL
            pos = Polyline._pythonizePlist(transferred)
            transferred = neg_handle
            neg_handle = ffi.NULL
            neg = Polyline._pythonizePlist(transferred)
            return pos, neg
        except BaseException:
            for polyline in pos:
                polyline.close()
            if pos_handle != ffi.NULL:
                lib.cavc_plinelist_f(pos_handle)
            if neg_handle != ffi.NULL:
                lib.cavc_plinelist_f(neg_handle)
            raise

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
        pos_equal_eps = _positive_float(pos_equal_eps, "pos_equal_eps")
        options = ffi.new("cavc_pline_self_intersect_o*")
        status = lib.cavc_pline_self_intersect_o_init(options)
        _check_status(status, "initialize self-intersection options")
        options.pos_equal_eps = pos_equal_eps

        result = ffi.new("uint8_t*")
        status = lib.cavc_pline_scan_for_self_intersect(
            self.native, options, result)
        _check_status(status, "scan polyline for self-intersection")
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
        if not isinstance(other, Polyline):
            raise TypeError("other must be a Polyline")
        pos_equal_eps = _positive_float(pos_equal_eps, "pos_equal_eps")
        options = ffi.new("cavc_pline_contains_o*")
        status = lib.cavc_pline_contains_o_init(options)
        _check_status(status, "initialize polyline containment options")
        options.pos_equal_eps = pos_equal_eps

        result = ffi.new("uint32_t*")
        status = lib.cavc_pline_contains(
            self.native, other.native, options, result)
        _check_status(status, "evaluate polyline containment")
        return self._CONTAINS_RESULTS.get(result[0], "unknown")

    @property
    def orientation(self) -> str:
        """
        Get the orientation of the polyline.

        Returns "open", "cw" (clockwise), or "ccw" (counter-clockwise).
        """
        o = ffi.new("uint32_t*")
        status = lib.cavc_pline_orientation(self.native, o)
        _check_status(status, "evaluate polyline orientation")
        return {0: "open", 1: "cw", 2: "ccw"}.get(o[0], "unknown")

    def closest_point(self, x: float, y: float,
                      pos_equal_eps: float = 1e-5) -> ClosestPointResult:
        """
        Find the closest point on this polyline to the given point.

        Returns a ClosestPointResult with seg_index, x, y, distance.
        Raises GeometryError if the polyline has no segments.
        """
        x = _finite_float(x, "x")
        y = _finite_float(y, "y")
        pos_equal_eps = _positive_float(pos_equal_eps, "pos_equal_eps")
        seg_idx = ffi.new("uint32_t*")
        cx = ffi.new("double*")
        cy = ffi.new("double*")
        dist = ffi.new("double*")
        ret = lib.cavc_pline_closest_point(
            self.native, x, y, pos_equal_eps, seg_idx, cx, cy, dist)
        if ret == 2:
            raise GeometryError("Polyline has no segments")
        _check_status(ret, "find closest point")
        return ClosestPointResult(
            seg_index=int(seg_idx[0]), x=float(cx[0]),
            y=float(cy[0]), distance=float(dist[0]))

    def point_at_length(self, target_length: float) -> PointAtLengthResult:
        """
        Find the point at a given path length along the polyline.

        Raises GeometryError if the target length exceeds the total path length.
        """
        target_length = _finite_float(target_length, "target_length")
        if target_length < 0:
            raise ValueError("target_length must be non-negative")
        if len(self) == 0:
            # The native implementation currently panics for this case before
            # its FFI layer can return the documented empty-polyline status.
            raise GeometryError("Polyline is empty")
        seg_idx = ffi.new("uint32_t*")
        px = ffi.new("double*")
        py = ffi.new("double*")
        ret = lib.cavc_pline_find_point_at_path_length(
            self.native, target_length, seg_idx, px, py)
        if ret == 2:
            raise GeometryError(
                "Target length exceeds total path length or polyline is empty")
        _check_status(ret, "find point at path length")
        return PointAtLengthResult(
            seg_index=int(seg_idx[0]), x=float(px[0]), y=float(py[0]))

    def to_lines(self, error_distance: float = 0.01) -> Polyline:
        """
        Convert all arc segments to approximate line segments.

        Returns a new Polyline with all bulge values equal to zero.
        """
        error_distance = _positive_float(error_distance, "error_distance")
        result = ffi.new("cavc_pline**")
        status = lib.cavc_pline_arcs_to_approx_lines(
            self.native, error_distance, result)
        _check_status(status, "convert arcs to lines")
        _check_handle(result[0], "convert arcs to lines")
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
        index = self._ensure_in_range(index)
        x = _finite_float(x, "x")
        y = _finite_float(y, "y")
        pos_equal_eps = _positive_float(pos_equal_eps, "pos_equal_eps")
        ret = lib.cavc_pline_rotate_start(
            self.native, index, x, y, pos_equal_eps)
        if ret == 2:
            raise GeometryError(
                "Cannot rotate start: polyline may be open or index invalid")
        _check_status(ret, "rotate polyline start")

    def find_intersects(self, other: Polyline,
                        pos_equal_eps: float = 1e-5) -> IntersectsResult:
        """
        Find all intersections between this polyline and another.

        Returns an IntersectsResult containing basic and overlapping intersections.
        """
        if not isinstance(other, Polyline):
            raise TypeError("other must be a Polyline")
        pos_equal_eps = _positive_float(pos_equal_eps, "pos_equal_eps")
        result_ptr = ffi.new("cavc_intersects_result**")
        status = lib.cavc_pline_find_intersects(
            self.native, other.native, pos_equal_eps, result_ptr)
        _check_status(status, "find polyline intersections")
        result_handle = result_ptr[0]
        _check_handle(result_handle, "find polyline intersections")

        try:
            # Extract basic intersections
            basic_count = ffi.new("uint32_t*")
            status = lib.cavc_intersects_result_get_basic_count(
                result_handle, basic_count)
            _check_status(status, "get basic intersection count")
            basic_list = []
            intr = ffi.new("cavc_basic_intersect*")
            for i in range(basic_count[0]):
                status = lib.cavc_intersects_result_get_basic(
                    result_handle, i, intr)
                _check_status(status, "get basic intersection")
                basic_list.append(BasicIntersect(
                    seg_index1=int(intr.start_index1),
                    seg_index2=int(intr.start_index2),
                    x=float(intr.point_x), y=float(intr.point_y)))

            # Extract overlapping intersections
            overlap_count = ffi.new("uint32_t*")
            status = lib.cavc_intersects_result_get_overlapping_count(
                result_handle, overlap_count)
            _check_status(status, "get overlapping intersection count")
            overlap_list = []
            ointr = ffi.new("cavc_overlapping_intersect*")
            for i in range(overlap_count[0]):
                status = lib.cavc_intersects_result_get_overlapping(
                    result_handle, i, ointr)
                _check_status(status, "get overlapping intersection")
                overlap_list.append(OverlappingIntersect(
                    seg_index1=int(ointr.start_index1),
                    seg_index2=int(ointr.start_index2),
                    x1=float(ointr.point1_x), y1=float(ointr.point1_y),
                    x2=float(ointr.point2_x), y2=float(ointr.point2_y)))
        finally:
            lib.cavc_intersects_result_f(result_handle)

        return IntersectsResult(basic=basic_list, overlapping=overlap_list)
