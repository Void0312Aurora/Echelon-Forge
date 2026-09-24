from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.runners import audit_ci_lanes


REPO_ROOT = audit_ci_lanes.REPO_ROOT
MANIFEST = REPO_ROOT / "tests" / "suites" / "ci_lane_manifest.json"


def test_ci_lane_manifest_covers_all_primary_lanes() -> None:
  report = audit_ci_lanes.build_report()

  assert report["report_authority"] == "maintained_lane_manifest"
  assert report["summary"] == {
    "lane_count": 5,
    "primary_lane_count": 5,
    "workflow_job_count": 5,
    "workflow_count": 3,
  }
  assert {row["id"] for row in report["lanes"]} == audit_ci_lanes.PRIMARY_LANES


def test_ci_lane_markdown_keeps_failure_audience_and_budget_visible() -> None:
  report = audit_ci_lanes.build_report()
  markdown = audit_ci_lanes.format_markdown(report)

  assert "Failure audience" in markdown
  assert "parallelism" in markdown
  assert "`research`" in markdown


def test_ci_lane_audit_rejects_a_stale_workflow_job(tmp_path: Path) -> None:
  payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
  payload["lanes"][0]["jobs"] = ["missing-job"]
  manifest = tmp_path / "ci_lane_manifest.json"
  manifest.write_text(json.dumps(payload), encoding="utf-8")

  with pytest.raises(audit_ci_lanes.CiLaneAuditError, match="missing jobs"):
    audit_ci_lanes.build_report(root=REPO_ROOT, manifest_path=manifest)
