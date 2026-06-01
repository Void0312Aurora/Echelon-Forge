from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_source_rights_signoff_request_packet as packet,
)
from tools.maintenance import a2_retained_manifest_integrity as integrity  # noqa: E402


HEX64 = re.compile(r"^[a-f0-9]{64}$")


def _walk(payload: Any) -> list[Any]:
    values = [payload]
    if isinstance(payload, dict):
        for value in payload.values():
            values.extend(_walk(value))
    elif isinstance(payload, list):
        for value in payload:
            values.extend(_walk(value))
    return values


def test_source_rights_signoff_request_packet_is_fail_closed_checklist() -> None:
    artifact = packet.generate_source_rights_signoff_request_packet()

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

    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["authority_guards"].values())
    assert artifact["authority_guards"]["source_truth_authority_granted"] is False
    assert artifact["authority_guards"]["allowed_output_release_authority_granted"] is False
    assert artifact["authority_guards"]["runtime_authority_granted"] is False
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["fuze_authority_granted"] is False


def test_source_rights_signoff_request_records_input_refs_with_hashes() -> None:
    artifact = packet.generate_source_rights_signoff_request_packet()
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
    artifact = packet.generate_source_rights_signoff_request_packet()
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
    artifact = packet.generate_source_rights_signoff_request_packet()

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
    artifact = packet.generate_source_rights_signoff_request_packet()

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
    for value in _walk(artifact):
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

    artifact = packet.generate_source_rights_signoff_request_packet(
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
            sys.executable,
            "tools/maintenance/a2_blastfrag_source_rights_signoff_request_packet.py",
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
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["authority_guards"].values())
    assert HEX64.fullmatch(manifest["artifacts"][0]["sha256"])

    summary = integrity.check_retained_manifest_integrity(
        manifest_paths=[manifest_path]
    )
    assert summary["missing_total"] == 0
    assert summary["sha_mismatch_total"] == 0
    assert summary["guard_true_total"] == 0
