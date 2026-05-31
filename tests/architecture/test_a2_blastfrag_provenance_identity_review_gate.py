from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_provenance_identity_review_gate as gate,
)


def test_a2_blastfrag_provenance_identity_review_gate_current_repo_is_blocked(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_provenance_identity_review_gate(
        repo_root=REPO_ROOT,
        retained_review_dir=tmp_path,
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.provenance_identity_review_gate.v1"
    assert artifact["status"] == (
        "blocked_non_authoritative_provenance_identity_review_gate"
    )
    assert artifact["review_target"] == "res_001_002_provenance_identity_release_review"
    assert artifact["residual_gate_results"] == {
        "RES-001": "blocked",
        "RES-002": "blocked",
    }
    assert artifact["blocking_residual_ids"] == [
        "RES-001",
        "RES-002",
        "RES-013/014-boundary",
    ]

    decision = artifact["review_decision"]
    assert decision["release_grade_review_ready"] is False
    assert decision["release_grade_review_blocked"] is True
    assert decision["authority_release_included"] is False
    assert decision["retained_review_artifact_included"] is True
    assert decision["retained_source_payload_pack_included"] is True

    source_payload_consumption = artifact["source_payload_pack_consumption"]
    assert source_payload_consumption["manifest_source"] == (
        "canonical_source_payload_pack"
    )
    assert source_payload_consumption["payload_retention_satisfied"] is True
    assert source_payload_consumption["retained_payload_count"] == 3
    assert source_payload_consumption["required_payload_count"] == 3
    assert source_payload_consumption["rights_review_blocked"] is True
    assert source_payload_consumption["allowed_output_policy_blocked"] is True
    assert source_payload_consumption["benchmark_consumption_review_blocked"] is True
    assert source_payload_consumption["independent_review_signoff_blocked"] is True
    assert source_payload_consumption["authority_release_included"] is False

    assert [row["check_id"] for row in artifact["review_checks"]] == [
        "REVIEW-RES001-001",
        "REVIEW-RES001-002",
        "REVIEW-RES001-003",
        "REVIEW-RES001-004",
        "REVIEW-RES002-001",
        "REVIEW-RES002-002",
        "REVIEW-RES002-003",
        "REVIEW-RES001-002-001",
    ]
    assert [row["review_surface"] for row in artifact["review_checks"]] == [
        "retained_source_artifact_pack",
        "allowed_output_policy",
        "benchmark_consumption_trace",
        "comparison_output_hash",
        "clean_release_identity",
        "release_validation_status",
        "retained_identity_surface",
        "independent_review_signoff",
    ]
    assert [row["release_grade_satisfied"] for row in artifact["review_checks"]] == [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    ]

    retained_source = artifact["review_checks"][0]
    assert retained_source["author_side_satisfied"] is True
    assert retained_source["status"] == "author_side_closed_release_grade_blocked"
    assert retained_source["observed_evidence"]["verified_source_artifact_ids"] == [
        "PIN-BFM-001",
        "PIN-BFM-002",
    ]
    assert retained_source["observed_evidence"]["sha256_pinned_artifact_ids"] == [
        "PIN-BFM-001",
        "PIN-BFM-002",
    ]
    assert (
        retained_source["observed_evidence"]["required_source_artifact_payload_count"]
        == 3
    )
    assert retained_source["observed_evidence"]["source_pack_manifest_exists"] is True
    assert retained_source["observed_evidence"]["source_pack_manifest_source"] == (
        "canonical_source_payload_pack"
    )
    assert retained_source["observed_evidence"]["source_pack_status"] == (
        "partial_payloads_retained_release_review_blocked"
    )
    assert retained_source["observed_evidence"]["rights_review_status"] == (
        "public_distribution_statement_supported_candidate_not_signed_off"
    )
    assert retained_source["observed_evidence"]["all_payloads_exist"] is True
    assert retained_source["observed_evidence"]["all_payload_hashes_match"] is True
    assert retained_source["observed_evidence"]["retained_payload_count"] == 3
    assert retained_source["observed_evidence"]["payload_retention_satisfied"] is True
    assert retained_source["observed_evidence"]["missing_required_payload_ids"] == []
    assert "source payload pack manifest missing" not in retained_source[
        "observed_evidence"
    ]["release_grade_blocking_reasons"]

    allowed_output = artifact["review_checks"][1]
    assert allowed_output["author_side_satisfied"] is True
    assert allowed_output["observed_evidence"]["policy_status"] == (
        "release_candidate_fail_closed_policy_frozen"
    )
    assert allowed_output["observed_evidence"]["policy_source"] == (
        "canonical_source_payload_pack"
    )
    assert allowed_output["observed_evidence"]["missing_forbidden_outputs"] == []

    benchmark = artifact["review_checks"][2]
    assert benchmark["author_side_satisfied"] is True
    assert benchmark["observed_evidence"]["explicit_non_consumed_artifact_ids"] == [
        "PIN-BFM-001",
        "PIN-BFM-002",
    ]
    assert benchmark["observed_evidence"]["release_consumed_artifact_ids"] == []
    assert benchmark["observed_evidence"]["source_payload_retention_satisfied"] is True
    assert benchmark["observed_evidence"]["source_pack_chain_status"] == (
        "explicit_non_consumption_only_release_chain_missing"
    )

    comparison = artifact["review_checks"][3]
    assert comparison["author_side_satisfied"] is True
    assert comparison["status"] == "author_side_closed_release_grade_blocked"
    assert comparison["observed_evidence"]["comparison_output_hashes"] == []
    assert comparison["observed_evidence"][
        "source_pack_comparison_output_hash_status"
    ] == "partial_hash_manifest_present_release_review_blocked"
    assert comparison["observed_evidence"][
        "source_pack_selected_beco_cached_output_hash_count"
    ] == 9
    assert comparison["observed_evidence"][
        "candidate_result_hashes_are_not_comparison_output_hashes"
    ] is True
    assert comparison["observed_evidence"]["candidate_result_artifact_hash_count"] == 8

    identity = artifact["review_checks"][4]
    assert identity["author_side_satisfied"] is True
    identity_evidence = identity["observed_evidence"]
    assert identity_evidence["worktree_state"] == (
        "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present"
    )
    assert identity_evidence["output_anchor_count"] == 3

    validation = artifact["review_checks"][5]
    assert validation["author_side_satisfied"] is True
    assert validation["observed_evidence"] == {
        "identity_current_validation_status": "not_validated",
        "validation_manifest_calibration_status": "unvalidated",
    }

    retained_identity = artifact["review_checks"][6]
    assert retained_identity["author_side_satisfied"] is True
    assert retained_identity["observed_evidence"]["stage_b_retained_origin_summary"][
        "independent_release_artifact_present"
    ] is False
    assert retained_identity["observed_evidence"]["stage_c_retained_origin_summary"][
        "stock_runtime_authority_present"
    ] is False

    signoff = artifact["review_checks"][7]
    assert signoff["author_side_satisfied"] is False
    assert signoff["observed_evidence"]["signoff_manifest_exists"] is False
    assert signoff["observed_evidence"]["reviewer_signoff_status"] == "missing"

    assert artifact["residual_condition_trace"] == [
        {
            "residual_id": "RES-001",
            "author_side_closed_check_ids": [
                "REVIEW-RES001-001",
                "REVIEW-RES001-002",
                "REVIEW-RES001-003",
                "REVIEW-RES001-004",
            ],
            "author_side_blocking_check_ids": ["REVIEW-RES001-002-001"],
            "release_grade_blocking_check_ids": [
                "REVIEW-RES001-001",
                "REVIEW-RES001-002",
                "REVIEW-RES001-003",
                "REVIEW-RES001-004",
                "REVIEW-RES001-002-001",
            ],
            "gate_result": "blocked",
        },
        {
            "residual_id": "RES-002",
            "author_side_closed_check_ids": [
                "REVIEW-RES002-001",
                "REVIEW-RES002-002",
                "REVIEW-RES002-003",
            ],
            "author_side_blocking_check_ids": ["REVIEW-RES001-002-001"],
            "release_grade_blocking_check_ids": [
                "REVIEW-RES002-001",
                "REVIEW-RES002-002",
                "REVIEW-RES002-003",
                "REVIEW-RES001-002-001",
            ],
            "gate_result": "blocked",
        },
    ]

    closeout_summary = artifact["release_provenance_closeout_gate_summary"]
    assert closeout_summary["release_closeout_ready"] is False
    assert closeout_summary["release_closeout_blocked"] is True

    assert artifact["authority_guards_all_false"] is True
    assert not any(artifact["non_authoritative_guards"].values())


def test_a2_blastfrag_provenance_identity_review_gate_prefers_canonical_source_pack(
    tmp_path: Path,
) -> None:
    fallback_path = tmp_path / gate.SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME
    fallback_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "a2.provenance_identity_retained_source_artifact_pack.v1"
                ),
                "status": "missing_retained_source_artifact_pack",
                "artifacts": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    artifact = gate.generate_provenance_identity_review_gate(
        repo_root=REPO_ROOT,
        retained_review_dir=tmp_path,
    )

    retained_source = artifact["review_checks"][0]
    evidence = retained_source["observed_evidence"]
    assert evidence["source_pack_manifest_source"] == "canonical_source_payload_pack"
    assert evidence["source_pack_manifest_ref"].endswith(
        "retained_artifacts/source_payload_pack_20260531/"
        "source_artifact_pack_manifest.json"
    )
    assert evidence["source_pack_manifest_exists"] is True
    assert evidence["payload_retention_satisfied"] is True
    assert evidence["retained_payload_count"] == 3
    assert retained_source["release_grade_satisfied"] is False
    assert "source payload pack manifest missing" not in retained_source[
        "blocking_summary"
    ]


def test_a2_blastfrag_provenance_identity_review_gate_fails_closed_for_optimistic_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    original_read_text = gate._read_text
    comparison_hash = "a" * 64

    def optimistic_read_text(path: Path) -> str:
        text = original_read_text(path)
        if path == gate.DOC_REFS["artifact_pin_manifest"]:
            return text.replace(
                (
                    "| `forbidden_release_action` | `do not treat pending, "
                    "verified-candidate or sanity-only artifacts as acquired "
                    "calibration inputs` |"
                ),
                (
                    "| `forbidden_release_action` | `do not treat pending, "
                    "verified-candidate or sanity-only artifacts as acquired "
                    "calibration inputs` |\n"
                    "| `allowed_output_policy_status` | `release_grade_frozen` |"
                ),
            )
        if path == gate.DOC_REFS["surrogate_identity_manifest"]:
            text = text.replace(
                "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present",
                "clean_release_candidate",
            )
            text = text.replace("not_validated", "validated")
            return text.replace("/tmp/a2_", "retained_artifacts/a2_")
        if path == gate.DOC_REFS["validation_manifest"]:
            text = text.replace("unvalidated", "validated")
            return (
                f"{text}\nreviewer candidate note: comparison-output-sha256 "
                f"{comparison_hash}\n"
            )
        return text

    monkeypatch.setattr(gate, "_read_text", optimistic_read_text)

    artifact = gate.generate_provenance_identity_review_gate(
        repo_root=REPO_ROOT,
        retained_review_dir=tmp_path,
    )

    checks = {row["check_id"]: row for row in artifact["review_checks"]}
    assert checks["REVIEW-RES001-002"]["release_grade_satisfied"] is False
    assert checks["REVIEW-RES001-002"]["observed_evidence"]["policy_status"] == (
        "release_candidate_fail_closed_policy_frozen"
    )
    assert checks["REVIEW-RES001-004"]["release_grade_satisfied"] is True
    assert checks["REVIEW-RES002-001"]["release_grade_satisfied"] is True
    assert checks["REVIEW-RES002-002"]["release_grade_satisfied"] is True

    assert checks["REVIEW-RES001-001"]["release_grade_satisfied"] is False
    assert checks["REVIEW-RES001-003"]["release_grade_satisfied"] is False
    assert checks["REVIEW-RES002-003"]["release_grade_satisfied"] is False
    assert checks["REVIEW-RES001-002-001"]["release_grade_satisfied"] is False
    assert artifact["status"] == (
        "blocked_non_authoritative_provenance_identity_review_gate"
    )
    assert artifact["residual_gate_results"] == {
        "RES-001": "blocked",
        "RES-002": "blocked",
    }
    assert artifact["review_decision"]["release_grade_review_ready"] is False
    assert artifact["authority_guards_all_false"] is True


def test_a2_blastfrag_provenance_identity_review_gate_fails_closed_when_source_evidence_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    original_read_text = gate._read_text

    def missing_verified_source_text(path: Path) -> str:
        text = original_read_text(path)
        if path == gate.DOC_REFS["artifact_pin_manifest"]:
            return text.replace("verified_candidate_artifact", "candidate_route_recorded")
        return text

    monkeypatch.setattr(gate, "_read_text", missing_verified_source_text)

    artifact = gate.generate_provenance_identity_review_gate(
        repo_root=REPO_ROOT,
        retained_review_dir=tmp_path,
    )

    source_pack = artifact["review_checks"][0]
    benchmark_trace = artifact["review_checks"][2]
    assert source_pack["author_side_satisfied"] is False
    assert source_pack["status"] == "blocked_author_side_evidence_missing"
    assert benchmark_trace["author_side_satisfied"] is False
    assert benchmark_trace["status"] == "blocked_author_side_evidence_missing"
    assert artifact["residual_condition_trace"][0]["author_side_closed_check_ids"] == [
        "REVIEW-RES001-002",
        "REVIEW-RES001-004",
    ]
    assert artifact["residual_gate_results"]["RES-001"] == "blocked"


def test_a2_blastfrag_provenance_identity_review_gate_rejects_incomplete_source_pack(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        gate,
        "CANONICAL_SOURCE_PAYLOAD_PACK_DIR",
        tmp_path / "absent_canonical_source_payload_pack",
    )
    source_pack_path = tmp_path / gate.SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME
    source_pack_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "a2.provenance_identity_retained_source_artifact_pack.v1"
                ),
                "status": "release_retained_source_artifact_pack",
                "rights_review_status": "release_reviewed",
                "benchmark_consumption_chain_status": "release_reviewed",
                "artifacts": [
                    {
                        "artifact_id": "PIN-BFM-001",
                        "source_artifact_label": "TP-20 PDF",
                        "relative_path": "missing/tp20.pdf",
                        "sha256": (
                            "293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20"
                            "baad56e39fb8423f165f"
                        ),
                        "retention_status": "release_retained",
                        "rights_status": "release_reviewed",
                        "allowed_use": "benchmark_design_reference_candidate_only",
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    artifact = gate.generate_provenance_identity_review_gate(
        repo_root=REPO_ROOT,
        retained_review_dir=tmp_path,
    )

    retained_source = artifact["review_checks"][0]
    assert retained_source["observed_evidence"]["source_pack_manifest_exists"] is True
    assert retained_source["observed_evidence"]["source_pack_manifest_source"] == (
        "retained_review_dir_fallback"
    )
    assert retained_source["observed_evidence"]["all_payloads_exist"] is False
    assert retained_source["observed_evidence"]["all_payload_hashes_match"] is False
    assert retained_source["observed_evidence"]["payload_retention_satisfied"] is False
    assert retained_source["release_grade_satisfied"] is False
    assert retained_source["status"] == "author_side_closed_release_grade_blocked"
    assert "payload retention or sha256 matching is incomplete" in retained_source[
        "blocking_summary"
    ]


def test_a2_blastfrag_provenance_identity_review_gate_cli_writes_retained_artifact(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "cli_output_manifest.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_provenance_identity_review_gate.py",
            "--write-retained-artifact",
            "--retained-output-dir",
            str(tmp_path),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    cli_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert cli_payload["schema_version"] == (
        "a2.provenance_identity_review_retained_manifest.v1"
    )
    assert cli_payload["status"] == (
        "retained_provenance_identity_review_artifact_non_authoritative"
    )
    assert cli_payload["source_artifact_payloads_retained"] is True
    assert cli_payload["source_payload_release_blockers"] == {
        "rights_review_blocked": True,
        "allowed_output_policy_blocked": True,
        "benchmark_consumption_review_blocked": True,
        "comparison_output_hash_blocked": True,
        "independent_review_signoff_blocked": True,
    }
    assert cli_payload["independent_review_signoff_present"] is False
    assert cli_payload["retained_artifact_count"] == 1
    assert cli_payload["all_artifacts_exist"] is True
    assert not any(cli_payload["non_authoritative_guards"].values())

    retained_gate_path = tmp_path / gate.REVIEW_ARTIFACT_FILENAME
    retained_manifest_path = tmp_path / gate.REVIEW_MANIFEST_FILENAME
    assert retained_gate_path.exists()
    assert retained_manifest_path.exists()
    retained_gate = json.loads(retained_gate_path.read_text(encoding="utf-8"))
    assert retained_gate["status"] == (
        "blocked_non_authoritative_provenance_identity_review_gate"
    )
    assert retained_gate["residual_gate_results"] == {
        "RES-001": "blocked",
        "RES-002": "blocked",
    }
