# Changelog

All notable user-visible changes are documented here. The project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Production packaging metadata, installation and geometry documentation.
- Interactive examples for core polyline and shape operations.
- Wrappers for orientation, point queries, containment, intersection queries,
  arc linearization, start rotation, and shapes with holes.
- Deterministic native-resource cleanup through `close()` and context managers.
- Branch-coverage reporting and a 90% Python coverage gate.

### Fixed

- Preserve every polyline returned by multi-result boolean and offset operations.
- Convert all native error statuses and null handles into Python exceptions.
- Reject non-finite geometry inputs and invalid numerical tolerances.
- Clean up partial native allocations when Python or FFI operations fail.
- Validate shape inputs and support sequence-compatible polyline insertion.
- Cover overlapping intersections, self-intersections, start rotation, boolean
  holes, copy/lifecycle behavior, and native ABI result extraction.
