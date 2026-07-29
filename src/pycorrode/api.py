"""Public build and loading operations."""

from __future__ import annotations

import os
import sys
from importlib import machinery, util
from types import ModuleType

from ._build.artifact import install_artifact
from ._build.cache import BuildCache
from ._build.cargo import build_cargo_project
from ._build.fingerprint import extension_fingerprint
from ._build.project import materialize_project
from ._build.toolchain import Toolchain
from .errors import PyCorrodeLoadError
from .models import BuildResult, ExtensionSpec


def build_extension(
    spec: ExtensionSpec,
    *,
    cache_dir: str | os.PathLike[str] | None = None,
    cargo: str | os.PathLike[str] | None = None,
    force: bool = False,
) -> BuildResult:
    """Build an extension, or return its validated cached artifact.

    Args:
        spec: Description of the extension source and Cargo dependencies.
        cache_dir: Override the platform-specific pycorrode cache directory.
        cargo: Path or command name for the Cargo executable.
        force: Discard the matching cache entry and rebuild it.
    """

    toolchain = Toolchain.discover(cargo)
    cache = BuildCache(cache_dir)
    fingerprint = extension_fingerprint(spec, toolchain)
    module_name = f"_pycorrode_{fingerprint[:16]}"
    entry = cache.entry(fingerprint)

    with entry.lock():
        if force:
            entry.reset()
        else:
            cached = entry.cached_result()
            if cached is not None:
                return cached

        project = materialize_project(entry.project_dir, spec, module_name)
        source_artifact, diagnostics = build_cargo_project(
            project=project,
            target_dir=entry.target_dir,
            module_name=module_name,
            release=spec.release,
            toolchain=toolchain,
        )
        artifact = install_artifact(
            source_artifact,
            entry.artifact_dir,
            module_name,
        )
        result = BuildResult(
            cache_key=fingerprint,
            module_name=module_name,
            artifact=artifact,
            cache_hit=False,
            diagnostics=diagnostics,
        )
        entry.mark_complete(result, spec, toolchain)
        return result


def load_extension(result: BuildResult) -> ModuleType:
    """Load a previously built extension into the current interpreter."""

    module_name = result.module_name
    artifact = result.artifact.resolve()

    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing

    if not artifact.is_file():
        raise PyCorrodeLoadError(
            f"Compiled extension artifact does not exist: {artifact}"
        )

    loader = machinery.ExtensionFileLoader(module_name, os.fspath(artifact))
    module_spec = util.spec_from_file_location(
        module_name,
        artifact,
        loader=loader,
    )
    if module_spec is None:
        raise PyCorrodeLoadError(
            f"Python could not create an import specification for {artifact}"
        )

    try:
        module = util.module_from_spec(module_spec)
        sys.modules[module_name] = module
        loader.exec_module(module)
    except Exception as error:
        sys.modules.pop(module_name, None)
        raise PyCorrodeLoadError(
            f"Could not load compiled extension {artifact}: {error}"
        ) from error

    return module


def compile_extension(
    spec: ExtensionSpec,
    *,
    cache_dir: str | os.PathLike[str] | None = None,
    cargo: str | os.PathLike[str] | None = None,
    force: bool = False,
) -> ModuleType:
    """Build and immediately load an extension."""

    result = build_extension(
        spec,
        cache_dir=cache_dir,
        cargo=cargo,
        force=force,
    )
    return load_extension(result)
