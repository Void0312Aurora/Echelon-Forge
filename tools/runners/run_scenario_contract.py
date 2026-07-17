#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.suite_manifest import (
    load_contract_suite_manifest,
    resolve_repo_or_abs,
)


def _resolve_repo_or_abs(path: str, repo_root: str) -> str:
    return resolve_repo_or_abs(
        path,
        repo_root,
        empty_message="contract suite path entries must be non-empty",
    )


def _load_suite_specs(path: str, repo_root: str) -> list[str]:
    manifest = load_contract_suite_manifest(path, repo_root)
    return [entry.resolved for entry in manifest.entries]


def main() -> int:
    repo_root = REPO_ROOT
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from python.testing.runtime import ensure_repo_imports

    ensure_repo_imports()

    from python.testing.contracts import ContractSkipped, run_contract

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
