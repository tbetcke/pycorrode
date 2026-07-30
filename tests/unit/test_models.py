from __future__ import annotations

from pathlib import Path

import pytest

from pycorrode import (
    CargoDependency,
    ExtensionSpec,
    PyCorrodeConfigurationError,
)


def test_discovers_pyfunction_exports() -> None:
    spec = ExtensionSpec(
        name="example",
        source="""
#[pyo3::pyfunction]
fn first() {}

#[pyfunction(name = "renamed")]
pub(crate) async fn second() {}
""",
    )

    assert spec.exports == ("first", "second")


def test_normalizes_dependencies_and_features() -> None:
    spec = ExtensionSpec(
        name="example",
        source="#[pyfunction]\nfn exported() {}",
        dependencies={
            "z-crate": "1",
            "a-crate": CargoDependency(
                version=" 2 ",
                features=(" derive ", "derive"),
                default_features=False,
            ),
        },
    )

    assert list(spec.dependencies) == ["a-crate", "z-crate"]
    assert spec.dependencies["a-crate"] == CargoDependency(
        version="2",
        features=("derive",),
        default_features=False,
    )
    assert CargoDependency("2", ("derive",), False) == spec.dependencies[
        "a-crate"
    ]


def test_normalizes_git_and_relative_path_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    git_dependency = CargoDependency(
        git=" https://example.com/example/repository.git ",
        branch=" feature-branch ",
        features=("serde",),
    )
    revision_dependency = CargoDependency(
        git="https://example.com/example/repository.git",
        rev=" 0123456789abcdef0123456789abcdef01234567 ",
    )
    path_dependency = CargoDependency(
        path="crates/local-dependency",
        features=("fast",),
    )

    assert git_dependency.git == "https://example.com/example/repository.git"
    assert git_dependency.canonical() == {
        "default_features": True,
        "features": ["serde"],
        "git": "https://example.com/example/repository.git",
        "branch": "feature-branch",
    }
    assert revision_dependency.canonical() == {
        "default_features": True,
        "features": [],
        "git": "https://example.com/example/repository.git",
        "rev": "0123456789abcdef0123456789abcdef01234567",
    }
    assert path_dependency.path == str(
        (tmp_path / "crates/local-dependency").resolve()
    )
    assert path_dependency.canonical() == {
        "default_features": True,
        "features": ["fast"],
        "path": str((tmp_path / "crates/local-dependency").resolve()),
    }


@pytest.mark.parametrize(
    "dependency",
    [
        {},
        {"version": "1", "git": "https://example.com/repository.git"},
        {"version": "1", "path": "local-dependency"},
        {"git": "https://example.com/repository.git", "path": "local-dependency"},
    ],
)
def test_requires_exactly_one_dependency_source(
    dependency: dict[str, str],
) -> None:
    with pytest.raises(PyCorrodeConfigurationError, match="exactly one"):
        CargoDependency(**dependency)


@pytest.mark.parametrize(
    ("dependency", "message"),
    [
        ({"version": "1", "branch": "main"}, "require a Git source"),
        ({"path": "local-dependency", "rev": "abc1234"}, "require a Git source"),
        (
            {
                "git": "https://example.com/repository.git",
                "branch": "main",
                "rev": "abc1234",
            },
            "mutually exclusive",
        ),
    ],
)
def test_rejects_invalid_git_selectors(
    dependency: dict[str, str],
    message: str,
) -> None:
    with pytest.raises(PyCorrodeConfigurationError, match=message):
        CargoDependency(**dependency)


@pytest.mark.parametrize(
    "dependency",
    [
        {"version": ""},
        {"git": " "},
        {"path": ""},
        {"git": "https://example.com/repository.git", "branch": ""},
        {"git": "https://example.com/repository.git", "rev": " "},
    ],
)
def test_rejects_empty_dependency_sources(
    dependency: dict[str, str],
) -> None:
    with pytest.raises(PyCorrodeConfigurationError, match="cannot be empty"):
        CargoDependency(**dependency)


@pytest.mark.parametrize("name", ["has-dash", "1starts_with_number", ""])
def test_rejects_invalid_module_names(name: str) -> None:
    with pytest.raises(PyCorrodeConfigurationError):
        ExtensionSpec(
            name=name,
            source="#[pyfunction]\nfn exported() {}",
        )


def test_requires_discoverable_or_explicit_exports() -> None:
    with pytest.raises(PyCorrodeConfigurationError, match="No #"):
        ExtensionSpec(name="example", source="fn private() {}")

    spec = ExtensionSpec(
        name="example",
        source="fn registered_manually() {}",
        exports=("registered_manually",),
    )
    assert spec.exports == ("registered_manually",)


def test_rejects_managed_pyo3_dependencies() -> None:
    with pytest.raises(PyCorrodeConfigurationError, match="managed"):
        ExtensionSpec(
            name="example",
            source="#[pyfunction]\nfn exported() {}",
            dependencies={"pyo3": "0.29"},
        )
