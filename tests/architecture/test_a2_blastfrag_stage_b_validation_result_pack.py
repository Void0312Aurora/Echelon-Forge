from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_stage_b_validation_result_pack as result_pack


def test_a2_blastfrag_stage_b_validation_result_pack_current_repo_is_non_authoritative() -> None:
    artifact = result_pack.generate_stage_b_validation_result_pack(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_b_validation_result_pack.v1"
    assert artifact["status"] == "candidate_non_authoritative_stage_b_result_pack"

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["candidate_scope_label"] == "near_miss_0_35m"
    assert scope["runtime_miss_distance_bucket"] == "near_miss"

    artifact_hashes = artifact["artifact_hashes"]
    assert len(artifact_hashes) == 3
    assert [row["artifact_id"] for row in artifact_hashes] == [
        "ART-SCAFFOLD-001",
        "ART-SCOPE-PROBE-001",
        "ART-STAGE-B-SNAPSHOT-001",
    ]
    assert all(len(row["sha256"]) == 64 for row in artifact_hashes)

    result_summary = artifact["result_table_summary"]
    assert result_summary["all_hard_gates_pass_in_current_snapshot"] is True
    assert result_summary["hard_gate_pass_is_release"] is False
    assert result_summary["failed_criteria_ids"] == []
    assert result_summary["reviewed_benchmarks"] == [
        "BFM-BM-001",
        "BFM-BM-003",
        "BFM-BM-005",
        "BFM-BM-006",
    ]
    assert result_summary["primary_release_scope"] == "effect_scale_authority_only"
    assert (
        result_summary["review_status"]
        == "author_result_pack_only_pending_independent_review"
    )
    assert len(result_summary["evidence_artifact_hashes"]["validation_scaffold"]) == 64
    assert len(result_summary["evidence_artifact_hashes"]["scope_boundary_probe"]) == 64
    assert len(result_summary["evidence_artifact_hashes"]["stage_b_snapshot"]) == 64

    release = artifact["release_readiness_interpretation"]
    assert release["current_hard_gate_snapshot_pass"] is True
    assert release["hard_gate_pass_is_release"] is False
    assert release["release_ready"] is False
    assert release["release_target"] == "effect_scale_authority_only"
    assert release["stage_c_component_probability_release_included"] is False
    assert release["stock_runtime_authority_granted"] is False

    uncertainty = artifact["uncertainty_result_summary"]
    assert uncertainty["fragment_areal_density_cv"] <= 0.05
    assert uncertainty["blast_impulse_cv"] <= 0.05
    assert uncertainty["fragment_energy_cv"] <= 0.05
    assert uncertainty["penetration_margin_cv"] <= 0.05
    assert uncertainty["seed_window_cv_pass"] is True
    assert "candidate uncertainty snapshot only" in uncertainty["result_interpretation"]

    scope_audit = artifact["scope_audit_summary"]
    assert scope_audit["miss_distance_row_count"] == 3
    assert scope_audit["miss_distance_monotonic_pass"] is True
    assert scope_audit["closure_mechanism_response_active"] is True
    assert "candidate closure-sensitive response is present" in scope_audit["closure_limitation_note"]
    assert "RES-008 remains open" in scope_audit["scope_guard_interpretation"]

    independence = artifact["independence_audit"]
    assert [row["benchmark_id"] for row in independence] == [
        "BFM-BM-001",
        "BFM-BM-002",
        "BFM-BM-003",
        "BFM-BM-004",
        "BFM-BM-005",
        "BFM-BM-006",
    ]
    bm005 = next(row for row in independence if row["benchmark_id"] == "BFM-BM-005")
    assert bm005["independence_class"] == "not_independent_real_validation"
    assert bm005["current_release_role"] == "integrated_mechanism_load_hygiene_only"
    assert bm005["audit_outcome"] == "candidate_hygiene_only_not_independent_validation"
    bm006 = next(row for row in independence if row["benchmark_id"] == "BFM-BM-006")
    assert bm006["audit_outcome"] == "administrative_gate_only"

    findings = artifact["current_findings"]
    assert "stable content hashes" in findings[0]
    assert "all current Stage B hard gates pass" in findings[1]
    assert "must not be narrated as independent surrogate validation" in findings[2]

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False


def test_a2_blastfrag_stage_b_validation_result_pack_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_b_validation_result_pack.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_b_validation_result_pack.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["status"] == "candidate_non_authoritative_stage_b_result_pack"
    assert artifact["result_table_summary"]["all_hard_gates_pass_in_current_snapshot"] is True
    assert artifact["scope_audit_summary"]["closure_mechanism_response_active"] is True
