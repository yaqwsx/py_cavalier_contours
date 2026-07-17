# cavalier_contours upgrade plan

## Current state

The production dependency is pinned to `cavalier_contours` and
`cavalier_contours_ffi` commit
`768834191e7f59903bbff21152878c6ed542c817`, the upstream `0.7.0` release from
2026-01-02. This is still the latest published release.

Upstream `master` commit `f23c2955be810801f2d6c51c4185b1fb389cb0e6`
contains later fixes for repeated-position and collapsed near-vertex offset
inputs. A compatibility build against that exact commit passes the complete
Python suite. The repeated-position regression in `test/test_boolean.py`
documents a concrete behavioral difference: `0.7.0` returns non-finite
geometry, while the candidate returns a finite eight-vertex offset.

## Upgrade sequence

1. Keep upstream versions deterministic. Upgrade both Rust crates to the same
   tag or full commit and update `Cargo.lock` in one isolated change.
2. Review the upstream changelog and the generated C header diff. Any changed
   C option struct, result ownership rule, error code, or function signature
   requires an explicit Python wrapper review.
3. Remove the strict `xfail` from the repeated-position regression. An XPASS
   is intentionally a failure so an upgrade cannot silently leave the marker
   behind.
4. Run all Python tests, Rust ABI tests, branch coverage, Ruff, Mypy, Clippy,
   rustfmt, and the Rust 1.88 MSRV check.
5. Build and install both wheel and sdist artifacts in clean environments.
   Run the hosted CPython/platform wheel matrix before merging.
6. Compare representative boolean, intersection, arc, shape-with-hole, and
   offset results against the previous dependency. Record intentional numeric
   or topology changes in `CHANGELOG.md`.

## Recommended next dependency change

Before the first public release, pin both crates to upstream commit
`f23c2955be810801f2d6c51c4185b1fb389cb0e6`. It fixes a reproduced non-finite
offset result and has already passed the wrapper compatibility suite. Keep the
change in its own pull request so reverting it only requires restoring
`Cargo.toml` and `Cargo.lock`.

When upstream publishes the next release containing these fixes, prefer the
crates.io versions for resilient source builds:

```toml
cavalier_contours = "<new-version>"
cavalier_contours_ffi = "<same-new-version>"
```

Do not mix versions of the core and FFI crates.

## Merge gates

- No unexpected dependency changes in `Cargo.lock`.
- The repeated-position offset has finite area and length.
- Python branch coverage remains at least 90%.
- All Python and Rust tests pass in debug and release artifact builds.
- Rust 1.88 remains sufficient, or the support-policy change is documented.
- Wheel and sdist metadata, installation, and import checks pass.
- Hosted Linux, Windows, and macOS wheel jobs pass.

## Future upgrade monitoring

Check the upstream release page and changelog before each project release.
Test unreleased upstream commits in a non-blocking scheduled CI lane when they
contain geometry fixes relevant to this wrapper; production dependencies must
remain pinned to a reviewed tag or full commit.
