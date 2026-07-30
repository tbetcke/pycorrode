# Architecture

`pycorrode` is split into a public Python API and an internal runtime build
pipeline. The installed package does not contain a native extension.

## Build pipeline

1. `ExtensionSpec` validates the requested module, dependencies, and exports.
2. `Toolchain` locates and fingerprints Cargo and rustc.
3. `extension_fingerprint` hashes the source, build settings, Python ABI,
   platform, and Rust toolchain.
4. `BuildCache` acquires a lock for the content-addressed entry.
5. `materialize_project` writes an isolated Cargo package from bundled
   templates.
6. Cargo builds a `cdylib` with machine-readable JSON diagnostics.
7. The reported native artifact is copied to a filename using Python's active
   extension suffix.
8. A completion record makes the cache entry visible to later callers.
9. `ExtensionFileLoader` imports the fingerprint-named module.

Generated projects use the `PYO3_BUILD_EXTENSION_MODULE` environment variable
and set `PYO3_PYTHON` to the current interpreter. Their `build.rs` delegates
platform-specific extension-module linker arguments to `pyo3-build-config`.

## Module naming

The native module name is `_pycorrode_` followed by the first sixteen
characters of the extension fingerprint. This same value is used for:

- Cargo's library target
- the PyO3 module name and exported `PyInit_*` symbol
- the installed native-library filename
- Python's extension loader

The user-provided friendly name participates in the fingerprint but is not used
as the native symbol. Native modules are process-global and are not reliably
unloaded, so immutable content-addressed names prevent a rebuilt module from
silently resolving to an older binary already present in `sys.modules`.

## Cache consistency

An entry is usable only when its `build.json` exists, has the expected schema
and cache key, and names an existing artifact. Project and metadata files are
written with same-filesystem atomic replacements. Builds for the same key are
serialized with a file lock.

Incomplete projects and Cargo target directories are retained so an interrupted
or failed build can reuse Cargo's incremental work. `force=True` removes the
entry while holding its external lock.

## Current limitations

- Git dependency tag selectors are not yet exposed.
- Mutable Git and local path dependency contents require `force=True` to
  invalidate an existing completed cache entry.
- Automatic export discovery targets ordinary `#[pyfunction]` declarations.
- PyO3 classes and manually assembled modules require future registration APIs.
- Builds target the current interpreter and host platform; cross-compilation
  and `abi3` are not yet exposed.
- Compiled code and dependency build scripts are trusted native code.
