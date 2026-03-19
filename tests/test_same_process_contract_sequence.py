#!/usr/bin/env python3

from __future__ import annotations


def main() -> int:
    from python.testing.runtime import ensure_repo_imports, resolve_repo_path

    ensure_repo_imports()

    from python.testing.scenario_contract_runner import run_contract

    spec_paths = [
        resolve_repo_path("tests", "contracts", "unit", "comm", "task_order_and_mission_link.json"),
        resolve_repo_path("tests", "contracts", "unit", "comm", "scenario_loader_mission_semantics.json"),
    ]

    for spec_path in spec_paths:
        ok, message = run_contract(spec_path)
        if not ok:
            print(f"FAIL: {spec_path}: {message}")
            return 1
        print(f"PASS: {spec_path}: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
