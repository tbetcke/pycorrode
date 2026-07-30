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


def _initialize_git_repository(root: Path, branch: str) -> str:
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(
        ["git", "checkout", "--quiet", "-b", branch],
        cwd=root,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True)
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
        cwd=root,
        check=True,
    )
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


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
def test_builds_with_path_git_selectors_and_features(tmp_path: Path) -> None:
    path_dependency = tmp_path / "path-dependency"
    _write_dependency_crate(
        path_dependency,
        package_name="path-dependency",
        feature="triple",
        expression="value * 3",
    )

    branch_dependency = tmp_path / "branch-dependency"
    _write_dependency_crate(
        branch_dependency,
        package_name="branch-dependency",
        feature="increment",
        expression="value + 1",
    )
    _initialize_git_repository(branch_dependency, "feature-branch")

    revision_dependency = tmp_path / "revision-dependency"
    _write_dependency_crate(
        revision_dependency,
        package_name="revision-dependency",
        feature="decrement",
        expression="value - 1",
    )
    revision = _initialize_git_repository(revision_dependency, "main")

    spec = ExtensionSpec(
        name="dependency_sources",
        source="""
use pyo3::prelude::*;

#[pyfunction]
fn combine(value: i64) -> i64 {
    path_dependency::transform(value)
        + branch_dependency::transform(value)
        + revision_dependency::transform(value)
}
""",
        dependencies={
            "branch-dependency": CargoDependency(
                git=branch_dependency.as_uri(),
                branch="feature-branch",
                features=("increment",),
            ),
            "path-dependency": CargoDependency(
                path=path_dependency,
                features=("triple",),
            ),
            "revision-dependency": CargoDependency(
                git=revision_dependency.as_uri(),
                rev=revision,
                features=("decrement",),
            ),
        },
    )

    result = build_extension(spec, cache_dir=tmp_path / "cache")
    module = load_extension(result)

    assert module.combine(4) == 20
