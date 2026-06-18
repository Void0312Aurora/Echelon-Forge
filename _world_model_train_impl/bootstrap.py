"""Repository import bootstrap for the world-model training CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[1])


def configure_repo_imports() -> None:
    build_dir_names: list[str] = []
    env_build_dir = os.environ.get("CMO_BUILD_DIR", "").strip()
    if env_build_dir:
        build_dir_names.append(env_build_dir)
    build_dir_names.extend(["build-workshop", "build-gpu", "build"])
    for build_dir_name in build_dir_names:
        build_dir = (
            build_dir_name
            if os.path.isabs(build_dir_name)
            else os.path.join(_REPO_ROOT, build_dir_name)
        )
        if not os.path.isdir(build_dir):
            continue
        for name in ("ef_py", "ef_py.cpython-313-x86_64-linux-gnu.so"):
            if os.path.exists(os.path.join(build_dir, name)) or any(
                fname.startswith("ef_py") and fname.endswith(".so")
                for fname in os.listdir(build_dir)
            ):
                if build_dir in sys.path:
                    sys.path.remove(build_dir)
                sys.path.insert(0, build_dir)
                break
        if sys.path and sys.path[0] == build_dir:
            break
    if _REPO_ROOT in sys.path:
        sys.path.remove(_REPO_ROOT)
    sys.path.insert(0, _REPO_ROOT)


configure_repo_imports()
