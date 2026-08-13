from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.architecture.helpers import ensure_repo_root_on_sys_path
from tests.architecture.damage_model.helpers import (
  EXPECTED_BECO_SHA256,
  EXPECTED_TP20_SHA256,
  EXPECTED_TP21_SHA256,
  HEX64,
  assert_authority_guards_false,
  run_maintenance_cli,
  run_maintenance_cli_in_process,
  walk_payload,
)

ensure_repo_root_on_sys_path()

pytestmark = pytest.mark.governance_audit


@pytest.fixture(scope="module")
def source_payload_pack_bundle(
  tmp_path_factory: pytest.TempPathFactory,
) -> tuple[dict[str, Any], Path]:
  from tools.maintenance.source_governance import payload_pack

  output_dir = tmp_path_factory.mktemp("source_payload_pack")
  artifact = payload_pack.write_source_payload_pack(output_dir=output_dir)
  return artifact, output_dir


@pytest.fixture(scope="module")
def source_rights_policy_bundle(
  tmp_path_factory: pytest.TempPathFactory,
) -> tuple[dict[str, Any], Path]:
  from tools.maintenance.source_governance import rights_output_policy as output_policy

  output_dir = tmp_path_factory.mktemp("source_rights_policy")
  artifact = output_policy.write_retained_source_rights_output_policy_gate(
    output_dir=output_dir
  )
  return artifact, output_dir


def test_source_payload_pack_records_partial_current_repo_identity(
  source_payload_pack_bundle: tuple[dict[str, Any], Path],
) -> None:
  artifact, _output_dir = source_payload_pack_bundle
  assert artifact["schema_version"] == "a2.source_payload_pack.v1"
  assert artifact["status"] == "partial_payloads_retained_release_review_blocked"
  assert artifact["residual_gate_results"] == {
    "RES-001": "blocked",
    "RES-002": "blocked",
  }
  assert artifact["res_001_gate_result"]["gate_result"] == "blocked"
  assert artifact["source_payload_pack_decision"][
    "source_payload_pack_closed"
  ] is False
  assert artifact["source_payload_pack_decision"][
    "source_payload_pack_partial"
  ] is True
  assert artifact["source_payload_pack_decision"]["required_payload_count"] == 3
  assert artifact["source_payload_pack_decision"]["retained_payload_count"] == 3
  assert artifact["source_payload_pack_decision"]["missing_payload_count"] == 0
  assert artifact["source_payload_pack_decision"]["all_required_payloads_retained"] is True
  assert artifact["source_payload_pack_decision"]["all_retained_payload_hashes_match"] is True
  assert artifact["source_payload_pack_decision"]["release_grade_rights_reviewed"] is False


def test_source_payload_pack_retains_expected_payload_inventory(
  source_payload_pack_bundle: tuple[dict[str, Any], Path],
) -> None:
  artifact, _output_dir = source_payload_pack_bundle
  retained = artifact["retained_payload_inventory"]
  retained_by_label = {row["source_artifact_label"]: row for row in retained}

  assert list(retained_by_label) == ["TP-20 PDF", "BEC-O-V1.xlsx", "TP-21 PDF"]
  assert retained_by_label["TP-20 PDF"]["actual_sha256"] == EXPECTED_TP20_SHA256
  assert retained_by_label["BEC-O-V1.xlsx"]["actual_sha256"] == EXPECTED_BECO_SHA256
  assert retained_by_label["TP-21 PDF"]["actual_sha256"] == EXPECTED_TP21_SHA256
  assert all(row["hash_matches_expected"] is True for row in retained)
  assert all(
    row["rights_status"]
    == "official_public_candidate_only_rights_not_release_reviewed"
    for row in retained
  )
  assert all(row["benchmark_consumed_for_release"] is False for row in retained)
  assert artifact["missing_payloads"] == []


