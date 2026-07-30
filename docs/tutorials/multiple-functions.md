# Multiple functions

One extension can contain several `#[pyfunction]` declarations. They are
compiled together and exposed on the same Python module.

## Complete example

```python
--8<-- "examples/two_functions/example.py"
```

Run it:

```bash
uv run python examples/two_functions/example.py
```

You should see:

```text
6 + 7 = 13
6 * 7 = 42
```

## How export discovery works

The source contains two ordinary annotated functions:

```rust
#[pyfunction]
fn add(left: i64, right: i64) -> i64 {
    left + right
}

#[pyfunction]
fn multiply(left: i64, right: i64) -> i64 {
    left * right
}
```

`ExtensionSpec` discovers both names in source order. The generated module
registers each function, producing:

```python
extension.add(6, 7)
extension.multiply(6, 7)
```

## Specify exports explicitly

Automatic discovery intentionally targets straightforward Rust declarations.
If macros or unusual formatting prevent discovery, provide the Rust function
names:

```python
spec = ExtensionSpec(
    name="two_functions",
    source=rust_source,
    exports=("add", "multiply"),
)
```

Export names must be unique Rust identifiers. They refer to the Rust function
names used during generated module registration.

## Next step

The [NumPy arrays](numpy-arrays.md) tutorial adds an external Cargo dependency
and passes borrowed array data into Rust.
