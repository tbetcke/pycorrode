"""Pass a NumPy array to Rust and sum its elements."""

import numpy as np

from pycorrode import ExtensionSpec, compile_extension

extension = compile_extension(
    ExtensionSpec(
        name="numpy_sum",
        source="""
use numpy::PyReadonlyArrayDyn;
use pyo3::prelude::*;

#[pyfunction]
fn sum_array(array: PyReadonlyArrayDyn<'_, f64>) -> f64 {
    array.as_array().sum()
}
""",
        dependencies={"numpy": "0.29"},
    )
)

values = np.array([[1.0, 2.5], [3.0, 4.5]], dtype=np.float64)
result = extension.sum_array(values)

print(f"The sum of {values} is {result}")
assert result == 11.0
