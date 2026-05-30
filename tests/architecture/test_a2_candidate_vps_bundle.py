from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_candidate_vps_bundle as bundle


def test_a2_candidate_vps_bundle_current_repo_is_non_authoritative_and_review_ready() -> None:
    artifact = bundle.generate_candidate_bundle(repo_root=REPO_ROOT)

    assert artifact["bundle_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0_candidate_bundle_v0"
    )
    assert artifact["schema_version"] == "a2.vps_candidate_bundle.v1"
    assert artifact["status"] == "candidate_non_authoritative_bundle"

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["miss_distance_bucket"] == "near_miss_0_35m"

    boundary = artifact["authority_boundary"]
    assert not boundary["stock_descriptor_created"]
    assert not boundary["stock_database_authority_granted"]
    assert not boundary["effect_scale_authority_in_stock"]
    assert not boundary["component_failure_probability_authority_in_stock"]
    assert not boundary["pk_authority"]
    assert not boundary["deterministic_fuze_authority"]

    docs = artifact["documentation_status"]
    assert docs["ready_for_review"]
    assert docs["placeholder_hits"] == []

    doc_refs = artifact["doc_refs"]
    for ref in doc_refs.values():
        assert (REPO_ROOT / ref).exists()

    source_groups = artifact["source_groups"]
    assert len(source_groups) >= 4
    assert {entry["group_id"] for entry in source_groups} == {
        "target_geometry",
        "warhead_and_fuze",
        "mechanism_load_methods",
        "component_fragility_methods",
    }
    for entry in source_groups:
        assert (REPO_ROOT / entry["ledger_ref"]).exists()
        assert len(entry["selected_source_ids"]) >= 4

    residuals = artifact["open_residual_ids"]
    assert "RES-001" in residuals
    assert "RES-009" in residuals
    assert "RES-013" in residuals
    assert "RES-014" in residuals

    validation_summary = artifact["validation_scaffold_summary"]
    assert validation_summary["validation_status"] == "not_run"
    assert (
        validation_summary["current_authority_boundary"]["runtime_descriptor_status"]
        == "not_created"
    )
    assert validation_summary["implemented_benchmarks"] == [
        "BFM-BM-001",
        "BFM-BM-002",
        "BFM-BM-003",
        "BFM-BM-004",
        "BFM-BM-005",
        "BFM-BM-006",
    ]
    assert validation_summary["draft_descriptor_status"] == "schema_aligned_non_authoritative_draft"

    acceptance_summary = artifact["validation_acceptance_criteria_summary"]
    assert acceptance_summary["criteria_status"] == "frozen_pre_run_stage_b_effect_scale_only"
    assert acceptance_summary["primary_release_scope"] == "effect_scale_authority_only"
    assert acceptance_summary["component_probability_release_status"] == "deferred_to_stage_c"
    assert acceptance_summary["review_status"] == "author_frozen_pending_independent_review"
    assert acceptance_summary["runtime_descriptor_action"] == (
        "forbidden_until_review_record_and_benchmark_results_exist"
    )
    assert acceptance_summary["hard_gate_benchmarks"] == [
        "BFM-BM-001",
        "BFM-BM-003",
        "BFM-BM-005",
        "BFM-BM-006",
    ]
    assert acceptance_summary["deferred_items"] == [
        "BFM-DEF-001",
        "BFM-DEF-002",
        "BFM-DEF-003",
        "BFM-DEF-004",
    ]

    scope_summary = artifact["validation_scope_and_independence_summary"]
    assert scope_summary["scope_manifest_status"] == "frozen_pre_run_stage_b_effect_scale_only"
    assert scope_summary["primary_release_scope"] == "effect_scale_authority_only"
    assert scope_summary["independence_status"] == "documented_pre_run_pending_result_audit"
    assert scope_summary["review_status"] == "author_frozen_pending_independent_review"
    assert "runtime coarse bucket near_miss" in scope_summary["runtime_bucket_note"]
    assert scope_summary["boundary_probes"] == [
        "SCP-PROBE-001",
        "SCP-PROBE-002",
        "SCP-PROBE-003",
    ]
    assert scope_summary["out_of_scope_labels"] == [
        "closure_bucket != high",
        "direct_hit",
        "head_on",
        "high_off_boresight",
        "tail_chase",
        "weapon_family != blast_fragmentation",
    ]
    assert scope_summary["documented_benchmarks"] == [
        "BFM-BM-001",
        "BFM-BM-002",
        "BFM-BM-003",
        "BFM-BM-004",
        "BFM-BM-005",
        "BFM-BM-006",
    ]

    probe_summary = artifact["validation_scope_probe_summary"]
    assert probe_summary["status"] == "candidate_non_authoritative_scope_probe_results"
    assert probe_summary["scope"]["candidate_scope_label"] == "near_miss_0_35m"
    assert probe_summary["miss_distance_probe"]["probe_id"] == "SCP-PROBE-001"
    assert probe_summary["miss_distance_probe"]["row_count"] == 3
    assert probe_summary["miss_distance_probe"]["metrics"][
        "blast_scaled_distance_monotonic_increasing_pass"
    ]
    assert probe_summary["miss_distance_probe"]["metrics"][
        "fragment_areal_density_monotonic_decreasing_pass"
    ]
    assert probe_summary["miss_distance_probe"]["standoff_values_m"] == [0.25, 0.35, 0.45]
    assert probe_summary["closure_probe"]["probe_id"] == "SCP-PROBE-002"
    assert probe_summary["closure_probe"]["row_count"] == 3
    assert not probe_summary["closure_probe"]["metrics"]["mechanism_response_active"]
    assert probe_summary["closure_probe"]["metrics"][
        "mechanism_response_constant_across_closure"
    ]
    assert probe_summary["closure_probe"]["closure_values_mps"] == [700.0, 900.0, 1100.0]
    assert "does not consume closure_mps" in probe_summary["closure_probe"]["limitation_note"]
    assert probe_summary["aspect_guard_probe"]["probe_id"] == "SCP-PROBE-003"
    assert probe_summary["aspect_guard_probe"]["accepted_scope_labels"] == ["beam"]
    assert probe_summary["aspect_guard_probe"]["rejected_scope_labels"] == [
        "head_on",
        "tail_chase",
        "high_off_boresight",
        "direct_hit",
        "closure_bucket != high",
        "weapon_family != blast_fragmentation",
    ]

    stage_b_snapshot_summary = artifact["validation_benchmark_snapshot_summary"]
    assert stage_b_snapshot_summary["status"] == "candidate_non_authoritative_stage_b_snapshot"
    assert stage_b_snapshot_summary["all_hard_gates_pass_in_current_snapshot"]
    assert stage_b_snapshot_summary["failed_criteria_ids"] == []
    assert stage_b_snapshot_summary["reviewed_benchmarks"] == [
        "BFM-BM-001",
        "BFM-BM-003",
        "BFM-BM-005",
        "BFM-BM-006",
    ]
    assert (
        stage_b_snapshot_summary["review_status"]
        == "author_snapshot_only_pending_independent_review"
    )
    assert stage_b_snapshot_summary["fragment_areal_density_cv"] <= 0.05
    assert stage_b_snapshot_summary["fragment_energy_cv"] <= 0.05
    assert stage_b_snapshot_summary["penetration_margin_cv"] <= 0.05

    review_readiness = artifact["validation_review_readiness_summary"]
    assert (
        review_readiness["review_readiness_status"]
        == "author_review_ready_pending_independent_review"
    )
    assert review_readiness["primary_release_scope"] == "effect_scale_authority_only"
    assert review_readiness["independent_review_status"] == "not_started"
    assert review_readiness["benchmark_snapshot_status"] == "candidate_snapshot_generated"
    assert (
        review_readiness["stock_runtime_action"]
        == "forbidden_until_independent_review_and_residual_closeout"
    )
    assert review_readiness["review_ids"] == [
        "RR-ES-001",
        "RR-ES-002",
        "RR-ES-003",
        "RR-ES-004",
        "RR-ES-005",
    ]

    artifact_pin_summary = artifact["artifact_pin_manifest_summary"]
    assert artifact_pin_summary["manifest_status"] == "author_frozen_pending_independent_review"
    assert artifact_pin_summary["primary_release_scope"] == "effect_scale_authority_only"
    assert artifact_pin_summary["status_counts"]["acquired_for_candidate"] >= 4
    assert artifact_pin_summary["status_counts"]["sanity_only"] >= 1
    assert artifact_pin_summary["status_counts"]["pending_acquisition"] >= 2
    assert artifact_pin_summary["status_counts"]["rejected"] >= 2

    identity_summary = artifact["surrogate_identity_manifest_summary"]
    assert identity_summary["model_ref"] == (
        "candidate://a2/runtime-aligned-vps/"
        "f16c-aim120c-blastfrag-beam-high-nearmiss-0_35m-v0"
    )
    assert identity_summary["model_version"] == "v0_candidate_runtime_aligned"
    assert identity_summary["worktree_state"] == "dirty_and_untracked_present"
    assert identity_summary["current_validation_status"] == "not_validated"
    assert identity_summary["primary_release_scope"] == "effect_scale_authority_only"
    assert identity_summary["output_anchor_count"] == 3

    geometry_summary = artifact["target_geometry_assumption_summary"]
    assert geometry_summary["author_status"] == "frozen_for_stage_b_review_only"
    assert geometry_summary["target_type"] == "F-16C_Block50"
    assert geometry_summary["used_by_stage_b_yes_count"] >= 1
    assert geometry_summary["unsupported_row_count"] >= 2

    warhead_summary = artifact["warhead_scope_summary"]
    assert warhead_summary["weapon_class"] == "AIM-120C-class"
    assert warhead_summary["weapon_family"] == "blast_fragmentation"
    assert warhead_summary["consumed_by_surrogate_yes_count"] >= 2
    assert warhead_summary["rejected_rows"] >= 1

    exercise = artifact["runtime_aligned_authority_exercise_summary"]
    assert exercise["status"] == "test_local_authority_exercise_only"
    assert not exercise["authority_boundary"]["stock_database_authority_granted"]
    assert exercise["effect_scale_descriptor_candidate"]["effect_scale_authority"]
    assert not exercise["effect_scale_descriptor_candidate"][
        "component_failure_probability_authority"
    ]
    assert exercise["component_failure_probability_descriptor_candidate"][
        "component_failure_probability_authority"
    ]
    assert not exercise["component_failure_probability_descriptor_candidate"][
        "effect_scale_authority"
    ]


def test_a2_candidate_vps_bundle_cli_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "a2_candidate_vps_bundle.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_candidate_vps_bundle.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["status"] == "candidate_non_authoritative_bundle"
    assert artifact["documentation_status"]["ready_for_review"] is True
    assert artifact["authority_boundary"]["stock_database_authority_granted"] is False
    assert (
        artifact["validation_acceptance_criteria_summary"]["primary_release_scope"]
        == "effect_scale_authority_only"
    )
    assert (
        artifact["validation_scope_and_independence_summary"]["scope_manifest_status"]
        == "frozen_pre_run_stage_b_effect_scale_only"
    )
    assert (
        artifact["validation_scope_probe_summary"]["closure_probe"]["metrics"][
            "mechanism_response_constant_across_closure"
        ]
        is True
    )
    assert (
        artifact["validation_benchmark_snapshot_summary"][
            "all_hard_gates_pass_in_current_snapshot"
        ]
        is True
    )
