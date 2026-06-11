from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tests.architecture.helpers import (
    PYTHON_EXECUTABLE,
    REPO_ROOT,
    ensure_repo_root_on_sys_path,
)
from tests.architecture.damage_model.helpers import (
    EXPECTED_BECO_SHA256,
    EXPECTED_TP20_SHA256,
    EXPECTED_TP21_SHA256,
    HEX64,
    assert_authority_guards_false,
    walk_payload,
)

ensure_repo_root_on_sys_path()

from tools.maintenance.source_governance import (  # noqa: E402
    payload_pack,
    rights_output_policy as output_policy,
)
from tools.maintenance.external_signoff_evidence import (  # noqa: E402
    signoff_request as signoff_request_packet,
)
from tools.maintenance.retained_artifacts import manifest_integrity as integrity  # noqa: E402


def test_source_payload_pack_current_repo_is_partial(tmp_path: Path) -> None:
    artifact = payload_pack.write_source_payload_pack(output_dir=tmp_path)

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

    retained_beco = tmp_path / "payloads" / "BEC-O-V1.xlsx"
    assert retained_beco.exists()
    assert payload_pack._sha256_file(retained_beco) == EXPECTED_BECO_SHA256
    retained_tp20 = tmp_path / "payloads" / "TP-20.pdf"
    retained_tp21 = tmp_path / "payloads" / "TP-21.pdf"
    assert retained_tp20.exists()
    assert retained_tp21.exists()
    assert payload_pack._sha256_file(retained_tp20) == EXPECTED_TP20_SHA256
    assert payload_pack._sha256_file(retained_tp21) == EXPECTED_TP21_SHA256

    source_manifest = json.loads(
        (tmp_path / payload_pack.SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME).read_text(
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
    subprocess.run(
        [
            PYTHON_EXECUTABLE,
            "tools/maintenance/damage_model_source_governance.py",
            "payload-pack",
            "--write-retained-artifacts",
            "--output-dir",
            str(retained_dir),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
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


def test_source_rights_output_policy_current_repo_is_blocked_release_candidate(tmp_path: Path) -> None:
    artifact = output_policy.write_retained_source_rights_output_policy_gate(
        output_dir=tmp_path
    )

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

    manifest = json.loads(
        (tmp_path / output_policy.RETAINED_MANIFEST_FILENAME).read_text()
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
    output_path = tmp_path / "source_rights_output_policy_gate.json"
    retained_dir = tmp_path / "retained"
    subprocess.run(
        [
            PYTHON_EXECUTABLE,
            "tools/maintenance/damage_model_source_governance.py",
            "rights-output-policy",
            "--write-retained-artifacts",
            "--output-dir",
            str(retained_dir),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
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



# Source-rights signoff request is part of source evidence governance.
def test_source_rights_signoff_request_is_fail_closed_checklist() -> None:
    artifact = signoff_request_packet.generate_source_rights_signoff_request_packet()

    assert artifact["schema_version"] == "a2.source_rights_signoff_request_packet.v1"
    assert artifact["request_id"] == (
        "TC-A2-BF-003-RIGHTS-SIGNOFF-REQUEST-20260601"
    )
    assert artifact["status"] == (
        "retained_fail_closed_source_rights_signoff_request_packet"
    )
    assert artifact["packet_type"] == (
        "source_rights_allowed_output_signoff_request_checklist"
    )
    assert artifact["approval_granted"] is False
    assert artifact["release_grade_satisfied"] is False
    assert artifact["admission_granted"] is False
    assert artifact["fail_closed"] is True

    policy = artifact["current_policy_status"]
    assert policy["status"] == (
        "blocked_release_candidate_rights_supported_policy_fail_closed"
    )
    assert policy["policy_status"] == "release_candidate_fail_closed_policy_frozen"
    assert policy["fail_closed"] is True
    assert policy["approval_granted"] is False
    assert policy["release_grade_satisfied"] is False
    assert policy["source_gate_release_grade_satisfied"] is False
    assert policy["allowed_output_policy_release_grade_satisfied"] is False
    assert policy["comparison_outputs_admitted"] is False
    assert policy["benchmark_consumption_release_grade_satisfied"] is False
    assert policy["current_selected_comparison_output_hash_count"] == 0

    assert_authority_guards_false(artifact)
    assert artifact["authority_guards"]["source_truth_authority_granted"] is False
    assert artifact["authority_guards"]["allowed_output_release_authority_granted"] is False
    assert artifact["authority_guards"]["runtime_authority_granted"] is False
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["fuze_authority_granted"] is False


def test_source_rights_signoff_request_records_input_refs_with_hashes() -> None:
    artifact = signoff_request_packet.generate_source_rights_signoff_request_packet()
    refs = {row["artifact_key"]: row for row in artifact["input_refs"]}

    assert set(refs) == {
        "source_rights_output_policy_gate",
        "source_payload_pack_manifest",
        "res005_tp21_selected_case_admission_review_gate",
        "res006_beco_replacement_tolerance_admission_gate",
    }
    assert refs["source_rights_output_policy_gate"]["required_for_request_packet"] is True
    assert refs["source_payload_pack_manifest"]["required_for_request_packet"] is True
    assert refs["source_rights_output_policy_gate"]["present"] is True
    assert refs["source_payload_pack_manifest"]["present"] is True
    assert HEX64.fullmatch(refs["source_rights_output_policy_gate"]["sha256"])
    assert HEX64.fullmatch(refs["source_payload_pack_manifest"]["sha256"])
    assert refs["source_rights_output_policy_gate"]["schema_version"] == (
        "a2.source_rights_output_policy_gate.v1"
    )
    assert refs["source_payload_pack_manifest"]["schema_version"] == (
        "a2.provenance_identity_retained_source_artifact_pack.v1"
    )

    for key in (
        "res005_tp21_selected_case_admission_review_gate",
        "res006_beco_replacement_tolerance_admission_gate",
    ):
        assert refs[key]["required_for_request_packet"] is False
        if refs[key]["present"]:
            assert HEX64.fullmatch(refs[key]["sha256"])
        else:
            assert refs[key]["status"] == "missing_optional_fail_closed"


def test_source_rights_signoff_request_identifies_hash_only_review_items() -> None:
    artifact = signoff_request_packet.generate_source_rights_signoff_request_packet()
    items = {row["item_id"]: row for row in artifact["requested_hash_only_review_items"]}

    assert set(items) == {
        "RES-005-RETAINED-PAYLOAD-SHA256",
        "RES-006-RETAINED-PAYLOAD-SHA256",
        "RES-005-TP21-SELECTED-CASE-HASH-ONLY-OUTPUTS",
        "RES-006-BECO-HASH-ONLY-OUTPUTS",
    }

    tp21_payload = items["RES-005-RETAINED-PAYLOAD-SHA256"]
    assert tp21_payload["request_review_allowed"] is True
    assert HEX64.fullmatch(tp21_payload["hash_only_outputs"]["payload_sha256"])
    assert tp21_payload["approval_granted"] is False

    tp21 = items["RES-005-TP21-SELECTED-CASE-HASH-ONLY-OUTPUTS"]
    assert tp21["request_review_allowed"] is False
    assert tp21["request_review_status"] == (
        "blocked_missing_selected_case_hash_inputs_fail_closed"
    )
    assert tp21["hash_only_outputs"]["selected_debris_output_hash_count"] == 0
    assert tp21["hash_only_outputs"]["selected_output_preimage_sha256_present"] is False
    assert HEX64.fullmatch(tp21["hash_only_outputs"]["payload_sha256"])
    assert HEX64.fullmatch(
        tp21["hash_only_outputs"]["controlled_criteria_vocabulary_sha256"]
    )
    assert HEX64.fullmatch(tp21["hash_only_outputs"]["selected_debris_output_set_sha256"])
    assert tp21["raw_selected_outputs_retained"] is False
    assert tp21["raw_source_content_retained"] is False

    beco = items["RES-006-BECO-HASH-ONLY-OUTPUTS"]
    assert beco["request_review_allowed"] is True
    assert beco["request_review_status"] == (
        "requestable_for_allowed_output_and_replacement_review_not_admitted"
    )
    hashes = beco["hash_only_outputs"]
    assert hashes["comparison_row_count"] == 9
    assert hashes["cached_anchor_count"] == 9
    assert hashes["recalculated_anchor_count"] == 9
    assert hashes["mismatch_count"] == 9
    assert hashes["exact_hash_check_passed"] is False
    assert HEX64.fullmatch(hashes["cached_selected_output_set_sha256"])
    assert HEX64.fullmatch(hashes["recalculated_selected_output_set_sha256"])
    assert len(hashes["rows"]) == 9
    for row in hashes["rows"]:
        assert HEX64.fullmatch(row["cached_anchor_sha256"])
        assert HEX64.fullmatch(row["recalculated_output_sha256"])
        assert HEX64.fullmatch(row["formula_sha256"])
        assert row["raw_value_disclosed"] is False
        assert row["formula_text_disclosed"] is False
    assert beco["approval_granted"] is False


def test_source_rights_signoff_request_names_signoffs_and_forbidden_outputs() -> None:
    artifact = signoff_request_packet.generate_source_rights_signoff_request_packet()

    signoff_ids = [row["signoff_id"] for row in artifact["requested_signoff_items"]]
    assert signoff_ids == [
        "source_rights_independent_review",
        "allowed_output_policy_release_grade_review",
        "tp21_selected_case_hash_only_allowed_output_review",
        "beco_hash_only_allowed_output_review",
        "beco_lineage_tolerance_and_replacement_review",
        "benchmark_consumption_release_decision",
        "authority_boundary_confirmation",
    ]
    assert all(row["current_status"] == "missing_fail_closed" for row in artifact["requested_signoff_items"])
    assert all(row["approval_granted"] is False for row in artifact["requested_signoff_items"])
    assert len(artifact["current_missing_items"]) == len(signoff_ids)

    forbidden = {row["output_id"]: row for row in artifact["explicit_forbidden_outputs"]}
    assert "source_payload_body_or_bulk_content" in forbidden
    assert "spreadsheet_formulas_or_cell_ranges" in forbidden
    assert "tp21_source_prose_tables_figures_or_numeric_values" in forbidden
    assert "beco_raw_cell_values_or_tool_output_tables" in forbidden
    assert "beco_temporary_workbook_copy_stdout_or_stderr" in forbidden
    assert all(row["requestable"] is False for row in forbidden.values())
    assert all(row["approval_granted"] is False for row in forbidden.values())

    shape = artifact["hash_only_allowed_request_shape"]
    assert shape["request_may_reference_prior_retained_json_only"] is True
    assert "comparison_output_sha256" in shape["allowed_retained_fields"]
    assert "recalculated_output_sha256" in shape["allowed_retained_fields"]
    assert "source numeric values" in shape["required_absences"]
    assert "spreadsheet formulas" in shape["required_absences"]
    assert shape["approval_granted"] is False
    assert shape["release_grade_satisfied"] is False


def test_source_rights_signoff_request_retains_no_raw_source_or_output_keys() -> None:
    artifact = signoff_request_packet.generate_source_rights_signoff_request_packet()

    forbidden_raw_keys = {
        "cell",
        "sheet",
        "formula",
        "raw_value",
        "raw_output_value",
        "raw_output_table",
        "source_table_payload",
        "source_table_rows",
        "selected_output_preimage",
        "stdout",
        "stderr",
        "temporary_workbook_copy",
    }
    for value in walk_payload(artifact):
        if isinstance(value, dict):
            assert not (forbidden_raw_keys & set(value))

    serialized = json.dumps(artifact, ensure_ascii=False)
    assert "extracted_text" not in serialized
    assert "raw_output_value" not in serialized
    assert "selected_output_raw_value" not in serialized
    assert "spreadsheet_tool_output_tables" in serialized


def test_source_rights_signoff_request_tolerates_missing_optional_packets(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.json"

    artifact = signoff_request_packet.generate_source_rights_signoff_request_packet(
        retained_dir=tmp_path / "retained",
        res005_selected_case_gate_path=missing,
        res006_replacement_tolerance_gate_path=missing,
    )
    refs = {row["artifact_key"]: row for row in artifact["input_refs"]}
    items = {row["item_id"]: row for row in artifact["requested_hash_only_review_items"]}

    assert artifact["status"] == (
        "retained_fail_closed_source_rights_signoff_request_packet"
    )
    assert refs["res005_tp21_selected_case_admission_review_gate"]["present"] is False
    assert refs["res006_beco_replacement_tolerance_admission_gate"]["present"] is False
    assert items["RES-005-TP21-SELECTED-CASE-HASH-ONLY-OUTPUTS"][
        "request_review_status"
    ] == "res005_selected_case_packet_missing_fail_closed"
    assert items["RES-006-BECO-HASH-ONLY-OUTPUTS"]["hash_only_outputs"]["rows"] == []
    assert items["RES-006-BECO-HASH-ONLY-OUTPUTS"]["request_review_allowed"] is False
    assert artifact["approval_granted"] is False
    assert artifact["authority_guards_all_false"] is True


def test_source_rights_signoff_request_cli_writes_manifest_integrity_clean(
    tmp_path: Path,
) -> None:
    retained_dir = tmp_path / "retained"
    output_path = tmp_path / "packet_cli.json"

    result = subprocess.run(
        [
            PYTHON_EXECUTABLE,
            "tools/maintenance/damage_model_external_evidence.py",
            "signoff-request",
            "--retained-dir",
            str(retained_dir),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert result.stdout == ""
    output_packet = json.loads(output_path.read_text(encoding="utf-8"))
    assert HEX64.fullmatch(output_packet["retained_artifact_sha256"])
    assert HEX64.fullmatch(output_packet["retained_manifest_sha256"])

    packet_path = retained_dir / "source_rights_signoff_request_packet.json"
    manifest_path = retained_dir / "manifest.json"
    assert packet_path.is_file()
    assert manifest_path.is_file()

    retained_packet = json.loads(packet_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert retained_packet["schema_version"] == (
        "a2.source_rights_signoff_request_packet.v1"
    )
    assert manifest["schema_version"] == (
        "a2.source_rights_signoff_request_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "retained_fail_closed_source_rights_signoff_request_packet"
    )
    assert manifest["approval_granted"] is False
    assert manifest["release_grade_satisfied"] is False
    assert manifest["fail_closed"] is True
    assert manifest["requested_signoff_item_count"] == 7
    assert manifest["requested_hash_only_review_item_count"] == 4
    assert_authority_guards_false(manifest)
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])

    summary = integrity.check_retained_manifest_integrity(
        manifest_paths=[manifest_path]
    )
    assert summary["missing_total"] == 0
    assert summary["sha_mismatch_total"] == 0
    assert summary["guard_true_total"] == 0
