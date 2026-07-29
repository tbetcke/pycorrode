"""Cargo subprocess integration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ..errors import PyCorrodeBuildError
from .artifact import parse_cargo_messages
from .project import GeneratedProject
from .toolchain import Toolchain


def build_cargo_project(
    *,
    project: GeneratedProject,
    target_dir: Path,
    module_name: str,
    release: bool,
    toolchain: Toolchain,
) -> tuple[Path, str]:
    """Build one generated project and return its Cargo cdylib artifact."""

    target_dir.mkdir(parents=True, exist_ok=True)
    command = [
        toolchain.cargo,
        "build",
        "--manifest-path",
        os.fspath(project.manifest),
        "--lib",
        "--message-format=json-render-diagnostics",
    ]
    if release:
        command.append("--release")
    if project.lockfile.is_file():
        command.append("--locked")

    environment = os.environ.copy()
    environment.update(
        {
            "CARGO_TARGET_DIR": os.fspath(target_dir.resolve()),
            "CARGO_TERM_COLOR": "never",
            "PYO3_BUILD_EXTENSION_MODULE": "1",
            "PYO3_PYTHON": sys.executable,
        }
    )

    try:
        completed = subprocess.run(
            command,
            cwd=project.root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise PyCorrodeBuildError(
            f"Could not execute Cargo: {error}",
            command=command,
        ) from error

    messages = parse_cargo_messages(completed.stdout, module_name)
    diagnostics = _combine_diagnostics(messages.diagnostics, completed.stderr)
    if completed.returncode != 0:
        raise PyCorrodeBuildError(
            f"Cargo failed to build extension {module_name!r}",
            diagnostics=diagnostics,
            command=command,
            returncode=completed.returncode,
        )
    if not messages.artifacts:
        raise PyCorrodeBuildError(
            f"Cargo completed without reporting a cdylib for {module_name!r}",
            diagnostics=diagnostics,
            command=command,
            returncode=completed.returncode,
        )

    existing = [path for path in messages.artifacts if path.is_file()]
    if not existing:
        reported = "\n".join(os.fspath(path) for path in messages.artifacts)
        raise PyCorrodeBuildError(
            "Cargo reported cdylib artifacts, but none exist",
            diagnostics=_combine_diagnostics(diagnostics, reported),
            command=command,
            returncode=completed.returncode,
        )
    return existing[0], diagnostics


def _combine_diagnostics(*values: str) -> str:
    return "\n".join(value.strip() for value in values if value.strip())
