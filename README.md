# pycorrode

[![CI](https://github.com/tbetcke/pycorrode/actions/workflows/ci.yml/badge.svg)](https://github.com/tbetcke/pycorrode/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-b7410e)](https://tbetcke.github.io/pycorrode/)

`pycorrode` builds small [PyO3](https://pyo3.rs/) extension modules on demand,
caches the resulting native library, and loads it into the running Python
interpreter.

The project is currently an alpha. Its first API intentionally covers a narrow
use case: provide Rust source containing one or more `#[pyfunction]` functions
and receive an importable Python extension module.

## Requirements

- Python 3.11 or newer
- `cargo` and `rustc` on `PATH`
- a platform toolchain capable of building Python native extensions
- network access to dependency sources for the first build, unless cached

`pycorrode` is pure Python. It uses the existing Rust toolchain at runtime and
does not install Cargo or rustc.

## Installation from a checkout

With [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/tbetcke/pycorrode.git
cd pycorrode
uv sync --extra dev
```

Or with `venv` and `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --editable ".[dev]"
```

## Quick start

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

assert extension.double(21) == 42
```

The first run invokes Cargo. Later calls with the same source, dependencies,
interpreter, platform, and toolchain reuse the validated cached artifact.

## Documentation

The [documentation site](https://tbetcke.github.io/pycorrode/) includes:

- a [getting-started guide](https://tbetcke.github.io/pycorrode/getting-started/)
- tutorials for [multiple functions](https://tbetcke.github.io/pycorrode/tutorials/multiple-functions/),
  [NumPy arrays](https://tbetcke.github.io/pycorrode/tutorials/numpy-arrays/),
  and [Rust-backed iteration](https://tbetcke.github.io/pycorrode/tutorials/rust-backed-iterator/)
- how-to guides for [Cargo dependencies](https://tbetcke.github.io/pycorrode/how-to/dependencies/),
  caching, errors, and troubleshooting
- the generated [Python API reference](https://tbetcke.github.io/pycorrode/reference/api/)
- architecture and security explanations

## Examples

```bash
uv run python examples/double/example.py
uv run python examples/two_functions/example.py
uv run --extra examples python examples/numpy_sum/example.py
uv run --extra examples python examples/numpy_iterator/example.py
```

## Development

Install all development surfaces:

```bash
uv sync --extra dev --extra docs --extra examples
```

Run the checks:

```bash
uv run --extra dev ruff check .
uv run --extra dev pytest
uv run --extra docs mkdocs build --strict
uv build
```

Preview the documentation:

```bash
uv run --extra docs mkdocs serve
```

## Security

Rust source, Cargo dependencies, dependency build scripts, and the compiled
extension all execute native code with the current user's permissions. Never
compile or load untrusted source or dependency declarations.

See the full [security model](https://tbetcke.github.io/pycorrode/explanation/security/).

## License

`pycorrode` is distributed under the [MIT License](LICENSE).

## AI Notice

This project was co-designed with GPT-5.6.
