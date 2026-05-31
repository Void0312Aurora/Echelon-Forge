from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_release_provenance_closeout_gate as gate,
)


def test_a2_blastfrag_release_provenance_closeout_gate_current_repo_is_blocked(
) -> None:
    artifact = gate.generate_release_provenance_closeout_gate(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.release_provenance_closeout_gate.v1"
    assert (
        artifact["status"]
        == "blocked_non_authoritative_release_provenance_closeout_candidate"
    )
    assert artifact["review_target"] == "res_001_002_release_provenance_closeout_lane"
    assert (
        artifact["readiness_level"]
        == "author_side_subitems_present_but_release_grade_closeout_blocked"
    )

    decision = artifact["release_closeout_decision"]
    assert decision["release_closeout_ready"] is False
    assert decision["release_closeout_blocked"] is True
    assert decision["author_side_subitems_recorded"] is True
    assert decision["authority_release_included"] is False

    assert [row["check_id"] for row in artifact["closeout_checks"]] == [
        "CLOSEOUT-RES001-001",
        "CLOSEOUT-RES001-002",
        "CLOSEOUT-RES001-003",
        "CLOSEOUT-RES002-001",
        "CLOSEOUT-RES002-002",
    ]
    assert [row["closeout_surface"] for row in artifact["closeout_checks"]] == [
        "retained_source_artifact",
        "allowed_output_policy",
        "benchmark_consumption_trace",
        "release_identity_cleanliness",
        "author_retained_pack_vs_release_identity",
    ]
    assert all(row["author_side_satisfied"] for row in artifact["closeout_checks"])
    assert not any(
        row["release_grade_satisfied"] for row in artifact["closeout_checks"]
    )
    assert [row["status"] for row in artifact["closeout_checks"]] == [
        "blocked_release_grade_evidence_missing",
        "blocked_release_grade_evidence_missing",
        "blocked_release_grade_evidence_missing",
        "blocked_release_grade_evidence_missing",
        "blocked_release_grade_evidence_missing",
    ]

    retained_source = artifact["closeout_checks"][0]
    assert retained_source["observed_author_side_evidence"][
        "verified_source_artifact_ids"
    ] == ["PIN-BFM-001", "PIN-BFM-002"]
    assert retained_source["observed_author_side_evidence"][
        "sha256_pinned_artifact_ids"
    ] == ["PIN-BFM-001", "PIN-BFM-002"]
    assert retained_source["blocking_artifact_ids"] == [
        "PIN-BFM-001",
        "PIN-BFM-002",
    ]
    assert "retention_pending" in retained_source["blocking_summary"]

    allowed_output = artifact["closeout_checks"][1]
    assert allowed_output["policy_status"] == "missing"
    assert allowed_output["observed_author_side_evidence"]["missing_forbidden_outputs"] == []
    assert allowed_output["observed_author_side_evidence"]["forbidden_outputs"] == [
        "effect_scale_authority",
        "component_failure_probability_authority",
        "pk_authority",
        "deterministic_fuze_authority",
    ]

    benchmark = artifact["closeout_checks"][2]
    assert benchmark["observed_author_side_evidence"][
        "explicit_non_consumed_artifact_ids"
    ] == ["PIN-BFM-001", "PIN-BFM-002"]
    assert benchmark["observed_author_side_evidence"]["release_consumed_artifact_ids"] == []
    assert "comparison-output hashes" in benchmark["blocking_summary"]

    identity = artifact["closeout_checks"][3]
    identity_evidence = identity["observed_author_side_evidence"]
    assert identity_evidence["worktree_state"] == (
        "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present"
    )
    assert identity_evidence["current_validation_status"] == "not_validated"
    assert identity_evidence["output_anchor_count"] >= 3
    assert "worktree_state is not clean_release_candidate" in identity[
        "blocking_summary"
    ]

    retained_gap = artifact["closeout_checks"][4]
    retained_evidence = retained_gap["observed_author_side_evidence"]
    assert retained_evidence["stage_b_status"] == "author_retained_candidate_artifacts_only"
    assert (
        retained_evidence["stage_c_status"]
        == "author_retained_stage_c_component_probability_candidate_artifacts_only"
    )
    assert retained_evidence["stage_b_retained_origin_summary"][
        "independent_release_artifact_present"
    ] is False
    assert retained_evidence["stage_c_retained_origin_summary"][
        "stock_runtime_authority_present"
    ] is False

    assert artifact["residual_condition_trace"] == [
        {
            "residual_id": "RES-001",
            "author_side_satisfied_check_ids": [
                "CLOSEOUT-RES001-001",
                "CLOSEOUT-RES001-002",
                "CLOSEOUT-RES001-003",
            ],
            "release_grade_blocking_check_ids": [
                "CLOSEOUT-RES001-001",
                "CLOSEOUT-RES001-002",
                "CLOSEOUT-RES001-003",
            ],
            "gate_result": "blocked",
        },
        {
            "residual_id": "RES-002",
            "author_side_satisfied_check_ids": [
                "CLOSEOUT-RES002-001",
                "CLOSEOUT-RES002-002",
            ],
            "release_grade_blocking_check_ids": [
                "CLOSEOUT-RES002-001",
                "CLOSEOUT-RES002-002",
            ],
            "gate_result": "blocked",
        },
    ]
    assert artifact["blocking_residual_ids"] == [
        "RES-001",
        "RES-001",
        "RES-001",
        "RES-002",
        "RES-002",
        "RES-013/014-boundary",
    ]

    shared = artifact["shared_provenance_identity_gate_summary"]
    assert (
        shared["status"]
        == "blocked_non_authoritative_package_provenance_identity_candidate"
    )
    assert "RES-001" in shared["blocking_residual_ids"]
    assert "RES-002" in shared["blocking_residual_ids"]

    assert artifact["remaining_release_grade_paths"]["RES-001"] == [
        "canonical retained source artifact pack",
        "release-grade allowed-output policy freeze",
        "benchmark-consumption trace with comparison-output hashes and reviewer signoff",
    ]
    assert "clean release candidate identity state" in artifact[
        "remaining_release_grade_paths"
    ]["RES-002"]

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["effect_scale_authority_released"] is False
    assert guards["component_failure_probability_authority_released"] is False
    assert guards["pk_authority_released"] is False
    assert guards["deterministic_fuze_authority_released"] is False


def test_a2_blastfrag_release_provenance_closeout_gate_fails_closed_for_optimistic_release_fields(
    monkeypatch,
) -> None:
    original_read_text = gate._read_text

    def optimistic_read_text(path: Path) -> str:
        text = original_read_text(path)
        if path == gate.DOC_REFS["artifact_pin_manifest"]:
            text = text.replace(
                "verified_candidate_artifact_bundle / retention_pending",
                "verified_candidate_artifact_bundle / release_retained",
            )
            text = text.replace(
                "verified_candidate_artifact / retention_pending",
                "verified_candidate_artifact / release_retained",
            )
            text = text.replace(
                "not_consumed_for_stage_b_release",
                "release_retained_benchmark_input",
            )
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
            return f"{text}\ncomparison-output-sha256: optimistic-test-only\n"
        return text

    monkeypatch.setattr(gate, "_read_text", optimistic_read_text)

    artifact = gate.generate_release_provenance_closeout_gate(repo_root=REPO_ROOT)

    assert (
        artifact["status"]
        == "blocked_non_authoritative_release_provenance_closeout_candidate"
    )
    assert artifact["release_closeout_decision"]["release_closeout_ready"] is False
    assert [row["release_grade_satisfied"] for row in artifact["closeout_checks"]] == [
        True,
        True,
        True,
        True,
        False,
    ]
    assert artifact["residual_condition_trace"][0]["gate_result"] == (
        "release_closeout_ready_by_this_gate"
    )
    assert artifact["residual_condition_trace"][1]["release_grade_blocking_check_ids"] == [
        "CLOSEOUT-RES002-002"
    ]
    assert artifact["blocking_residual_ids"] == ["RES-002", "RES-013/014-boundary"]
    assert artifact["closeout_checks"][4]["status"] == (
        "blocked_release_grade_evidence_missing"
    )
    assert "author-side retained packs are present" in artifact["closeout_checks"][4][
        "blocking_summary"
    ]

    guards = artifact["non_authoritative_guards"]
    assert guards["effect_scale_authority_released"] is False
    assert guards["component_failure_probability_authority_released"] is False
    assert guards["pk_authority_released"] is False
    assert guards["deterministic_fuze_authority_released"] is False


def test_a2_blastfrag_release_provenance_closeout_gate_fails_closed_when_author_side_source_evidence_missing(
    monkeypatch,
) -> None:
    original_read_text = gate._read_text

    def missing_verified_source_text(path: Path) -> str:
        text = original_read_text(path)
        if path == gate.DOC_REFS["artifact_pin_manifest"]:
            return text.replace("verified_candidate_artifact", "candidate_route_recorded")
        return text

    monkeypatch.setattr(gate, "_read_text", missing_verified_source_text)

    artifact = gate.generate_release_provenance_closeout_gate(repo_root=REPO_ROOT)

    retained_source = artifact["closeout_checks"][0]
    benchmark_trace = artifact["closeout_checks"][2]
    assert retained_source["author_side_satisfied"] is False
    assert retained_source["status"] == "blocked_author_side_evidence_missing"
    assert benchmark_trace["author_side_satisfied"] is False
    assert benchmark_trace["status"] == "blocked_author_side_evidence_missing"
    assert artifact["residual_condition_trace"][0]["author_side_satisfied_check_ids"] == [
        "CLOSEOUT-RES001-002"
    ]
    assert artifact["release_closeout_decision"]["release_closeout_blocked"] is True


def test_a2_blastfrag_release_provenance_closeout_gate_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_release_provenance_closeout_gate.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_release_provenance_closeout_gate.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert (
        artifact["status"]
        == "blocked_non_authoritative_release_provenance_closeout_candidate"
    )
    assert artifact["review_target"] == "res_001_002_release_provenance_closeout_lane"
    assert artifact["closeout_checks"][0]["check_id"] == "CLOSEOUT-RES001-001"
