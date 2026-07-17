# Support policy

## Python

`py_cavalier_contours` supports CPython 3.10 and newer. CI tests the oldest
supported CPython release and a current CPython release. A Python version may
be removed after it reaches upstream end of life; such a change will be noted
in the changelog and package metadata.

PyPy is not currently supported because the native CFFI distribution is not
tested there.

## Platforms

Prebuilt wheels are published for the architectures listed in the release
workflow. Other platforms may work by building the source distribution with a
stable Rust toolchain and a C compiler, but are supported on a best-effort
basis.

## Rust toolchain

Building from the source distribution requires Rust 1.88 or newer. The minimum
supported Rust version is recorded in `Cargo.toml` and checked by Cargo before
compilation.

## Compatibility

The project follows semantic versioning. Before version 1.0, a minor release
may include documented public API changes. Patch releases preserve the public
API and contain compatible fixes.

Numerical results can vary slightly across platforms. Applications should use
scale-appropriate tolerances rather than exact floating-point equality.

## Getting help

Use the project issue tracker for reproducible bugs and feature requests. An
effective geometry bug report includes the package version, Python/platform
information, input vertices and bulges, closed/open state, tolerance options,
expected result, and actual result.
