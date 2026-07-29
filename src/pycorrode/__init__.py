"""Build and load small PyO3 extension modules at runtime."""

from importlib.metadata import PackageNotFoundError, version

from .api import build_extension, compile_extension, load_extension
from .errors import (
    PyCorrodeBuildError,
    PyCorrodeConfigurationError,
    PyCorrodeError,
    PyCorrodeLoadError,
    PyCorrodeToolchainError,
)
from .models import BuildResult, CargoDependency, ExtensionSpec

try:
    __version__ = version("pycorrode")
except PackageNotFoundError:  # pragma: no cover - only an unpackaged source tree
    __version__ = "0.0.0"

__all__ = [
    "BuildResult",
    "CargoDependency",
    "ExtensionSpec",
    "PyCorrodeBuildError",
    "PyCorrodeConfigurationError",
    "PyCorrodeError",
    "PyCorrodeLoadError",
    "PyCorrodeToolchainError",
    "__version__",
    "build_extension",
    "compile_extension",
    "load_extension",
]
