"""Public exception hierarchy."""

from __future__ import annotations

from collections.abc import Sequence


class PyCorrodeError(Exception):
    """Base class for all expected pycorrode failures."""


class PyCorrodeConfigurationError(PyCorrodeError, ValueError):
    """An extension specification is invalid."""


class PyCorrodeToolchainError(PyCorrodeError):
    """Cargo or rustc is unavailable or could not be inspected."""


class PyCorrodeBuildError(PyCorrodeError):
    """Cargo failed to build a generated extension project.

    Attributes:
        diagnostics: Rendered compiler diagnostics and Cargo output.
        command: Command arguments used for the failed process.
        returncode: Process exit status, when one was available.
    """

    def __init__(
        self,
        message: str,
        *,
        diagnostics: str = "",
        command: Sequence[str] = (),
        returncode: int | None = None,
    ) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics
        self.command = tuple(command)
        self.returncode = returncode

    def __str__(self) -> str:
        message = super().__str__()
        if self.diagnostics:
            return f"{message}\n\n{self.diagnostics}"
        return message


class PyCorrodeLoadError(PyCorrodeError, ImportError):
    """A compiled extension could not be loaded by Python."""
