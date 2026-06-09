from __future__ import annotations

import json
from pathlib import Path

from tests.architecture.damage_model.helpers import (
    assert_authority_guards_false,
    assert_hex64,
    assert_no_keys_anywhere,
    assert_retained_manifest_clean,
    run_maintenance_cli,
)
from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path, read_json

ensure_repo_root_on_sys_path()

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_res005_tp21_debris_admission_gate as debris_gate,
    a2_blastfrag_res005_tp21_selected_case_admission_gate as selected_case_gate,
    a2_blastfrag_res005_tp21_selected_case_candidate_packet as candidate_packet,
)
from tools.maintenance import a2_retained_manifest_integrity as integrity  # noqa: E402


def test_selected_output_admission_fails_closed_without_selected_case() -> None:
    artifact = debris_gate.generate_tp21_debris_admission_gate()

    assert artifact["schema_version"] == "a2.res005_tp21_debris_admission_gate.v1"
    assert artifact["status"] == "blocked_fail_closed_tp21_debris_admission_gate"
    assert artifact["residual_id"] == "RES-005"

    decision = artifact["admission_decision"]
    assert decision["decision"] == "not_admitted_fail_closed"
    assert decision["narrowly_closes_res005"] is False
    assert decision["closed_residual_ids_by_this_gate"] == []
    assert decision["closed_residual_subscopes_by_this_gate"] == []
    assert decision["benchmark_consumed_for_release"] is False
    assert decision["release_grade_validated"] is False
    assert len(decision["exact_blockers"]) == 4
    assert "page/section provenance labels" in decision["exact_blockers"][0]
    assert "selected output preimage hash" in decision["exact_blockers"][1]
    assert "reviewer signoff" in decision["exact_blockers"][2]
    assert "allowed-output policy" in decision["exact_blockers"][3]


def test_selected_output_anchor_set_is_hash_only_and_no_raw_source_payload() -> None:
    artifact = debris_gate.generate_tp21_debris_admission_gate()
    anchor_set = artifact["selected_debris_output_anchor_set"]

    assert_hex64(anchor_set["source_artifact_sha256"])
    assert_hex64(anchor_set["controlled_criteria_vocabulary_sha256"])
    assert_hex64(anchor_set["source_rights_policy_sha256"])
    assert_hex64(anchor_set["selected_debris_output_set_sha256"])
    assert anchor_set["selected_debris_output_hashes"] == []
    assert anchor_set["selected_debris_output_hash_count"] == 0
    assert anchor_set["selected_output_preimages_retained"] is False
    assert anchor_set["raw_tp21_source_content_retained"] is False
    assert anchor_set["source_tables_retained"] is False
    assert anchor_set["source_figures_retained"] is False
    assert anchor_set["source_numeric_values_retained"] is False
    assert anchor_set["benchmark_consumed_for_release"] is False

    reviewer_case = artifact["reviewer_selected_case_artifact"]
    assert reviewer_case["artifact_status"] == "missing_fail_closed"
    assert reviewer_case["page_section_provenance_labels_present"] is False
    assert reviewer_case["selected_output_preimage_hash_present"] is False
    assert reviewer_case["source_content_copied_to_dataset"] is False
    assert reviewer_case["source_tables_copied_to_dataset"] is False
    assert reviewer_case["source_numeric_values_copied_to_dataset"] is False

    forbidden_keys = {
        "raw_source_text",
        "source_table_payload",
        "source_table_rows",
        "document_numeric_value",
        "tp21_raw_value",
        "selected_output_raw_value",
    }
    assert_no_keys_anywhere(artifact, forbidden_keys)

    serialized = json.dumps(artifact, ensure_ascii=False)
    assert "extracted_text" not in serialized
    assert "source_table_payload" not in serialized
    assert "source_table_rows" not in serialized
    assert "selected_output_raw_value" not in serialized


