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
    a2_blastfrag_res005_tp21_selected_case_candidate_packet as packet,
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


def test_res005_tp21_selected_case_candidate_packet_fails_closed() -> None:
    artifact = packet.generate_selected_case_candidate_packet()

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


def test_res005_tp21_candidate_packet_records_required_input_refs() -> None:
    artifact = packet.generate_selected_case_candidate_packet()
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
        assert HEX64.fullmatch(row["sha256"])

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


def test_res005_tp21_candidate_packet_tracks_present_vs_missing() -> None:
    artifact = packet.generate_selected_case_candidate_packet()
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
    assert HEX64.fullmatch(criteria["controlled_criteria_vocabulary_sha256"])


def test_res005_tp21_candidate_packet_is_hash_ref_label_only() -> None:
    artifact = packet.generate_selected_case_candidate_packet()

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
    assert HEX64.fullmatch(preimage_policy["selected_debris_output_set_sha256"])
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
    for value in _walk(artifact):
        if isinstance(value, dict):
            assert not (forbidden_keys & set(value))

    serialized = json.dumps(artifact, ensure_ascii=False)
    assert "extracted_text" not in serialized
    assert "source_table_payload" not in serialized
    assert '"selected_output_raw_value":' not in serialized
    assert "raw_selected_output_payload" not in serialized


def test_res005_tp21_candidate_packet_preserves_authority_guards_false() -> None:
    artifact = packet.generate_selected_case_candidate_packet()

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


def test_res005_tp21_candidate_packet_cli_writes_manifest_integrity_clean(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "candidate_packet_cli.json"
    retained_dir = tmp_path / "retained"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res005_tp21_selected_case_candidate_packet.py",
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
        "blocked_fail_closed_tp21_selected_case_candidate_packet"
    )
    assert HEX64.fullmatch(artifact["retained_artifact_sha256"])
    assert HEX64.fullmatch(artifact["retained_manifest_sha256"])

    packet_path = retained_dir / "res005_tp21_selected_case_candidate_packet.json"
    manifest_path = retained_dir / "manifest.json"
    assert packet_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == (
        "a2.res005_tp21_selected_case_candidate_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "blocked_fail_closed_tp21_selected_case_candidate_packet"
    )
    assert HEX64.fullmatch(
        manifest["res005_tp21_selected_case_candidate_packet_artifact"]["sha256"]
    )
    assert manifest["benchmark_consumed_for_release"] is False
    assert manifest["raw_tp21_source_content_retained"] is False
    assert manifest["selected_output_raw_values_retained"] is False
    assert manifest["authority_guards_all_false"] is True
    assert not any(manifest["authority_guards"].values())

    summary = integrity.check_retained_manifest_integrity(
        manifest_paths=[manifest_path],
    )
    assert summary["missing_total"] == 0
    assert summary["sha_mismatch_total"] == 0
    assert summary["guard_true_total"] == 0
