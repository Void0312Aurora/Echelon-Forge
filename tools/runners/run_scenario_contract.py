#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from python.testing.scenario_contract_runner import ContractSkipped, run_contract

    parser = argparse.ArgumentParser(description="Run a JSON-driven scenario contract check")
    parser.add_argument("--spec", required=True, nargs="+", help="One or more JSON contract spec paths")
    args = parser.parse_args()

    all_ok = True
    for spec_path in args.spec:
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
