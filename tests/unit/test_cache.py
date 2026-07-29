from __future__ import annotations

from pathlib import Path

from pycorrode import BuildResult, ExtensionSpec
from pycorrode._build.cache import BuildCache
from pycorrode._build.toolchain import Toolchain


def test_completed_cache_entry_round_trips(tmp_path: Path) -> None:
    cache = BuildCache(tmp_path)
    entry = cache.entry("abc123")
    entry.artifact_dir.mkdir(parents=True)
    artifact = entry.artifact_dir / "example.so"
    artifact.write_bytes(b"native")
    result = BuildResult(
        cache_key="abc123",
        module_name="_pycorrode_abc123",
        artifact=artifact,
        cache_hit=False,
        diagnostics="warning",
    )
    spec = ExtensionSpec(
        name="example",
        source="#[pyfunction]\nfn exported() {}",
    )
    toolchain = Toolchain(
        cargo="/cargo",
        cargo_version="cargo 1.0",
        rustc="/rustc",
        rustc_version="rustc 1.0",
        target="test-target",
    )

    entry.mark_complete(result, spec, toolchain)

    cached = entry.cached_result()
    assert cached is not None
    assert cached.cache_hit
    assert cached.artifact == artifact
    assert cached.diagnostics == "warning"


def test_incomplete_cache_entry_is_ignored(tmp_path: Path) -> None:
    entry = BuildCache(tmp_path).entry("abc123")
    entry.root.mkdir(parents=True)

    assert entry.cached_result() is None
