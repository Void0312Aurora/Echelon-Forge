#!/usr/bin/env python3

from __future__ import annotations

import argparse
import glob
import importlib
import json
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
  if group == "sim_kernel":
    return (
      "subprocess",
      sorted(glob.glob(resolve_repo_path("tests", "contracts", "unit", "kernel", "*.json"))),
      "no simulation kernel contracts found",
    )
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
    choices=["chain", "env", "unit", "bridges", "route_generator", "same_process", "sim_kernel"],
    help="Contract group to run. Repeat to select multiple groups. Defaults to all groups.",
  )
  parser.add_argument(
    "--default-group",
    choices=["all", "sim_kernel"],
    default="all",
    help="Default group set to run when --group is omitted.",
  )
  return parser.parse_args()


def main() -> int:
  from python.testing.runtime import ensure_repo_imports

  ensure_repo_imports()
  args = parse_args()
  if args.groups:
    groups = list(args.groups)
  elif args.default_group == "sim_kernel":
    groups = ["sim_kernel"]
  else:
    groups = ["chain", "env", "unit", "bridges", "route_generator", "same_process"]

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


def test_scenario_contract_runner_reexports_contract_entrypoints() -> None:
  legacy = importlib.import_module("python.testing.scenario_contract_runner")
  contracts = importlib.import_module("python.testing.contracts")

  assert legacy.ContractSkipped is contracts.ContractSkipped
  assert legacy.run_contract is contracts.run_contract
  assert legacy.run_loader_command_chain_contract is contracts.run_loader_command_chain_contract
  assert legacy.run_route_generator_contract is contracts.run_route_generator_contract
  assert legacy.run_env_regression_contract is contracts.run_env_regression_contract
  assert legacy.run_unit_regression_contract is contracts.run_unit_regression_contract
  assert legacy.run_scripted_bridge_contract is contracts.run_scripted_bridge_contract


def test_run_contract_legacy_entrypoint_dispatches_via_new_package(tmp_path, monkeypatch) -> None:
  legacy = importlib.import_module("python.testing.scenario_contract_runner")
  contracts = importlib.import_module("python.testing.contracts")
  spec_path = tmp_path / "contract.json"
  spec_path.write_text(json.dumps({"type": "loader_command_chain"}), encoding="utf-8")
  calls: list[str] = []

  def fake_handler(path: str) -> tuple[bool, str]:
    calls.append(path)
    return True, "compat dispatch passed"

  monkeypatch.setitem(contracts._CONTRACT_HANDLERS, "loader_command_chain", fake_handler)

  assert legacy.run_contract(str(spec_path)) == (True, "compat dispatch passed")
  assert calls == [str(spec_path)]


def test_run_direct_specs_uses_legacy_compat_entrypoint(monkeypatch, capsys) -> None:
  legacy = importlib.import_module("python.testing.scenario_contract_runner")
  calls: list[str] = []

  def fake_run_contract(path: str) -> tuple[bool, str]:
    calls.append(path)
    return True, "batch smoke passed"

  monkeypatch.setattr(legacy, "run_contract", fake_run_contract)

  assert _run_direct_specs(["tests/contracts/example.json"]) == 0
  assert calls == ["tests/contracts/example.json"]
  assert "PASS: tests/contracts/example.json: batch smoke passed" in capsys.readouterr().out


def test_runtime_build_dirs_prefers_artifacts_and_linux_order(tmp_path, monkeypatch) -> None:
  runtime = importlib.import_module("python.testing.runtime")
  monkeypatch.delenv("CMO_BUILD_DIR", raising=False)
  monkeypatch.setattr(runtime, "_is_windows", lambda: False)

  for name in ("build-local-win", "build-workshop", "build-gpu", "build", "build-facade-local"):
    (tmp_path / name).mkdir()
  (tmp_path / "build-gpu" / "ef_py.cpython-test.so").write_text("", encoding="utf-8")

  assert runtime.build_dirs(str(tmp_path)) == [
    str(tmp_path / "build-gpu"),
    str(tmp_path / "build-workshop"),
    str(tmp_path / "build"),
    str(tmp_path / "build-facade-local"),
  ]


def test_runtime_build_dirs_keeps_windows_local_priority(tmp_path, monkeypatch) -> None:
  runtime = importlib.import_module("python.testing.runtime")
  monkeypatch.delenv("CMO_BUILD_DIR", raising=False)
  monkeypatch.setattr(runtime, "_is_windows", lambda: True)

  for name in ("build-local-win", "build-workshop"):
    (tmp_path / name).mkdir()
  (tmp_path / "build-local-win" / "Release").mkdir()
  (tmp_path / "build-local-win" / "Release" / "ef_py.cp311-win_amd64.pyd").write_text("", encoding="utf-8")
  (tmp_path / "build-workshop" / "ef_py.cpython-test.so").write_text("", encoding="utf-8")

  assert runtime.build_dirs(str(tmp_path))[:2] == [
    str(tmp_path / "build-local-win"),
    str(tmp_path / "build-workshop"),
  ]


def test_subprocess_pythonpath_uses_runtime_build_order(tmp_path, monkeypatch) -> None:
  runtime = importlib.import_module("python.testing.runtime")
  env_build = tmp_path / "custom-build"
  fallback_build = tmp_path / "build"
  env_build.mkdir()
  fallback_build.mkdir()
  (fallback_build / "ef_py.cpython-test.so").write_text("", encoding="utf-8")
  monkeypatch.setenv("CMO_BUILD_DIR", str(env_build))
  monkeypatch.setattr(runtime, "_is_windows", lambda: False)

  assert _subprocess_pythonpath_parts(str(tmp_path)) == [
    str(fallback_build),
    str(env_build),
    str(tmp_path),
  ]


if __name__ == "__main__":
  raise SystemExit(main())
