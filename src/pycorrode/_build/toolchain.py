"""Discovery and inspection of the local Rust toolchain."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..errors import PyCorrodeToolchainError


@dataclass(frozen=True, slots=True)
class Toolchain:
    """Resolved Cargo and rustc executables and compatibility information."""

    cargo: str
    cargo_version: str
    rustc: str
    rustc_version: str
    target: str

    @classmethod
    def discover(
        cls,
        cargo: str | os.PathLike[str] | None = None,
    ) -> Toolchain:
        cargo_path = _resolve_executable(cargo or "cargo", "Cargo")
        rustc_path = _resolve_executable("rustc", "Rust compiler")
        cargo_version = _command_output([cargo_path, "--version"], "Cargo")
        verbose_rustc = _command_output([rustc_path, "-vV"], "Rust compiler")
        rustc_version = verbose_rustc.splitlines()[0]
        target = next(
            (
                line.partition(":")[2].strip()
                for line in verbose_rustc.splitlines()
                if line.startswith("host:")
            ),
            "",
        )
        if not target:
            raise PyCorrodeToolchainError(
                "rustc -vV did not report a host target"
            )
        return cls(
            cargo=cargo_path,
            cargo_version=cargo_version,
            rustc=rustc_path,
            rustc_version=rustc_version,
            target=target,
        )

    def canonical(self) -> dict[str, str]:
        return {
            "cargo": self.cargo,
            "cargo_version": self.cargo_version,
            "rustc": self.rustc,
            "rustc_version": self.rustc_version,
            "target": self.target,
        }


def _resolve_executable(
    command: str | os.PathLike[str],
    description: str,
) -> str:
    value = os.fspath(command)
    if Path(value).parent != Path("."):
        path = Path(value).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            # rustup dispatches through argv[0], so resolving the cargo/rustc
            # proxy symlink would change which tool it executes.
            return os.path.abspath(path)
        raise PyCorrodeToolchainError(
            f"{description} executable does not exist or is not executable: {path}"
        )

    resolved = shutil.which(value)
    if resolved is None:
        raise PyCorrodeToolchainError(
            f"{description} executable {value!r} was not found on PATH"
        )
    return os.path.abspath(resolved)


def _command_output(command: list[str], description: str) -> str:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise PyCorrodeToolchainError(
            f"Could not execute {description}: {error}"
        ) from error
    output = "\n".join(
        value.strip()
        for value in (completed.stdout, completed.stderr)
        if value.strip()
    )
    if completed.returncode != 0:
        raise PyCorrodeToolchainError(
            f"{description} inspection failed with exit code "
            f"{completed.returncode}: {output}"
        )
    return output
