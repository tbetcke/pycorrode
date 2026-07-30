# pycorrode

`pycorrode` builds small [PyO3](https://pyo3.rs/) extension modules on demand
by invoking the user's Cargo toolchain, caches the resulting native library, and
loads it into the running Python interpreter.

The project is currently an alpha. Its first API intentionally covers a narrow
use case: provide Rust source containing one or more `#[pyfunction]` functions
and receive an importable Python extension module.

## Requirements

- Python 3.11 or newer
- A working `cargo` and `rustc` installation
- Network access to crates.io for the first build, unless the required crates
  are already in Cargo's cache
- A platform toolchain capable of building Python native extensions

`pycorrode` itself is a pure Python package. The Rust toolchain is a runtime
system requirement and is not installed by `pip` or `uv`.

## Installation

From a checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Using uv

With [`uv`](https://docs.astral.sh/uv/) installed, create the project
environment and install the development extra:

```bash
uv sync --extra dev
```

`uv` creates `.venv` automatically and installs the checkout as an editable
package. Cargo and rustc must still be installed separately and available on
`PATH`.

Run the included example:

```bash
uv run python examples/double/example.py
```

The two-functions example compiles a single extension containing both `add`
and `multiply`:

```bash
uv run python examples/two_functions/example.py
```

The NumPy example passes a `float64` array to Rust without copying it, sums its
elements there, and returns the result:

```bash
uv run --extra examples python examples/numpy_sum/example.py
```

Run the development checks or build distributions without activating the
virtual environment:

```bash
uv run --extra dev ruff check .
uv run --extra dev pytest
uv build
```

To install only the package's runtime dependencies, omit the development
extra:

```bash
uv sync
```

## Quick start

```python
from pycorrode import ExtensionSpec, compile_extension

spec = ExtensionSpec(
    name="double",
    source="""
use pyo3::prelude::*;

#[pyfunction]
fn double(value: i64) -> i64 {
    value * 2
}
""",
)

module = compile_extension(spec)
assert module.double(21) == 42
```

By default, `pycorrode` discovers straightforward functions annotated with
`#[pyfunction]`. For macros or formatting that cannot be discovered
automatically, list the Rust function names explicitly:

```python
spec = ExtensionSpec(
    name="custom",
    source=rust_source,
    exports=("first_function", "second_function"),
)
```

Additional crates.io dependencies can be declared as strings:

```python
spec = ExtensionSpec(
    name="uses_dependency",
    source=rust_source,
    dependencies={"serde": "1.0"},
)
```

Or with features:

```python
from pycorrode import CargoDependency, ExtensionSpec

spec = ExtensionSpec(
    name="uses_serde",
    source=rust_source,
    dependencies={
        "serde": CargoDependency(
            version="1.0",
            features=("derive",),
        )
    },
)
```

## Build and load separately

Compilation and importing are separate operations:

```python
from pycorrode import build_extension, load_extension

result = build_extension(spec)
print(result.artifact)
print(result.cache_hit)

module = load_extension(result)
```

Use a temporary or application-specific cache when required:

```python
result = build_extension(spec, cache_dir="/path/to/cache")
```

The default cache follows the platform's user-cache convention. Set
`PYCORRODE_CACHE_DIR` to override it globally.

## How the cache works

The cache key incorporates:

- Rust source and exported function names
- Cargo dependency declarations and PyO3 version
- Python implementation and ABI
- operating system and architecture
- Cargo and Rust compiler versions and Rust target
- build profile and the generated-project schema version

Each entry contains its generated Cargo project, Cargo target directory,
renamed Python extension, metadata, and a completion marker. A per-entry file
lock prevents concurrent processes from building the same extension
simultaneously.

Use `force=True` to rebuild an entry:

```python
result = build_extension(spec, force=True)
```

## Errors

Toolchain, configuration, compilation, and loading failures use subclasses of
`PyCorrodeError`. Rust diagnostics are available on
`PyCorrodeBuildError.diagnostics`.

```python
from pycorrode import PyCorrodeBuildError

try:
    module = compile_extension(spec)
except PyCorrodeBuildError as error:
    print(error.diagnostics)
```

## Security

Rust source, Cargo dependencies, dependency build scripts, and the compiled
extension all execute native code with the current user's permissions. Never
compile or load untrusted source or dependency declarations.

## Development

```bash
ruff check .
pytest
python -m build
```

The integration tests invoke Cargo and compile a real PyO3 module:

```bash
pytest -m integration
```

Set `PYCORRODE_SKIP_INTEGRATION=1` to skip them in an environment without an
available Rust registry or native compiler.

See [the architecture notes](docs/architecture.md) for the runtime build
pipeline and current limitations.

## AI Notice

This project was co-designed with GPT-5.6.
