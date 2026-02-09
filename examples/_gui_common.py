"""
Shared infrastructure for interactive matplotlib-based examples.

Provides polyline/shape rendering, draggable vertices, info text display,
and common color constants.
"""
import matplotlib.pyplot as plt

from py_cavalier_contours import Vertex, Polyline, Shape, GeometryError

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLORS = {
    "polyline_a":       "#2196F3",
    "polyline_b":       "#FF9800",
    "result_pos":       "#4CAF50",
    "result_neg":       "#F44336",
    "offset":           "#9C27B0",
    "highlight":        "#FFEB3B",
    "vertex":           "#E91E63",
    "query_point":      "#00BCD4",
    "closest_point":    "#FF5722",
}

FILL_COLORS = {
    "polyline_a":       "#BBDEFB",
    "polyline_b":       "#FFE0B2",
    "result_pos":       "#C8E6C9",
    "result_neg":       "#FFCDD2",
    "offset":           "#E1BEE7",
}

RENDER_ERROR_DIST = 0.005


def polyline_coords(polyline):
    """Extract x, y coordinate arrays from a polyline, linearizing arcs."""
    linearized = polyline.to_lines(error_distance=RENDER_ERROR_DIST)
    xs, ys = [], []
    for v in linearized:
        xs.append(v.x)
        ys.append(v.y)
    if polyline.closed and xs:
        xs.append(xs[0])
        ys.append(ys[0])
    return xs, ys


def draw_polyline(ax, polyline, color="#2196F3", fill=None, linewidth=2,
                  linestyle="-", zorder=2, label=None):
    """Draw a polyline on an axes. Returns list of artists."""
    xs, ys = polyline_coords(polyline)
    if not xs:
        return []
    artists = []
    if fill and polyline.closed:
        art = ax.fill(xs, ys, color=fill, alpha=0.4, zorder=zorder - 1,
                       label=None)
        artists.extend(art)
    line, = ax.plot(xs, ys, color=color, linewidth=linewidth,
                    linestyle=linestyle, zorder=zorder, label=label)
    artists.append(line)
    return artists


def draw_polylines(ax, polylines, color="#2196F3", fill=None, **kwargs):
    """Draw multiple polylines. Returns list of artists."""
    artists = []
    for p in polylines:
        artists.extend(draw_polyline(ax, p, color=color, fill=fill, **kwargs))
    return artists


def draw_shape(ax, shape, outer_color="#2196F3", outer_fill="#BBDEFB",
               hole_color="#F44336", hole_fill="white", **kwargs):
    """Draw a Shape (outer boundaries + holes). Returns list of artists."""
    artists = []
    for p in shape.ccw_polylines:
        artists.extend(draw_polyline(ax, p, color=outer_color, fill=outer_fill,
                                     **kwargs))
    for p in shape.cw_polylines:
        artists.extend(draw_polyline(ax, p, color=hole_color, fill=hole_fill,
                                     zorder=kwargs.get("zorder", 2) + 1))
    return artists


def vertex_positions(polyline):
    """Get arrays of vertex x, y positions (original, not linearized)."""
    xs = [polyline[i].x for i in range(len(polyline))]
    ys = [polyline[i].y for i in range(len(polyline))]
    return xs, ys


def combined_bounding_box(*objects, padding=0.1):
    """Compute combined bounding box across polylines and shapes.

    Returns (min_x, min_y, max_x, max_y) with padding fraction applied.
    """
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')

    for obj in objects:
        if isinstance(obj, Shape):
            plines = obj.ccw_polylines + obj.cw_polylines
        elif isinstance(obj, Polyline):
            plines = [obj]
        elif isinstance(obj, (list, tuple)):
            plines = obj
        else:
            continue
        for p in plines:
            if len(p) == 0:
                continue
            bx0, by0, bx1, by1 = p.bounding_box()
            min_x, min_y = min(min_x, bx0), min(min_y, by0)
            max_x, max_y = max(max_x, bx1), max(max_y, by1)

    dx = (max_x - min_x) * padding or 1.0
    dy = (max_y - min_y) * padding or 1.0
    return min_x - dx, min_y - dy, max_x + dx, max_y + dy


def fit_view(ax, *objects, padding=0.1):
    """Set axes limits to fit all given polylines/shapes with padding."""
    min_x, min_y, max_x, max_y = combined_bounding_box(*objects, padding=padding)
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.set_aspect("equal")