def test_source_payload_pack_records_rights_and_benchmark_boundaries(
  source_payload_pack_bundle: tuple[dict[str, Any], Path],
) -> None:
  artifact, _output_dir = source_payload_pack_bundle
  policy = artifact["rights_allowed_output_policy_status"]

  assert policy["rights_review_status"] == (
    "public_distribution_statement_supported_candidate_not_signed_off"
  )
  assert policy["rights_release_grade_satisfied"] is False
  assert policy["allowed_output_policy_status"] == (
    "release_candidate_fail_closed_policy_frozen"
  )
  assert policy["allowed_output_policy_frozen"] is True
  assert policy["candidate_public_distribution_supported"] is True
  assert policy["allowed_output_release_grade_satisfied"] is False

  benchmark = artifact["benchmark_consumption_trace"]
  assert benchmark["explicit_non_consumed_artifact_ids"] == [
    "PIN-BFM-001",
    "PIN-BFM-002",
  ]
  assert benchmark["release_consumed_artifact_ids"] == []
  assert benchmark["benchmark_consumption_release_grade_satisfied"] is False

  comparison = artifact["comparison_output_hash_status"]
  assert comparison["comparison_output_hash_status"] == (
    "partial_hash_manifest_present_release_review_blocked"
  )
  assert comparison["selected_beco_cached_output_hash_count"] == 9
  assert len(comparison["selected_comparison_output_hashes"]) == 9
  assert all(
    row["comparison_hash_is_calibration"] is False
    for row in comparison["selected_comparison_output_hashes"]
  )
  assert comparison["benchmark_consumed_for_release"] is False
  assert comparison["comparison_output_release_grade_satisfied"] is False

  assert_authority_guards_false(
    artifact,
    guards_key="non_authoritative_guards",
  )


def test_source_payload_pack_writes_retained_payloads_and_manifest(
  source_payload_pack_bundle: tuple[dict[str, Any], Path],
) -> None:
  from tools.maintenance.source_governance import payload_pack

  _artifact, output_dir = source_payload_pack_bundle
  retained_beco = output_dir / "payloads" / "BEC-O-V1.xlsx"

  assert retained_beco.exists()
  assert payload_pack._sha256_file(retained_beco) == EXPECTED_BECO_SHA256
  retained_tp20 = output_dir / "payloads" / "TP-20.pdf"
  retained_tp21 = output_dir / "payloads" / "TP-21.pdf"
  assert retained_tp20.exists()
  assert retained_tp21.exists()
  assert payload_pack._sha256_file(retained_tp20) == EXPECTED_TP20_SHA256
  assert payload_pack._sha256_file(retained_tp21) == EXPECTED_TP21_SHA256

  source_manifest = json.loads(
    (output_dir / payload_pack.SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME).read_text(
      encoding="utf-8"
    )
  )
  assert source_manifest["schema_version"] == (
    "a2.provenance_identity_retained_source_artifact_pack.v1"
  )
  assert source_manifest["status"] == "partial_payloads_retained_release_review_blocked"
  assert source_manifest["all_payloads_exist"] is True
  assert source_manifest["all_payload_hashes_match"] is True
  assert source_manifest["rights_review_status"] == (
    "public_distribution_statement_supported_candidate_not_signed_off"
  )
  assert source_manifest["allowed_output_policy_status"] == (
    "release_candidate_fail_closed_policy_frozen"
  )
  assert source_manifest["comparison_output_hash_status"] == (
    "partial_hash_manifest_present_release_review_blocked"
  )
  assert_authority_guards_false(
    source_manifest,
    guards_key="non_authoritative_guards",
  )


def test_source_payload_pack_fails_closed_when_payloads_absent(
  monkeypatch,
  tmp_path: Path,
) -> None:
  from tools.maintenance.source_governance import payload_pack

  monkeypatch.setattr(payload_pack, "_discover_payload_candidates", lambda **_: [])

  artifact = payload_pack.generate_source_payload_pack(
    output_dir=tmp_path,
    copy_available_payloads=True,
  )

  assert artifact["status"] == "blocked_missing_required_source_payloads"
  assert artifact["source_payload_pack_decision"]["source_payload_pack_blocked"] is True
  assert artifact["source_payload_pack_decision"]["retained_payload_count"] == 0
  assert artifact["source_payload_pack_decision"]["missing_payload_count"] == 3
  assert artifact["rights_allowed_output_policy_status"]["rights_review_status"] == (
    "missing_payload_rights_review"
  )
  assert "required_source_payloads_missing_or_mismatched" in artifact[
    "res_001_gate_result"
  ]["blocking_conditions"]
  assert artifact["res_001_gate_result"]["gate_result"] == "blocked"
  assert_authority_guards_false(
    artifact,
    guards_key="non_authoritative_guards",
  )


