"""
05_shape_with_holes.py -- Interactive shapes with outer boundaries and holes.

Demonstrates:
  - Creating an outer rectangle boundary (CCW) with circular holes (CW)
  - Building a Shape and offsetting it
  - Adjusting hole radii with sliders
  - Dragging hole centers and outer boundary vertices
"""
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, CheckButtons

from py_cavalier_contours import Vertex, Polyline, Shape, GeometryError
from _gui_common import (
    draw_polyline, draw_shape, fit_view, DraggableVertices, DraggablePoint,
    InfoText, COLORS, FILL_COLORS,
)

# ---------------------------------------------------------------------------
# Initial geometry
# ---------------------------------------------------------------------------
outer = Polyline([
    Vertex(0, 0), Vertex(10, 0), Vertex(10, 8), Vertex(0, 8),
], closed=True)

# Hole centers and radii
hole1_cx, hole1_cy, hole1_r = 3.0, 4.0, 1.0
hole2_cx, hole2_cy, hole2_r = 7.0, 4.0, 1.5


def make_circle_cw(cx, cy, r):
    """Create a clockwise circle (hole) from center and radius."""
    return Polyline([
        Vertex(cx + r, cy, -1),
        Vertex(cx - r, cy, -1),
    ], closed=True)


# ---------------------------------------------------------------------------
# Figure layout
# ---------------------------------------------------------------------------
fig = plt.figure("05 - Shape with Holes", figsize=(11, 7))
fig.subplots_adjust(left=0.05, right=0.65, top=0.95, bottom=0.05)
ax = fig.add_subplot(111)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3)

# Controls
ax_offset = fig.add_axes([0.70, 0.78, 0.25, 0.04])
ax_r1 = fig.add_axes([0.70, 0.70, 0.25, 0.04])
ax_r2 = fig.add_axes([0.70, 0.62, 0.25, 0.04])
ax_show_offset = fig.add_axes([0.70, 0.52, 0.25, 0.08])

slider_offset = Slider(ax_offset, "Offset", -2.0, 2.0, valinit=0.0)
slider_r1 = Slider(ax_r1, "Hole 1 R", 0.2, 3.0, valinit=hole1_r)
slider_r2 = Slider(ax_r2, "Hole 2 R", 0.2, 3.0, valinit=hole2_r)
check_show_offset = CheckButtons(ax_show_offset, ["Show offset result"], [True])

# Info
info = InfoText(ax, x=0.02, y=0.98)

result_artists = []


def update(_=None):
    global result_artists
    for a in result_artists:
        a.remove()
    result_artists = []

    r1 = slider_r1.val
    r2 = slider_r2.val
    offset_dist = slider_offset.val
    show_offset = check_show_offset.get_status()[0]

    # Build holes from draggable centers
    c1x, c1y = drag_h1.x, drag_h1.y
    c2x, c2y = drag_h2.x, drag_h2.y
    hole1 = make_circle_cw(c1x, c1y, r1)
    hole2 = make_circle_cw(c2x, c2y, r2)

    # Build shape
    try:
        shape = Shape([outer, hole1, hole2])
    except (GeometryError, Exception) as e:
        info.clear()
        info.set("Error", str(e))
        fig.canvas.draw_idle()
        return

    # Draw original shape
    result_artists.extend(
        draw_shape(ax, shape, outer_color=COLORS["polyline_a"],
                   outer_fill=FILL_COLORS["polyline_a"],
                   hole_color=COLORS["result_neg"], hole_fill="white",
                   linewidth=2, zorder=2))

    # Info
    info.clear()
    info.set("Outer area", f"{outer.area():.2f}")
    info.set("Hole 1", f"center=({c1x:.1f},{c1y:.1f}), r={r1:.2f}, area={hole1.area():.4f}")
    info.set("Hole 2", f"center=({c2x:.1f},{c2y:.1f}), r={r2:.2f}, area={hole2.area():.4f}")
    net_area = outer.area() + hole1.area() + hole2.area()
    info.set("Net area", f"{net_area:.2f}")
    info.set("CCW plines", str(len(shape.ccw_polylines)))
    info.set("CW plines", str(len(shape.cw_polylines)))

    # Compute and draw offset
    if show_offset and offset_dist != 0:
        try:
            offset_shape = shape.offset(offset_dist)
            result_artists.extend(
                draw_shape(ax, offset_shape,
                           outer_color=COLORS["result_pos"],
                           outer_fill=FILL_COLORS["result_pos"],
                           hole_color=COLORS["offset"],
                           hole_fill="#F3E5F5",
                           linewidth=1.5, zorder=3))
            info.set("Offset dist", f"{offset_dist:.3f}")
            info.set("Offset CCW", str(len(offset_shape.ccw_polylines)))
            info.set("Offset CW", str(len(offset_shape.cw_polylines)))

            off_area = sum(p.area() for p in offset_shape.ccw_polylines) + \
                       sum(p.area() for p in offset_shape.cw_polylines)
            info.set("Offset area", f"{off_area:.2f}")
        except (GeometryError, Exception) as e:
            info.set("Offset", f"Error: {e}")

    drag_outer.refresh()
    fit_view(ax, outer, padding=0.15)
    fig.canvas.draw_idle()


# Draggable elements
drag_outer = DraggableVertices(ax, outer, update, color=COLORS["polyline_a"])
drag_h1 = DraggablePoint(ax, hole1_cx, hole1_cy, update,
                          color=COLORS["result_neg"], size=80, zorder=10)
drag_h2 = DraggablePoint(ax, hole2_cx, hole2_cy, update,
                          color=COLORS["result_neg"], size=80, zorder=10)

slider_offset.on_changed(update)
slider_r1.on_changed(update)
slider_r2.on_changed(update)
check_show_offset.on_clicked(update)

update()
plt.show()
