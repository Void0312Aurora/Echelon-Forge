from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.source_governance import admission_audit as audit


def _write(path: Path, text: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding="utf-8")


def _minimal_ledger() -> str:
  return """# Source Ledger

状态：candidate / non-authoritative。包含 source_ref、发布方、权利、scope、交叉验证、residual 和 authority 边界。

| source_id | source_ref | 发布方 | 权利 | scope | 交叉验证 | residual | admission / authority |
|---|---|---|---|---|---|---|---|
| `A2-TEST-001` | https://example.invalid/report.pdf | Public holder | public; cite only | method-only / partial | cross-check pending | residual open | candidate / non-authoritative |
"""


def test_source_admission_audit_current_docs_have_no_error_level_gaps() -> None:
  result = audit.audit_a2_source_admission(audit.REPO_ROOT)

  assert result.checked_ledgers >= 9
  assert result.checked_candidate_docs >= 9
  assert result.checked_calibration_docs >= 6
  assert not [issue for issue in result.issues if issue.severity == "error"]
  assert not [issue for issue in result.issues if issue.severity == "warning"]


def test_source_admission_audit_rejects_candidate_manifest_authority_grants(
  tmp_path: Path,
) -> None:
  _write(
    tmp_path
    / "docs/task/air_combat/a2_high_fidelity_damage_model/data_collection/example/source_ledger.zh.md",
    _minimal_ledger(),
  )
  _write(
    tmp_path
    / (
      "docs/task/air_combat/a2_high_fidelity_damage_model/calibration/"
      "bad_candidate/validation_manifest_bad.zh.md"
    ),
    """# Bad Candidate Manifest

状态：candidate / non-authoritative。

| field | value |
|---|---|
| `validation_status` | `passed` |
| `validation_artifact_sha256` | `abc123` |
| `effect_scale_authority` | `true` |
""",
  )

  result = audit.audit_a2_source_admission(tmp_path)
  codes = {issue.code for issue in result.issues}

  assert "calibration-doc-status-passed" in codes
  assert "calibration-doc-authority-true" in codes


def test_source_admission_audit_warns_on_unpinned_source_rows(tmp_path: Path) -> None:
  _write(
    tmp_path
    / "docs/task/air_combat/a2_high_fidelity_damage_model/data_collection/example/source_ledger.zh.md",
    """# Source Ledger

状态：candidate / non-authoritative。包含 source_ref、发布方、权利、scope、交叉验证、residual 和 authority 边界。

| source_id | source_ref | 发布方 | 权利 | scope | 交叉验证 | residual | admission / authority |
|---|---|---|---|---|---|---|---|
| `A2-TEST-002` | title only, no stable handle | Public holder | public | method-only | cross-check pending | residual open | candidate / non-authoritative |
""",
  )

  result = audit.audit_a2_source_admission(tmp_path)
  assert any(issue.code == "ledger-row-unstable-source-ref" for issue in result.issues)


def test_source_admission_audit_checks_candidate_update_docs(tmp_path: Path) -> None:
  _write(
    tmp_path
    / "docs/task/air_combat/a2_high_fidelity_damage_model/data_collection/example/source_ledger.zh.md",
    _minimal_ledger(),
  )
  _write(
    tmp_path
    / (
      "docs/task/air_combat/a2_high_fidelity_damage_model/data_collection/example/"
      "source_pin_update_bad_20260528.zh.md"
    ),
    """# Bad Candidate Update

| field | value |
|---|---|
| `source_ref` | https://example.invalid/public-report.pdf |
| `validation_status` | `passed` |
| `pk_authority` | `true` |
""",
  )

  result = audit.audit_a2_source_admission(tmp_path)
  codes = {issue.code for issue in result.issues}

  assert result.checked_candidate_docs == 1
  assert "candidate-doc-missing-non-authority" in codes
  assert "candidate-doc-status-passed" in codes
  assert "candidate-doc-authority-true" in codes


def test_source_admission_audit_requires_reasonableness_for_community_updates(
  tmp_path: Path,
) -> None:
  _write(
    tmp_path
    / "docs/task/air_combat/a2_high_fidelity_damage_model/data_collection/example/source_ledger.zh.md",
    _minimal_ledger(),
  )
  _write(
    tmp_path
    / (
      "docs/task/air_combat/a2_high_fidelity_damage_model/data_collection/example/"
      "source_pin_update_third_party_community_20260528.zh.md"
    ),
    """# Third Party Candidate Update

状态：community input / non-authoritative。

| source_id | source_ref | role |
|---|---|---|
| `A2-TEST-COMM-001` | https://example.invalid/community-data | community data |
""",
  )

  result = audit.audit_a2_source_admission(tmp_path)

  assert any(
    issue.code == "candidate-doc-missing-third-party-label"
    for issue in result.issues
  )
  assert any(
    issue.code == "candidate-doc-missing-third-party-reasonableness"
    for issue in result.issues
  )
