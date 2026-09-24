from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.runners import audit_test_authority


pytestmark = pytest.mark.governance_audit


def _write_manifest(path: Path, *, name: str, test_path: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(
      {
        "name": name,
        "owner": "test-owner",
        "failure_audience": "test audience",
        "execution_strategy": "pytest-manifest-file",
        "paths": [test_path],
      }
    ),
    encoding="utf-8",
  )


def test_derived_inventory_assigns_every_architecture_test_once() -> None:
  report = audit_test_authority.build_inventory()

  assert report["report_authority"] == "derived_non_authoritative"
  assert report["source_of_truth"] == [
    "tests/suites/architecture_guard_suite.json",
    "tests/suites/governance_audit_suite.json",
  ]
  assert report["summary"]["architecture_test_files"] == report["summary"]["manifest_entries"]
  assert report["summary"]["architecture_test_files"] == len(report["tests"])
  assert {row["path"] for row in report["tests"]} == audit_test_authority._live_architecture_test_files(
    audit_test_authority.REPO_ROOT
  )
  assert all(
    row["owner"] and row["failure_audience"] and row["execution_strategy"]
    for row in report["tests"]
  )


def test_inventory_rejects_cross_manifest_overlap(tmp_path: Path) -> None:
  test_path = "tests/architecture/test_overlap.py"
  (tmp_path / test_path).parent.mkdir(parents=True, exist_ok=True)
  (tmp_path / test_path).write_text("def test_overlap():\n  assert True\n", encoding="utf-8")
  first = tmp_path / "first.json"
  second = tmp_path / "second.json"
  _write_manifest(first, name="first", test_path=test_path)
  _write_manifest(second, name="second", test_path=test_path)

  with pytest.raises(audit_test_authority.AuthorityAuditError, match="multiple tier manifests"):
    audit_test_authority.build_inventory(
      root=tmp_path,
      manifest_paths=[first, second],
      live_test_files=[test_path],
    )


def test_markdown_report_preserves_non_authoritative_boundary() -> None:
  report = audit_test_authority.build_inventory()
  markdown = audit_test_authority.format_markdown(report, limit=2)

  assert "derived_non_authoritative" in markdown
  assert "Source of truth" in markdown
  assert "Archive policy changed by this audit: `False`" in markdown
  assert "Source-scan refs" in markdown
