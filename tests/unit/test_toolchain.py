from __future__ import annotations

import pytest

from pycorrode import PyCorrodeToolchainError
from pycorrode._build.toolchain import Toolchain


def test_missing_explicit_cargo_has_clear_error(tmp_path) -> None:
    with pytest.raises(PyCorrodeToolchainError, match="does not exist"):
        Toolchain.discover(tmp_path / "missing-cargo")
