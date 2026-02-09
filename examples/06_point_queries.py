"""
06_point_queries.py -- Interactive point-based queries on polylines.

Demonstrates:
  - closest_point: find the nearest point on a polyline to a draggable query point
  - point_at_length: slide a marker along the polyline perimeter
  - winding_number: visualize inside/outside status
  - contains: drag a test rectangle to test containment relationships
"""
from copy import copy

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

from py_cavalier_contours import Vertex, Polyline, GeometryError
from _gui_common import (
    draw_polyline, fit_view, DraggableVertices, DraggablePoint,
    InfoText, COLORS, FILL_COLORS,
)

# ---------------------------------------------------------------------------
# Initial geometry
# ---------------------------------------------------------------------------
square = Polyline([
    Vertex(0, 0), Vertex(4, 0), Vertex(4, 4), Vertex(0, 4),
], closed=True)

# Small test rectangle for containment
test_rect = Polyline([
    Vertex(1, 1), Vertex(3, 1), Vertex(3, 3), Vertex(1, 3),
], closed=True)

# ---------------------------------------------------------------------------
# Figure layout
# ---------------------------------------------------------------------------
fig = plt.figure("06 - Point Queries", figsize=(11, 7))
fig.subplots_adjust(left=0.05, right=0.65, top=0.95, bottom=0.05)
ax = fig.add_subplot(111)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3)

# Slider for point_at_length
ax_path_len = fig.add_axes([0.70, 0.50, 0.25, 0.04])
slider_path_len = Slider(ax_path_len, "Path length", 0.0,
                          square.length() - 0.001, valinit=0.0)

# Info text
info = InfoText(ax, x=0.02, y=0.98)

# State for drawn artists
result_artists = []


def update(_=None):
    global result_artists
    for a in result_artists:
        a.remove()
    result_artists = []

    # Draw the main square
    result_artists.extend(
        draw_polyline(ax, square, color=COLORS["polyline_a"],
                      fill=FILL_COLORS["polyline_a"], linewidth=2))

    # -- Closest point query --
    qx, qy = drag_query.x, drag_query.y
    try:
        cp = square.closest_point(qx, qy)
        # Draw line from query to closest point
        line, = ax.plot([qx, cp.x], [qy, cp.y], color=COLORS["closest_point"],
                        linestyle="--", linewidth=1.5, zorder=5)
        result_artists.append(line)
        # Draw closest point marker
        sc = ax.scatter([cp.x], [cp.y], color=COLORS["closest_point"],
                        s=80, zorder=6, edgecolors="white", linewidths=1.5,
                        marker="D")
        result_artists.append(sc)

        info.clear()
        info.set("Query", f"({qx:.2f}, {qy:.2f})")
        info.set("Closest", f"({cp.x:.2f}, {cp.y:.2f})")
        info.set("Distance", f"{cp.distance:.4f}")
        info.set("Segment", str(cp.seg_index))
    except GeometryError:
        info.clear()
        info.set("Query", f"({qx:.2f}, {qy:.2f})")
        info.set("Closest", "error")

    # -- Winding number --
    wn = square.winding_number(qx, qy)
    inside = "INSIDE" if wn != 0 else "OUTSIDE"
    info.set("Winding #", f"{wn:+d} ({inside})")

    # -- Point at length --
    try:
        perimeter = square.length()
        slider_path_len.valmax = perimeter - 0.001
        target_len = min(slider_path_len.val, perimeter - 0.001)
        pal = square.point_at_length(target_len)
        sc2 = ax.scatter([pal.x], [pal.y], color=COLORS["result_pos"],
                         s=100, zorder=7, edgecolors="white", linewidths=2,
                         marker="o")
        result_artists.append(sc2)
        info.set("Path pos", f"({pal.x:.2f}, {pal.y:.2f}) at L={target_len:.2f}")
    except GeometryError:
        info.set("Path pos", "error")

    # -- Containment test --
    # Rebuild test_rect from drag_test center
    cx, cy = drag_test.x, drag_test.y
    test_rect.clear()
    test_rect.append(Vertex(cx - 1, cy - 1))
    test_rect.append(Vertex(cx + 1, cy - 1))
    test_rect.append(Vertex(cx + 1, cy + 1))
    test_rect.append(Vertex(cx - 1, cy + 1))

    try:
        containment = square.contains(test_rect)
    except GeometryError:
        containment = "error"

    contain_colors = {
        "pline2_inside_pline1": COLORS["result_pos"],
        "pline1_inside_pline2": COLORS["polyline_b"],
        "disjoint": COLORS["result_neg"],
        "intersected": COLORS["highlight"],
    }
    rect_color = contain_colors.get(containment, "#888888")
    result_artists.extend(
        draw_polyline(ax, test_rect, color=rect_color, linewidth=2, zorder=4))
    info.set("Containment", containment)

    # Update vertex scatter positions
    drag_sq.refresh()

    fit_view(ax, square, test_rect, padding=0.3)
    fig.canvas.draw_idle()


# Draggable elements
drag_sq = DraggableVertices(ax, square, update, color=COLORS["polyline_a"])
drag_query = DraggablePoint(ax, 2.0, 2.0, update,
                            color=COLORS["query_point"], size=120, zorder=8)
drag_test = DraggablePoint(ax, 2.0, 2.0, update,
                           color=COLORS["polyline_b"], size=80, zorder=8)

slider_path_len.on_changed(update)

# Initial draw
update()
plt.show()
