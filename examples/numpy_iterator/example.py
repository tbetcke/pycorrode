"""Delegate Python iteration to a Rust iterator created from a NumPy array."""

from collections.abc import Iterator

import numpy as np

from pycorrode import ExtensionSpec, compile_extension

extension = compile_extension(
    ExtensionSpec(
        name="numpy_iterator",
        source="""
use numpy::PyReadonlyArrayDyn;
use pyo3::prelude::*;

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
""",
        dependencies={"numpy": "0.29"},
    )
)


class RustBackedArrayIterator(Iterator[float]):
    """A Python iterator whose iteration state lives in Rust."""

    def __init__(self, values: np.ndarray) -> None:
        self._rust_iterator = extension.make_rust_iterator(values)

    def __iter__(self) -> "RustBackedArrayIterator":
        return self

    def __next__(self) -> float:
        return next(self._rust_iterator)


values = np.array([[1.0, 2.5], [3.0, 4.5]], dtype=np.float64)
iterator = RustBackedArrayIterator(values)

first = next(iterator)
remaining = list(iterator)
result = [first, *remaining]

print(f"Rust yielded {result}")
assert result == values.ravel().tolist()
