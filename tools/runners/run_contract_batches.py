#!/usr/bin/env python3

"""Run grouped JSON contract batches from tests/contracts/.

Each ``--group`` resolves a path glob (or explicit file list) under
``tests/contracts/`` and executes the selected specs either in subprocesses
(via :mod:`tools.runners.run_scenario_contract`) or directly in-process (via
:mod:`python.testing.contracts`). Defaults to all maintained groups when no
``--group``/``--default-group`` is given.
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys


def _repo_root() -> str:
  return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve_specs(group: str) -> tuple[str, list[str], str]:
  from python.testing.runtime import resolve_repo_path

  if group == "chain":
    return ("subprocess", sorted(glob.glob(resolve_repo_path("tests", "contracts", "chain", "**", "*.json"), recursive=True)), "no chain contracts found")
  if group == "unit":
    return ("subprocess", sorted(glob.glob(resolve_repo_path("tests", "contracts", "unit", "**", "*.json"), recursive=True)), "no unit regression contracts found")
  if group == "sim_kernel":
    return (
      "subprocess",
      sorted(glob.glob(resolve_repo_path("tests", "contracts", "unit", "kernel", "*.json"))),
      "no simulation kernel contracts found",
    )
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


def _subprocess_pythonpath_parts(repo_root: str) -> list[str]:
  from python.testing.runtime import iter_build_dirs

  parts = list(iter_build_dirs(repo_root))
  parts.append(repo_root)
  return parts


def _run_subprocess_specs(spec_paths: list[str]) -> int:
  from python.testing.runtime import ensure_repo_imports, resolve_repo_path

  repo_root = ensure_repo_imports()
  pythonpath_parts = _subprocess_pythonpath_parts(repo_root)
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
  from python.testing.contracts import ContractSkipped, run_contract

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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Run grouped JSON contract batches from tests/contracts.")
  parser.add_argument(
    "--group",
    dest="groups",
    action="append",
    choices=["chain", "unit", "route_generator", "same_process", "sim_kernel"],
    help="Contract group to run. Repeat to select multiple groups. Defaults to all groups.",
  )
  parser.add_argument(
    "--default-group",
    choices=["all", "sim_kernel"],
    default="all",
    help="Default group set to run when --group is omitted.",
  )
  return parser.parse_args(argv)


def main() -> int:
  from python.testing.runtime import ensure_repo_imports

  ensure_repo_imports()
  args = parse_args()
  if args.groups:
    groups = list(args.groups)
  elif args.default_group == "sim_kernel":
    groups = ["sim_kernel"]
  else:
    groups = ["chain", "unit", "route_generator", "same_process"]

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
  repo_root = _repo_root()
  if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
  raise SystemExit(main())
