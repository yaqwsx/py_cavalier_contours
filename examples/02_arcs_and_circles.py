"""
02_arcs_and_circles.py -- Interactive exploration of arc segments (bulge values).

Demonstrates:
  - Creating arcs and circles using bulge values
  - Visualizing how bulge controls arc curvature
  - Linearization with to_lines() at varying error tolerances
  - Comparing arc vs. linearized area and perimeter
"""
import math

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, CheckButtons

from py_cavalier_contours import Vertex, Polyline, GeometryError
from _gui_common import (
    draw_polyline, polyline_coords, fit_view, DraggableVertices,
    InfoText, COLORS, FILL_COLORS, RENDER_ERROR_DIST,
)

# ---------------------------------------------------------------------------
# Initial geometry
# ---------------------------------------------------------------------------
# Circle of radius 1 from two semicircular arcs
circle = Polyline([
    Vertex(1, 0, 1),
    Vertex(-1, 0, 1),
], closed=True)

# Demo arc: two endpoints with adjustable bulge
arc_pline = Polyline([
    Vertex(-2, -3, 0.5),
    Vertex(2, -3, 0),
], closed=False)

# ---------------------------------------------------------------------------
# Figure layout
# ---------------------------------------------------------------------------
fig = plt.figure("02 - Arcs and Circles", figsize=(11, 7))
fig.subplots_adjust(left=0.05, right=0.65, top=0.95, bottom=0.05)
ax = fig.add_subplot(111)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3)

# Controls
ax_bulge = fig.add_axes([0.70, 0.75, 0.25, 0.04])
ax_error = fig.add_axes([0.70, 0.67, 0.25, 0.04])
ax_show_lin = fig.add_axes([0.70, 0.56, 0.25, 0.08])

slider_bulge = Slider(ax_bulge, "Bulge", -2.0, 2.0, valinit=0.5)
slider_error = Slider(ax_error, "Error dist", 0.001, 0.5, valinit=0.01)
check_show_lin = CheckButtons(ax_show_lin, ["Show linearization"], [True])

# Info
info = InfoText(ax, x=0.02, y=0.98)

result_artists = []


def update(_=None):
    global result_artists
    for a in result_artists:
        a.remove()
    result_artists = []

    bulge_val = slider_bulge.val
    error_dist = slider_error.val
    show_lin = check_show_lin.get_status()[0]

    # Update the arc's bulge value
    v0 = arc_pline[0]
    arc_pline[0] = Vertex(v0.x, v0.y, bulge_val)

    # -- Draw the circle (always visible) --
    result_artists.extend(
        draw_polyline(ax, circle, color=COLORS["polyline_a"],
                      fill=FILL_COLORS["polyline_a"], linewidth=2))

    # -- Draw the demo arc (high-res for "true" curve) --
    result_artists.extend(
        draw_polyline(ax, arc_pline, color=COLORS["polyline_b"], linewidth=2.5))

    # -- Linearization overlay --
    if show_lin:
        try:
            linearized_arc = arc_pline.to_lines(error_distance=error_dist)
            # Draw individual segments with visible vertices
            xs, ys = [], []
            for v in linearized_arc:
                xs.append(v.x)
                ys.append(v.y)
            if xs:
                line, = ax.plot(xs, ys, color=COLORS["result_pos"],
                                linewidth=1.5, linestyle="-", zorder=4,
                                marker=".", markersize=5)
                result_artists.append(line)
        except GeometryError:
            pass

        try:
            linearized_circ = circle.to_lines(error_distance=error_dist)
            xs, ys = [], []
            for v in linearized_circ:
                xs.append(v.x)
                ys.append(v.y)
            if linearized_circ.closed and xs:
                xs.append(xs[0])
                ys.append(ys[0])
            if xs:
                line, = ax.plot(xs, ys, color=COLORS["result_pos"],
                                linewidth=1, linestyle="-", zorder=4,
                                marker=".", markersize=4)
                result_artists.append(line)
        except GeometryError:
            pass

    # -- Info panel --
    info.clear()

    # Arc info
    sweep_deg = math.degrees(4 * math.atan(abs(bulge_val))) if bulge_val != 0 else 0
    info.set("Bulge", f"{bulge_val:.4f}")
    info.set("Sweep angle", f"{sweep_deg:.1f} deg")

    # Circle info
    c_area = circle.area()
    c_perim = circle.length()
    info.set("Circle area", f"{c_area:.6f} (pi={math.pi:.6f})")
    info.set("Circle perim", f"{c_perim:.6f} (2pi={2*math.pi:.6f})")

    # Linearization stats
    if show_lin:
        try:
            lin_c = circle.to_lines(error_distance=error_dist)
            lin_a = arc_pline.to_lines(error_distance=error_dist)
            info.set("Circ lin verts", str(len(lin_c)))
            info.set("Circ area err", f"{abs(lin_c.area() - math.pi):.2e}")
            info.set("Arc lin verts", str(len(lin_a)))
        except GeometryError:
            pass

    info.set("Error dist", f"{error_dist:.4f}")

    drag_arc.refresh()
    fit_view(ax, circle, arc_pline, padding=0.2)
    fig.canvas.draw_idle()


# Draggable vertices for the arc endpoints
drag_arc = DraggableVertices(ax, arc_pline, update, color=COLORS["polyline_b"])

slider_bulge.on_changed(update)
slider_error.on_changed(update)
check_show_lin.on_clicked(update)

update()
plt.show()
