from __future__ import annotations

import json
from pathlib import Path

from tools.runners import audit_test_system


def _write(path: Path, text: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding="utf-8")


def test_build_audit_excludes_archive_and_counts_smoke_surfaces(tmp_path: Path) -> None:
  _write(
    tmp_path / "tests/smoke/ci_smoke_suite.json",
    json.dumps(
      {
        "name": "test_smoke",
        "paths": ["tests/runtime/test_runtime_gate.py::test_runtime_gate"],
      }
    ),
  )
  _write(
    tmp_path / "tests/smoke/ci_contract_suite.json",
    json.dumps(
      {
        "name": "contract_smoke",
        "specs": ["tests/contracts/unit/comm/runtime_gate.json"],
      }
    ),
  )
  _write(
    tmp_path / "tests/runtime/test_runtime_gate.py",
    "def test_runtime_gate():\n  assert True\n",
  )
  _write(
    tmp_path / "tests/runtime/hidden_runtime_cases.py",
    "class RuntimeCases:\n  def test_hidden_case(self):\n    assert True\n",
  )
  _write(
    tmp_path / "tests/archive/test_old_gate.py",
    "def test_old_gate():\n  assert False\n",
  )
  _write(
    tmp_path / "tests/contracts/unit/comm/runtime_gate.json",
    json.dumps({"type": "unit_regression", "check_kind": "comm", "cases": []}),
  )

  audit = audit_test_system.build_audit(
    root=tmp_path,
    test_files=[
      "tests/runtime/test_runtime_gate.py",
      "tests/runtime/hidden_runtime_cases.py",
      "tests/archive/test_old_gate.py",
      "tests/contracts/unit/comm/runtime_gate.json",
    ],
  )

  assert audit["summary"]["active_files"] == 3
  assert audit["summary"]["pytest_smoke_entries"] == 1
  assert audit["summary"]["contract_json_files"] == 1
  assert audit["summary"]["contract_smoke_specs"] == 1
  assert audit["summary"]["hidden_mixin_test_files"] == 1
  assert not any(
    row["path"] == "tests/archive/test_old_gate.py"
    for row in audit["top_risk_files"]
  )


def test_class_test_methods_are_not_double_counted(tmp_path: Path) -> None:
  _write(
    tmp_path / "tests/runtime/test_class_cases.py",
    "\n".join(
      [
        "class TestRuntimeCases:",
        "  def test_method_case(self):",
        "    assert True",
        "",
        "def test_top_level_case():",
        "  assert True",
        "",
      ]
    ),
  )

  stats = audit_test_system.analyze_python_test_file(
    tmp_path,
    "tests/runtime/test_class_cases.py",
    pytest_smoke_files=set(),
  )

  assert stats["test_items"] == 2
  assert stats["max_test_item_asserts"] == 1


def test_analyze_python_test_file_flags_literal_heavy_source_scan(
  tmp_path: Path,
) -> None:
  asserts = "\n".join(
    f"  assert data['key_{index}'] == 'value_{index}'" for index in range(130)
  )
  _write(
    tmp_path / "tests/runtime/test_hardcoded_snapshot.py",
    "\n".join(
      [
        "from pathlib import Path",
        "",
        "def test_hardcoded_snapshot():",
        *[
          f"  source_{index} = Path('src/core/source_{index}.cpp').read_text(encoding='utf-8')"
          for index in range(5)
        ],
        "  data = {",
        *[f"    'key_{index}': 'value_{index}'," for index in range(130)],
        "  }",
        "  assert 'SimulationKernel' in source_0",
        asserts,
        "",
      ]
    ),
  )

  stats = audit_test_system.analyze_python_test_file(
    tmp_path,
    "tests/runtime/test_hardcoded_snapshot.py",
    pytest_smoke_files=set(),
  )

  assert stats["max_test_item_span"] >= audit_test_system.OVERSIZED_TEST_ITEM_LINES
  assert "oversized_test_item" in stats["risk_flags"]
  assert "assert_heavy" in stats["risk_flags"]
  assert "literal_heavy" in stats["risk_flags"]
  assert "source_scan_guard" in stats["risk_flags"]
  assert "not_smoke_gated" in stats["risk_flags"]


def test_markdown_report_includes_risk_and_contract_sections(tmp_path: Path) -> None:
  _write(
    tmp_path / "tests/smoke/ci_smoke_suite.json",
    json.dumps({"name": "emptyish", "paths": ["tests/runtime/test_small.py"]}),
  )
  _write(
    tmp_path / "tests/smoke/ci_contract_suite.json",
    json.dumps({"name": "contract_smoke", "specs": []}),
  )
  _write(tmp_path / "tests/runtime/test_small.py", "def test_small():\n  assert True\n")

  audit = audit_test_system.build_audit(
    root=tmp_path,
    test_files=["tests/runtime/test_small.py"],
  )
  markdown = audit_test_system._format_markdown(audit, limit=5)

  assert "# Test System Audit" in markdown
  assert "## Top Risk Files" in markdown
  assert "## Contract Groups" in markdown
