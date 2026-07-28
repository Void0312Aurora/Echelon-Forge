#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.runtime_bootstrap import ensure_repo_imports
from python.testing.suite_manifest import (
    load_pytest_suite_manifest,
    load_suite_object,
    resolve_pytest_entry,
    resolve_repo_or_abs,
)


ensure_repo_imports()


def _resolve_repo_or_abs(path: str) -> str:
    return resolve_repo_or_abs(path, REPO_ROOT)


def _resolve_pytest_entry(entry: str) -> tuple[str, str]:
    resolved = resolve_pytest_entry(entry, REPO_ROOT)
    return resolved.resolved, resolved.check_path


def _load_suite(path: str) -> dict[str, object]:
    return load_suite_object(path)


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
    manifest = load_pytest_suite_manifest(str(args.suite), REPO_ROOT)
    if manifest.missing_entries:
        print(f"[pytest-suite] {manifest.name}: stale path entries detected:", file=sys.stderr)
        for missing in manifest.missing_entries:
            print(f"  - {missing.raw}", file=sys.stderr)
        print(
            "[pytest-suite] update the checked-in suite manifest before relying on CI or docs references",
            file=sys.stderr,
        )
        return 2

    pytest_args = list(args.pytest_args or [])
    resolved_paths = [entry.resolved for entry in manifest.entries]
    cmd = [sys.executable, "-m", "pytest", "-q", *resolved_paths, *pytest_args]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
