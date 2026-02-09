"""
01_basic_polyline.py -- Interactive exploration of polyline properties and transforms.

Demonstrates:
  - Building a square and triangle from Vertex objects
  - Querying length, area, bounding_box, orientation
  - Transforming with scale, translate, reverse
  - Dragging vertices to reshape polygons interactively
"""
from copy import copy

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons, Button, CheckButtons

from py_cavalier_contours import Vertex, Polyline
from _gui_common import (
    draw_polyline, fit_view, DraggableVertices, InfoText,
    COLORS, FILL_COLORS,
)

# ---------------------------------------------------------------------------
# Initial geometry
# ---------------------------------------------------------------------------
square = Polyline([
    Vertex(0, 0), Vertex(1, 0), Vertex(1, 1), Vertex(0, 1),
], closed=True)

triangle = Polyline([
    Vertex(2, 0), Vertex(5, 0), Vertex(2, 4),
], closed=True)

# ---------------------------------------------------------------------------
# Figure layout
# ---------------------------------------------------------------------------
fig = plt.figure("01 - Basic Polyline Properties & Transforms", figsize=(11, 7))
fig.subplots_adjust(left=0.05, right=0.65, top=0.95, bottom=0.05)
ax = fig.add_subplot(111)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3)

# Control panel axes (right side)
ax_target = fig.add_axes([0.70, 0.78, 0.25, 0.15])
ax_scale = fig.add_axes([0.70, 0.68, 0.25, 0.04])
ax_tx = fig.add_axes([0.70, 0.60, 0.25, 0.04])
ax_ty = fig.add_axes([0.70, 0.52, 0.25, 0.04])
ax_reverse = fig.add_axes([0.70, 0.43, 0.25, 0.06])
ax_reset = fig.add_axes([0.70, 0.35, 0.25, 0.05])

# Widgets
radio_target = RadioButtons(ax_target, ["Square", "Triangle"], active=0)
ax_target.set_title("Apply to", fontsize=9)
slider_scale = Slider(ax_scale, "Scale", 0.1, 5.0, valinit=1.0)
slider_tx = Slider(ax_tx, "Translate X", -5, 10, valinit=0.0)
slider_ty = Slider(ax_ty, "Translate Y", -5, 10, valinit=0.0)
check_reverse = CheckButtons(ax_reverse, ["Reverse direction"], [False])
btn_reset = Button(ax_reset, "Reset Sliders")

# Info text
info = InfoText(ax, x=0.02, y=0.98)

# State
result_artists = []


def get_target():
    label = radio_target.value_selected
    return square if label == "Square" else triangle


def update(_=None):
    global result_artists
    for a in result_artists:
        a.remove()
    result_artists = []

    # Draw originals (dashed)
    result_artists.extend(
        draw_polyline(ax, square, color=COLORS["polyline_a"],
                      fill=FILL_COLORS["polyline_a"], linestyle="--",
                      linewidth=1, zorder=1))
    result_artists.extend(
        draw_polyline(ax, triangle, color=COLORS["polyline_b"],
                      fill=FILL_COLORS["polyline_b"], linestyle="--",
                      linewidth=1, zorder=1))

    # Compute transform on target
    target = get_target()
    transformed = copy(target)

    s = slider_scale.val
    tx = slider_tx.val
    ty = slider_ty.val
    reversed_on = check_reverse.get_status()[0]

    transformed.scale(s)
    transformed.translate(tx, ty)
    if reversed_on:
        transformed.reverse()

    # Draw transformed (solid)
    if target is square:
        result_artists.extend(
            draw_polyline(ax, transformed, color=COLORS["polyline_a"],
                          fill=FILL_COLORS["polyline_a"], linewidth=2.5,
                          zorder=3, label="Square (transformed)"))
        # Also draw triangle solid (untransformed)
        result_artists.extend(
            draw_polyline(ax, triangle, color=COLORS["polyline_b"],
                          fill=FILL_COLORS["polyline_b"], linewidth=2,
                          zorder=2, label="Triangle"))
    else:
        result_artists.extend(
            draw_polyline(ax, transformed, color=COLORS["polyline_b"],
                          fill=FILL_COLORS["polyline_b"], linewidth=2.5,
                          zorder=3, label="Triangle (transformed)"))
        result_artists.extend(
            draw_polyline(ax, square, color=COLORS["polyline_a"],
                          fill=FILL_COLORS["polyline_a"], linewidth=2,
                          zorder=2, label="Square"))

    # Update vertex scatter positions
    drag_sq.refresh()
    drag_tri.refresh()

    # Update info
    bbox = transformed.bounding_box()
    info.clear()
    info.set("Shape", "Square" if target is square else "Triangle")
    info.set("Vertices", str(len(transformed)))
    info.set("Length", f"{transformed.length():.4f}")
    info.set("Area", f"{transformed.area():.4f}")
    info.set("BBox", f"({bbox[0]:.2f}, {bbox[1]:.2f})-({bbox[2]:.2f}, {bbox[3]:.2f})")
    info.set("Orientation", transformed.orientation)
    info.set("Scale", f"{s:.2f}")
    info.set("Translate", f"({tx:.2f}, {ty:.2f})")
    info.set("Reversed", str(reversed_on))

    fit_view(ax, square, triangle, transformed, padding=0.15)
    fig.canvas.draw_idle()


def reset_sliders(_=None):
    slider_scale.reset()
    slider_tx.reset()
    slider_ty.reset()


# Connect widgets
slider_scale.on_changed(update)
slider_tx.on_changed(update)
slider_ty.on_changed(update)
radio_target.on_clicked(update)
check_reverse.on_clicked(update)
btn_reset.on_clicked(reset_sliders)

# Draggable vertices
drag_sq = DraggableVertices(ax, square, update, color=COLORS["polyline_a"])
drag_tri = DraggableVertices(ax, triangle, update, color=COLORS["polyline_b"])

# Initial draw
update()
plt.show()
