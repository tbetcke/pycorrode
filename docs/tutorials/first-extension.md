# Your first extension

In this tutorial you will compile a Rust function, call it from Python, and see
how `pycorrode` finds its export.

## 1. Start with the complete program

The repository includes this tested example:

```python
--8<-- "examples/double/example.py"
```

Run it from the repository root:

```bash
uv run python examples/double/example.py
```

The output is:

```text
42
```

## 2. Describe the extension

The `ExtensionSpec` gives this build a friendly name:

```python
ExtensionSpec(name="double", source=rust_source)
```

The friendly name participates in the cache fingerprint. Internally,
`pycorrode` generates a content-addressed native module name so rebuilt
extensions cannot collide with an older module already loaded into the process.

## 3. Expose a PyO3 function

The Rust source imports the PyO3 prelude and marks `double` with
`#[pyfunction]`:

```rust
use pyo3::prelude::*;

#[pyfunction]
fn double(value: i64) -> i64 {
    value * 2
}
```

`pycorrode` discovers ordinary annotated function declarations and registers
them in the generated PyO3 module. PyO3 performs the conversion between the
Python integer and Rust's `i64`.

## 4. Build and load

`compile_extension(spec)` builds and immediately loads the extension:

```python
extension = compile_extension(spec)
```

The return value behaves like an imported Python module:

```python
answer = extension.double(21)
assert answer == 42
```

## 5. Try a change

Change the Rust expression to `value * 3` and call `extension.double(14)`.
Because the Rust source participates in the cache key, the changed specification
produces a new native artifact.

## What you learned

You now know how to:

- describe an extension with `ExtensionSpec`;
- expose a Rust function with `#[pyfunction]`;
- compile and load it with `compile_extension`;
- call the result like an ordinary Python module.

Continue with [Multiple functions](multiple-functions.md) to expose more than
one operation from the same build.
