"""
03_boolean_operations.py -- Interactive boolean operations on overlapping polylines.

Demonstrates:
  - Union, intersection, difference, and symmetric difference
  - Dragging rectangle vertices to reshape inputs
  - Switching operations with radio buttons
  - Inspecting positive (outlines) and negative (holes) result polylines
"""
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, CheckButtons

from py_cavalier_contours import Vertex, Polyline, GeometryError
from _gui_common import (
    draw_polyline, draw_polylines, fit_view, DraggableVertices,
    InfoText, COLORS, FILL_COLORS,
)

# ---------------------------------------------------------------------------
# Initial geometry: two overlapping rectangles
# ---------------------------------------------------------------------------
rect_a = Polyline([
    Vertex(0, 0), Vertex(6, 0), Vertex(6, 4), Vertex(0, 4),
], closed=True)

rect_b = Polyline([
    Vertex(4, 2), Vertex(10, 2), Vertex(10, 6), Vertex(4, 6),
], closed=True)

# ---------------------------------------------------------------------------
# Figure layout
# ---------------------------------------------------------------------------
fig = plt.figure("03 - Boolean Operations", figsize=(11, 7))
fig.subplots_adjust(left=0.05, right=0.65, top=0.95, bottom=0.05)
ax = fig.add_subplot(111)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3)

# Controls
ax_op = fig.add_axes([0.70, 0.60, 0.25, 0.30])
ax_show = fig.add_axes([0.70, 0.50, 0.25, 0.08])

radio_op = RadioButtons(ax_op, [
    "Union", "Intersection", "Difference (A-B)",
    "Difference (B-A)", "Symmetric Diff",
], active=0)
ax_op.set_title("Operation", fontsize=9)

check_show = CheckButtons(ax_show, ["Show inputs"], [True])

# Info
info = InfoText(ax, x=0.02, y=0.98)

result_artists = []

OPERATIONS = {
    "Union": lambda a, b: a.union(b),
    "Intersection": lambda a, b: a.intersect(b),
    "Difference (A-B)": lambda a, b: a.difference(b),
    "Difference (B-A)": lambda a, b: b.difference(a),
    "Symmetric Diff": lambda a, b: a.symmetric_difference(b),
}


def update(_=None):
    global result_artists
    for a in result_artists:
        a.remove()
    result_artists = []

    op_name = radio_op.value_selected
    show_inputs = check_show.get_status()[0]

    # Draw inputs
    if show_inputs:
        result_artists.extend(
            draw_polyline(ax, rect_a, color=COLORS["polyline_a"],
                          fill=FILL_COLORS["polyline_a"], linewidth=1.5,
                          linestyle="--", zorder=1, label="A"))
        result_artists.extend(
            draw_polyline(ax, rect_b, color=COLORS["polyline_b"],
                          fill=FILL_COLORS["polyline_b"], linewidth=1.5,
                          linestyle="--", zorder=1, label="B"))

    # Compute boolean operation
    info.clear()
    info.set("Operation", op_name)
    info.set("Area A", f"{rect_a.area():.2f}")
    info.set("Area B", f"{rect_b.area():.2f}")

    op_fn = OPERATIONS[op_name]
    try:
        pos, neg = op_fn(rect_a, rect_b)

        # Draw positive results (outlines)
        for p in pos:
            result_artists.extend(
                draw_polyline(ax, p, color=COLORS["result_pos"],
                              fill=FILL_COLORS["result_pos"], linewidth=2,
                              zorder=3))
        # Draw negative results (holes)
        for p in neg:
            result_artists.extend(
                draw_polyline(ax, p, color=COLORS["result_neg"],
                              fill=FILL_COLORS["result_neg"], linewidth=2,
                              zorder=4))

        pos_area = sum(p.area() for p in pos)
        neg_area = sum(p.area() for p in neg)
        info.set("Positive", f"{len(pos)} pline(s), area={pos_area:.2f}")
        info.set("Negative", f"{len(neg)} pline(s), area={neg_area:.2f}")
        info.set("Total area", f"{pos_area + neg_area:.2f}")
    except (GeometryError, Exception) as e:
        info.set("Result", f"Error: {e}")

    drag_a.refresh()
    drag_b.refresh()

    fit_view(ax, rect_a, rect_b, padding=0.15)
    fig.canvas.draw_idle()


# Draggable vertices
drag_a = DraggableVertices(ax, rect_a, update, color=COLORS["polyline_a"])
drag_b = DraggableVertices(ax, rect_b, update, color=COLORS["polyline_b"])

radio_op.on_clicked(update)
check_show.on_clicked(update)

update()
plt.show()
