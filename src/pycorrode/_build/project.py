"""Generation of isolated Cargo projects."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from ..models import CargoDependency, ExtensionSpec


@dataclass(frozen=True, slots=True)
class GeneratedProject:
    """Important paths in a generated Cargo package."""

    root: Path
    manifest: Path
    lockfile: Path


def materialize_project(
    root: Path,
    spec: ExtensionSpec,
    module_name: str,
) -> GeneratedProject:
    """Write the generated Cargo project without touching unchanged files."""

    source_dir = root / "src"
    source_dir.mkdir(parents=True, exist_ok=True)

    templates = files("pycorrode._templates")
    manifest_template = templates.joinpath("Cargo.toml.tmpl").read_text(
        encoding="utf-8"
    )
    lib_template = templates.joinpath("lib.rs.tmpl").read_text(encoding="utf-8")
    build_script = templates.joinpath("build.rs").read_text(encoding="utf-8")

    manifest = (
        manifest_template.replace("__MODULE_NAME__", module_name)
        .replace("__PYO3_VERSION__", spec.pyo3_version)
        .replace("__DEPENDENCIES__", _render_dependencies(spec))
    )
    registrations = "\n".join(
        _registration(export) for export in spec.exports or ()
    )
    library = (
        lib_template.replace("__MODULE_NAME__", module_name)
        .replace("__REGISTRATIONS__", registrations)
    )
    user_source = spec.source
    if not user_source.endswith("\n"):
        user_source += "\n"

    _write_if_changed(root / "Cargo.toml", manifest)
    _write_if_changed(root / "build.rs", build_script)
    _write_if_changed(source_dir / "lib.rs", library)
    _write_if_changed(source_dir / "user_code.rs", user_source)

    return GeneratedProject(
        root=root,
        manifest=root / "Cargo.toml",
        lockfile=root / "Cargo.lock",
    )


def _render_dependencies(spec: ExtensionSpec) -> str:
    return "\n".join(
        f"{name} = {_dependency_value(dependency)}"
        for name, dependency in spec.dependencies.items()
    )


def _dependency_value(dependency: CargoDependency) -> str:
    if (
        dependency.version is not None
        and dependency.default_features
        and not dependency.features
    ):
        return json.dumps(dependency.version)

    if dependency.version is not None:
        fields = [f"version = {json.dumps(dependency.version)}"]
    elif dependency.git is not None:
        fields = [f"git = {json.dumps(dependency.git)}"]
    else:
        assert dependency.path is not None
        fields = [f"path = {json.dumps(dependency.path)}"]
    if not dependency.default_features:
        fields.append("default-features = false")
    if dependency.features:
        features = ", ".join(json.dumps(feature) for feature in dependency.features)
        fields.append(f"features = [{features}]")
    return "{ " + ", ".join(fields) + " }"


def _registration(export: str) -> str:
    return (
        "    pyo3::types::PyModuleMethods::add_function(\n"
        "        m,\n"
        f"        pyo3::wrap_pyfunction!({export}, m)?,\n"
        "    )?;"
    )


def _write_if_changed(path: Path, content: str) -> None:
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