def test_source_payload_pack_rejects_hash_mismatch(tmp_path: Path) -> None:
  from tools.maintenance.source_governance import payload_pack

  wrong_beco = tmp_path / "payloads" / "BEC-O-V1.xlsx"
  wrong_beco.parent.mkdir(parents=True)
  wrong_beco.write_bytes(b"not the retained spreadsheet payload")

  artifact = payload_pack.generate_source_payload_pack(
    output_dir=tmp_path,
    copy_available_payloads=False,
  )

  beco_rows = [
    row
    for row in artifact["all_payload_inventory"]
    if row["source_artifact_label"] == "BEC-O-V1.xlsx"
  ]
  assert len(beco_rows) == 1
  assert beco_rows[0]["payload_exists"] is True
  assert beco_rows[0]["hash_matches_expected"] is False
  assert beco_rows[0]["retained_for_pack"] is False

  missing_beco = [
    row
    for row in artifact["missing_payloads"]
    if row["source_artifact_label"] == "BEC-O-V1.xlsx"
  ]
  assert len(missing_beco) == 1
  assert missing_beco[0]["missing_reason"] == "payload_sha256_mismatch"
  assert artifact["status"] in {
    "blocked_missing_required_source_payloads",
    "partial_non_authoritative_source_payload_pack",
  }
  assert artifact["res_001_gate_result"]["gate_result"] == "blocked"


