"""Repository import bootstrap for the world-model training CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[1])


def _has_ef_py_artifact(path: str) -> bool:
    try:
        names = os.listdir(path)
    except OSError:
        return False
    return any(
        name == "ef_py"
        or (name.startswith("ef_py") and name.endswith((".so", ".pyd")))
        for name in names
    )


def configure_repo_imports() -> None:
    env_build_dir = os.environ.get("CMO_BUILD_DIR", "").strip()
    if env_build_dir:
        explicit_build_dir = (
            env_build_dir
            if os.path.isabs(env_build_dir)
            else os.path.join(_REPO_ROOT, env_build_dir)
        )
        explicit_build_dir = os.path.abspath(explicit_build_dir)
        if not os.path.isdir(explicit_build_dir):
            raise RuntimeError(f"CMO_BUILD_DIR does not exist: {explicit_build_dir}")
        if not _has_ef_py_artifact(explicit_build_dir):
            raise RuntimeError(
                "CMO_BUILD_DIR does not contain an ef_py artifact: "
                f"{explicit_build_dir}"
            )
        build_dir_names = [explicit_build_dir]
    else:
        build_dir_names = ["build-workshop", "build-gpu", "build"]

    for build_dir_name in build_dir_names:
        build_dir = (
            build_dir_name
            if os.path.isabs(build_dir_name)
            else os.path.join(_REPO_ROOT, build_dir_name)
        )
        if not os.path.isdir(build_dir):
            continue
        if _has_ef_py_artifact(build_dir):
            if build_dir in sys.path:
                sys.path.remove(build_dir)
            sys.path.insert(0, build_dir)
        if sys.path and sys.path[0] == build_dir:
            break
    if _REPO_ROOT in sys.path:
        sys.path.remove(_REPO_ROOT)
    sys.path.insert(0, _REPO_ROOT)


configure_repo_imports()
