# py_cavalier_contours

`py_cavalier_contours` is a Python interface to the Rust
[`cavalier_contours`](https://github.com/jbuckmccready/cavalier_contours)
library. It provides native-speed operations on 2D polylines made from straight
line and constant-radius arc segments.

The package supports CPython 3.10 and newer on the platforms for which a wheel
is published. A source distribution is also provided for other platforms with
a Rust toolchain.

## Features

- Open and closed polylines with line and circular-arc segments
- Length, signed area, orientation, bounding-box, and winding-number queries
- Closest-point and point-at-path-length queries
- Union, intersection, difference, and symmetric difference
- Parallel offsets and self-intersection detection
- Shapes containing multiple outer boundaries and holes
- Arc linearization and in-place scale, translation, and reversal

## Installation

Install the latest release from PyPI:

```console
python -m pip install py_cavalier_contours
```

The interactive examples use Matplotlib:

```console
python -m pip install "py_cavalier_contours[examples]"
```

## Quickstart

```python
from py_cavalier_contours import Polyline, Vertex

square = Polyline(
    [
        Vertex(0.0, 0.0),
        Vertex(2.0, 0.0),
        Vertex(2.0, 2.0),
        Vertex(0.0, 2.0),
    ],
    closed=True,
)

print(square.length())       # 8.0
print(square.area())         # 4.0 (signed; positive means counter-clockwise)
print(square.orientation)    # "ccw"
print(square.winding_number(1.0, 1.0))  # non-zero means inside

# A positive offset lies to the left of each directed segment. For this
# counter-clockwise square, that is an inward offset.
inset_parts = square.offset(0.25)

other = Polyline(
    [
        Vertex(1.0, 1.0),
        Vertex(3.0, 1.0),
        Vertex(3.0, 3.0),
        Vertex(1.0, 3.0),
    ],
    closed=True,
)
outlines, holes = square.union(other)
```

Boolean operations return `(positive_polylines, negative_polylines)`, where
positive polylines are counter-clockwise outlines and negative polylines are
clockwise holes.

## Geometry conventions

Each `Vertex(x, y, bulge)` starts the segment leading to the next vertex. For a
closed polyline, the final vertex starts the closing segment back to the first
vertex.

- `bulge == 0` creates a straight segment.
- `bulge > 0` creates a counter-clockwise arc.
- `bulge < 0` creates a clockwise arc.
- `bulge = tan(sweep_angle / 4)`; an absolute bulge of `1` is a semicircle.

Area is signed: counter-clockwise closed polylines have positive area and
clockwise polylines have negative area. `Shape` expects outer boundaries to be
counter-clockwise and holes to be clockwise.

Offset distance is measured to the left of the polyline's direction. Thus a
positive offset moves a counter-clockwise boundary inward and a clockwise
boundary outward. Reverse the polyline or negate the distance to choose the
other side.

Many topology operations accept epsilon parameters. Coordinates and epsilon
values use the same units. The defaults (`1e-5` for most polyline operations)
are suitable for modest coordinate ranges, but applications using very large
or very small coordinates should choose tolerances appropriate to their scale.

## Examples

After installing the `examples` extra, run an example from a repository
checkout:

```console
python examples/01_basic_polyline.py
python examples/02_arcs_and_circles.py
python examples/03_boolean_operations.py
python examples/04_offset.py
python examples/05_shape_with_holes.py
python examples/06_point_queries.py
```

The examples are interactive Matplotlib applications: vertices can be dragged,
and controls update the result in real time.

## Development

Building from source requires CPython 3.10 or newer, Rust 1.88 or newer, and a
C compiler. Clone the repository, then create an isolated
environment and install the development dependencies:

```console
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,examples]"
pytest
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

Useful checks before submitting a change are:

```console
ruff check py_cavalier_contours test examples
mypy --disable-error-code attr-defined py_cavalier_contours/*.py
pytest --cov=py_cavalier_contours --cov-branch --cov-report=term-missing
cargo fmt --all -- --check
cargo test --locked
maturin build --release --locked
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and
[SUPPORT.md](SUPPORT.md) for the compatibility policy. Rust dependency updates
follow the gates in
[docs/cavalier-contours-upgrade.md](docs/cavalier-contours-upgrade.md).

## License

This project is licensed under the MIT License; see [LICENCE](LICENCE).
Licenses and notices for native dependencies distributed in the wheel are in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
