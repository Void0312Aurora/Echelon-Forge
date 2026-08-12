"""CLI-surface tests for ``tools/runners/run_pytest_suite.py``.

These pin the ``--deselect-marker`` tier filter for local and explicit suite
invocations, and pin that an invocation without the flag keeps the historical
command shape byte for byte. CI smoke itself does not pass the flag: its
protection against wholesale audit-tier entries is the static manifest
meta-test ``test_ci_smoke_takes_no_governance_audit_files_wholesale``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.runners import run_pytest_suite


SUITE_ENTRY = "tests/runners/test_run_pytest_suite_cli.py"


def _write_suite(tmp_path: Path, *entries: str) -> Path:
  suite_path = tmp_path / "suite.json"
  suite_path.write_text(
    json.dumps({"name": "cli_fixture", "paths": list(entries) or [SUITE_ENTRY]}),
    encoding="utf-8",
  )
  return suite_path


def _capture_command(monkeypatch) -> list[list[str]]:
  commands: list[list[str]] = []

  def _fake_run(cmd, **kwargs):
    commands.append(list(cmd))
    return subprocess.CompletedProcess(args=cmd, returncode=0)

  monkeypatch.setattr(run_pytest_suite.subprocess, "run", _fake_run)
  return commands


def test_command_without_deselect_markers_keeps_the_historical_shape() -> None:
  cmd = run_pytest_suite.build_pytest_command(["alpha.py", "beta.py::test_case"])

  assert cmd == [sys.executable, "-m", "pytest", "-q", "alpha.py", "beta.py::test_case"]


def test_single_deselect_marker_becomes_a_negated_marker_expression() -> None:
  cmd = run_pytest_suite.build_pytest_command(
    ["alpha.py"],
    deselect_markers=["governance_audit"],
  )

  assert cmd == [
    sys.executable,
    "-m",
    "pytest",
    "-q",
    "-m",
    "not (governance_audit)",
    "alpha.py",
  ]


def test_repeated_deselect_markers_combine_with_and() -> None:
  expression = run_pytest_suite.build_deselect_expression(
    ["governance_audit", "slow or flaky"]
  )

  assert expression == "not (governance_audit) and not (slow or flaky)"


def test_deselect_expression_parenthesizes_compound_expressions() -> None:
  # Without the parentheses, "not slow or flaky" would re-select every flaky
  # test that is not slow, inverting the intended filter.
  assert run_pytest_suite.build_deselect_expression(["slow or flaky"]) == (
    "not (slow or flaky)"
  )


def test_deselect_expression_is_empty_when_no_markers_are_requested() -> None:
  assert run_pytest_suite.build_deselect_expression([]) == ""


def test_pytest_args_stay_after_the_suite_paths() -> None:
  cmd = run_pytest_suite.build_pytest_command(
    ["alpha.py"],
    deselect_markers=["governance_audit"],
    pytest_args=["-x", "-m", "governance_audit"],
  )

  assert cmd[-3:] == ["-x", "-m", "governance_audit"]
  assert cmd.index("not (governance_audit)") < cmd.index("alpha.py")


def test_parse_args_defaults_to_no_deselect_markers(monkeypatch) -> None:
  monkeypatch.setattr(
    sys,
    "argv",
    ["run_pytest_suite.py", "--suite", "tests/smoke/ci_smoke_suite.json"],
  )

  args = run_pytest_suite.parse_args()

  assert args.deselect_markers == []


def test_parse_args_collects_repeated_deselect_markers(monkeypatch) -> None:
  monkeypatch.setattr(
    sys,
    "argv",
    [
      "run_pytest_suite.py",
      "--suite",
      "tests/smoke/ci_smoke_suite.json",
      "--deselect-marker",
      "governance_audit",
      "--deselect-marker",
      " slow ",
    ],
  )

  args = run_pytest_suite.parse_args()

  assert args.deselect_markers == ["governance_audit", "slow"]


def test_parse_args_rejects_a_blank_deselect_marker(monkeypatch) -> None:
  monkeypatch.setattr(
    sys,
    "argv",
    [
      "run_pytest_suite.py",
      "--suite",
      "tests/smoke/ci_smoke_suite.json",
      "--deselect-marker",
      "   ",
    ],
  )

  with pytest.raises(SystemExit) as excinfo:
    run_pytest_suite.parse_args()

  assert excinfo.value.code == 2


def test_main_without_the_flag_runs_pytest_without_a_marker_filter(
  tmp_path: Path,
  monkeypatch,
) -> None:
  suite_path = _write_suite(tmp_path)
  commands = _capture_command(monkeypatch)
  monkeypatch.setattr(
    sys,
    "argv",
    ["run_pytest_suite.py", "--suite", str(suite_path)],
  )

  assert run_pytest_suite.main() == 0
  assert len(commands) == 1
  assert "-m" not in commands[0][3:]
  assert Path(commands[0][-1]).name == "test_run_pytest_suite_cli.py"


def test_main_forwards_the_deselect_expression_to_pytest(
  tmp_path: Path,
  monkeypatch,
) -> None:
  suite_path = _write_suite(tmp_path)
  commands = _capture_command(monkeypatch)
  monkeypatch.setattr(
    sys,
    "argv",
    [
      "run_pytest_suite.py",
      "--suite",
      str(suite_path),
      "--deselect-marker",
      "governance_audit",
    ],
  )

  assert run_pytest_suite.main() == 0
  marker_index = commands[0].index("-m", 3)
  assert commands[0][marker_index + 1] == "not (governance_audit)"


def test_main_returns_the_pytest_exit_code(tmp_path: Path, monkeypatch) -> None:
  suite_path = _write_suite(tmp_path)

  def _fake_run(cmd, **kwargs):
    return subprocess.CompletedProcess(args=cmd, returncode=5)

  monkeypatch.setattr(run_pytest_suite.subprocess, "run", _fake_run)
  monkeypatch.setattr(
    sys,
    "argv",
    [
      "run_pytest_suite.py",
      "--suite",
      str(suite_path),
      "--deselect-marker",
      "governance_audit",
    ],
  )

  assert run_pytest_suite.main() == 5
