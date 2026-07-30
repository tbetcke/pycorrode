# Getting started

This guide takes you from a source checkout to a callable Rust function in
Python.

## Requirements

You need:

- Python 3.11 or newer
- `cargo` and `rustc` on `PATH`
- a platform toolchain capable of building Python native extensions
- network access to crates.io for the first build, unless PyO3 is already in
  Cargo's cache

`pycorrode` is pure Python. It invokes your existing Rust toolchain at runtime;
installing the Python package does not install Rust.

## Install from a checkout

With [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/tbetcke/pycorrode.git
cd pycorrode
uv sync --extra dev
```

Or with the standard library's virtual environment support:

```bash
git clone https://github.com/tbetcke/pycorrode.git
cd pycorrode
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --editable ".[dev]"
```

Confirm that Python and Cargo are available:

```bash
python --version
cargo --version
```

## Compile one function

Create `example.py`:

```python
from pycorrode import ExtensionSpec, compile_extension

extension = compile_extension(
    ExtensionSpec(
        name="double",
        source="""
use pyo3::prelude::*;

#[pyfunction]
fn double(value: i64) -> i64 {
    value * 2
}
""",
    )
)

print(extension.double(21))
```

Run it:

```bash
python example.py
```

The first run invokes Cargo and prints:

```text
42
```

Run it again with the same interpreter and toolchain. `pycorrode` validates the
matching cache entry and loads the existing native artifact.

## What the code means

`ExtensionSpec` contains the friendly extension name, Rust source, dependencies,
and build settings. `compile_extension` performs two operations:

1. build or retrieve the matching native artifact;
2. load it as a Python module.

Every discovered `#[pyfunction]` becomes an attribute on that returned module.

## Next steps

- Work through [Your first extension](tutorials/first-extension.md) for a more
  detailed tour.
- Export [multiple functions](tutorials/multiple-functions.md) from one module.
- Add [Cargo dependencies](how-to/dependencies.md).
- Learn when to use the separate
  [`build_extension` and `load_extension`](how-to/caching.md#build-and-load-separately)
  operations.
