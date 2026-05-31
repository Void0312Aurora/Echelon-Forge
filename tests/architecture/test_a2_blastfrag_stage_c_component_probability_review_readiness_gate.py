from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_component_probability_review_readiness_gate as gate,
)


def test_a2_blastfrag_stage_c_component_probability_review_readiness_gate_is_blocked(
) -> None:
    artifact = gate.generate_stage_c_component_probability_review_readiness_gate(
        repo_root=REPO_ROOT
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert (
        artifact["schema_version"]
        == "a2.stage_c_component_probability_review_readiness_gate.v1"
    )
    assert artifact["status"] == "blocked_non_authoritative_stage_c_review_candidate"
    assert artifact["review_target"] == "component_failure_probability_authority_only"
    assert (
        artifact["readiness_level"]
        == "author_side_component_candidate_ready_but_not_fragility_review_closed"
    )

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["miss_distance_bucket"] == "near_miss"
    assert scope["candidate_scope_label"] == "near_miss_0_35m"
    assert scope["component_name"] == "right_aileron_actuator"
    assert scope["component_system"] == "flight_control"
    assert scope["component_redundancy_group_id"] == "lateral_flight_control_actuators"

    upstream = artifact["upstream_stage_b_dependency_summary"]
    assert upstream["dependency_role"] == (
        "separate_upstream_effect_scale_authority_track"
    )
    assert upstream["status"] == "blocked_non_authoritative_stage_b_release_candidate"
    assert upstream["release_target"] == "effect_scale_authority_only"
    assert upstream["dependency_preserved_as_blocked"] is True
    assert "RES-010" in upstream["blocking_residual_ids"]

    retained = artifact["retained_artifact_pack_summary"]
    assert (
        retained["status"]
        == "author_retained_stage_c_component_probability_candidate_artifacts_only"
    )
    assert retained["manifest_exists"] is True
    assert retained["retained_artifact_count"] == 4
    assert retained["all_artifacts_exist"] is True
    assert (
        retained["retention_scope"]
        == "stage_c_component_probability_author_side_candidate_only"
    )

    shared = artifact["shared_provenance_identity_gate_summary"]
    assert (
        shared["status"]
        == "blocked_non_authoritative_package_provenance_identity_candidate"
    )
    assert (
        shared["readiness_level"]
        == "author_side_pin_and_identity_surface_present_but_not_release_grade"
    )
    assert shared["satisfied_condition_count"] == 5
    assert shared["blocking_condition_count"] == 4
    assert shared["blocking_residual_ids"] == [
        "RES-001",
        "RES-002",
        "RES-013/014-boundary",
    ]

    candidate = artifact["candidate_row_summary"]
    assert candidate["component_name"] == "right_aileron_actuator"
    assert candidate["component_system"] == "flight_control"
    assert candidate["component_redundancy_group_id"] == "lateral_flight_control_actuators"
    assert candidate["component_failure_probability"] == 0.67
    assert candidate["baseline_component_probability_source"] == "synthetic_sigmoid"

    satisfied = artifact["satisfied_conditions"]
    assert [row["condition_id"] for row in satisfied] == [
        "READY-CP-001",
        "READY-CP-002",
        "READY-CP-003",
        "READY-CP-004",
        "READY-CP-005",
        "READY-CP-006",
        "READY-CP-007",
    ]

    blockers = artifact["blocking_conditions"]
    assert [row["blocker_id"] for row in blockers] == [
        "BLOCK-CP-001",
        "BLOCK-CP-002",
        "BLOCK-CP-003",
        "BLOCK-CP-004",
        "BLOCK-CP-005",
        "BLOCK-CP-008",
        "BLOCK-CP-009",
        "BLOCK-CP-011",
    ]
    assert artifact["blocking_residual_ids"] == [
        "RES-012",
        "RES-010",
        "RES-009",
        "RES-011",
        "RES-003",
        "RES-005",
        "RES-006",
        "RES-013/014-boundary",
    ]
    assert any("independent fragility review" in row["summary"] for row in blockers)
    assert any("validation manifest still stays at not_run" in row["summary"] for row in blockers)
    assert any("synthetic_sigmoid" in row["summary"] for row in blockers)
    assert any("uncertainty coverage" in row["summary"] for row in blockers)
    assert any("geometry truth remain candidate-only" in row["summary"] for row in blockers)
    assert any("fragment mechanism residual" in row["summary"] for row in blockers)
    assert any("blast mechanism residual" in row["summary"] for row in blockers)
    assert any("pk authority and deterministic fuze authority remain explicitly closed" in row["summary"] for row in blockers)

    boundaries = artifact["explicit_boundaries"]
    assert "do not treat this gate as independent fragility review" in boundaries
    assert "do not release pk or deterministic fuze from this Stage C gate" in boundaries

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["effect_scale_authority_in_stock"] is False
    assert guards["component_failure_probability_authority_in_stock"] is False
    assert guards["pk_authority"] is False
    assert guards["deterministic_fuze_authority"] is False


def test_a2_blastfrag_stage_c_component_probability_review_readiness_gate_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_component_probability_review_gate.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_c_component_probability_review_readiness_gate.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["status"] == "blocked_non_authoritative_stage_c_review_candidate"
    assert artifact["review_target"] == "component_failure_probability_authority_only"
    assert artifact["blocking_conditions"][0]["blocker_id"] == "BLOCK-CP-001"
