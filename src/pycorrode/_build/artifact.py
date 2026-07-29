"""Cargo output parsing and Python extension artifact installation."""

from __future__ import annotations

import json
import os
import shutil
import sysconfig
import uuid
from dataclasses import dataclass
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path

from ..errors import PyCorrodeBuildError

_NATIVE_SUFFIXES = {".dll", ".dylib", ".pyd", ".so"}


@dataclass(frozen=True, slots=True)
class CargoMessages:
    """Relevant information extracted from Cargo's JSON stream."""

    artifacts: tuple[Path, ...]
    diagnostics: str


def parse_cargo_messages(output: str, module_name: str) -> CargoMessages:
    """Extract the target cdylib and rendered compiler diagnostics."""

    artifacts: list[Path] = []
    diagnostics: list[str] = []

    for line in output.splitlines():
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            if line.strip():
                diagnostics.append(line)
            continue

        reason = message.get("reason")
        if reason == "compiler-message":
            rendered = message.get("message", {}).get("rendered")
            if rendered:
                diagnostics.append(rendered.rstrip())
            continue

        if reason != "compiler-artifact":
            continue
        target = message.get("target", {})
        crate_types = set(target.get("crate_types", ()))
        if target.get("name") != module_name or "cdylib" not in crate_types:
            continue
        for filename in message.get("filenames", ()):
            path = Path(filename)
            if path.suffix.lower() in _NATIVE_SUFFIXES:
                artifacts.append(path)

    return CargoMessages(
        artifacts=tuple(dict.fromkeys(artifacts)),
        diagnostics="\n".join(diagnostics).strip(),
    )


def python_extension_suffix() -> str:
    """Return the native-extension suffix for the active interpreter."""

    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    if isinstance(suffix, str) and suffix:
        return suffix
    if EXTENSION_SUFFIXES:
        return EXTENSION_SUFFIXES[0]
    raise PyCorrodeBuildError(
        "The current interpreter does not report a native extension suffix"
    )


def install_artifact(
    source: Path,
    artifact_dir: Path,
    module_name: str,
) -> Path:
    """Atomically copy and rename a Cargo cdylib for Python importing."""

    if not source.is_file():
        raise PyCorrodeBuildError(
            f"Cargo reported an artifact that does not exist: {source}"
        )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    destination = artifact_dir / f"{module_name}{python_extension_suffix()}"
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination
