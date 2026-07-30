"""Value objects used by the public API."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import KW_ONLY, dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import cast

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
    """A Cargo dependency for a generated project."""

    version: str | None = None
    features: tuple[str, ...] = ()
    default_features: bool = True
    _: KW_ONLY
    git: str | None = None
    path: str | Path | None = None
    branch: str | None = None
    rev: str | None = None

    def __post_init__(self) -> None:
        sources = {
            "version": self.version,
            "git": self.git,
            "path": self.path,
        }
        selected_sources = [
            name for name, value in sources.items() if value is not None
        ]
        if len(selected_sources) != 1:
            raise PyCorrodeConfigurationError(
                "Cargo dependencies must specify exactly one of version, git, or path"
            )

        if self.version is not None:
            if not isinstance(self.version, str) or not self.version.strip():
                raise PyCorrodeConfigurationError(
                    "Cargo dependency versions cannot be empty"
                )
            object.__setattr__(self, "version", self.version.strip())

        if self.git is not None:
            if not isinstance(self.git, str) or not self.git.strip():
                raise PyCorrodeConfigurationError(
                    "Cargo dependency Git URLs cannot be empty"
                )
            object.__setattr__(self, "git", self.git.strip())

        if self.path is not None:
            if isinstance(self.path, str) and not self.path.strip():
                raise PyCorrodeConfigurationError(
                    "Cargo dependency paths cannot be empty"
                )
            try:
                path = Path(self.path).expanduser().resolve()
            except (OSError, RuntimeError, TypeError) as error:
                raise PyCorrodeConfigurationError(
                    f"Invalid Cargo dependency path: {self.path!r}"
                ) from error
            object.__setattr__(self, "path", str(path))

        selectors = [
            name
            for name, value in (("branch", self.branch), ("rev", self.rev))
            if value is not None
        ]
        if selectors and self.git is None:
            raise PyCorrodeConfigurationError(
                "Cargo dependency branch and rev selectors require a Git source"
            )
        if len(selectors) > 1:
            raise PyCorrodeConfigurationError(
                "Cargo dependency branch and rev selectors are mutually exclusive"
            )

        if self.branch is not None:
            if not isinstance(self.branch, str) or not self.branch.strip():
                raise PyCorrodeConfigurationError(
                    "Cargo dependency Git branches cannot be empty"
                )
            object.__setattr__(self, "branch", self.branch.strip())

        if self.rev is not None:
            if not isinstance(self.rev, str) or not self.rev.strip():
                raise PyCorrodeConfigurationError(
                    "Cargo dependency Git revisions cannot be empty"
                )
            object.__setattr__(self, "rev", self.rev.strip())

        features: list[str] = []
        for feature in self.features:
            if not isinstance(feature, str) or not feature.strip():
                raise PyCorrodeConfigurationError(
                    "Cargo dependency feature names cannot be empty"
                )
            features.append(feature.strip())
        normalized_features = tuple(sorted(set(features)))
        object.__setattr__(self, "features", normalized_features)

    def canonical(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""

        result: dict[str, object] = {
            "default_features": self.default_features,
            "features": list(self.features),
        }
        if self.version is not None:
            result["version"] = self.version
        elif self.git is not None:
            result["git"] = self.git
            if self.branch is not None:
                result["branch"] = self.branch
            elif self.rev is not None:
                result["rev"] = self.rev
        else:
            result["path"] = self.path
        return result


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

        dependencies = cast(
            Mapping[str, CargoDependency],
            self.dependencies,
        )
        return {
            "dependencies": {
                name: dependency.canonical()
                for name, dependency in dependencies.items()
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
