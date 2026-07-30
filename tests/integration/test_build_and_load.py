from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from pycorrode import CargoDependency, ExtensionSpec, build_extension, load_extension

pytestmark = pytest.mark.integration


def _integration_available() -> bool:
    return (
        os.environ.get("PYCORRODE_SKIP_INTEGRATION") != "1"
        and shutil.which("cargo") is not None
        and shutil.which("rustc") is not None
    )


def _write_dependency_crate(
    root: Path,
    *,
    package_name: str,
    feature: str,
    expression: str,
) -> None:
    source_dir = root / "src"
    source_dir.mkdir(parents=True)
    (root / "Cargo.toml").write_text(
        f"""\
[package]
name = "{package_name}"
version = "0.1.0"
edition = "2021"

[features]
{feature} = []
"""
    )
    (source_dir / "lib.rs").write_text(
        f"""\
#[cfg(feature = "{feature}")]
pub fn transform(value: i64) -> i64 {{
    {expression}
}}
"""
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


@pytest.mark.skipif(
    not _integration_available() or shutil.which("git") is None,
    reason="Rust dependency integration requires Cargo, rustc, and Git",
)
def test_builds_with_path_git_and_feature_dependencies(tmp_path: Path) -> None:
    path_dependency = tmp_path / "path-dependency"
    _write_dependency_crate(
        path_dependency,
        package_name="path-dependency",
        feature="triple",
        expression="value * 3",
    )

    git_dependency = tmp_path / "git-dependency"
    _write_dependency_crate(
        git_dependency,
        package_name="git-dependency",
        feature="increment",
        expression="value + 1",
    )
    subprocess.run(["git", "init", "--quiet"], cwd=git_dependency, check=True)
    subprocess.run(["git", "add", "."], cwd=git_dependency, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=pycorrode tests",
            "-c",
            "user.email=tests@pycorrode.invalid",
            "commit",
            "--quiet",
            "-m",
            "Initial dependency",
        ],
        cwd=git_dependency,
        check=True,
    )

    spec = ExtensionSpec(
        name="dependency_sources",
        source="""
use pyo3::prelude::*;

#[pyfunction]
fn combine(value: i64) -> i64 {
    path_dependency::transform(value) + git_dependency::transform(value)
}
""",
        dependencies={
            "git-dependency": CargoDependency(
                git=git_dependency.as_uri(),
                features=("increment",),
            ),
            "path-dependency": CargoDependency(
                path=path_dependency,
                features=("triple",),
            ),
        },
    )

    result = build_extension(spec, cache_dir=tmp_path / "cache")
    module = load_extension(result)

    assert module.combine(4) == 17
