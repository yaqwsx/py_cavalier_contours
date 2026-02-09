"""
04_offset.py -- Interactive parallel offset of polylines.

Demonstrates:
  - Offsetting an L-shaped polygon inward and outward
  - Seeing how inward offset can split into multiple disjoint polylines
  - Adjusting offset distance and number of concentric offsets
  - Dragging vertices to reshape the polygon
"""
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

from py_cavalier_contours import Vertex, Polyline, GeometryError
from _gui_common import (
    draw_polyline, draw_polylines, fit_view, DraggableVertices,
    InfoText, COLORS, FILL_COLORS,
)

# ---------------------------------------------------------------------------
# Initial geometry: L-shape
# ---------------------------------------------------------------------------
l_shape = Polyline([
    Vertex(0, 0),
    Vertex(6, 0),
    Vertex(6, 2),
    Vertex(2, 2),
    Vertex(2, 6),
    Vertex(0, 6),
], closed=True)

# ---------------------------------------------------------------------------
# Figure layout
# ---------------------------------------------------------------------------
fig = plt.figure("04 - Parallel Offset", figsize=(11, 7))
fig.subplots_adjust(left=0.05, right=0.65, top=0.95, bottom=0.05)
ax = fig.add_subplot(111)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3)

# Controls
ax_dist = fig.add_axes([0.70, 0.75, 0.25, 0.04])
ax_count = fig.add_axes([0.70, 0.67, 0.25, 0.04])

slider_dist = Slider(ax_dist, "Offset dist", -3.0, 3.0, valinit=0.5)
slider_count = Slider(ax_count, "# Offsets", 1, 5, valinit=1, valstep=1)

# Info
info = InfoText(ax, x=0.02, y=0.98)

result_artists = []

# Graduated purple shades for concentric offsets
OFFSET_SHADES = ["#CE93D8", "#BA68C8", "#AB47BC", "#9C27B0", "#7B1FA2"]
OFFSET_FILLS = ["#F3E5F5", "#E1BEE7", "#CE93D8", "#BA68C8", "#AB47BC"]


def update(_=None):
    global result_artists
    for a in result_artists:
        a.remove()
    result_artists = []

    dist = slider_dist.val
    count = int(slider_count.val)

    # Draw original L-shape
    result_artists.extend(
        draw_polyline(ax, l_shape, color=COLORS["polyline_a"],
                      fill=FILL_COLORS["polyline_a"], linewidth=2))

    # Compute and draw concentric offsets
    info.clear()
    info.set("Original area", f"{l_shape.area():.2f}")
    info.set("Offset dist", f"{dist:.3f}")

    all_offset_plines = []
    for i in range(count):
        d = dist * (i + 1)
        try:
            results = l_shape.offset(d)
        except GeometryError:
            results = []

        shade_idx = min(i, len(OFFSET_SHADES) - 1)
        for p in results:
            result_artists.extend(
                draw_polyline(ax, p, color=OFFSET_SHADES[shade_idx],
                              fill=OFFSET_FILLS[shade_idx], linewidth=1.5,
                              zorder=3 + i))
        all_offset_plines.extend(results)

        if results:
            areas = ", ".join(f"{p.area():.2f}" for p in results)
            info.set(f"Offset {i+1} (d={d:.2f})", f"{len(results)} pline(s), area={areas}")
        else:
            info.set(f"Offset {i+1} (d={d:.2f})", "collapsed (empty)")

    drag_verts.refresh()

    objs = [l_shape] + all_offset_plines
    if objs:
        fit_view(ax, *objs, padding=0.15)
    fig.canvas.draw_idle()


# Draggable vertices
drag_verts = DraggableVertices(ax, l_shape, update, color=COLORS["polyline_a"])

slider_dist.on_changed(update)
slider_count.on_changed(update)

update()
plt.show()
