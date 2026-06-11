from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import wp_doc_closure_audit as audit


def _write(path: Path, text: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding="utf-8")


def test_wp_doc_closure_audit_accepts_current_wp9_package() -> None:
  result = audit.audit_wp(audit.REPO_ROOT, "WP9")

  assert result.folder == "docs/task/simulation_architecture/archive/wp9_contract_infrastructure_closure"
  assert result.acceptance_reviews
  assert not [issue for issue in result.issues if issue.severity == "error"]


def test_wp_doc_closure_audit_reports_required_peer_and_index_gaps(tmp_path: Path) -> None:
  _write(
    tmp_path / "docs/task/simulation_architecture/README.md",
    "# Simulation Architecture\n\nWP10\n",
  )
  _write(
    tmp_path / "docs/task/simulation_architecture/README.zh.md",
    "# 仿真架构\n\nWP10\n",
  )
  _write(
    tmp_path
    / "docs/task/simulation_architecture/wp10_example/example_wp10_20260520.md",
    "# WP10 Example\n\n[missing](missing.md)\n",
  )
  _write(
    tmp_path / "docs/task/review/README.md",
    "# Review\n",
  )
  _write(
    tmp_path / "docs/task/review/README.zh.md",
    "# 审查\n",
  )
  _write(
    tmp_path / "docs/task/review/wp10_example_acceptance_review_20260520.md",
    "# WP10 Example Acceptance\n",
  )

  result = audit.audit_wp(tmp_path, "WP10")
  codes = {issue.code for issue in result.issues}

  assert "missing-required-zh-peer" in codes
  assert "missing-acceptance-zh-peer" in codes
  assert "review-index-missing-acceptance" in codes
  assert "broken-markdown-link" in codes


def test_wp_doc_closure_audit_normalizes_decimal_wp_labels() -> None:
  assert audit.normalize_wp_key("WP2.5") == "wp25"
  assert audit.normalize_wp_key("wp7_5") == "wp75"
  assert audit.display_wp("wp25") == "WP2.5"
  assert audit.display_wp("wp9") == "WP9"


def test_wp_doc_closure_audit_builds_stable_wp16_summary() -> None:
  result = audit.audit_wp(audit.REPO_ROOT, "WP16")
  summary = audit.build_wp_closure_summary(audit.REPO_ROOT, result)

  assert summary.primary_task_doc == (
    "docs/task/simulation_architecture/archive/wp16_runtime_spine_consolidation/"
    "runtime_spine_consolidation_wp16_20260521.md"
  )
  assert summary.task_status == "2026-05-21 complete / accepted runtime-spine consolidation."
  assert summary.planned_stage is False
  assert summary.task_docs_count >= 15
  assert summary.canonical_task_docs_count >= 8
  assert summary.acceptance_reviews_count == 1
  assert summary.missing_acceptance_review_expected is False
  assert summary.required_zh_peer_status.required_total == 8
  assert summary.required_zh_peer_status.required_missing == 0
  assert summary.required_zh_peer_status.all_present is True
  assert len(summary.readme_index_mentions) == 4
  assert summary.authority_boundary == "generated-summary-hint-only"
  assert summary.canonical_authority == "human-reviewed acceptance review"
  assert "Do not treat the current summary as an acceptance decision." in summary.checklist
  assert "Never mark the WP accepted from generated output alone." in summary.checklist


def test_wp_doc_closure_audit_summary_command_is_read_only_and_stable() -> None:
  text_buffer = io.StringIO()
  json_buffer = io.StringIO()

  with redirect_stdout(text_buffer):
    exit_code_text = audit.main(["--repo-root", str(audit.REPO_ROOT), "--wp", "WP16", "--summary"])
  with redirect_stdout(json_buffer):
    exit_code_json = audit.main(["--repo-root", str(audit.REPO_ROOT), "--wp", "WP16", "--summary", "--json"])

  text_output = text_buffer.getvalue()
  json_output = json_buffer.getvalue()
  payload = json.loads(json_output)

  assert exit_code_text == 0
  assert exit_code_json == 0
  assert "## WP16 Closure Summary" in text_output
  assert "missing acceptance review expected: no" in text_output
  assert (
    "authority: generated-summary-hint-only; canonical acceptance remains the human-reviewed acceptance review."
    in text_output
  )
  assert "docs/task/review/archive/wp-acceptance/README.md: mentioned" in text_output
  assert payload[0]["wp"] == "WP16"
  assert payload[0]["planned_stage"] is False
  assert payload[0]["missing_acceptance_review_expected"] is False
  assert payload[0]["required_zh_peer_status"]["all_present"] is True
  assert payload[0]["checklist"][0].startswith("Generated summary is advisory only")
