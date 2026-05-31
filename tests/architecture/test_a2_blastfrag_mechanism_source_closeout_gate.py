from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_mechanism_source_closeout_gate as gate,
)


def test_a2_blastfrag_mechanism_source_closeout_gate_current_repo_is_blocked_review_ready() -> None:
    artifact = gate.generate_mechanism_source_closeout_gate(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.mechanism_source_closeout_gate.v1"
    assert (
        artifact["status"]
        == "blocked_non_authoritative_mechanism_source_closeout_candidate"
    )
    assert artifact["review_target"] == (
        "res_003_004_005_006_mechanism_source_closeout_lane"
    )
    assert artifact["readiness_level"] == (
        "author_side_evidence_present_but_calibrated_authority_blocked"
    )

    assert artifact["documentation_status"]["ready_for_review"] is True
    assert artifact["documentation_status"]["placeholder_hits"] == []
    for ref in artifact["doc_refs"].values():
        assert (REPO_ROOT / ref).exists()

    assert artifact["current_gate_results"] == {
        "RES-003": "blocked_author_side_review_ready",
        "RES-004": "blocked_author_side_review_ready",
        "RES-005": "blocked_author_side_review_ready",
        "RES-006": "blocked_author_side_review_ready",
    }
    decision = artifact["closeout_decision"]
    assert decision["mechanism_source_closeout_ready"] is False
    assert decision["mechanism_source_closeout_blocked"] is True
    assert decision["author_side_subitems_recorded"] is True
    assert decision["closed_residual_ids_by_this_gate"] == []
    assert decision["authority_release_included"] is False

    assert [row["check_id"] for row in artifact["closeout_checks"]] == [
        "CLOSEOUT-RES003-001",
        "CLOSEOUT-RES003-002",
        "CLOSEOUT-RES004-001",
        "CLOSEOUT-RES004-002",
        "CLOSEOUT-RES005-001",
        "CLOSEOUT-RES005-002",
        "CLOSEOUT-RES006-001",
        "CLOSEOUT-RES006-002",
    ]
    assert all(row["author_side_satisfied"] for row in artifact["closeout_checks"])
    assert not any(row["release_grade_satisfied"] for row in artifact["closeout_checks"])
    assert {row["status"] for row in artifact["closeout_checks"]} == {
        "blocked_release_grade_evidence_missing"
    }

    res003 = artifact["closeout_checks"][0]
    assert "F16-TG-SRC-012" in res003["observed_author_side_evidence"][
        "source_evidence"
    ]["present_source_ids"]
    assert "PIN-F16-003" in res003["observed_author_side_evidence"][
        "pin_evidence"
    ]["sanity_only_pin_ids"]
    assert "engineering hitboxes are not calibrated vulnerability geometry" in res003[
        "blocking_summary"
    ]

    res004 = artifact["closeout_checks"][2]
    assert res004["observed_author_side_evidence"]["warhead_scope_summary"][
        "weapon_class"
    ] == "AIM-120C-class"
    assert "PIN-AIM120-TPC-REJ" in res004["observed_author_side_evidence"][
        "pin_evidence"
    ]["rejected_pin_ids"]
    assert "variant-specific warhead mass" in res004["blocking_summary"]

    res005 = artifact["closeout_checks"][5]
    assert res005["observed_author_side_evidence"]["bm005_audit_outcome"] == (
        "candidate_hygiene_only_not_independent_validation"
    )
    assert res005["observed_author_side_evidence"][
        "stage_c_gate_band_fragment_energy_pass"
    ] is True
    assert "toy/integration hygiene" in res005["blocking_summary"]

    res006 = artifact["closeout_checks"][6]
    assert "PIN-BFM-001" in res006["observed_author_side_evidence"][
        "pin_evidence"
    ]["retention_pending_pin_ids"]
    assert "VPS-BFM-003" in res006["observed_author_side_evidence"][
        "source_evidence"
    ]["rejected_or_pending_source_ids"]
    assert "retained comparison outputs" in res006["blocking_summary"]

    assert artifact["residual_condition_trace"] == [
        {
            "residual_id": "RES-003",
            "author_side_satisfied_check_ids": [
                "CLOSEOUT-RES003-001",
                "CLOSEOUT-RES003-002",
            ],
            "release_grade_blocking_check_ids": [
                "CLOSEOUT-RES003-001",
                "CLOSEOUT-RES003-002",
            ],
            "gate_result": "blocked_author_side_review_ready",
        },
        {
            "residual_id": "RES-004",
            "author_side_satisfied_check_ids": [
                "CLOSEOUT-RES004-001",
                "CLOSEOUT-RES004-002",
            ],
            "release_grade_blocking_check_ids": [
                "CLOSEOUT-RES004-001",
                "CLOSEOUT-RES004-002",
            ],
            "gate_result": "blocked_author_side_review_ready",
        },
        {
            "residual_id": "RES-005",
            "author_side_satisfied_check_ids": [
                "CLOSEOUT-RES005-001",
                "CLOSEOUT-RES005-002",
            ],
            "release_grade_blocking_check_ids": [
                "CLOSEOUT-RES005-001",
                "CLOSEOUT-RES005-002",
            ],
            "gate_result": "blocked_author_side_review_ready",
        },
        {
            "residual_id": "RES-006",
            "author_side_satisfied_check_ids": [
                "CLOSEOUT-RES006-001",
                "CLOSEOUT-RES006-002",
            ],
            "release_grade_blocking_check_ids": [
                "CLOSEOUT-RES006-001",
                "CLOSEOUT-RES006-002",
            ],
            "gate_result": "blocked_author_side_review_ready",
        },
    ]


def test_a2_blastfrag_mechanism_source_closeout_gate_keeps_authority_guards_false() -> None:
    artifact = gate.generate_mechanism_source_closeout_gate(repo_root=REPO_ROOT)

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["target_geometry_authority_granted"] is False
    assert guards["aim120c_warhead_authority_granted"] is False
    assert guards["fragment_mechanism_authority_granted"] is False
    assert guards["blast_mechanism_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False

    evidence = artifact["mechanism_load_evidence_summary"]
    assert evidence["validation_scaffold_status"] == "not_run"
    assert evidence["stage_b_all_hard_gates_pass"] is True
    assert evidence["stage_b_review_status"] == (
        "author_snapshot_only_pending_independent_review"
    )
    assert evidence["stage_c_baseline_component_probability_source"] == (
        "synthetic_sigmoid"
    )
    assert any("engineering hitboxes" in risk for risk in artifact["behavior_risks"])
    assert any("toy probes" in risk for risk in artifact["behavior_risks"])
    assert any("RES-013 Pk" in note for note in artifact["integration_notes"])
    assert any(
        "RES-014 deterministic fuze" in note for note in artifact["integration_notes"]
    )


def test_a2_blastfrag_mechanism_source_closeout_gate_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "mechanism_source_closeout_gate.json"

    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_mechanism_source_closeout_gate.py",
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
    assert artifact["schema_version"] == "a2.mechanism_source_closeout_gate.v1"
    assert artifact["current_gate_results"]["RES-003"] == (
        "blocked_author_side_review_ready"
    )
    assert artifact["current_gate_results"]["RES-006"] == (
        "blocked_author_side_review_ready"
    )
    assert artifact["non_authoritative_guards"]["pk_authority_granted"] is False
    assert (
        artifact["non_authoritative_guards"]["deterministic_fuze_authority_granted"]
        is False
    )
