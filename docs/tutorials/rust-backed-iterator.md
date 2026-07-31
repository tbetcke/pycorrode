# Rust-backed iteration

This tutorial passes a NumPy array to Rust, creates an iterator in Rust, and
returns it to Python. A small Python iterator then delegates every request for
the next value to the Rust iterator.

## Install the example dependency

The example uses the repository's optional NumPy dependency:

```bash
uv sync --extra examples
```

## Run the complete example

```python
--8<-- "examples/numpy_iterator/example.py"
```

Execute it:

```bash
uv run --extra examples python examples/numpy_iterator/example.py
```

The output is:

```text
Rust yielded [1.0, 2.5, 3.0, 4.5]
```

## Create owned iterator state in Rust

The factory accepts a read-only NumPy array of any dimensionality:

```rust
#[pyfunction]
fn make_rust_iterator(array: PyReadonlyArrayDyn<'_, f64>) -> RustArrayIterator {
    let values = array
        .as_array()
        .iter()
        .copied()
        .collect::<Vec<_>>()
        .into_iter();

    RustArrayIterator { values }
}
```

The NumPy view is valid only for the duration of the function call. The example
therefore copies its values into a `Vec<f64>` and calls `into_iter()`. The
returned object owns that Rust iterator, so it remains valid after the function
returns and is unaffected by later changes to the NumPy array.

## Expose the Rust iterator to Python

`RustArrayIterator` is a PyO3 class whose only state is Rust's
`std::vec::IntoIter<f64>`:

```rust
#[pyclass]
struct RustArrayIterator {
    values: std::vec::IntoIter<f64>,
}

#[pymethods]
impl RustArrayIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self) -> Option<f64> {
        self.values.next()
    }
}
```

Each `__next__` call advances the stored Rust iterator once. PyO3 converts
`Some(value)` to a Python float and converts `None` to `StopIteration`.

Only `make_rust_iterator` needs to be listed as an extension export.
`pycorrode` registers that `#[pyfunction]`, and PyO3 converts its returned
`RustArrayIterator` into a Python object.

## Delegate from a Python iterator

The Python wrapper creates the Rust iterator in `__init__` and forwards each
`__next__` call:

```python
class RustBackedArrayIterator(Iterator[float]):
    def __init__(self, values: np.ndarray) -> None:
        self._rust_iterator = extension.make_rust_iterator(values)

    def __iter__(self) -> "RustBackedArrayIterator":
        return self

    def __next__(self) -> float:
        return next(self._rust_iterator)
```

The sequence for every value request is:

1. Python calls `RustBackedArrayIterator.__next__`.
2. The wrapper calls `next()` on the PyO3 object.
3. Rust advances `IntoIter<f64>` and returns its next value.
4. PyO3 converts the result back to Python.

When Rust exhausts the iterator, its `None` result becomes `StopIteration`, so
normal Python consumers such as `list()`, `for`, and `sum()` work as expected.

## Where to go next

Read the [architecture explanation](../explanation/architecture.md) to see how
`pycorrode` generates and loads the module containing the factory function.
