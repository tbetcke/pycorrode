"""Value objects used by the public API."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from .errors import PyCorrodeConfigurationError

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DEPENDENCY_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
_PYFUNCTION = re.compile(
    r"""
    \#\s*\[\s*(?:pyo3::)?pyfunction(?:\s*\([^\]]*\))?\s*\]
    (?:\s*\#\s*\[[^\]]+\])*
    \s*
    (?:pub(?:\s*\([^)]*\))?\s+)?
    (?:async\s+)?
    (?:unsafe\s+)?
    fn\s+(?:r\#)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)


@dataclass(frozen=True, slots=True)
class CargoDependency:
    """A crates.io dependency for a generated Cargo project."""

    version: str
    features: tuple[str, ...] = ()
    default_features: bool = True

    def __post_init__(self) -> None:
        version = self.version.strip()
        if not version:
            raise PyCorrodeConfigurationError(
                "Cargo dependency versions cannot be empty"
            )
        features = tuple(sorted(set(self.features)))
        if any(not feature.strip() for feature in features):
            raise PyCorrodeConfigurationError(
                "Cargo dependency feature names cannot be empty"
            )
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "features", features)

    def canonical(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""

        return {
            "default_features": self.default_features,
            "features": list(self.features),
            "version": self.version,
        }


DependencyInput = str | CargoDependency


@dataclass(frozen=True, slots=True)
class ExtensionSpec:
    """Description of a generated PyO3 extension module."""

    name: str
    source: str
    dependencies: Mapping[str, DependencyInput] = field(default_factory=dict)
    exports: tuple[str, ...] | None = None
    release: bool = True
    pyo3_version: str = "0.29.0"

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.name):
            raise PyCorrodeConfigurationError(
                f"Extension name must be a Python identifier, got {self.name!r}"
            )
        if not self.source.strip():
            raise PyCorrodeConfigurationError("Rust source cannot be empty")

        pyo3_version = self.pyo3_version.removeprefix("=").strip()
        if not pyo3_version:
            raise PyCorrodeConfigurationError("PyO3 version cannot be empty")
        object.__setattr__(self, "pyo3_version", pyo3_version)

        dependencies: dict[str, CargoDependency] = {}
        for name, value in self.dependencies.items():
            if not _DEPENDENCY_NAME.fullmatch(name):
                raise PyCorrodeConfigurationError(
                    f"Invalid Cargo dependency name: {name!r}"
                )
            if name in {"pyo3", "pyo3-build-config"}:
                raise PyCorrodeConfigurationError(
                    f"{name!r} is managed by pycorrode and cannot be overridden"
                )
            dependency = (
                CargoDependency(value) if isinstance(value, str) else value
            )
            if not isinstance(dependency, CargoDependency):
                raise PyCorrodeConfigurationError(
                    f"Dependency {name!r} must be a version string or "
                    "CargoDependency"
                )
            dependencies[name] = dependency
        object.__setattr__(
            self,
            "dependencies",
            MappingProxyType(dict(sorted(dependencies.items()))),
        )

        exports = (
            discover_pyfunctions(self.source)
            if self.exports is None
            else tuple(self.exports)
        )
        if not exports:
            raise PyCorrodeConfigurationError(
                "No #[pyfunction] functions were discovered; pass exports=(...) "
                "when the functions cannot be detected automatically"
            )
        if len(set(exports)) != len(exports):
            raise PyCorrodeConfigurationError("Export names must be unique")
        for export in exports:
            if not _IDENTIFIER.fullmatch(export):
                raise PyCorrodeConfigurationError(
                    f"Export names must be Rust identifiers, got {export!r}"
                )
        object.__setattr__(self, "exports", exports)

    def canonical(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""

        return {
            "dependencies": {
                name: dependency.canonical()
                for name, dependency in self.dependencies.items()
            },
            "exports": list(self.exports or ()),
            "name": self.name,
            "pyo3_version": self.pyo3_version,
            "release": self.release,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class BuildResult:
    """The output of a successful extension build."""

    cache_key: str
    module_name: str
    artifact: Path
    cache_hit: bool
    diagnostics: str = ""


def discover_pyfunctions(source: str) -> tuple[str, ...]:
    """Discover ordinary Rust functions annotated with ``#[pyfunction]``."""

    return tuple(match.group("name") for match in _PYFUNCTION.finditer(source))
