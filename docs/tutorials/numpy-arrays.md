# NumPy arrays

This tutorial passes a NumPy `float64` array into Rust, borrows its data through
the Rust `numpy` crate, and computes a sum.

## Install the example dependency

The repository defines NumPy as an optional `examples` dependency:

```bash
uv sync --extra examples
```

## Run the complete example

```python
--8<-- "examples/numpy_sum/example.py"
```

Execute it:

```bash
uv run --extra examples python examples/numpy_sum/example.py
```

## Declare the Rust dependency

The extension specification adds the Rust `numpy` crate:

```python
dependencies={"numpy": "0.29"}
```

A string dependency value is shorthand for a crates.io version. `pycorrode`
adds it to the generated `Cargo.toml` alongside its managed PyO3 dependency.

## Borrow the array

The Rust function accepts `PyReadonlyArrayDyn<'_, f64>`:

```rust
fn sum_array(array: PyReadonlyArrayDyn<'_, f64>) -> f64 {
    array.as_array().sum()
}
```

`PyReadonlyArrayDyn` accepts arrays of any dimensionality with the requested
element type. `as_array()` produces a read-only ndarray view over the NumPy
storage, so the function can sum the input without first copying it into a Rust
`Vec`.

!!! note "Data type matters"

    This signature expects `float64`. Passing an array with an incompatible
    dtype results in a Python type-conversion error. The example constructs its
    array with `dtype=np.float64` explicitly.

## Where to go next

Continue with [Rust-backed iteration](rust-backed-iterator.md) to pass a NumPy
array into a Rust iterator and delegate Python iteration to it. Use the
[Cargo dependencies](../how-to/dependencies.md) guide for features, Git
repositories, branches, revisions, and local paths.
