# Configure Cargo dependencies

Pass dependency declarations through `ExtensionSpec.dependencies`. The mapping
key is the Cargo dependency name; its value is either a version string or a
`CargoDependency`.

## Use a crates.io version

The compact form accepts a version requirement:

```python
spec = ExtensionSpec(
    name="uses_regex",
    source=rust_source,
    dependencies={"regex": "1"},
)
```

Use `CargoDependency` when you need features or default-feature control:

```python
dependencies={
    "serde": CargoDependency(
        version="1",
        features=("derive",),
        default_features=False,
    )
}
```

## Use a Git repository

Track the repository's default branch:

```python
dependencies={
    "remote-crate": CargoDependency(
        git="https://github.com/owner/remote-crate.git",
        features=("fast",),
    )
}
```

Select a branch:

```python
dependencies={
    "remote-crate": CargoDependency(
        git="https://github.com/owner/remote-crate.git",
        branch="main",
        features=("fast",),
    )
}
```

Pin a commit using Cargo's `rev` field:

```python
dependencies={
    "remote-crate": CargoDependency(
        git="https://github.com/owner/remote-crate.git",
        rev="0123456789abcdef0123456789abcdef01234567",
        features=("fast",),
    )
}
```

`branch` and `rev` are mutually exclusive. Both require `git`.

!!! tip "Prefer immutable revisions for reproducibility"

    A branch can move without changing the extension specification. Pin a
    commit when builds must resolve the same source over time.

## Use a local path

```python
dependencies={
    "local-crate": CargoDependency(
        path="../local-crate",
        features=("simd",),
    )
}
```

Relative paths are resolved against the current working directory when the
`CargoDependency` is created. The resulting absolute path is written into the
generated project because that project lives inside the pycorrode cache.

Both strings and `pathlib.Path` values are accepted:

```python
from pathlib import Path

dependency = CargoDependency(path=Path("crates/local-crate"))
```

## Choose exactly one source

Every `CargoDependency` requires exactly one of:

- `version`
- `git`
- `path`

Feature flags and `default_features` work with every source type.

## Rebuild mutable dependencies

The cache fingerprints dependency declarations, not the content behind a local
path or moving Git branch. After the dependency changes, force a rebuild:

```python
module = compile_extension(spec, force=True)
```

See [Caching and rebuilds](caching.md) for the full cache model.
