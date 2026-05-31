from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_stage_b_release_readiness_gate as gate


def test_a2_blastfrag_stage_b_release_readiness_gate_current_repo_is_blocked() -> None:
    artifact = gate.generate_stage_b_release_readiness_gate(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_b_release_readiness_gate.v1"
    assert artifact["status"] == "blocked_non_authoritative_stage_b_release_candidate"
    assert artifact["release_target"] == "effect_scale_authority_only"
    assert (
        artifact["readiness_level"]
        == "author_side_candidate_review_ready_but_not_release_ready"
    )

    release = artifact["release_decision"]
    assert release["release_ready"] is False
    assert release["release_blocked"] is True
    assert release["current_hard_gate_snapshot_pass"] is True
    assert release["hard_gate_pass_is_release"] is False
    assert release["blocked_even_when_hard_gates_pass"] is True
    assert release["release_target"] == "effect_scale_authority_only"
    assert release["stage_c_component_probability_release_included"] is False
    assert release["stock_runtime_authority_granted"] is False

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["miss_distance_bucket"] == "near_miss_0_35m"

    satisfied = artifact["satisfied_conditions"]
    assert [row["condition_id"] for row in satisfied] == [
        "READY-001",
        "READY-002",
        "READY-003",
        "READY-004",
        "READY-005",
        "READY-006",
    ]

    blockers = artifact["blocking_conditions"]
    blocker_ids = [row["blocker_id"] for row in blockers]
    assert blocker_ids == [
        "BLOCK-001",
        "BLOCK-002",
        "BLOCK-003",
        "BLOCK-006",
        "BLOCK-007",
        "BLOCK-009",
        "BLOCK-011",
        "BLOCK-012",
    ]
    assert artifact["blocking_residual_ids"] == [
        "RES-010",
        "RES-002",
        "RES-001",
        "RES-008",
        "RES-010",
        "RES-012",
        "RES-011",
        "RES-013/014-boundary",
    ]
    assert artifact["stage_b_effect_scale_residual_scope"] == [
        "RES-007",
        "RES-008",
        "RES-010",
        "RES-011",
        "RES-012",
    ]
    assert artifact["open_stage_b_effect_scale_residual_ids"] == [
        "RES-010",
        "RES-011",
        "RES-012",
    ]

    assert any("independent review record is still missing" in row["summary"] for row in blockers)
    assert any("canonical retained artifact pack is present" in row["summary"] for row in blockers)
    assert any("clean release-grade identity state" in row["summary"] for row in blockers)
    assert any("externally verified and checksummed" in row["summary"] for row in blockers)
    assert any("candidate closure-sensitive response is present" in row["summary"] for row in blockers)
    assert any("RES-008 remains open" in row["summary"] for row in blockers)
    assert any("validation manifest still stays at not_run" in row["summary"] for row in blockers)
    assert any("independent benchmark/input separation review remains open" in row["summary"] for row in blockers)
    assert any("uncertainty coverage and independent closeout remain open" in row["summary"] for row in blockers)
    assert any("stock runtime authority remains explicitly closed" in row["summary"] for row in blockers)

    retained = artifact["retained_artifact_pack_summary"]
    assert retained["status"] == "author_retained_candidate_artifacts_only"
    assert retained["manifest_exists"] is True
    assert retained["retained_artifact_count"] == 4
    assert retained["all_artifacts_exist"] is True

    shared = artifact["shared_provenance_identity_gate_summary"]
    assert (
        shared["status"]
        == "blocked_non_authoritative_package_provenance_identity_candidate"
    )
    assert (
        shared["readiness_level"]
        == "author_side_pin_and_identity_surface_present_but_not_release_grade"
    )
    assert shared["satisfied_condition_count"] >= 5
    assert shared["blocking_condition_count"] >= 3
    assert "RES-001" in shared["blocking_residual_ids"]
    assert "RES-002" in shared["blocking_residual_ids"]
    assert "RES-013/014-boundary" in shared["blocking_residual_ids"]

    boundaries = artifact["explicit_boundaries"]
    assert "do not treat this gate as independent review" in boundaries
    assert "do not treat this gate as stock runtime authority" in boundaries

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_database_authority_granted"] is False
    assert guards["effect_scale_authority_in_stock"] is False
    assert guards["component_failure_probability_authority_in_stock"] is False
    assert guards["pk_authority"] is False
    assert guards["deterministic_fuze_authority"] is False


def test_a2_blastfrag_stage_b_release_readiness_gate_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_b_release_readiness_gate.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_b_release_readiness_gate.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["status"] == "blocked_non_authoritative_stage_b_release_candidate"
    assert artifact["release_target"] == "effect_scale_authority_only"
    assert artifact["blocking_conditions"][0]["blocker_id"] == "BLOCK-001"