class DraggableVertices:
    """Makes polyline vertices draggable on a matplotlib axes.

    On drag, updates the polyline vertex coordinates (preserving bulge)
    and calls on_update callback.
    """

    PICK_RADIUS_PX = 10

    def __init__(self, ax, polyline, on_update, color="#E91E63", zorder=10):
        self.ax = ax
        self.polyline = polyline
        self.on_update = on_update
        self._dragging_index = None

        xs, ys = vertex_positions(polyline)
        self.scatter = ax.scatter(xs, ys, color=color, s=60, zorder=zorder,
                                  edgecolors="white", linewidths=1.5, picker=True)

        self._cid_press = ax.figure.canvas.mpl_connect(
            "button_press_event", self._on_press)
        self._cid_motion = ax.figure.canvas.mpl_connect(
            "motion_notify_event", self._on_motion)
        self._cid_release = ax.figure.canvas.mpl_connect(
            "button_release_event", self._on_release)

    def _on_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        contains, info = self.scatter.contains(event)
        if contains and len(info["ind"]) > 0:
            self._dragging_index = info["ind"][0]

    def _on_motion(self, event):
        if self._dragging_index is None or event.inaxes != self.ax:
            return
        idx = self._dragging_index
        v = self.polyline[idx]
        self.polyline[idx] = Vertex(event.xdata, event.ydata, v.bulge)
        self._update_scatter()
        self.on_update()

    def _on_release(self, event):
        self._dragging_index = None

    def _update_scatter(self):
        xs, ys = vertex_positions(self.polyline)
        self.scatter.set_offsets(list(zip(xs, ys)))
        self.ax.figure.canvas.draw_idle()

    def refresh(self):
        """Refresh scatter positions from current polyline state."""
        self._update_scatter()

    def get_artists(self):
        return [self.scatter]

    def disconnect(self):
        fig = self.ax.figure
        fig.canvas.mpl_disconnect(self._cid_press)
        fig.canvas.mpl_disconnect(self._cid_motion)
        fig.canvas.mpl_disconnect(self._cid_release)


class DraggablePoint:
    """A single draggable point on a matplotlib axes (not attached to a polyline)."""

    def __init__(self, ax, x, y, on_update, color="#00BCD4", size=100, zorder=10):
        self.ax = ax
        self.x = x
        self.y = y
        self.on_update = on_update
        self._dragging = False

        self.scatter = ax.scatter([x], [y], color=color, s=size, zorder=zorder,
                                  edgecolors="white", linewidths=2, picker=True,
                                  marker="o")

        self._cid_press = ax.figure.canvas.mpl_connect(
            "button_press_event", self._on_press)
        self._cid_motion = ax.figure.canvas.mpl_connect(
            "motion_notify_event", self._on_motion)
        self._cid_release = ax.figure.canvas.mpl_connect(
            "button_release_event", self._on_release)

    def _on_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        contains, _ = self.scatter.contains(event)
        if contains:
            self._dragging = True

    def _on_motion(self, event):
        if not self._dragging or event.inaxes != self.ax:
            return
        self.x = event.xdata
        self.y = event.ydata
        self.scatter.set_offsets([[self.x, self.y]])
        self.on_update()

    def _on_release(self, event):
        self._dragging = False

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.scatter.set_offsets([[x, y]])

    def get_artists(self):
        return [self.scatter]

    def disconnect(self):
        fig = self.ax.figure
        fig.canvas.mpl_disconnect(self._cid_press)
        fig.canvas.mpl_disconnect(self._cid_motion)
        fig.canvas.mpl_disconnect(self._cid_release)


class InfoText:
    """Displays key-value info as text on an axes."""

    def __init__(self, ax, x=0.02, y=0.98, fontsize=9):
        self.ax = ax
        self._entries = {}
        self._order = []
        self._text = ax.text(x, y, "", transform=ax.transAxes,
                             verticalalignment="top", fontsize=fontsize,
                             fontfamily="monospace",
                             bbox=dict(boxstyle="round,pad=0.4",
                                       facecolor="#F5F5F5", alpha=0.9))

    def set(self, key, value):
        if key not in self._entries:
            self._order.append(key)
        self._entries[key] = value
        self._refresh()

    def clear(self):
        self._entries.clear()
        self._order.clear()
        self._refresh()

    def _refresh(self):
        lines = [f"{k}: {v}" for k, v in
                 ((k, self._entries[k]) for k in self._order)]
        self._text.set_text("\n".join(lines))

    def get_artists(self):
        return [self._text]
