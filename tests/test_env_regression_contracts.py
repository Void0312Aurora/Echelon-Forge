#!/usr/bin/env python3

from __future__ import annotations

import glob


def main() -> int:
    from python.testing.runtime import ensure_repo_imports, resolve_repo_path

    ensure_repo_imports()

    from python.testing.scenario_contract_runner import ContractSkipped, run_contract

    spec_paths = sorted(glob.glob(resolve_repo_path("tests", "contracts", "env", "*", "*.json")))
    if not spec_paths:
        print("FAIL: no env regression contracts found")
        return 1

    for spec_path in spec_paths:
        try:
            ok, message = run_contract(spec_path)
        except ContractSkipped as exc:
            print(f"SKIP: {spec_path}: {exc}")
            continue
        if not ok:
            print(f"FAIL: {spec_path}: {message}")
            return 1
        print(f"PASS: {spec_path}: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
