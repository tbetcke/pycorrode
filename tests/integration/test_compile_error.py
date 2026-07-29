from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from pycorrode import ExtensionSpec, PyCorrodeBuildError, build_extension

pytestmark = pytest.mark.integration


def _integration_available() -> bool:
    return (
        os.environ.get("PYCORRODE_SKIP_INTEGRATION") != "1"
        and shutil.which("cargo") is not None
        and shutil.which("rustc") is not None
    )


@pytest.mark.skipif(
    not _integration_available(),
    reason="Rust integration tests are disabled or no toolchain is available",
)
def test_compile_error_contains_rust_diagnostics(tmp_path: Path) -> None:
    spec = ExtensionSpec(
        name="broken",
        source="""
use pyo3::prelude::*;

#[pyfunction]
fn broken() -> i64 {
    this is not valid rust
}
""",
    )

    with pytest.raises(PyCorrodeBuildError) as caught:
        build_extension(spec, cache_dir=tmp_path)

    assert caught.value.returncode
    assert "error" in caught.value.diagnostics.lower()
    assert not list(tmp_path.glob("v1/modules/*/build.json"))