def test_selected_output_admission_preserves_authority_guards_false() -> None:
    artifact = debris_gate.generate_tp21_debris_admission_gate()

    assert_authority_guards_false(artifact, guards_key="non_authoritative_guards")
    assert artifact["non_authoritative_guards"]["stock_database_authority_granted"] is False
    assert artifact["non_authoritative_guards"]["runtime_authority_granted"] is False
    assert artifact["non_authoritative_guards"]["effect_scale_authority_granted"] is False
    assert artifact["non_authoritative_guards"][
        "component_failure_probability_authority_granted"
    ] is False
    assert artifact["non_authoritative_guards"]["pk_authority_granted"] is False
    assert artifact["non_authoritative_guards"][
        "deterministic_fuze_authority_granted"
    ] is False


def test_selected_output_admission_requirements_are_concrete() -> None:
    artifact = debris_gate.generate_tp21_debris_admission_gate()

    selected_requirements = artifact["selected_output_requirements"]
    provenance_requirements = artifact["page_section_provenance_requirements"]

    assert len(selected_requirements) == 8
    assert all(
        row["current_status"] == "selected_output_preimage_missing"
        for row in selected_requirements
    )
    assert all(
        row["source_content_must_not_be_copied_to_dataset"]
        for row in selected_requirements
    )

    assert [row["label_key"] for row in provenance_requirements] == [
        "tp21_page_locator_label",
        "tp21_section_or_figure_locator_label",
        "reviewer_case_selection_id",
        "selected_output_preimage_sha256",
        "allowed_output_signoff_id",
    ]
    assert provenance_requirements[-1]["current_status"] == (
        "missing_allowed_output_signoff"
    )
    assert all(row["raw_source_content_retained"] is False for row in provenance_requirements)


