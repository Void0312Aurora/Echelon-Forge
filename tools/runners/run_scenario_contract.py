#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def _resolve_repo_or_abs(path: str, repo_root: str) -> str:
    raw = str(path).strip()
    if not raw:
        raise ValueError("contract suite path entries must be non-empty")
    if os.path.isabs(raw):
        return os.path.abspath(raw)
    return os.path.abspath(os.path.join(repo_root, *raw.replace("\\", "/").split("/")))


def _load_suite_specs(path: str, repo_root: str) -> list[str]:
    suite_path = _resolve_repo_or_abs(path, repo_root)
    with open(suite_path, "r", encoding="utf-8") as handle:
        suite: dict[str, Any] = json.load(handle)
    if not isinstance(suite, dict):
        raise TypeError(f"expected contract suite JSON object at {suite_path!r}")
    raw_specs = suite.get("specs", suite.get("paths", []))
    if not isinstance(raw_specs, list) or not raw_specs:
        raise ValueError(f"contract suite {suite_path!r} has no non-empty 'specs' list")

    specs: list[str] = []
    for raw in raw_specs:
        if not isinstance(raw, str):
            raise TypeError("contract suite spec entries must be strings")
        specs.append(_resolve_repo_or_abs(raw, repo_root))
    return specs


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from python.testing.runtime import ensure_repo_imports

    ensure_repo_imports()

    from python.testing.scenario_contract_runner import ContractSkipped, run_contract

    parser = argparse.ArgumentParser(description="Run JSON-driven scenario contract checks")
    parser.add_argument("--spec", nargs="+", default=[], help="One or more JSON contract spec paths")
    parser.add_argument(
        "--suite",
        action="append",
        default=[],
        help="Checked-in JSON suite manifest with a 'specs' list. Repeatable.",
    )
    args = parser.parse_args()

    spec_paths: list[str] = []
    for suite_path in args.suite:
        spec_paths.extend(_load_suite_specs(str(suite_path), repo_root))
    spec_paths.extend(_resolve_repo_or_abs(spec, repo_root) for spec in args.spec)
    if not spec_paths:
        parser.error("at least one --spec or --suite is required")

    missing_specs = [spec_path for spec_path in spec_paths if not os.path.exists(spec_path)]
    if missing_specs:
        print("[contract-runner] stale spec path entries detected:", file=sys.stderr)
        for spec_path in missing_specs:
            print(f"  - {spec_path}", file=sys.stderr)
        return 2

    all_ok = True
    for spec_path in spec_paths:
        try:
            ok, message = run_contract(os.path.abspath(spec_path))
        except ContractSkipped as exc:
            print(f"SKIP: {spec_path}: {exc}")
            continue
        if ok:
            print(f"PASS: {spec_path}: {message}")
            continue
        print(f"FAIL: {spec_path}: {message}")
        all_ok = False
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
