---
hide:
  - navigation
  - toc
---

<div class="pycorrode-hero" markdown>

<p class="pycorrode-kicker">Python ergonomics · Rust performance</p>

# Compile small Rust extensions when Python needs them

`pycorrode` turns Rust functions annotated with `#[pyfunction]` into an
importable Python module, then caches the native artifact for the next run.

[Get started](getting-started.md){ .md-button .md-button--primary }
[Explore the API](reference/api.md){ .md-button }

</div>

```python
from pycorrode import ExtensionSpec, compile_extension

extension = compile_extension(
    ExtensionSpec(
        name="double",
        source="""
use pyo3::prelude::*;

#[pyfunction]
fn double(value: i64) -> i64 {
    value * 2
}
""",
    )
)

assert extension.double(21) == 42
```

<div class="grid cards" markdown>

-   **Build on demand**

    ---

    Describe the extension in Python. `pycorrode` generates an isolated Cargo
    project and invokes the local Rust toolchain.

    [Compile your first extension](tutorials/first-extension.md)

-   **Reuse native artifacts**

    ---

    Cache keys account for source, dependencies, Python ABI, platform, and
    toolchain, so unchanged extensions load without rebuilding.

    [Understand caching](how-to/caching.md)

-   **Bring Cargo dependencies**

    ---

    Use crates.io versions, Git repositories, commit revisions, branches, local
    paths, feature flags, and default-feature controls.

    [Configure dependencies](how-to/dependencies.md)

-   **See Rust diagnostics**

    ---

    Toolchain, configuration, compiler, and loader failures use a focused
    exception hierarchy with Cargo diagnostics preserved.

    [Handle failures](how-to/error-handling.md)

</div>

!!! warning "Alpha software"

    `pycorrode` currently targets a deliberately narrow API: ordinary PyO3
    functions built for the active interpreter and host platform. Review the
    [current limitations](explanation/architecture.md#current-limitations)
    before adopting it in production.

## Where to go next

- Follow [Getting started](getting-started.md) for installation and the shortest
  route to a working extension.
- Use the [tutorials](tutorials/first-extension.md) to learn through complete,
  executable examples.
- Open the [how-to guides](how-to/dependencies.md) when you have a specific
  task to complete.
- Consult the [Python API reference](reference/api.md) for signatures and
  exceptions.
- Read the [architecture](explanation/architecture.md) to understand the build
  pipeline and cache design.
