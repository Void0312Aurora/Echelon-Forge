from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.runners import run_pytest_suite


def test_resolve_pytest_entry_accepts_repo_relative_file() -> None:
  resolved, check_path = run_pytest_suite._resolve_pytest_entry(
    "tests/runners/test_run_pytest_suite.py"
  )

  assert resolved == check_path
  assert resolved.endswith("tests\\runners\\test_run_pytest_suite.py") or resolved.endswith(
    "tests/runners/test_run_pytest_suite.py"
  )


def test_resolve_pytest_entry_preserves_nodeid_suffix_for_pytest() -> None:
  resolved, check_path = run_pytest_suite._resolve_pytest_entry(
    "tests/runners/test_run_pytest_suite.py::test_resolve_pytest_entry_accepts_repo_relative_file"
  )

  assert check_path.endswith("tests\\runners\\test_run_pytest_suite.py") or check_path.endswith(
    "tests/runners/test_run_pytest_suite.py"
  )
  assert resolved == (
    f"{check_path}::test_resolve_pytest_entry_accepts_repo_relative_file"
  )


def test_resolve_pytest_entry_keeps_missing_nodeid_check_on_base_path() -> None:
  resolved, check_path = run_pytest_suite._resolve_pytest_entry(
    "tests/runners/missing_runner_test.py::test_missing"
  )

  assert check_path.endswith("tests\\runners\\missing_runner_test.py") or check_path.endswith(
    "tests/runners/missing_runner_test.py"
  )
  assert resolved == f"{check_path}::test_missing"


def test_main_reports_stale_manifest_entries_with_exit_code_2(
  tmp_path: Path,
  monkeypatch,
  capsys,
) -> None:
  suite_path = tmp_path / "suite.json"
  suite_path.write_text(
    json.dumps({"name": "stale", "paths": ["tests/runners/missing.py"]}),
    encoding="utf-8",
  )
  monkeypatch.setattr(
    sys,
    "argv",
    ["run_pytest_suite.py", "--suite", str(suite_path)],
  )

  assert run_pytest_suite.main() == 2
  stderr = capsys.readouterr().err
  assert "[pytest-suite] stale: stale path entries detected:" in stderr
  assert "tests/runners/missing.py" in stderr
