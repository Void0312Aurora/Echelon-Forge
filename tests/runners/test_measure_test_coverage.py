from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tools.runners import measure_test_coverage


def _write_suite(path: Path, entries: list[str]) -> None:
  path.write_text(
    json.dumps({"name": "test_coverage_suite", "paths": entries}),
    encoding="utf-8",
  )


def test_load_suite_paths_preserves_pytest_nodeids(tmp_path: Path) -> None:
  suite_path = tmp_path / "suite.json"
  _write_suite(
    suite_path,
    [
      "tests/runners/test_run_pytest_suite.py::test_resolve_pytest_entry_accepts_repo_relative_file"
    ],
  )

  resolved = measure_test_coverage._load_suite_paths(suite_path)

  assert len(resolved) == 1
  assert "::test_resolve_pytest_entry_accepts_repo_relative_file" in resolved[0]
  assert "tests/runners/test_run_pytest_suite.py" in resolved[0].replace("\\", "/")


def test_load_suite_paths_fails_on_stale_manifest_entries(tmp_path: Path) -> None:
  suite_path = tmp_path / "suite.json"
  _write_suite(suite_path, ["tests/runners/missing_coverage_runner_test.py"])

  with pytest.raises(FileNotFoundError, match="stale entries"):
    measure_test_coverage._load_suite_paths(suite_path)


def test_main_can_write_metadata_when_all_reports_are_skipped(
  tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  output_dir = tmp_path / "coverage-reports"
  monkeypatch.setattr(
    sys,
    "argv",
    [
      "measure_test_coverage.py",
      "--skip-python",
      "--skip-cpp",
      "--output-dir",
      str(output_dir),
    ],
  )

  assert measure_test_coverage.main() == 0

  metadata = json.loads(
    (output_dir / "coverage-run-metadata.json").read_text(encoding="utf-8")
  )
  assert metadata["python_sources"] == list(
    measure_test_coverage.DEFAULT_PYTHON_SOURCES
  )
  assert metadata["results"] == []


def test_main_records_unavailable_cpp_report_when_requested(
  tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  output_dir = tmp_path / "coverage-reports"
  monkeypatch.setattr(
    sys,
    "argv",
    [
      "measure_test_coverage.py",
      "--skip-python",
      "--skip-unavailable-reports",
      "--cpp-object-dir",
      str(tmp_path / "missing-build"),
      "--output-dir",
      str(output_dir),
    ],
  )

  assert measure_test_coverage.main() == 0

  metadata = json.loads(
    (output_dir / "coverage-run-metadata.json").read_text(encoding="utf-8")
  )
  assert len(metadata["results"]) == 1
  assert metadata["results"][0]["name"] == "cpp-gcovr"
  assert metadata["results"][0]["returncode"] == 0
  assert metadata["results"][0]["skipped"]


def test_python_module_tool_falls_back_to_current_interpreter(
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  monkeypatch.setattr(measure_test_coverage, "_venv_tool", lambda _name: None)
  monkeypatch.setattr(measure_test_coverage, "_module_available", lambda _name: True)

  command = measure_test_coverage._python_module_tool("gcovr")

  assert command == [sys.executable, "-m", "gcovr"]
