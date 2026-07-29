"""Compile and call a tiny Rust extension."""

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
