"""Deterministic extension cache keys."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import sysconfig

from ..models import ExtensionSpec
from .artifact import python_extension_suffix
from .toolchain import Toolchain

_PROJECT_SCHEMA = 1


def extension_fingerprint(spec: ExtensionSpec, toolchain: Toolchain) -> str:
    """Hash all inputs which can affect extension compatibility or output."""

    payload = {
        "platform": {
            "machine": platform.machine(),
            "system": sys.platform,
        },
        "project_schema": _PROJECT_SCHEMA,
        "python": {
            "abiflags": getattr(sys, "abiflags", ""),
            "cache_tag": sys.implementation.cache_tag,
            "executable": sys.executable,
            "extension_suffix": python_extension_suffix(),
            "implementation": sys.implementation.name,
            "soabi": sysconfig.get_config_var("SOABI"),
            "version": list(sys.version_info[:3]),
        },
        "spec": spec.canonical(),
        "toolchain": toolchain.canonical(),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()
