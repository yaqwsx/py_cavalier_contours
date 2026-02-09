from __future__ import annotations
from typing import List, Any

from .py_cavalier_contours import lib, ffi
from .polyline import Polyline, Vertex


class Shape:
    """
    A 2D shape represented as a collection of polylines -- outer boundaries
    (counter-clockwise) and holes (clockwise).

    Shapes are constructed from a list of closed Polylines. The constructor
    automatically sorts them into outer boundaries and holes based on their
    winding orientation.
    """
    __slots__ = "native",

    def __init__(self, polylines: List[Polyline]) -> None:
        # Create a plinelist and push cloned polylines into it
        plinelist = ffi.new("cavc_plinelist**")
        lib.cavc_plinelist_create(len(polylines), plinelist)
        plinelist_handle = plinelist[0]

        for pline in polylines:
            # Clone each polyline since the shape takes ownership
            p_clone = ffi.new("cavc_pline**")
            lib.cavc_pline_clone(pline.native, p_clone)
            lib.cavc_plinelist_push(plinelist_handle, p_clone[0])

        shape = ffi.new("cavc_shape**")
        lib.cavc_shape_create(plinelist_handle, shape)
        # Note: shape_create consumes the plinelist, so we don't free it
        lib.cavc_plinelist_f(plinelist_handle)
        self.native = shape[0]

    def __del__(self) -> None:
        lib.cavc_shape_f(self.native)

    def _extract_polylines(self, get_count, get_pline_count,
                           get_pline_vertex_data,
                           get_pline_is_closed) -> List[Polyline]:
        """Helper to extract polylines from a shape (CCW or CW)."""
        count = ffi.new("uint32_t*")
        get_count(self.native, count)

        result: List[Polyline] = []
        for i in range(count[0]):
            # Get vertex count for this polyline
            vcount = ffi.new("uint32_t*")
            get_pline_count(self.native, i, vcount)

            # Get is_closed
            is_closed = ffi.new("uint8_t*")
            get_pline_is_closed(self.native, i, is_closed)

            # Get vertex data
            vertex_buf = ffi.new("cavc_vertex[]", vcount[0])
            get_pline_vertex_data(self.native, i, vertex_buf)

            # Create Polyline from vertex data
            p_native = ffi.new("cavc_pline**")
            lib.cavc_pline_create(vertex_buf, vcount[0], is_closed[0], p_native)
            polyline = Polyline.__new__(Polyline)
            polyline.native = p_native[0]
            result.append(polyline)

        return result

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
        options = ffi.new("cavc_shape_offset_o*")
        lib.cavc_shape_offset_o_init(options)
        options.pos_equal_eps = pos_equal_eps
        options.offset_dist_eps = offset_dist_eps
        options.slice_join_eps = slice_join_eps

        result = ffi.new("cavc_shape**")
        lib.cavc_shape_parallel_offset(self.native, distance, options, result)

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
        lib.cavc_shape_get_ccw_count(self.native, ccw_count)
        cw_count = ffi.new("uint32_t*")
        lib.cavc_shape_get_cw_count(self.native, cw_count)
        return f"Shape(outer={ccw_count[0]}, holes={cw_count[0]})"
