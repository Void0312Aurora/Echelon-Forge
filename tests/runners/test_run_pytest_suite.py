from __future__ import annotations

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
