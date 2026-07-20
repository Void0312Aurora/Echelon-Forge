#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_BUILD_DIR = os.environ.get("CMO_BUILD_DIR", "").strip()


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


if ENV_BUILD_DIR:
    explicit_build_dir = (
        ENV_BUILD_DIR
        if os.path.isabs(ENV_BUILD_DIR)
        else os.path.join(REPO_ROOT, ENV_BUILD_DIR)
    )
    explicit_build_dir = os.path.abspath(explicit_build_dir)
    if not os.path.isdir(explicit_build_dir):
        raise RuntimeError(f"CMO_BUILD_DIR does not exist: {explicit_build_dir}")
    if not _has_ef_py_artifact(explicit_build_dir):
        raise RuntimeError(
            "CMO_BUILD_DIR does not contain an ef_py artifact: "
            f"{explicit_build_dir}"
        )
    BUILD_DIR_NAMES = [explicit_build_dir]
else:
    BUILD_DIR_NAMES = ["build-workshop", "build-gpu", "build", "build-facade-local"]

for build_dir_name in BUILD_DIR_NAMES:
    build_dir = build_dir_name if os.path.isabs(build_dir_name) else os.path.join(REPO_ROOT, build_dir_name)
    if not os.path.isdir(build_dir):
        continue
    if _has_ef_py_artifact(build_dir):
        if build_dir in sys.path:
            sys.path.remove(build_dir)
        sys.path.insert(0, build_dir)
    if sys.path and sys.path[0] == build_dir:
        break
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.rl.support.multi_agent_benchmark import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
