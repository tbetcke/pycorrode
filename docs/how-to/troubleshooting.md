# Troubleshooting

## Cargo or rustc cannot be found

Confirm both tools are on the same `PATH` used to start Python:

```bash
cargo --version
rustc --version
```

You can also pass a Cargo executable explicitly:

```python
module = compile_extension(spec, cargo="/path/to/cargo")
```

## No `#[pyfunction]` functions were discovered

Automatic discovery targets ordinary annotated function declarations. For
macro-generated code or unusual formatting, list the Rust names explicitly:

```python
spec = ExtensionSpec(
    name="custom",
    source=rust_source,
    exports=("first_function", "second_function"),
)
```

## Cargo cannot download a crate

The first build needs access to crates.io and any configured Git hosts unless
the sources already exist in Cargo's cache. Check proxy, registry, certificate,
and Git authentication settings in the environment that launched Python.

## A local or branch dependency changed but behavior did not

The cache key contains the declaration, not mutable external content. Rebuild
the matching entry:

```python
module = compile_extension(spec, force=True)
```

## A NumPy argument is rejected

Match the dtype expected by the Rust signature. For the included example:

```python
values = np.asarray(values, dtype=np.float64)
```

Array dimensionality and mutability also need to match the PyO3/numpy wrapper
type used by the Rust function.

## A native artifact cannot be loaded

Loading can fail when the artifact is missing, damaged, or incompatible with
the active Python interpreter. Confirm you are using the interpreter that
built the extension, then force a rebuild. If the error persists, inspect the
`PyCorrodeLoadError` message and the build diagnostics.

## Integration tests cannot use the Rust registry

Skip integration tests explicitly in restricted environments:

```bash
PYCORRODE_SKIP_INTEGRATION=1 pytest
```

Unit tests continue to cover validation, cache metadata, project generation,
and diagnostic parsing.
