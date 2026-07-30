"""Compile and call two functions from one Rust extension."""

from pycorrode import ExtensionSpec, compile_extension

extension = compile_extension(
    ExtensionSpec(
        name="two_functions",
        source="""
use pyo3::prelude::*;

#[pyfunction]
fn add(left: i64, right: i64) -> i64 {
    left + right
}

#[pyfunction]
fn multiply(left: i64, right: i64) -> i64 {
    left * right
}
""",
    )
)

sum_result = extension.add(6, 7)
product_result = extension.multiply(6, 7)

print(f"6 + 7 = {sum_result}")
print(f"6 * 7 = {product_result}")

assert sum_result == 13
assert product_result == 42
