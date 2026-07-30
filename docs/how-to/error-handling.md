# Handle errors

Catch `PyCorrodeError` to handle every expected library failure, or catch a
specific subclass when recovery differs by stage.

## Catch build failures

```python
from pycorrode import PyCorrodeBuildError, compile_extension

try:
    module = compile_extension(spec)
except PyCorrodeBuildError as error:
    print(error.diagnostics)
```

`PyCorrodeBuildError` preserves:

- `diagnostics`: rendered compiler messages and Cargo output;
- `command`: the command that failed;
- `returncode`: the process exit status, when available.

Converting the exception to a string includes diagnostics after its main
message.

## Distinguish failure stages

```python
from pycorrode import (
    PyCorrodeBuildError,
    PyCorrodeConfigurationError,
    PyCorrodeLoadError,
    PyCorrodeToolchainError,
)

try:
    module = compile_extension(spec)
except PyCorrodeConfigurationError as error:
    print(f"Invalid extension specification: {error}")
except PyCorrodeToolchainError as error:
    print(f"Rust toolchain unavailable: {error}")
except PyCorrodeBuildError as error:
    print(error.diagnostics)
except PyCorrodeLoadError as error:
    print(f"Native module could not be loaded: {error}")
```

## Let failures propagate in development

During development, an uncaught `PyCorrodeBuildError` is often the most useful
behavior: its string representation includes the Rust diagnostic context.
Catch it when an application can add context, choose a fallback, or present the
failure more clearly.

See [Troubleshooting](troubleshooting.md) for common causes.
