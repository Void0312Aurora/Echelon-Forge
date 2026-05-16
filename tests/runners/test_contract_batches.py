#!/usr/bin/env python3

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _resolve_specs(group: str) -> tuple[str, list[str], str]:
    from python.testing.runtime import resolve_repo_path

    if group == "chain":
        return ("subprocess", sorted(glob.glob(resolve_repo_path("tests", "contracts", "chain", "**", "*.json"), recursive=True)), "no chain contracts found")
    if group == "env":
        return ("direct", sorted(glob.glob(resolve_repo_path("tests", "contracts", "env", "*", "*.json"))), "no env regression contracts found")
    if group == "unit":
        return ("subprocess", sorted(glob.glob(resolve_repo_path("tests", "contracts", "unit", "**", "*.json"), recursive=True)), "no unit regression contracts found")
    if group == "bridges":
        return ("subprocess", sorted(glob.glob(resolve_repo_path("tests", "contracts", "bridges", "**", "*.json"), recursive=True)), "no scripted bridge contracts found")
    if group == "route_generator":
        return ("direct", sorted(glob.glob(resolve_repo_path("tests", "contracts", "route_generator", "*.json"))), "no route generator contracts found")
    if group == "same_process":
        return (
            "direct",
            [
                resolve_repo_path("tests", "contracts", "unit", "comm", "task_order_common_core_defaults.json"),
                resolve_repo_path("tests", "contracts", "unit", "comm", "scenario_loader_common_core_semantics.json"),
                resolve_repo_path("tests", "contracts", "unit", "comm", "task_order_and_mission_link.json"),
                resolve_repo_path("tests", "contracts", "unit", "comm", "scenario_loader_mission_semantics.json"),
            ],
            "no same-process contracts found",
        )
    raise ValueError(f"unknown contract batch group: {group}")


def _run_subprocess_specs(spec_paths: list[str]) -> int:
    from python.testing.runtime import ensure_repo_imports, resolve_repo_path

    repo_root = ensure_repo_imports()
    pythonpath_parts = [resolve_repo_path("build"), repo_root]
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    child_env = dict(os.environ)
    child_env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    runner = resolve_repo_path("tools", "runners", "run_scenario_contract.py")

    for spec_path in spec_paths:
        proc = subprocess.run(
            [sys.executable, runner, "--spec", spec_path],
            cwd=repo_root,
            env=child_env,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        if proc.returncode != 0:
            if not stdout and not stderr:
                print(f"FAIL: {spec_path}: contract subprocess exited with code {proc.returncode}")
            return 1
    return 0


def _run_direct_specs(spec_paths: list[str]) -> int:
    from python.testing.scenario_contract_runner import ContractSkipped, run_contract

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run grouped JSON contract batches from tests/contracts.")
    parser.add_argument(
        "--group",
        dest="groups",
        action="append",
        choices=["chain", "env", "unit", "bridges", "route_generator", "same_process"],
        help="Contract group to run. Repeat to select multiple groups. Defaults to all groups.",
    )
    return parser.parse_args()


def main() -> int:
    from python.testing.runtime import ensure_repo_imports

    ensure_repo_imports()
    args = parse_args()
    groups = list(args.groups or ["chain", "env", "unit", "bridges", "route_generator", "same_process"])

    for group in groups:
        mode, spec_paths, empty_message = _resolve_specs(group)
        if not spec_paths:
            print(f"FAIL: {empty_message}")
            return 1
        if mode == "subprocess":
            rc = _run_subprocess_specs(spec_paths)
        else:
            rc = _run_direct_specs(spec_paths)
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