def test_selected_output_admission_cli_writes_retained_artifacts(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "gate_cli.json"
    retained_dir = tmp_path / "retained"

    result = run_maintenance_cli(
        "a2_blastfrag_res005_tp21_debris_admission_gate.py",
        "--retained-dir",
        retained_dir,
        "--output",
        output_path,
    )

    assert result.stdout == ""
    artifact = read_json(output_path)
    assert artifact["schema_version"] == "a2.res005_tp21_debris_admission_gate.v1"
    assert artifact["retained_artifact_sha256"]
    assert artifact["retained_anchor_set_sha256"]
    assert artifact["retained_manifest_sha256"]

    gate_path = retained_dir / "res005_tp21_debris_admission_gate.json"
    anchor_path = retained_dir / "selected_debris_output_anchor_set.json"
    manifest_path = retained_dir / "manifest.json"
    assert gate_path.exists()
    assert anchor_path.exists()
    assert manifest_path.exists()

    manifest = read_json(manifest_path)
    assert manifest["schema_version"] == (
        "a2.res005_tp21_debris_admission_retained_manifest.v1"
    )
    assert manifest["status"] == "blocked_fail_closed_tp21_debris_admission_gate"
    assert_hex64(
        manifest["res005_tp21_debris_admission_gate_artifact"]["sha256"]
    )
    assert_hex64(
        manifest["selected_debris_output_anchor_set_artifact"]["sha256"]
    )
    assert_authority_guards_false(manifest, guards_key="non_authoritative_guards")


def test_selected_case_admission_review_packet_fails_closed() -> None:
    artifact = selected_case_gate.generate_selected_case_admission_gate()

    assert artifact["schema_version"] == (
        "a2.res005_tp21_selected_case_admission_review_gate.v1"
    )
    assert artifact["schema"]["name"] == "res005_tp21_selected_case_admission_review_gate"
    assert artifact["package"]["task_cluster"] == "TC-A2-BF-003-RES005-TP21"
    assert artifact["residual_id"] == "RES-005"
    assert artifact["status"] == (
        "blocked_fail_closed_tp21_selected_case_admission_review_packet"
    )

    decision = artifact["decision"]
    assert decision["status"] == "blocked"
    assert decision["decision"] == "not_admitted_fail_closed"
    assert decision["fail_closed"] is True
    assert decision["selected_tp21_case_admitted"] is False
    assert decision["narrowly_closes_res005"] is False
    assert decision["closed_residual_ids_by_this_gate"] == []
    assert decision["closed_residual_subscopes_by_this_gate"] == []
    assert decision["residual_status_after_gate"] == (
        "open_fail_closed_tp21_selected_debris_outputs_missing"
    )
    assert decision["benchmark_consumed_for_release"] is False
    assert decision["release_grade_validated"] is False

    assert artifact["residual"]["closed_by_this_gate"] is False
    assert artifact["residual"]["residual_closed"] is False


def test_selected_case_admission_records_input_refs_with_hashes() -> None:
    artifact = selected_case_gate.generate_selected_case_admission_gate()
    refs = {row["artifact_id"]: row for row in artifact["input_refs"]}

    assert set(refs) == {
        "res005_prior_debris_admission_gate",
        "res005_selected_debris_output_anchor_set",
        "source_rights_output_policy_gate",
        "residual_register",
        "mechanism_admission_failclosed_backlog",
        "candidate_acceptance_status",
        "task_cluster_execution_status",
        "validation_res005_tp21_debris_admission_note",
    }
    for row in refs.values():
        assert row["relative_path"]
        assert_hex64(row["sha256"])

    assert refs["res005_prior_debris_admission_gate"]["schema_version"] == (
        "a2.res005_tp21_debris_admission_gate.v1"
    )
    assert refs["res005_selected_debris_output_anchor_set"]["schema_version"] == (
        "a2.res005_tp21_selected_debris_anchor_set.v1"
    )
    assert refs["source_rights_output_policy_gate"]["schema_version"] == (
        "a2.source_rights_output_policy_gate.v1"
    )


def test_selected_case_admission_required_items_are_missing_owner_inputs() -> None:
    artifact = selected_case_gate.generate_selected_case_admission_gate()

    required = artifact["required_reviewer_signoff_items"]
    missing = artifact["current_missing_items"]
    assert len(required) == 6
    assert len(missing) == 6
    assert all(row["present"] is False for row in required)
    assert all(row["current_status"] == "missing_fail_closed" for row in required)

    missing_ids = [row["item_id"] for row in missing]
    assert missing_ids == [
        "TP21-SELECTED-CASE-LOCATOR",
        "TP21-SELECTED-OUTPUT-PREIMAGE-SHA256",
        "TP21-SELECTED-DEBRIS-OUTPUT-ANCHOR-SET",
        "TP21-INDEPENDENT-REVIEWER-SIGNOFF",
        "TP21-ALLOWED-OUTPUT-SIGNOFF",
        "TP21-AUTHORITY-BOUNDARY-SIGNOFF",
    ]

    evidence = artifact["selected_case_evidence_state"]
    assert evidence["reviewer_selected_case_locator_present"] is False
    assert evidence["selected_output_preimage_sha256_present"] is False
    assert evidence["selected_debris_output_hash_count"] == 0
    assert evidence["independent_reviewer_signoff_present"] is False
    assert evidence["allowed_output_signoff_present"] is False


def test_selected_case_admission_packet_is_hash_ref_label_only() -> None:
    artifact = selected_case_gate.generate_selected_case_admission_gate()

    assert artifact["benchmark_consumed_for_release"] is False
    assert artifact["raw_tp21_source_content_retained"] is False
    assert artifact["raw_selected_outputs_retained"] is False
    assert artifact["hash_only_ref_only_label_only"] is True
    assert artifact["source_payload_body_retained"] is False
    assert artifact["source_tables_retained"] is False
    assert artifact["source_figures_retained"] is False
    assert artifact["source_numeric_values_retained"] is False

    prior = artifact["prior_debris_gate_summary"]
    assert prior["selected_debris_output_hash_count"] == 0
    assert_hex64(prior["selected_debris_output_set_sha256"])
    assert_hex64(prior["controlled_criteria_vocabulary_sha256"])

    rights = artifact["source_rights_policy_summary"]
    assert rights["current_comparison_outputs_admitted"] is False
    assert rights["release_grade_satisfied"] is False
    assert rights["tp21_payload_ref"]["benchmark_consumed_for_release"] is False
    assert rights["tp21_payload_ref"]["release_consumption_allowed"] is False
    assert_hex64(rights["tp21_payload_ref"]["payload_sha256"])

    forbidden_keys = {
        "raw_source_text",
        "source_table_payload",
        "source_table_rows",
        "document_numeric_value",
        "tp21_raw_value",
        "selected_output_raw_value",
        "raw_selected_output_payload",
        "selected_output_preimage",
    }
    assert_no_keys_anywhere(artifact, forbidden_keys)

    serialized = json.dumps(artifact, ensure_ascii=False)
    assert "extracted_text" not in serialized
    assert "source_table_payload" not in serialized
    assert "selected_output_raw_value" not in serialized


def test_selected_case_admission_preserves_authority_guards_false() -> None:
    artifact = selected_case_gate.generate_selected_case_admission_gate()

    assert_authority_guards_false(artifact)
    assert artifact["authority_guards"]["fragment_mechanism_authority_granted"] is False
    assert artifact["authority_guards"][
        "component_failure_probability_authority_granted"
    ] is False
    assert artifact["authority_guards"]["effect_scale_authority_granted"] is False
    assert artifact["authority_guards"]["stock_database_authority_granted"] is False
    assert artifact["authority_guards"]["runtime_authority_granted"] is False
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_selected_case_admission_cli_writes_manifest_integrity_clean(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "gate_cli.json"
    retained_dir = tmp_path / "retained"

    result = run_maintenance_cli(
        "a2_blastfrag_res005_tp21_selected_case_admission_gate.py",
        "--retained-dir",
        retained_dir,
        "--output",
        output_path,
    )

    assert result.stdout == ""
    artifact = read_json(output_path)
    assert artifact["status"] == (
        "blocked_fail_closed_tp21_selected_case_admission_review_packet"
    )
    assert_hex64(artifact["retained_artifact_sha256"])
    assert_hex64(artifact["retained_manifest_sha256"])

    gate_path = retained_dir / "res005_tp21_selected_case_admission_review_gate.json"
    manifest_path = retained_dir / "manifest.json"
    assert gate_path.exists()
    assert manifest_path.exists()

    manifest = read_json(manifest_path)
    assert manifest["schema_version"] == (
        "a2.res005_tp21_selected_case_admission_review_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "blocked_fail_closed_tp21_selected_case_admission_review_packet"
    )
    assert_hex64(
        manifest[
            "res005_tp21_selected_case_admission_review_gate_artifact"
        ]["sha256"]
    )
    assert manifest["benchmark_consumed_for_release"] is False
    assert manifest["raw_tp21_source_content_retained"] is False
    assert_authority_guards_false(manifest)
    assert_retained_manifest_clean(integrity, manifest_path)


def test_selected_case_candidate_packet_fails_closed() -> None:
    artifact = candidate_packet.generate_selected_case_candidate_packet()

    assert artifact["schema_version"] == (
        "a2.res005_tp21_selected_case_candidate_packet.v1"
    )
    assert artifact["schema"]["name"] == "res005_tp21_selected_case_candidate_packet"
    assert artifact["package"]["worker_id"] == (
        "TC-A2-BF-003-RES005-TP21-CANDIDATE-SELECTION"
    )
    assert artifact["residual_id"] == "RES-005"
    assert artifact["status"] == (
        "blocked_fail_closed_tp21_selected_case_candidate_packet"
    )

    status = artifact["candidate_selection_status"]
    assert status["status"] == "blocked"
    assert status["decision"] == "not_ready_fail_closed"
    assert status["fail_closed"] is True
    assert status["selected_case_candidate_packet_ready"] is False
    assert status["selected_case_admitted_for_release"] is False
    assert status["narrowly_closes_res005"] is False
    assert status["residual_status_after_packet"] == "open_fail_closed_res005"
    assert status["benchmark_consumed_for_release"] is False
    assert status["release_grade_validated"] is False

    assert artifact["res005_closure_granted"] is False
    assert artifact["authority_granted_by_this_packet"] is False


def test_selected_case_candidate_records_required_input_refs() -> None:
    artifact = candidate_packet.generate_selected_case_candidate_packet()
    refs = {row["artifact_id"]: row for row in artifact["input_refs"]}

    assert set(refs) == {
        "source_artifact_pack_manifest",
        "res005_tp21_debris_admission_gate",
        "selected_debris_output_anchor_set",
        "source_rights_output_policy_gate",
        "res005_tp21_selected_case_admission_review_gate",
    }
    for row in refs.values():
        assert row["relative_path"]
        assert_hex64(row["sha256"])

    assert refs["source_artifact_pack_manifest"]["schema_version"] == (
        "a2.provenance_identity_retained_source_artifact_pack.v1"
    )
    assert refs["res005_tp21_debris_admission_gate"]["schema_version"] == (
        "a2.res005_tp21_debris_admission_gate.v1"
    )
    assert refs["selected_debris_output_anchor_set"]["schema_version"] == (
        "a2.res005_tp21_selected_debris_anchor_set.v1"
    )
    assert refs["source_rights_output_policy_gate"]["schema_version"] == (
        "a2.source_rights_output_policy_gate.v1"
    )
    assert refs["res005_tp21_selected_case_admission_review_gate"][
        "schema_version"
    ] == "a2.res005_tp21_selected_case_admission_review_gate.v1"


def test_selected_case_candidate_tracks_present_vs_missing() -> None:
    artifact = candidate_packet.generate_selected_case_candidate_packet()
    present = {row["item_id"]: row for row in artifact["present_vs_missing"]}

    assert present["TP21-PAYLOAD-RETAINED-HASH-MATCHED"]["present"] is True
    assert present["TP21-CONTROLLED-CRITERIA-VOCABULARY"]["present"] is True
    assert present["TP21-REVIEWER-SELECTED-CASE-LOCATOR"]["present"] is False
    assert present["TP21-SELECTED-OUTPUT-PREIMAGE-SHA256"]["present"] is False
    assert present["TP21-SELECTED-OUTPUT-HASH-ANCHORS"]["present"] is False
    assert present["TP21-INDEPENDENT-REVIEWER-SIGNOFF"]["present"] is False
    assert present["TP21-ALLOWED-OUTPUT-SIGNOFF"]["present"] is False

    missing_ids = [row["item_id"] for row in artifact["current_missing_items"]]
    assert missing_ids == [
        "TP21-REVIEWER-SELECTED-CASE-LOCATOR",
        "TP21-SELECTED-OUTPUT-PREIMAGE-SHA256",
        "TP21-SELECTED-OUTPUT-HASH-ANCHORS",
        "TP21-INDEPENDENT-REVIEWER-SIGNOFF",
        "TP21-ALLOWED-OUTPUT-SIGNOFF",
    ]

    criteria = artifact["selection_criteria"]
    assert criteria["controlled_criteria_key_count"] == 8
    assert criteria["criteria_are_labels_only"] is True
    assert criteria["criteria_are_not_raw_tp21_values"] is True
    assert criteria["criteria_are_not_calibration_authority"] is True
    assert_hex64(criteria["controlled_criteria_vocabulary_sha256"])


def test_selected_case_candidate_packet_is_hash_ref_label_only() -> None:
    artifact = candidate_packet.generate_selected_case_candidate_packet()

    guarantees = artifact["candidate_evidence_guarantees"]
    assert guarantees["hash_only_ref_only_label_only"] is True
    assert guarantees["raw_tp21_source_content_retained"] is False
    assert guarantees["raw_tp21_source_content_copied"] is False
    assert guarantees["source_payload_body_retained"] is False
    assert guarantees["source_tables_retained"] is False
    assert guarantees["source_figures_retained"] is False
    assert guarantees["source_numeric_values_retained"] is False
    assert guarantees["selected_output_preimages_retained"] is False
    assert guarantees["selected_output_raw_values_retained"] is False
    assert guarantees["benchmark_consumed_for_release"] is False
    assert guarantees["release_evidence"] is False

    locator_policy = artifact["candidate_locator_policy"]
    assert locator_policy["locator_status"] == "missing_fail_closed"
    assert locator_policy["candidate_locator_labels_retained"] == []
    assert locator_policy["locator_labels_are_not_source_quotes"] is True
    assert locator_policy["source_prose_tables_figures_or_raw_values_retained"] is False

    preimage_policy = artifact["hash_only_preimage_policy"]
    assert preimage_policy["preimage_policy_status"] == "missing_hash_fail_closed"
    assert preimage_policy["selected_output_preimage_sha256_present"] is False
    assert preimage_policy["selected_output_preimage_retained"] is False
    assert preimage_policy["selected_output_raw_values_retained"] is False
    assert preimage_policy["selected_debris_output_hash_count"] == 0
    assert_hex64(preimage_policy["selected_debris_output_set_sha256"])
    assert preimage_policy["benchmark_consumed_for_release"] is False

    forbidden_keys = {
        "raw_source_text",
        "source_table_payload",
        "source_table_rows",
        "document_numeric_value",
        "tp21_raw_value",
        "selected_output_raw_value",
        "raw_selected_output_payload",
        "selected_output_preimage",
    }
    assert_no_keys_anywhere(artifact, forbidden_keys)

    serialized = json.dumps(artifact, ensure_ascii=False)
    assert "extracted_text" not in serialized
    assert "source_table_payload" not in serialized
    assert '"selected_output_raw_value":' not in serialized
    assert "raw_selected_output_payload" not in serialized


def test_selected_case_candidate_preserves_authority_guards_false() -> None:
    artifact = candidate_packet.generate_selected_case_candidate_packet()

    assert_authority_guards_false(artifact)
    assert artifact["authority_guards"]["fragment_mechanism_authority_granted"] is False
    assert artifact["authority_guards"][
        "component_failure_probability_authority_granted"
    ] is False
    assert artifact["authority_guards"]["effect_scale_authority_granted"] is False
    assert artifact["authority_guards"]["stock_database_authority_granted"] is False
    assert artifact["authority_guards"]["runtime_authority_granted"] is False
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_selected_case_candidate_cli_writes_manifest_integrity_clean(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "candidate_packet_cli.json"
    retained_dir = tmp_path / "retained"

    result = run_maintenance_cli(
        "a2_blastfrag_res005_tp21_selected_case_candidate_packet.py",
        "--retained-dir",
        retained_dir,
        "--output",
        output_path,
    )

    assert result.stdout == ""
    artifact = read_json(output_path)
    assert artifact["status"] == (
        "blocked_fail_closed_tp21_selected_case_candidate_packet"
    )
    assert_hex64(artifact["retained_artifact_sha256"])
    assert_hex64(artifact["retained_manifest_sha256"])

    packet_path = retained_dir / "res005_tp21_selected_case_candidate_packet.json"
    manifest_path = retained_dir / "manifest.json"
    assert packet_path.exists()
    assert manifest_path.exists()

    manifest = read_json(manifest_path)
    assert manifest["schema_version"] == (
        "a2.res005_tp21_selected_case_candidate_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "blocked_fail_closed_tp21_selected_case_candidate_packet"
    )
    assert_hex64(
        manifest["res005_tp21_selected_case_candidate_packet_artifact"]["sha256"]
    )
    assert manifest["benchmark_consumed_for_release"] is False
    assert manifest["raw_tp21_source_content_retained"] is False
    assert manifest["selected_output_raw_values_retained"] is False
    assert_authority_guards_false(manifest)

    assert_retained_manifest_clean(integrity, manifest_path)
