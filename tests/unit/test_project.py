from __future__ import annotations

import json
from pathlib import Path

from pycorrode import CargoDependency, ExtensionSpec
from pycorrode._build.project import materialize_project


def test_materializes_generated_project(tmp_path: Path) -> None:
    local_dependency = tmp_path / "local-dependency"
    spec = ExtensionSpec(
        name="double",
        source="#[pyfunction]\nfn double(value: i64) -> i64 { value * 2 }",
        dependencies={
            "git-dependency": CargoDependency(
                git="https://example.com/dependency.git",
                features=("serde",),
            ),
            "local-dependency": CargoDependency(
                path=local_dependency,
                features=("fast",),
                default_features=False,
            ),
            "regex": "1",
            "serde": CargoDependency(
                version="1",
                features=("derive",),
                default_features=False,
            )
        },
    )

    project = materialize_project(tmp_path, spec, "_pycorrode_deadbeef")

    manifest = project.manifest.read_text()
    library = (tmp_path / "src/lib.rs").read_text()
    user_source = (tmp_path / "src/user_code.rs").read_text()

    assert 'name = "_pycorrode_deadbeef"' in manifest
    assert 'pyo3 = { version = "=0.29.0"' in manifest
    assert (
        'serde = { version = "1", default-features = false, '
        'features = ["derive"] }'
    ) in manifest
    assert (
        'git-dependency = { git = "https://example.com/dependency.git", '
        'features = ["serde"] }'
    ) in manifest
    assert (
        f"local-dependency = {{ path = {json.dumps(str(local_dependency))}, "
        'default-features = false, features = ["fast"] }'
    ) in manifest
    assert 'regex = "1"' in manifest
    assert "#[pyo3(name = \"_pycorrode_deadbeef\")]" in library
    assert "pyo3::wrap_pyfunction!(double, m)?" in library
    assert user_source.endswith("\n")


def test_does_not_rewrite_unchanged_project_files(tmp_path: Path) -> None:
    spec = ExtensionSpec(
        name="example",
        source="#[pyfunction]\nfn exported() {}",
    )
    materialize_project(tmp_path, spec, "_pycorrode_deadbeef")
    manifest = tmp_path / "Cargo.toml"
    original_mtime = manifest.stat().st_mtime_ns

    materialize_project(tmp_path, spec, "_pycorrode_deadbeef")

    assert manifest.stat().st_mtime_ns == original_mtime
