from __future__ import annotations

import json
from pathlib import Path

from pycorrode._build.artifact import parse_cargo_messages


def test_parses_matching_cdylib_and_diagnostics(tmp_path: Path) -> None:
    artifact = tmp_path / "lib_pycorrode_test.so"
    output = "\n".join(
        [
            json.dumps(
                {
                    "reason": "compiler-message",
                    "message": {"rendered": "warning: an example\n"},
                }
            ),
            json.dumps(
                {
                    "reason": "compiler-artifact",
                    "target": {
                        "name": "dependency",
                        "crate_types": ["lib"],
                    },
                    "filenames": [str(tmp_path / "dependency.rlib")],
                }
            ),
            json.dumps(
                {
                    "reason": "compiler-artifact",
                    "target": {
                        "name": "_pycorrode_test",
                        "crate_types": ["cdylib"],
                    },
                    "filenames": [str(artifact)],
                }
            ),
        ]
    )

    messages = parse_cargo_messages(output, "_pycorrode_test")

    assert messages.artifacts == (artifact,)
    assert messages.diagnostics == "warning: an example"


def test_preserves_non_json_cargo_output_as_diagnostics() -> None:
    messages = parse_cargo_messages("ordinary cargo output", "_pycorrode_test")

    assert messages.artifacts == ()
    assert messages.diagnostics == "ordinary cargo output"
