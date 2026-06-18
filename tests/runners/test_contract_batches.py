from __future__ import annotations

import importlib
import json
import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
  sys.path.insert(0, REPO_ROOT)


def test_contract_package_exports_contract_entrypoints() -> None:
  contracts = importlib.import_module("python.testing.contracts")

  assert contracts.ContractSkipped
  assert contracts.run_contract
  assert contracts.run_loader_command_chain_contract
  assert contracts.run_route_generator_contract
  assert contracts.run_unit_regression_contract


def test_run_contract_entrypoint_dispatches_via_contract_package(tmp_path, monkeypatch) -> None:
  contracts = importlib.import_module("python.testing.contracts")
  spec_path = tmp_path / "contract.json"
  spec_path.write_text(json.dumps({"type": "loader_command_chain"}), encoding="utf-8")
  calls: list[str] = []

  def fake_handler(path: str) -> tuple[bool, str]:
    calls.append(path)
    return True, "contract dispatch passed"

  monkeypatch.setitem(contracts._CONTRACT_HANDLERS, "loader_command_chain", fake_handler)

  assert contracts.run_contract(str(spec_path)) == (True, "contract dispatch passed")
  assert calls == [str(spec_path)]


def test_run_direct_specs_uses_contract_package_entrypoint(monkeypatch, capsys) -> None:
  from tools.runners.run_contract_batches import _run_direct_specs

  contracts = importlib.import_module("python.testing.contracts")
  calls: list[str] = []

  def fake_run_contract(path: str) -> tuple[bool, str]:
    calls.append(path)
    return True, "batch smoke passed"

  monkeypatch.setattr(contracts, "run_contract", fake_run_contract)

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


def test_runtime_build_dirs_prefers_newest_linux_artifact(tmp_path, monkeypatch) -> None:
  runtime = importlib.import_module("python.testing.runtime")
  monkeypatch.delenv("CMO_BUILD_DIR", raising=False)
  monkeypatch.setattr(runtime, "_is_windows", lambda: False)

  for name in ("build-workshop", "build"):
    (tmp_path / name).mkdir()
  stale_artifact = tmp_path / "build-workshop" / "ef_py.cpython-test.so"
  current_artifact = tmp_path / "build" / "ef_py.cpython-test.so"
  stale_artifact.write_text("", encoding="utf-8")
  current_artifact.write_text("", encoding="utf-8")
  os.utime(stale_artifact, (100.0, 100.0))
  os.utime(current_artifact, (200.0, 200.0))

  assert runtime.build_dirs(str(tmp_path))[:2] == [
    str(tmp_path / "build"),
    str(tmp_path / "build-workshop"),
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
  from tools.runners.run_contract_batches import _subprocess_pythonpath_parts

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
