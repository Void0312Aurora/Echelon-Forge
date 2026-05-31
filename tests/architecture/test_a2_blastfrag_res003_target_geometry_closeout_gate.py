from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_res003_target_geometry_closeout_gate as gate,
)


def test_res003_target_geometry_closeout_closes_stage_b_witness_only() -> None:
    artifact = gate.generate_res003_target_geometry_closeout_gate(
        repo_root=REPO_ROOT
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.res003_target_geometry_closeout_gate.v1"
    assert artifact["status"] == (
        "res003_stage_b_effect_scale_witness_geometry_closeout_pass_release_blocked"
    )
    assert artifact["release_target"] == (
        "stage_b_effect_scale_witness_geometry_bookkeeping_only"
    )
    assert artifact["missing_evidence"] == []

    evidence = {row["evidence_id"]: row for row in artifact["consumed_evidence"]}
    assert set(evidence) == {
        "residual_register",
        "target_geometry_assumptions",
        "geometry_warhead_row_provenance_gate",
        "stage_b_independent_review_gate",
        "scope_bucket_independent_review_gate",
    }
    for row in evidence.values():
        assert row["present"] is True
        assert len(row["content_sha256"]) == 64
        assert row["content_hash"] == f"sha256:{row['content_sha256']}"
        assert row["size_bytes"] > 0

    assumption = artifact["stage_b_assumption_review"]
    assert assumption["status"] == "stage_b_assumption_surface_bounded"
    assert assumption["used_by_stage_b_geometry_items"] == [
        "outer_bbox",
        "beam_witness_panel",
    ]
    assert set(assumption["stage_b_source_ids"]) >= {
        "F16-TG-SRC-001",
        "F16-TG-SRC-002",
        "F16-TG-SRC-012",
    }
    assert assumption["row_findings"]["outer_bbox"]["support_level"] == (
        "candidate_dimension_anchor"
    )
    assert assumption["row_findings"]["beam_witness_panel"]["support_level"] == (
        "repo_authored_witness_geometry"
    )
    assert assumption["row_findings"]["right_aileron_actuator_projection"][
        "used_by_stage_b"
    ] == "no_for_stage_b_effect_scale_only"
    assert assumption["row_findings"]["internal_material_or_armor"][
        "support_level"
    ] == "unsupported"
    assert assumption["row_findings"]["occlusion_and_exposed_area_truth"][
        "support_level"
    ] == "unsupported"
    assert all(row["pass"] for row in assumption["checks"])

    provenance = artifact["provenance_interlock"]
    assert provenance["status"] == "row_provenance_interlock_preserved"
    assert provenance["upstream_res003_status"]["author_side_subslice_ready"] is True
    assert provenance["upstream_res003_status"]["release_grade"] is False
    assert provenance["upstream_res003_status"]["closed_by_this_gate"] is False
    assert all(row["pass"] for row in provenance["checks"])

    stage_b = artifact["stage_b_review_interlock"]
    assert stage_b["status"] == "stage_b_review_interlock_bounded"
    assert stage_b["bfm_bm_003_independence_row"]["allowed_claim"] == (
        "sampling replay and convergence inside witness-geometry bookkeeping"
    )
    assert stage_b["bfm_bm_003_independence_row"]["forbidden_claim"] == (
        "true F-16 exposure geometry or direction-pattern truth"
    )
    assert all(row["pass"] for row in stage_b["checks"])

    res003 = artifact["residual_closeout_decisions"]["RES-003"]
    assert res003["stage_b_effect_scale_witness_geometry"] == (
        "closed_narrow_non_authoritative"
    )
    assert res003["closed_residual_subscope"] == (
        "stage_b_effect_scale_witness_geometry_bookkeeping"
    )
    assert res003["global_target_geometry_authority"] == "not_granted"
    assert res003["real_f16_component_geometry_material_occlusion"] == "blocked"
    assert res003["phase5_component_probability_geometry_dependency"] == "blocked"
    assert res003["residual_register_edit_required_by_this_gate"] is False

    decision = artifact["closeout_decision"]
    assert decision["stage_b_effect_scale_witness_geometry_closeout_complete"] is True
    assert decision["stage_b_effect_scale_closeout_is_release_authority"] is False
    assert decision["global_res003_target_geometry_closeout_complete"] is False
    assert decision["real_f16_vulnerability_geometry_closeout_complete"] is False
    assert decision["closed_residual_ids_by_this_gate"] == []
    assert decision["closed_residual_subscopes_by_this_gate"] == [
        "RES-003:stage_b_effect_scale_witness_geometry_bookkeeping"
    ]
    assert decision["release_ready"] is False
    assert decision["release_blocked"] is True


def test_res003_target_geometry_closeout_keeps_authority_guards_false() -> None:
    artifact = gate.generate_res003_target_geometry_closeout_gate(
        repo_root=REPO_ROOT
    )

    guards = artifact["authority_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["target_geometry_authority_granted"] is False
    assert guards["target_component_geometry_authority_granted"] is False
    assert guards["target_material_authority_granted"] is False
    assert guards["target_occlusion_authority_granted"] is False
    assert guards["witness_geometry_bookkeeping_promoted_to_truth"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False
    assert not any(value is True for value in guards.values())

    boundaries = "\n".join(artifact["explicit_boundaries"])
    assert "Stage B effect-scale witness-geometry bookkeeping" in boundaries
    assert "not true 3D exposure geometry" in boundaries
    assert "No real F-16 component coordinates" in boundaries
    assert "Phase 5 component_failure_probability authority remains blocked" in boundaries


def test_res003_target_geometry_closeout_fails_closed_without_evidence(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_res003_target_geometry_closeout_gate(
        repo_root=REPO_ROOT,
        package_dir=tmp_path,
    )

    assert artifact["status"] == "res003_target_geometry_closeout_fail_closed"
    assert artifact["closeout_decision"][
        "stage_b_effect_scale_witness_geometry_closeout_complete"
    ] is False
    assert artifact["residual_closeout_decisions"]["RES-003"][
        "stage_b_effect_scale_witness_geometry"
    ] == "fail_closed"
    assert artifact["closeout_decision"]["closed_residual_subscopes_by_this_gate"] == []
    assert [row["evidence_id"] for row in artifact["missing_evidence"]] == [
        "residual_register",
        "target_geometry_assumptions",
        "geometry_warhead_row_provenance_gate",
        "stage_b_independent_review_gate",
        "scope_bucket_independent_review_gate",
    ]
    assert artifact["minimum_gap_list"][0]["gap_id"] == "missing:residual_register"
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_res003_target_geometry_closeout_cli_writes_retained_json_and_doc(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "res003_target_geometry_closeout_20260531"
    doc_output = tmp_path / "validation_res003_target_geometry_closeout_gate.md"
    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res003_target_geometry_closeout_gate.py",
            "--output-dir",
            str(output_dir),
            "--doc-output",
            str(doc_output),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    command_summary = json.loads(result.stdout)
    assert command_summary["status"] == (
        "res003_stage_b_effect_scale_witness_geometry_closeout_pass_release_blocked"
    )
    gate_path = output_dir / "res003_target_geometry_closeout_gate.json"
    manifest_path = output_dir / "manifest.json"
    assert gate_path.is_file()
    assert manifest_path.is_file()
    assert doc_output.is_file()

    artifact = json.loads(gate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert artifact["closeout_decision"][
        "stage_b_effect_scale_witness_geometry_closeout_complete"
    ] is True
    assert artifact["closeout_decision"]["release_ready"] is False
    assert manifest["schema_version"] == (
        "a2.res003_target_geometry_closeout_manifest.v1"
    )
    assert manifest["status"] == "res003_target_geometry_closeout_retained_release_blocked"
    assert manifest["artifacts"][0]["artifact_key"] == (
        "res003_target_geometry_closeout_gate"
    )
    assert manifest["artifacts"][0]["content_sha256"] == command_summary[
        "gate_sha256"
    ]
    assert manifest["authority_guards"]["target_geometry_authority_granted"] is False
    assert "RES-003 is narrowly closed only for Stage B effect-scale witness-geometry bookkeeping" in doc_output.read_text(
        encoding="utf-8"
    )
