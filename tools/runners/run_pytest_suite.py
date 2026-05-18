#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()


def _resolve_repo_or_abs(path: str) -> str:
    raw = str(path).strip()
    if not raw:
        raise ValueError("suite path entries must be non-empty")
    if os.path.isabs(raw):
        return os.path.abspath(raw)
    return resolve_repo_path(*raw.replace("\\", "/").split("/"))


def _load_suite(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected suite JSON object at {path!r}")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a maintained pytest suite from a checked-in JSON manifest."
    )
    parser.add_argument("--suite", required=True, help="Path to the JSON suite manifest.")
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Additional args passed through to pytest after the suite paths.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    suite_path = _resolve_repo_or_abs(str(args.suite))
    suite = _load_suite(suite_path)
    suite_name = str(suite.get("name", os.path.splitext(os.path.basename(suite_path))[0]))
    raw_paths = suite.get("paths", [])
    if not isinstance(raw_paths, list) or not raw_paths:
        raise ValueError(f"pytest suite {suite_path!r} has no non-empty 'paths' list")

    resolved_paths: list[str] = []
    missing_paths: list[str] = []
    for raw in raw_paths:
        if not isinstance(raw, str):
            raise TypeError("pytest suite path entries must be strings")
        resolved = _resolve_repo_or_abs(raw)
        if not os.path.exists(resolved):
            missing_paths.append(str(raw))
            continue
        resolved_paths.append(resolved)

    if missing_paths:
        print(f"[pytest-suite] {suite_name}: stale path entries detected:", file=sys.stderr)
        for missing in missing_paths:
            print(f"  - {missing}", file=sys.stderr)
        print(
            "[pytest-suite] update the checked-in suite manifest before relying on CI or docs references",
            file=sys.stderr,
        )
        return 2

    pytest_args = list(args.pytest_args or [])
    cmd = [sys.executable, "-m", "pytest", "-q", *resolved_paths, *pytest_args]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
