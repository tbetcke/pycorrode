"""Runtime cache layout and completion metadata."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from filelock import FileLock
from platformdirs import user_cache_path

from ..models import BuildResult, ExtensionSpec
from .toolchain import Toolchain

_CACHE_SCHEMA = 1


def default_cache_dir() -> Path:
    """Return the configured or platform-specific cache root."""

    configured = os.environ.get("PYCORRODE_CACHE_DIR")
    if configured:
        return Path(configured).expanduser()
    return user_cache_path("pycorrode")


class BuildCache:
    """Own the versioned pycorrode cache namespace."""

    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        base = Path(root).expanduser() if root is not None else default_cache_dir()
        self.root = base / f"v{_CACHE_SCHEMA}"

    def entry(self, cache_key: str) -> CacheEntry:
        return CacheEntry(self.root, cache_key)


class CacheEntry:
    """Paths and operations for one content-addressed build."""

    def __init__(self, cache_root: Path, cache_key: str) -> None:
        self.cache_key = cache_key
        self.root = cache_root / "modules" / cache_key
        self.project_dir = self.root / "project"
        self.target_dir = self.root / "target"
        self.artifact_dir = self.root / "artifact"
        self.metadata_path = self.root / "build.json"
        self.lock_path = cache_root / "locks" / f"{cache_key}.lock"

    def lock(self) -> AbstractContextManager[FileLock]:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        return FileLock(self.lock_path)

    def cached_result(self) -> BuildResult | None:
        try:
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            if metadata.get("schema") != _CACHE_SCHEMA:
                return None
            if metadata.get("cache_key") != self.cache_key:
                return None
            artifact = self.artifact_dir / metadata["artifact"]
            if not artifact.is_file():
                return None
            return BuildResult(
                cache_key=self.cache_key,
                module_name=metadata["module_name"],
                artifact=artifact,
                cache_hit=True,
                diagnostics=metadata.get("diagnostics", ""),
            )
        except (KeyError, OSError, TypeError, ValueError):
            return None

    def reset(self) -> None:
        if self.root.exists():
            shutil.rmtree(self.root)

    def mark_complete(
        self,
        result: BuildResult,
        spec: ExtensionSpec,
        toolchain: Toolchain,
    ) -> None:
        metadata: dict[str, Any] = {
            "artifact": result.artifact.name,
            "built_at": datetime.now(UTC).isoformat(),
            "cache_key": self.cache_key,
            "diagnostics": result.diagnostics,
            "module_name": result.module_name,
            "schema": _CACHE_SCHEMA,
            "spec_name": spec.name,
            "toolchain": toolchain.canonical(),
        }
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.metadata_path.with_name(
            f".{self.metadata_path.name}.{uuid.uuid4().hex}.tmp"
        )
        try:
            temporary.write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, self.metadata_path)
        finally:
            temporary.unlink(missing_ok=True)
