from __future__ import annotations
from typing import Iterable, List, Any

from .py_cavalier_contours import lib, ffi  # type: ignore[import-not-found,attr-defined]
from .polyline import (
    Polyline, GeometryError, _check_handle, _check_status, _finite_float,
    _positive_float,
)


class Shape:
    """
    A 2D shape represented as a collection of polylines -- outer boundaries
    (counter-clockwise) and holes (clockwise).

    Shapes are constructed from a list of closed Polylines. The constructor
    automatically sorts them into outer boundaries and holes based on their
    winding orientation.
    """
    __slots__ = "native",

    def __init__(self, polylines: Iterable[Polyline]) -> None:
        self.native = ffi.NULL
        try:
            polylines = list(polylines)
        except TypeError as exc:
            raise TypeError("polylines must be an iterable of Polylines") from exc

        for pline in polylines:
            if not isinstance(pline, Polyline):
                raise TypeError("Shape can only contain Polylines")
            if pline.native == ffi.NULL:
                raise GeometryError(
                    "Shape cannot contain a released Polyline object")
            if not pline.closed:
                raise ValueError("Shape can only contain closed polylines")
            if len(pline) < 2:
                raise ValueError(
                    "Shape polylines must contain at least two vertices")

        # Create a plinelist and push cloned polylines into it.
        plinelist = ffi.new("cavc_plinelist**")
        status = lib.cavc_plinelist_create(len(polylines), plinelist)
        _check_status(status, "create shape polyline list")
        plinelist_handle = plinelist[0]
        _check_handle(plinelist_handle, "create shape polyline list")

        try:
            for pline in polylines:
                # The list takes ownership of each successfully pushed clone.
                p_clone = ffi.new("cavc_pline**")
                status = lib.cavc_pline_clone(pline.native, p_clone)
                _check_status(status, "clone shape polyline")
                _check_handle(p_clone[0], "clone shape polyline")
                try:
                    status = lib.cavc_plinelist_push(
                        plinelist_handle, p_clone[0])
                    _check_status(status, "append shape polyline")
                except BaseException:
                    lib.cavc_pline_f(p_clone[0])
                    raise

            shape = ffi.new("cavc_shape**")
            status = lib.cavc_shape_create(plinelist_handle, shape)
            _check_status(status, "create shape")
            _check_handle(shape[0], "create shape")
            self.native = shape[0]
        finally:
            # shape_create clones the list's polylines; it does not consume it.
            lib.cavc_plinelist_f(plinelist_handle)

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def close(self) -> None:
        """Release the native shape. Calling this more than once is safe."""
        native = getattr(self, "native", ffi.NULL)
        if native != ffi.NULL:
            lib.cavc_shape_f(native)
            self.native = ffi.NULL

    def __enter__(self) -> Shape:
        if self.native == ffi.NULL:
            raise GeometryError("Shape is closed")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def _extract_polylines(self, get_count, get_pline_count,
                           get_pline_vertex_data,
                           get_pline_is_closed) -> List[Polyline]:
        """Helper to extract polylines from a shape (CCW or CW)."""
        count = ffi.new("uint32_t*")
        status = get_count(self.native, count)
        _check_status(status, "get shape polyline count")

        result: List[Polyline] = []
        try:
            for i in range(count[0]):
                # Get vertex count for this polyline
                vcount = ffi.new("uint32_t*")
                status = get_pline_count(self.native, i, vcount)
                _check_status(status, "get shape polyline vertex count")

                # Get is_closed
                is_closed = ffi.new("uint8_t*")
                status = get_pline_is_closed(self.native, i, is_closed)
                _check_status(status, "get shape polyline closed state")

                # Get vertex data
                vertex_buf = ffi.new("cavc_vertex[]", vcount[0])
                status = get_pline_vertex_data(self.native, i, vertex_buf)
                _check_status(status, "get shape polyline vertices")

                # Create Polyline from vertex data
                p_native = ffi.new("cavc_pline**")
                status = lib.cavc_pline_create(
                    vertex_buf, vcount[0], is_closed[0], p_native)
                _check_status(status, "create extracted shape polyline")
                _check_handle(p_native[0], "create extracted shape polyline")
                polyline = Polyline.__new__(Polyline)
                polyline.native = p_native[0]
                result.append(polyline)

            return result
        except BaseException:
            for polyline in result:
                polyline.close()
            raise

    @property
    def ccw_polylines(self) -> List[Polyline]:
        """Outer boundary polylines (counter-clockwise orientation)."""
        return self._extract_polylines(
            lib.cavc_shape_get_ccw_count,
            lib.cavc_shape_get_ccw_polyline_count,
            lib.cavc_shape_get_ccw_polyline_vertex_data,
            lib.cavc_shape_get_ccw_polyline_is_closed,
        )

    @property
    def cw_polylines(self) -> List[Polyline]:
        """Hole polylines (clockwise orientation)."""
        return self._extract_polylines(
            lib.cavc_shape_get_cw_count,
            lib.cavc_shape_get_cw_polyline_count,
            lib.cavc_shape_get_cw_polyline_vertex_data,
            lib.cavc_shape_get_cw_polyline_is_closed,
        )

    def offset(self, distance: float, pos_equal_eps: float = 1e-5,
               offset_dist_eps: float = 1e-4,
               slice_join_eps: float = 1e-4) -> Shape:
        """
        Compute a parallel offset of the shape.

        Returns a new Shape with the offset applied.
        """
        distance = _finite_float(distance, "distance")
        pos_equal_eps = _positive_float(pos_equal_eps, "pos_equal_eps")
        offset_dist_eps = _positive_float(offset_dist_eps, "offset_dist_eps")
        slice_join_eps = _positive_float(slice_join_eps, "slice_join_eps")
        options = ffi.new("cavc_shape_offset_o*")
        status = lib.cavc_shape_offset_o_init(options)
        _check_status(status, "initialize shape offset options")
        options.pos_equal_eps = pos_equal_eps
        options.offset_dist_eps = offset_dist_eps
        options.slice_join_eps = slice_join_eps

        result = ffi.new("cavc_shape**")
        status = lib.cavc_shape_parallel_offset(
            self.native, distance, options, result)
        _check_status(status, "offset shape")
        _check_handle(result[0], "offset shape")

        shape = Shape.__new__(Shape)
        shape.native = result[0]
        return shape

    def __copy__(self) -> Shape:
        # Reconstruct from extracted polylines
        all_plines = self.ccw_polylines + self.cw_polylines
        return Shape(all_plines)

    def __deepcopy__(self, memo: Any) -> Shape:
        return self.__copy__()

    def __repr__(self) -> str:
        ccw_count = ffi.new("uint32_t*")
        status = lib.cavc_shape_get_ccw_count(self.native, ccw_count)
        _check_status(status, "get outer shape count")
        cw_count = ffi.new("uint32_t*")
        status = lib.cavc_shape_get_cw_count(self.native, cw_count)
        _check_status(status, "get shape hole count")
        return f"Shape(outer={ccw_count[0]}, holes={cw_count[0]})"
