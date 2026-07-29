from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from pycorrode import ExtensionSpec, build_extension, load_extension

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
def test_build_load_and_cache_real_extension(tmp_path: Path) -> None:
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

    first = build_extension(spec, cache_dir=tmp_path)
    second = build_extension(spec, cache_dir=tmp_path)
    module = load_extension(first)

    assert not first.cache_hit
    assert second.cache_hit
    assert second.artifact == first.artifact
    assert module.double(21) == 42
