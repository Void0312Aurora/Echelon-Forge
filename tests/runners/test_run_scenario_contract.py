from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
import pytest

from tools.runners import run_scenario_contract


def test_load_suite_specs_resolves_repo_relative_entries(tmp_path: Path) -> None:
  suite_path = tmp_path / "contract_suite.json"
  suite_path.write_text(
    json.dumps({"specs": ["tests/contracts/unit/example.json"]}),
    encoding="utf-8",
  )

  specs = run_scenario_contract._load_suite_specs(str(suite_path), str(tmp_path))

  assert specs == [str(tmp_path / "tests" / "contracts" / "unit" / "example.json")]


def test_load_suite_specs_accepts_paths_alias(tmp_path: Path) -> None:
  spec_path = tmp_path / "contract.json"
  suite_path = tmp_path / "contract_suite.json"
  suite_path.write_text(json.dumps({"paths": [str(spec_path)]}), encoding="utf-8")

  specs = run_scenario_contract._load_suite_specs(str(suite_path), str(tmp_path))

  assert specs == [str(spec_path)]


def test_main_runs_suite_and_explicit_specs(monkeypatch, tmp_path: Path) -> None:
  suite_spec = tmp_path / "suite_contract.json"
  explicit_spec = tmp_path / "explicit_contract.json"
  suite_path = tmp_path / "contract_suite.json"
  for path in (suite_spec, explicit_spec):
    path.write_text("{}", encoding="utf-8")
  suite_path.write_text(json.dumps({"specs": [str(suite_spec)]}), encoding="utf-8")

  calls: list[str] = []
  contract_runner = importlib.import_module("python.testing.contracts")

  def fake_run_contract(path: str) -> tuple[bool, str]:
    calls.append(path)
    return True, "suite contract passed"

  monkeypatch.setattr(contract_runner, "run_contract", fake_run_contract)
  monkeypatch.setattr(
    sys,
    "argv",
    [
      "run_scenario_contract.py",
      "--suite",
      str(suite_path),
      "--spec",
      str(explicit_spec),
    ],
  )

  assert run_scenario_contract.main() == 0
  assert calls == [str(suite_spec), str(explicit_spec)]


def test_main_reports_missing_suite_specs(monkeypatch, tmp_path: Path, capsys) -> None:
  missing_spec = tmp_path / "missing_contract.json"
  suite_path = tmp_path / "contract_suite.json"
  suite_path.write_text(json.dumps({"specs": [str(missing_spec)]}), encoding="utf-8")
  monkeypatch.setattr(
    sys,
    "argv",
    ["run_scenario_contract.py", "--suite", str(suite_path)],
  )

  assert run_scenario_contract.main() == 2
  assert str(missing_spec) in capsys.readouterr().err


@pytest.mark.parametrize('outcomes,allow_skips,status', [
  (['skip', 'skip'], False, 1), (['pass', 'skip'], False, 1),
  (['skip', 'skip'], True, 0), (['pass', 'skip'], True, 0),
  (['fail', 'skip'], True, 1), (['pass', 'pass'], False, 0),
])
@pytest.mark.parametrize('batch', [False, True])
def test_selected_completion_policy(monkeypatch, capsys, outcomes, allow_skips, status, batch):
  contracts = importlib.import_module('python.testing.contracts')
  def run(path):
    if path == 'skip':
      raise contracts.ContractSkipped('optional artifact absent')
    return path == 'pass', 'checked assertion'
  monkeypatch.setattr(contracts, 'run_contract', run)
  if batch:
    from tools.runners.run_contract_batches import _run_direct_specs
    execute = _run_direct_specs
  else:
    execute = run_scenario_contract.run_selected_contracts
  assert execute(outcomes, allow_skips=allow_skips) == status
  report = capsys.readouterr().out
  assert f'PASS={outcomes.count("pass")}' in report
  assert f'FAIL={outcomes.count("fail")}' in report
  assert f'SKIP={outcomes.count("skip")}' in report