def test_source_payload_pack_cli_writes_retained_json(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "cli_source_payload_pack.json"
  retained_dir = tmp_path / "retained"
  # Retained end-to-end smoke for the `source-governance` family: the one spawn
  # that still proves the real interpreter entrypoint wiring. See
  # test_cli_spawn_budget.py; the rest of the family runs in-process.
  run_maintenance_cli(
    "damage_model.py source-governance",
    "payload-pack",
    "--write-retained-artifacts",
    "--output-dir",
    retained_dir,
    "--output",
    output_path,
  )

  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["status"] == "partial_payloads_retained_release_review_blocked"
  assert [
    row["source_artifact_label"]
    for row in artifact["retained_payload_inventory"]
  ] == ["TP-20 PDF", "BEC-O-V1.xlsx", "TP-21 PDF"]
  assert artifact["missing_payloads"] == []
  assert artifact["source_artifact_pack_manifest_sha256"]
  assert artifact["retained_manifest_sha256"]
  assert (retained_dir / "source_payload_pack.json").exists()
  assert (retained_dir / "source_artifact_pack_manifest.json").exists()
  assert (retained_dir / "manifest.json").exists()
  assert_authority_guards_false(
    artifact,
    guards_key="non_authoritative_guards",
  )


def test_source_rights_output_policy_records_blocked_release_candidate_identity(
  source_rights_policy_bundle: tuple[dict[str, Any], Path],
) -> None:
  artifact, _output_dir = source_rights_policy_bundle
  assert artifact["schema_version"] == "a2.source_rights_output_policy_gate.v1"
  assert artifact["status"] == (
    "blocked_release_candidate_rights_supported_policy_fail_closed"
  )
  assert artifact["review_target"] == (
    "res_001_source_rights_review_allowed_output_policy"
  )

  result = artifact["res_001_gate_result"]
  assert result["gate_result"] == "blocked"
  assert result["release_grade_satisfied"] is False
  assert result["payload_retention_complete"] is True
  assert result["payload_hashes_match"] is True
  assert result["rights_supported_by_public_distribution_statement"] is True
  assert result["release_grade_rights_reviewed"] is False
  assert result["allowed_output_policy_frozen"] is True
  assert result["allowed_output_policy_release_grade_satisfied"] is False
  assert result["comparison_outputs_admitted"] is False
  assert result["benchmark_consumption_release_grade_satisfied"] is False
  assert result["blocking_conditions"] == [
    "independent_rights_reviewer_signoff_missing",
    "allowed_output_policy_release_grade_signoff_missing",
    "selected_comparison_output_hash_manifest_missing",
    "benchmark_consumption_release_signoff_missing",
    "authority_boundary_signoff_missing",
  ]


def test_source_rights_output_policy_freezes_allowed_output_policy(
  source_rights_policy_bundle: tuple[dict[str, Any], Path],
) -> None:
  artifact, _output_dir = source_rights_policy_bundle
  policy = artifact["allowed_output_policy"]

  assert policy["policy_status"] == "release_candidate_fail_closed_policy_frozen"
  assert policy["policy_frozen_by_this_gate"] is True
  assert policy["release_grade_satisfied"] is False
  assert policy["current_selected_comparison_output_hashes"] == []
  assert "retained_payload_file_sha256" in policy["allowed_hash_outputs"]
  assert "future_selected_comparison_output_sha256_only_after_reviewer_admission" in (
    policy["allowed_hash_outputs"]
  )
  assert "spreadsheet_tool_output_tables" in policy["forbidden_copy_outputs"]
  assert "comparison_outputs_without_selected_sha256_and_signoff" in policy[
    "forbidden_consume_outputs"
  ]


def test_source_rights_output_policy_retains_payload_rights_inventory(
  source_rights_policy_bundle: tuple[dict[str, Any], Path],
) -> None:
  artifact, _output_dir = source_rights_policy_bundle
  by_label = {
    row["source_artifact_label"]: row
    for row in artifact["payload_rights_inventory"]
  }

  assert list(by_label) == ["TP-20 PDF", "BEC-O-V1.xlsx", "TP-21 PDF"]
  assert by_label["TP-20 PDF"]["actual_sha256"] == EXPECTED_TP20_SHA256
  assert by_label["BEC-O-V1.xlsx"]["actual_sha256"] == EXPECTED_BECO_SHA256
  assert by_label["TP-21 PDF"]["actual_sha256"] == EXPECTED_TP21_SHA256

  assert all(row["payload_exists"] for row in by_label.values())
  assert all(row["hash_matches_expected"] for row in by_label.values())
  assert all(
    row["payload_retention_status"] == "retained_hash_matched"
    for row in by_label.values()
  )
  assert all(
    row["rights_status"]
    == "public_distribution_statement_supported_rights_review_candidate"
    for row in by_label.values()
  )
  assert all(
    row["rights_supported_by_public_distribution_statement"]
    for row in by_label.values()
  )
  assert all(row["rights_release_grade_satisfied"] is False for row in by_label.values())
  assert all(row["release_consumption_allowed"] is False for row in by_label.values())
  assert all(
    row["benchmark_consumed_for_release"] is False for row in by_label.values()
  )

  assert by_label["TP-20 PDF"]["rights_statement_evidence"]["statement_id"] == (
    "distribution_statement_a_public_release_unlimited"
  )
  assert by_label["BEC-O-V1.xlsx"]["rights_statement_evidence"]["statement_id"] == (
    "distribution_statement_a_public_release_unlimited"
  )
  assert by_label["TP-21 PDF"]["rights_statement_evidence"]["statement_id"] == (
    "public_release_distribution_unlimited"
  )
  assert by_label["BEC-O-V1.xlsx"]["output_policy"][
    "benchmark_consumption_allowed"
  ] is False
  assert "spreadsheet_formulas" in by_label["BEC-O-V1.xlsx"]["output_policy"][
    "copy_forbidden_outputs"
  ]


def test_source_rights_output_policy_lists_required_release_signoffs(
  source_rights_policy_bundle: tuple[dict[str, Any], Path],
) -> None:
  artifact, _output_dir = source_rights_policy_bundle
  signoff_fields = [
    row["field"] for row in artifact["required_release_signoff_fields"]
  ]

  assert signoff_fields == [
    "rights_reviewer_identity",
    "rights_review_decision",
    "allowed_output_policy_reviewer_identity",
    "allowed_output_policy_release_grade_status",
    "selected_comparison_output_hash_manifest_sha256",
    "benchmark_consumption_signoff",
    "authority_boundary_signoff",
  ]
  assert_authority_guards_false(
    artifact,
    guards_key="non_authoritative_guards",
  )


def test_source_rights_output_policy_writes_retained_manifest(
  source_rights_policy_bundle: tuple[dict[str, Any], Path],
) -> None:
  from tools.maintenance.source_governance import rights_output_policy as output_policy

  _artifact, output_dir = source_rights_policy_bundle
  manifest = json.loads(
    (output_dir / output_policy.RETAINED_MANIFEST_FILENAME).read_text()
  )

  assert manifest["schema_version"] == (
    "a2.source_rights_output_policy_retained_manifest.v1"
  )
  assert manifest["res_001_gate_result"]["gate_result"] == "blocked"
  assert len(manifest["source_rights_output_policy_gate"]["sha256"]) == 64
  assert_authority_guards_false(
    manifest,
    guards_key="non_authoritative_guards",
  )


def test_source_rights_output_policy_fails_closed_without_public_statement(
  monkeypatch,
) -> None:
  from tools.maintenance.source_governance import rights_output_policy as output_policy

  def no_statement(path: Path, content_type: str) -> dict[str, object]:
    return {
      "extraction_status": "test_no_statement",
      "statement_locator": "test",
      "statement_detected": False,
      "statement_id": "",
      "has_distribution_statement_a_label": False,
      "has_public_release_phrase": False,
      "has_unlimited_distribution_phrase": False,
    }

  monkeypatch.setattr(output_policy, "_extract_rights_evidence", no_statement)

  artifact = output_policy.generate_source_rights_output_policy_gate()

  assert artifact["status"] == (
    "blocked_public_distribution_statement_support_incomplete_fail_closed"
  )
  result = artifact["res_001_gate_result"]
  assert result["payload_retention_complete"] is True
  assert result["rights_supported_by_public_distribution_statement"] is False
  assert "public_distribution_statement_evidence_missing" in result[
    "blocking_conditions"
  ]
  assert all(
    row["rights_status"]
    == "rights_review_public_distribution_statement_not_supported_fail_closed"
    for row in artifact["payload_rights_inventory"]
  )
  assert_authority_guards_false(
    artifact,
    guards_key="non_authoritative_guards",
  )


def test_source_rights_output_policy_fails_closed_for_hash_mismatch(
  tmp_path: Path,
) -> None:
  from tools.maintenance.source_governance import rights_output_policy as output_policy

  bad_payload = tmp_path / "bad.pdf"
  bad_payload.write_bytes(b"not the retained source payload")
  source_manifest = {
    "package_id": output_policy.PACKAGE_ID,
    "schema_version": output_policy.SOURCE_ARTIFACT_PACK_SCHEMA_VERSION,
    "status": "test_manifest",
    "artifacts": [
      {
        "requirement_id": "PIN-BFM-TEST:bad",
        "artifact_id": "PIN-BFM-TEST",
        "source_id": "VPS-BFM-TEST",
        "source_artifact_label": "TP-20 PDF",
        "relative_path": str(bad_payload),
        "sha256": EXPECTED_TP20_SHA256,
        "benchmark_consumption_status": "not_consumed_for_stage_b_release",
      }
    ],
  }
  source_manifest_path = tmp_path / "source_artifact_pack_manifest.json"
  source_manifest_path.write_text(json.dumps(source_manifest), encoding="utf-8")

  artifact = output_policy.generate_source_rights_output_policy_gate(
    source_manifest_path=source_manifest_path,
    output_dir=tmp_path / "out",
  )

  assert artifact["status"] == "blocked_payload_retention_incomplete_fail_closed"
  result = artifact["res_001_gate_result"]
  assert result["payload_retention_complete"] is False
  assert result["payload_hashes_match"] is False
  assert result["rights_supported_by_public_distribution_statement"] is False
  assert "payload_retention_missing_or_hash_mismatch" in result[
    "blocking_conditions"
  ]
  row = artifact["payload_rights_inventory"][0]
  assert row["payload_exists"] is True
  assert row["hash_matches_expected"] is False
  assert row["payload_retention_status"] == "missing_or_hash_mismatch"
  assert row["rights_statement_evidence"]["extraction_status"] == (
    "payload_missing_or_hash_mismatch_fail_closed"
  )
  assert_authority_guards_false(
    artifact,
    guards_key="non_authoritative_guards",
  )


def test_source_rights_output_policy_cli_writes_json(
  tmp_path: Path,
) -> None:
  from tools.maintenance.source_governance import rights_output_policy as output_policy

  output_path = tmp_path / "source_rights_output_policy_gate.json"
  retained_dir = tmp_path / "retained"
  run_maintenance_cli_in_process(
    "damage_model.py source-governance",
    "rights-output-policy",
    "--write-retained-artifacts",
    "--output-dir",
    retained_dir,
    "--output",
    output_path,
  )

  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["status"] == (
    "blocked_release_candidate_rights_supported_policy_fail_closed"
  )
  assert artifact["res_001_gate_result"]["gate_result"] == "blocked"
  assert artifact["source_rights_output_policy_gate_sha256"]
  assert artifact["retained_manifest_sha256"]
  assert (retained_dir / output_policy.RIGHTS_POLICY_ARTIFACT_FILENAME).exists()
  assert (retained_dir / output_policy.RETAINED_MANIFEST_FILENAME).exists()
  assert_authority_guards_false(
    artifact,
    guards_key="non_authoritative_guards",
  )
