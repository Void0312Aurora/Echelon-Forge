#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_DIR_NAMES = []
ENV_BUILD_DIR = os.environ.get("CMO_BUILD_DIR", "").strip()
if ENV_BUILD_DIR:
    BUILD_DIR_NAMES.append(ENV_BUILD_DIR)
BUILD_DIR_NAMES.extend(["build-workshop", "build-gpu", "build", "build-facade-local"])
for build_dir_name in BUILD_DIR_NAMES:
    build_dir = build_dir_name if os.path.isabs(build_dir_name) else os.path.join(REPO_ROOT, build_dir_name)
    if not os.path.isdir(build_dir):
        continue
    for name in ("ef_py", "ef_py.cpython-313-x86_64-linux-gnu.so"):
        if os.path.exists(os.path.join(build_dir, name)) or any(
            fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(build_dir)
        ):
            if build_dir in sys.path:
                sys.path.remove(build_dir)
            sys.path.insert(0, build_dir)
            break
    if sys.path and sys.path[0] == build_dir:
        break
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.rl.multi_agent_benchmark import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
