# Contributing

Bug reports and focused pull requests are welcome. For security-sensitive
reports, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Development setup

The project requires CPython 3.10 or newer, Rust 1.88 or newer, and a C
compiler.

```console
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,examples]"
```

On Windows, use `.venv\Scripts\activate` to activate the environment.

## Before opening a pull request

Run the same core checks as CI:

```console
ruff check py_cavalier_contours test examples
mypy --disable-error-code attr-defined py_cavalier_contours/*.py
pytest --cov=py_cavalier_contours --cov-branch --cov-report=term-missing
cargo fmt --all -- --check
cargo test --locked
```

Add tests for behavioral changes and update the README or API docstrings when
public behavior changes. User-visible changes should also be recorded under
the Unreleased section of [CHANGELOG.md](CHANGELOG.md).

Do not commit generated native libraries, virtual environments, build output,
or generated CFFI packages.

## Releases

1. Make sure CI is green on `main` and the Unreleased changelog is complete.
2. Update the version in `Cargo.toml` and `Cargo.lock`.
3. Move changelog entries into a dated release section and merge the change.
4. Create a signed tag named `vX.Y.Z`, exactly matching the Cargo version.
5. Push the tag. CI builds and tests wheels and the source distribution before
   publishing through PyPI trusted publishing.

The release workflow rejects mismatched tags and never overwrites an existing
PyPI file.

The Rust dependency review and acceptance process is documented in
[docs/cavalier-contours-upgrade.md](docs/cavalier-contours-upgrade.md).
