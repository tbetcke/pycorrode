# Security model

`pycorrode` compiles and loads native code into the current Python process. Its
trust boundary is therefore the same as running a local compiler and importing
a native extension directly.

## What executes code

Treat all of the following as executable input:

- Rust source supplied to `ExtensionSpec`;
- crates.io packages and Git or path dependencies;
- dependency build scripts and procedural macros;
- the resulting native extension.

Each component runs with the permissions of the current user. Rust's memory
safety guarantees do not make untrusted build scripts or unsafe/native code
safe to execute.

## Safe operating practices

- Compile only source and dependency declarations you trust.
- Pin Git dependencies with `rev` when reproducibility matters.
- Review dependency features because they can enable additional code and build
  behavior.
- Use normal Cargo supply-chain controls and registry policies.
- Keep build caches user-private and avoid loading artifacts copied from an
  untrusted machine.
- Run untrusted experiments inside an operating-system sandbox or disposable
  environment rather than relying on `pycorrode` for isolation.

## Cache integrity

Completed cache entries are validated structurally before use, and project and
metadata files are replaced atomically. These measures protect consistency
against interrupted builds; they do not provide cryptographic provenance or
defend against a user who can modify the cache.

## Application deployment

Runtime compilation requires Cargo, rustc, dependency sources, and a native
build environment on the target machine. For locked-down production systems,
building and distributing a conventional wheel may be a better fit than
compiling code during application startup.
