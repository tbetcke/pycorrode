# Control caching and rebuilds

`pycorrode` stores generated Cargo projects and native artifacts in a
content-addressed cache.

## Use the default cache

No configuration is required:

```python
module = compile_extension(spec)
```

The default directory follows the operating system's user-cache convention.

## Override the cache globally

Set `PYCORRODE_CACHE_DIR` before running Python:

```bash
export PYCORRODE_CACHE_DIR=/path/to/pycorrode-cache
python application.py
```

## Override the cache for one operation

```python
module = compile_extension(
    spec,
    cache_dir="/path/to/application-cache",
)
```

The same option is accepted by `build_extension`.

## Force a rebuild

```python
module = compile_extension(spec, force=True)
```

Use `force=True` when:

- a local path dependency changed without changing its path;
- a Git branch points at a newer commit;
- you need to replace an incomplete or suspect cached build.

The matching cache entry is reset while its external lock is held, preventing
another process from observing a partial reset.

## Build and load separately

Use separate operations when you need artifact metadata or want to control when
native code is loaded:

```python
from pycorrode import build_extension, load_extension

result = build_extension(spec)

print(result.artifact)
print(result.cache_key)
print(result.cache_hit)
print(result.diagnostics)

module = load_extension(result)
```

`BuildResult.cache_hit` reports whether that build call reused a completed
entry.

## Understand cache identity

The fingerprint includes:

- Rust source and exported function names;
- Cargo dependency declarations and the PyO3 version;
- Python implementation, version, ABI, and extension suffix;
- operating system and architecture;
- Cargo and rustc versions and the Rust target;
- release/debug profile and generated-project schema version.

See [Architecture](../explanation/architecture.md#cache-consistency) for the
internal consistency rules.
