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
    a2_blastfrag_res005_tp21_selected_case_admission_gate as gate,
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


def test_res005_tp21_selected_case_review_packet_fails_closed() -> None:
    artifact = gate.generate_selected_case_admission_gate()

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


def test_res005_tp21_selected_case_packet_records_input_refs_with_hashes() -> None:
    artifact = gate.generate_selected_case_admission_gate()
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
        assert HEX64.fullmatch(row["sha256"])

    assert refs["res005_prior_debris_admission_gate"]["schema_version"] == (
        "a2.res005_tp21_debris_admission_gate.v1"
    )
    assert refs["res005_selected_debris_output_anchor_set"]["schema_version"] == (
        "a2.res005_tp21_selected_debris_anchor_set.v1"
    )
    assert refs["source_rights_output_policy_gate"]["schema_version"] == (
        "a2.source_rights_output_policy_gate.v1"
    )


def test_res005_tp21_selected_case_required_items_are_missing_owner_inputs() -> None:
    artifact = gate.generate_selected_case_admission_gate()

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


def test_res005_tp21_selected_case_packet_is_hash_ref_label_only() -> None:
    artifact = gate.generate_selected_case_admission_gate()

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
    assert HEX64.fullmatch(prior["selected_debris_output_set_sha256"])
    assert HEX64.fullmatch(prior["controlled_criteria_vocabulary_sha256"])

    rights = artifact["source_rights_policy_summary"]
    assert rights["current_comparison_outputs_admitted"] is False
    assert rights["release_grade_satisfied"] is False
    assert rights["tp21_payload_ref"]["benchmark_consumed_for_release"] is False
    assert rights["tp21_payload_ref"]["release_consumption_allowed"] is False
    assert HEX64.fullmatch(rights["tp21_payload_ref"]["payload_sha256"])

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
    for value in _walk(artifact):
        if isinstance(value, dict):
            assert not (forbidden_keys & set(value))

    serialized = json.dumps(artifact, ensure_ascii=False)
    assert "extracted_text" not in serialized
    assert "source_table_payload" not in serialized
    assert "selected_output_raw_value" not in serialized


def test_res005_tp21_selected_case_packet_preserves_authority_guards_false() -> None:
    artifact = gate.generate_selected_case_admission_gate()

    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["authority_guards"].values())
    assert artifact["authority_guards"]["fragment_mechanism_authority_granted"] is False
    assert artifact["authority_guards"][
        "component_failure_probability_authority_granted"
    ] is False
    assert artifact["authority_guards"]["effect_scale_authority_granted"] is False
    assert artifact["authority_guards"]["stock_database_authority_granted"] is False
    assert artifact["authority_guards"]["runtime_authority_granted"] is False
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_res005_tp21_selected_case_cli_writes_manifest_integrity_clean(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "gate_cli.json"
    retained_dir = tmp_path / "retained"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res005_tp21_selected_case_admission_gate.py",
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
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["status"] == (
        "blocked_fail_closed_tp21_selected_case_admission_review_packet"
    )
    assert HEX64.fullmatch(artifact["retained_artifact_sha256"])
    assert HEX64.fullmatch(artifact["retained_manifest_sha256"])

    gate_path = retained_dir / "res005_tp21_selected_case_admission_review_gate.json"
    manifest_path = retained_dir / "manifest.json"
    assert gate_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == (
        "a2.res005_tp21_selected_case_admission_review_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "blocked_fail_closed_tp21_selected_case_admission_review_packet"
    )
    assert HEX64.fullmatch(
        manifest[
            "res005_tp21_selected_case_admission_review_gate_artifact"
        ]["sha256"]
    )
    assert manifest["benchmark_consumed_for_release"] is False
    assert manifest["raw_tp21_source_content_retained"] is False
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["authority_guards"].values())

    summary = integrity.check_retained_manifest_integrity(
        manifest_paths=[manifest_path],
    )
    assert summary["missing_total"] == 0
    assert summary["sha_mismatch_total"] == 0
    assert summary["guard_true_total"] == 0
