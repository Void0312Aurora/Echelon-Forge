from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path, read_json
from tests.architecture.damage_model.helpers import run_maintenance_cli

ensure_repo_root_on_sys_path()

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_package_provenance_identity_gate as package_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_provenance_identity_review_gate as review_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_release_provenance_closeout_gate as closeout_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_res001_release_signoff_gate as release_signoff_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_res002_scoped_release_identity_gate as scoped_identity_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_b_release_closeout as effect_scale_release_closeout,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_b_release_readiness_gate as effect_scale_release_readiness,
)


# Release signoff and scoped release identity guardrails.
def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_release_signoff_gate_current_repo_is_narrowly_closeable(
    tmp_path: Path,
) -> None:
    artifact = release_signoff_gate.write_retained_artifacts(
        output_dir=tmp_path / "retained",
        report_path=tmp_path / "validation_res001_release_signoff_gate_20260531.zh.md",
    )

    assert artifact["schema_version"] == "a2.res001_release_signoff_gate.v1"
    assert artifact["status"] == (
        "narrowly_closeable_internal_release_signoff_fail_closed_boundaries"
    )
    decision = artifact["residual_decision"]
    assert decision["gate_result"] == (
        "narrowly_closeable_by_internal_release_signoff_gate"
    )
    assert decision["residual_closeable_by_this_gate"] is True
    assert decision["closed_residual_ids_by_this_gate"] == ["RES-001"]
    assert decision["missing_required_fields"] == []
    assert decision["release_grade_legal_rights_asserted"] is False
    assert decision["legal_advice_provided"] is False
    assert "RES-002" in decision["residual_ids_not_closed_by_this_gate"]
    assert "RES-005" in decision["residual_ids_not_closed_by_this_gate"]

    checks = {row["check_id"]: row["satisfied"] for row in artifact["required_checks"]}
    assert set(checks) == set(release_signoff_gate.REQUIRED_CHECKS)
    assert all(checks.values())

    payload = artifact["source_payload_retention"]
    assert payload["complete"] is True
    assert payload["payload_hashes_match"] is True
    assert payload["required_payload_count"] == 3
    assert payload["retained_payload_count"] == 3
    assert all(row["payload_exists"] for row in payload["payloads"])
    assert all(row["hash_matches_expected"] for row in payload["payloads"])
    assert all(
        row["benchmark_consumed_for_release"] is False for row in payload["payloads"]
    )

    rights = artifact["rights_and_output_policy"]
    assert rights["public_distribution_support_present"] is True
    assert rights["release_grade_legal_rights_asserted"] is False
    assert rights["release_grade_legal_rights_not_asserted"] is True
    assert rights["allowed_output_policy_status"] == (
        "release_candidate_fail_closed_policy_frozen"
    )
    assert rights["allowed_output_policy_frozen_fail_closed"] is True
    assert rights["raw_payload_bodies_non_copyable"] is True
    assert rights["copy_policy_summary"] == {
        "payload_bodies": "non_copyable",
        "spreadsheet_cells_formulas_outputs": "non_copyable",
        "comparison_values": "non_copyable",
        "hashes_and_policy_metadata": "copyable_as_evidence_only",
    }

    benchmark = artifact["benchmark_and_comparison_output_policy"]
    assert benchmark["benchmark_consumption_decision"]["decision"] == (
        "explicit_release_non_consumption"
    )
    assert benchmark["benchmark_consumption_decision"]["satisfied"] is True
    assert benchmark["benchmark_consumption_decision"][
        "source_release_consumed_requirement_ids"
    ] == []
    assert benchmark["benchmark_consumption_decision"][
        "mechanism_outputs_benchmark_consumed_for_release"
    ] is False
    assert benchmark["beco_outputs_release_consumed"] is False
    assert benchmark["tp21_outputs_release_consumed"] is False
    assert benchmark[
        "beco_tp21_outputs_not_release_consumed_unless_hash_only_admitted"
    ] is True
    assert benchmark["comparison_values_not_copied"] is True
    assert benchmark["hash_only_comparison_anchor_count"] == 9
    assert benchmark["tp21_selected_debris_output_hashes_present"] is False

    provenance = artifact["provenance_identity_review_consumption"]
    assert provenance["res001_author_side_checks_present"] is True
    assert provenance["provenance_gate_result_for_res001"] == "blocked"
    assert provenance["res002_not_closed_by_this_gate"] is True

    authority = artifact["authority_boundary_signoff"]
    assert authority["signed_off_by_this_gate"] is True
    assert authority["authority_guards_all_false"] is True
    assert authority["stock_effect_component_pk_fuze_authority_all_false"] is True
    assert not any(authority["non_authoritative_guards"].values())

    gate_json = tmp_path / "retained" / release_signoff_gate.GATE_FILENAME
    manifest_json = tmp_path / "retained" / release_signoff_gate.MANIFEST_FILENAME
    report = tmp_path / "validation_res001_release_signoff_gate_20260531.zh.md"
    assert gate_json.exists()
    assert manifest_json.exists()
    assert report.exists()
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "a2.res001_release_signoff_manifest.v1"
    assert manifest["residual_decision"]["closed_residual_ids_by_this_gate"] == [
        "RES-001"
    ]
    assert manifest["res001_release_signoff_gate"]["sha256"]
    assert manifest["validation_report"]["sha256"]
    assert not any(manifest["non_authoritative_guards"].values())


def test_release_signoff_gate_fails_closed_for_incomplete_payload(
    tmp_path: Path,
) -> None:
    source_manifest = json.loads(release_signoff_gate.SOURCE_ARTIFACT_PACK_MANIFEST.read_text())
    source_manifest["all_payloads_exist"] = False
    source_manifest["all_payload_hashes_match"] = False
    source_manifest["source_payloads_retained"] = False
    source_manifest["retained_payload_count"] = 2
    source_manifest["artifacts"][0]["relative_path"] = str(tmp_path / "missing.pdf")
    bad_source_manifest = _write_json(tmp_path / "source_manifest.json", source_manifest)

    artifact = release_signoff_gate.generate_res001_release_signoff_gate(
        source_manifest_path=bad_source_manifest,
        output_dir=tmp_path / "out",
    )

    assert artifact["status"] == "failed_closed_res001_release_signoff_evidence_incomplete"
    assert artifact["residual_decision"]["residual_closeable_by_this_gate"] is False
    assert artifact["residual_decision"]["closed_residual_ids_by_this_gate"] == []
    assert artifact["residual_decision"]["missing_required_fields"] == [
        "payload_retention_complete",
        "payload_hashes_match",
    ]
    assert artifact["authority_boundary_signoff"]["signed_off_by_this_gate"] is False


def test_release_signoff_gate_fails_closed_for_raw_comparison_value(
    tmp_path: Path,
) -> None:
    mechanism = json.loads(release_signoff_gate.MECHANISM_HASHES.read_text())
    mechanism["beco_workbook"]["selected_comparison_hashes"][0][
        "cached_formula_value"
    ] = "must-not-copy"
    bad_mechanism = _write_json(tmp_path / "mechanism_comparison_hashes.json", mechanism)

    artifact = release_signoff_gate.generate_res001_release_signoff_gate(
        mechanism_hashes_path=bad_mechanism,
        output_dir=tmp_path / "out",
    )

    assert artifact["status"] == "failed_closed_res001_release_signoff_evidence_incomplete"
    assert artifact["residual_decision"]["missing_required_fields"] == [
        "comparison_values_not_copied",
    ]
    assert artifact["benchmark_and_comparison_output_policy"][
        "benchmark_consumption_decision"
    ]["raw_comparison_values_detected"] is True


def test_release_signoff_gate_fails_closed_for_authority_guard(
    tmp_path: Path,
) -> None:
    rights = json.loads(release_signoff_gate.SOURCE_RIGHTS_GATE.read_text())
    rights["non_authoritative_guards"]["pk_authority"] = True
    bad_rights = _write_json(tmp_path / "source_rights_output_policy_gate.json", rights)

    artifact = release_signoff_gate.generate_res001_release_signoff_gate(
        source_rights_gate_path=bad_rights,
        output_dir=tmp_path / "out",
    )

    assert artifact["status"] == "failed_closed_res001_release_signoff_evidence_incomplete"
    assert artifact["residual_decision"]["missing_required_fields"] == [
        "authority_guards_all_false"
    ]
    authority = artifact["authority_boundary_signoff"]
    assert authority["authority_guards_all_false"] is False
    assert authority["stock_effect_component_pk_fuze_authority_all_false"] is False
    assert authority["non_authoritative_guards"]["pk_authority"] is True


def test_release_signoff_gate_cli_writes_default_artifacts() -> None:
    result = subprocess.run(
        [sys.executable, "tools/maintenance/a2_blastfrag_res001_release_signoff_gate.py"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert result.stdout == ""
    gate_path = release_signoff_gate.DEFAULT_OUTPUT_DIR / release_signoff_gate.GATE_FILENAME
    manifest_path = release_signoff_gate.DEFAULT_OUTPUT_DIR / release_signoff_gate.MANIFEST_FILENAME
    assert gate_path.exists()
    assert manifest_path.exists()
    artifact = json.loads(gate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert artifact["residual_decision"]["gate_result"] == (
        "narrowly_closeable_by_internal_release_signoff_gate"
    )
    assert manifest["residual_decision"]["closed_residual_ids_by_this_gate"] == [
        "RES-001"
    ]


def test_scoped_release_identity_gate_passes_scoped_surface() -> None:
    artifact = scoped_identity_gate.generate_res002_scoped_release_identity_gate(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.res002_scoped_release_identity_gate.v1"
    assert artifact["status"] == "scoped_res002_identity_pass_non_authoritative"
    assert artifact["decision"]["res002_scoped_package_identity"] == (
        "narrow_scoped_identity_pass"
    )
    assert artifact["decision"]["res002_residual_register_status_change"] == (
        "not_applied"
    )
    assert artifact["decision"]["release_validation_status_promoted"] is False
    assert artifact["decision"]["authority_release_included"] is False
    assert artifact["decision"]["global_release_identity_claimed"] is False

    model_identity = artifact["model_identity"]
    assert model_identity["model_ref"] == (
        "candidate://a2/runtime-aligned-vps/"
        "f16c-aim120c-blastfrag-beam-high-nearmiss-0_35m-v0"
    )
    assert model_identity["model_version"] == "v0_candidate_runtime_aligned"
    assert len(model_identity["head_commit"]) == 40
    assert model_identity["identity_manifest_validation_status"] == "not_validated"

    checks = artifact["identity_surface_checks"]
    assert checks["all_relevant_files_exist"] is True
    assert checks["required_retained_artifacts_under_repo_paths"] is True
    assert checks["source_payload_pack_retained_and_hash_verified"] is True
    assert checks["provenance_identity_review_consumed"] is True
    assert checks["authority_guards_all_false"] is True
    assert checks["missing_forbidden_outputs"] == []
    assert checks["legacy_identity_manifest_temp_anchor_count"] >= 3

    assert artifact["temporary_anchor_scan"]["scoped_surface_anchor_count"] == 0
    assert artifact["temporary_anchor_scan"]["scoped_surface_contains_temp_anchors"] is False
    assert scoped_identity_gate.TEMP_ANCHOR not in json.dumps(artifact, sort_keys=True)

    assert len(artifact["retained_artifact_directory_summary"]) == 8
    assert all(
        row["exists"] and row["file_count"] > 0
        for row in artifact["retained_artifact_directory_summary"]
    )
    assert len(artifact["retained_artifact_hash_inventory"]) >= 20
    assert len(artifact["relevant_file_hash_inventory"]) == len(scoped_identity_gate.DOC_REFS)
    assert all(row["sha256"] for row in artifact["relevant_file_hash_inventory"])
    assert artifact["dirty_worktree_note"]["global_worktree_dirty"] is True
    assert artifact["dirty_worktree_note"]["unrelated_dirty_path_count"] > 0
    assert artifact["policy_evaluation"]["standards_global_clean_policy"][
        "global_clean_worktree_required"
    ] is False

    guards = artifact["authority_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["runtime_authority_granted"] is False
    assert guards["effect_scale_authority_released"] is False
    assert guards["component_failure_probability_authority_released"] is False
    assert guards["pk_authority_released"] is False
    assert guards["deterministic_fuze_authority_released"] is False
    assert guards["validation_status_promoted"] is False
    assert guards["residual_register_edited"] is False


def test_scoped_release_identity_gate_fails_closed_when_global_clean_required() -> None:
    artifact = scoped_identity_gate.generate_res002_scoped_release_identity_gate(
        repo_root=REPO_ROOT,
        force_global_clean_required=True,
    )

    assert artifact["status"] == "failed_closed_global_clean_worktree_required"
    assert artifact["decision"]["res002_scoped_package_identity"] == "fail_closed"
    assert artifact["decision"]["global_clean_worktree_required"] is True
    assert artifact["policy_evaluation"][
        "global_dirty_policy_required_and_unsatisfied"
    ] is True
    assert "globally clean worktree" in artifact["decision"]["fail_closed_reason"]
    assert artifact["dirty_worktree_note"]["global_worktree_dirty"] is True
    assert artifact["decision"]["release_validation_status_promoted"] is False
    assert not any(artifact["authority_guards"].values())


def test_scoped_release_identity_gate_writes_retained_bundle(
    tmp_path: Path,
) -> None:
    manifest = scoped_identity_gate.write_retained_scoped_identity_artifact(
        repo_root=REPO_ROOT,
        retained_output_dir=tmp_path,
    )

    artifact_path = tmp_path / scoped_identity_gate.GATE_FILENAME
    manifest_path = tmp_path / scoped_identity_gate.MANIFEST_FILENAME
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert manifest_path.exists()
    assert artifact_path.exists()
    assert manifest["schema_version"] == "a2.res002_scoped_release_identity_manifest.v1"
    assert manifest["scoped_gate_status"] == artifact["status"]
    assert manifest["scoped_identity_decision"] == "narrow_scoped_identity_pass"
    assert manifest["retained_input_directory_count"] == 8
    assert manifest["retained_input_artifact_count"] == len(
        artifact["retained_artifact_hash_inventory"]
    )
    assert manifest["relevant_file_hash_count"] == len(scoped_identity_gate.DOC_REFS)
    assert manifest["temporary_anchor_scan"]["scoped_surface_anchor_count"] == 0
    assert manifest["artifacts"][0]["sha256"] == scoped_identity_gate._sha256_file(artifact_path)
    assert not any(manifest["authority_guards"].values())


def test_scoped_release_identity_gate_cli_default_writes_manifest(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools/maintenance/a2_blastfrag_res002_scoped_release_identity_gate.py"),
            "--retained-output-dir",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "a2.res002_scoped_release_identity_manifest.v1"
    assert payload["scoped_gate_status"] == (
        "scoped_res002_identity_pass_non_authoritative"
    )
    assert (tmp_path / scoped_identity_gate.GATE_FILENAME).exists()
    assert (tmp_path / scoped_identity_gate.MANIFEST_FILENAME).exists()


# Effect-scale release readiness and closeout guardrails.
def test_effect_scale_release_readiness_gate_current_repo_is_blocked() -> None:
    artifact = effect_scale_release_readiness.generate_stage_b_release_readiness_gate(repo_root=REPO_ROOT)

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
    assert artifact["open_stage_b_effect_scale_residual_ids"] == []
    assert artifact["authority_blocked_stage_b_effect_scale_residual_ids"] == [
        "RES-010",
        "RES-011",
        "RES-012",
    ]

    assert any("independent review record is still missing" in row["summary"] for row in blockers)
    assert any("canonical retained artifact pack is present" in row["summary"] for row in blockers)
    assert any("clean release-grade identity state" in row["summary"] for row in blockers)
    assert any("externally verified and checksummed" in row["summary"] for row in blockers)
    assert any("candidate closure-sensitive response is present" in row["summary"] for row in blockers)
    assert any("RES-008 remains non-authoritative" in row["summary"] for row in blockers)
    assert any("validation manifest still stays at not_run" in row["summary"] for row in blockers)
    assert any("independent benchmark/input separation review remains authority-blocked" in row["summary"] for row in blockers)
    assert any("uncertainty coverage and independent closeout remain authority-blocked" in row["summary"] for row in blockers)
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


def test_effect_scale_release_readiness_gate_cli_writes_json(
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


def test_effect_scale_release_closeout_preserves_blocked_release() -> None:
    artifact = effect_scale_release_closeout.generate_stage_b_release_closeout(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_b_release_closeout.v1"
    assert (
        artifact["status"]
        == "author_side_stage_b_release_closeout_complete_release_blocked"
    )
    assert artifact["release_target"] == "effect_scale_authority_only"
    assert artifact["focused_residual_ids"] == [
        "RES-007",
        "RES-008",
        "RES-010",
        "RES-011",
        "RES-012",
    ]

    release = artifact["release_decision"]
    assert release["current_hard_gate_snapshot_pass"] is True
    assert release["hard_gate_pass_is_release"] is False
    assert release["blocked_even_when_hard_gates_pass"] is True
    assert release["release_ready"] is False
    assert release["release_blocked"] is True
    assert release["stage_c_component_probability_release_included"] is False
    assert release["stock_runtime_authority_granted"] is False

    run_manifest = artifact["validation_run_manifest"]
    assert run_manifest["run_id"] == "STAGE-B-ES-RUN-20260531-001"
    assert run_manifest["run_status"] == "author_side_executed_non_authoritative"
    assert run_manifest["seed"] == 20260529
    assert run_manifest["sample_count"] == 4096
    assert run_manifest["scope_probe_standoffs_m"] == [0.25, 0.35, 0.45]
    assert run_manifest["scope_probe_closures_mps"] == [700.0, 900.0, 1100.0]

    execution = artifact["benchmark_result_execution_record"]
    assert execution["execution_status"] == "author_side_hard_gates_passed_non_release"
    assert execution["criteria_counts"] == {
        "criteria_count": 18,
        "passed_criteria_count": 18,
        "failed_criteria_count": 0,
        "failed_criteria_ids": [],
        "all_hard_gates_pass": True,
    }
    assert execution["hard_gate_pass_is_release"] is False
    assert len(execution["criteria_results"]) == 18
    assert all(row["pass"] for row in execution["criteria_results"])
    assert len(execution["artifact_hashes"]) == 3

    residuals = {
        row["residual_id"]: row
        for row in artifact["residual_gate_results"]
    }
    assert list(residuals) == [
        "RES-007",
        "RES-008",
        "RES-010",
        "RES-011",
        "RES-012",
    ]
    assert residuals["RES-007"]["gate_result"] == (
        "author_scope_closeout_passed_pending_independent_review"
    )
    assert residuals["RES-008"]["gate_result"] == (
        "author_scope_closeout_passed_pending_independent_review"
    )
    assert residuals["RES-010"]["gate_result"] == (
        "author_execution_record_passed_pending_independent_review"
    )
    assert residuals["RES-011"]["gate_result"] == (
        "author_uncertainty_closeout_passed_pending_independent_review"
    )
    assert residuals["RES-012"]["gate_result"] == (
        "author_independence_trace_complete_pending_independent_review"
    )
    assert all(row["author_side_closeout_complete"] is True for row in residuals.values())
    assert all(row["release_blocked"] is True for row in residuals.values())

    near_miss = artifact["near_miss_bucket_closeout"]
    assert near_miss["author_side_closeout_complete"] is True
    assert [row["standoff_m"] for row in near_miss["rows"]] == [0.25, 0.35, 0.45]
    assert near_miss["metrics"]["blast_scaled_distance_monotonic_increasing_pass"] is True
    assert near_miss["metrics"]["fragment_areal_density_monotonic_decreasing_pass"] is True
    assert near_miss["metrics"]["runtime_bucket_consistent_pass"] is True

    beam_high = artifact["beam_high_scope_closeout"]
    assert beam_high["author_side_closeout_complete"] is True
    assert [row["closure_mps"] for row in beam_high["closure_probe"]["rows"]] == [
        700.0,
        900.0,
        1100.0,
    ]
    closure_metrics = beam_high["closure_probe"]["metrics"]
    assert closure_metrics["mechanism_response_active"] is True
    assert closure_metrics["res008_closed_by_probe"] is False
    assert closure_metrics["independent_review_complete"] is False
    assert "direct_hit" in beam_high["aspect_guard"]["rejected_scope_labels"]

    uncertainty = artifact["uncertainty_closeout"]
    assert uncertainty["author_side_closeout_complete"] is True
    assert uncertainty["seed_window_cv_pass"] is True
    assert all(row["pass"] for row in uncertainty["cv_rows"])

    independence = artifact["independence_review_dependency_trace"]
    assert independence["author_side_closeout_complete"] is True
    bm005 = next(
        row
        for row in independence["benchmark_independence_rows"]
        if row["benchmark_id"] == "BFM-BM-005"
    )
    assert bm005["independence_class"] == "not_independent_real_validation"
    assert bm005["audit_outcome"] == "candidate_hygiene_only_not_independent_validation"
    assert independence["review_dependency_trace"][0]["owner"] == "independent_reviewer"
    assert independence["review_dependency_trace"][0]["status"] == "missing"

    dependencies = {
        row["dependency"]: row
        for row in artifact["remaining_release_dependencies"]
    }
    assert dependencies["independent_review"]["status"] == "blocked"
    assert dependencies["release_grade_provenance_identity"]["status"] == "blocked"
    assert dependencies["stock_runtime_descriptor"]["status"] == "forbidden"

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False


def test_effect_scale_release_closeout_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_b_release_closeout.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_b_release_closeout.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert (
        artifact["status"]
        == "author_side_stage_b_release_closeout_complete_release_blocked"
    )
    assert artifact["release_decision"]["hard_gate_pass_is_release"] is False
    assert artifact["residual_gate_results"][0]["residual_id"] == "RES-007"


# Provenance and identity release guardrails.
def test_package_provenance_identity_gate_is_blocked() -> None:
    artifact = package_gate.generate_package_provenance_identity_gate(
        repo_root=REPO_ROOT
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.package_provenance_identity_gate.v1"
    assert (
        artifact["status"]
        == "blocked_non_authoritative_package_provenance_identity_candidate"
    )
    assert (
        artifact["review_target"]
        == "shared_provenance_and_surrogate_identity_surface"
    )
    assert (
        artifact["readiness_level"]
        == "author_side_pin_and_identity_surface_present_but_not_release_grade"
    )

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["miss_distance_bucket"] == "near_miss_0_35m"

    pin_summary = artifact["artifact_pin_manifest_summary"]
    assert pin_summary["manifest_status"] == "author_frozen_pending_independent_review"
    assert (
        pin_summary["package_provenance_status"]
        == "official_public_artifacts_partially_verified_release_grade_closeout_pending"
    )
    assert pin_summary["status_counts"]["verified_candidate_artifact"] == 2
    assert pin_summary["status_counts"]["pending_acquisition"] == 0
    assert pin_summary["status_counts"]["sanity_only"] >= 1

    identity = artifact["surrogate_identity_summary"]
    assert identity["model_ref"].startswith("candidate://a2/runtime-aligned-vps/")
    assert identity["model_version"] == "v0_candidate_runtime_aligned"
    assert len(identity["repo_commit"]) == 40
    assert (
        identity["worktree_state"]
        == "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present"
    )
    assert identity["retained_artifact_pack_status"] == "present_author_side_non_authoritative"
    assert identity["retained_artifact_count"] == 4
    assert identity["current_validation_status"] == "not_validated"
    assert identity["output_anchor_count"] >= 3

    retained = artifact["retained_artifact_pack_summary"]
    assert retained["stage_b"]["status"] == "author_retained_candidate_artifacts_only"
    assert retained["stage_b"]["manifest_exists"] is True
    assert retained["stage_b"]["retained_artifact_count"] == 4
    assert retained["stage_b"]["all_artifacts_exist"] is True
    assert (
        retained["stage_c"]["status"]
        == "author_retained_stage_c_component_probability_candidate_artifacts_only"
    )
    assert retained["stage_c"]["manifest_exists"] is True
    assert retained["stage_c"]["retained_artifact_count"] == 4
    assert retained["stage_c"]["all_artifacts_exist"] is True

    satisfied = artifact["satisfied_conditions"]
    assert [row["condition_id"] for row in satisfied] == [
        "READY-PI-001",
        "READY-PI-002",
        "READY-PI-003",
        "READY-PI-004",
        "READY-PI-005",
    ]
    assert satisfied[0]["residual_ids"] == ["RES-001", "RES-002"]

    blockers = artifact["blocking_conditions"]
    assert [row["blocker_id"] for row in blockers] == [
        "BLOCK-PI-001",
        "BLOCK-PI-002",
        "BLOCK-PI-003",
        "BLOCK-PI-004",
    ]
    assert artifact["blocking_residual_ids"] == [
        "RES-001",
        "RES-002",
        "RES-002",
        "RES-013/014-boundary",
    ]
    assert any("externally verified and checksummed" in row["summary"] for row in blockers)
    assert any("not in a clean release-grade identity state" in row["summary"] for row in blockers)
    assert any(
        "do not close release-grade surrogate identity" in row["summary"]
        for row in blockers
    )
    assert any("pk authority or deterministic fuze authority" in row["summary"] for row in blockers)

    trace = artifact["residual_condition_trace"]
    assert trace == [
        {
            "residual_id": "RES-001",
            "satisfied_condition_ids": ["READY-PI-001", "READY-PI-002"],
            "blocking_condition_ids": ["BLOCK-PI-001"],
            "gate_result": "blocked",
        },
        {
            "residual_id": "RES-002",
            "satisfied_condition_ids": [
                "READY-PI-001",
                "READY-PI-003",
                "READY-PI-004",
                "READY-PI-005",
            ],
            "blocking_condition_ids": ["BLOCK-PI-002", "BLOCK-PI-003"],
            "gate_result": "blocked",
        },
    ]

    boundaries = artifact["explicit_boundaries"]
    assert "do not treat author-side retained packs as release-grade identity closure" in boundaries
    assert "do not treat candidate or sanity-only pins as acquired authority inputs" in boundaries

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["effect_scale_authority_in_stock"] is False
    assert guards["component_failure_probability_authority_in_stock"] is False
    assert guards["pk_authority"] is False
    assert guards["deterministic_fuze_authority"] is False


def test_package_provenance_identity_gate_fails_closed_for_optimistic_release_fields(
    monkeypatch,
) -> None:
    original_read_text = package_gate._read_text

    def optimistic_read_text(path: Path) -> str:
        text = original_read_text(path)
        if path == package_gate.DOC_REFS["artifact_pin_manifest"]:
            return text.replace(
                "official_public_artifacts_partially_verified_release_grade_closeout_pending",
                "release_grade_closed",
            )
        if path == package_gate.DOC_REFS["surrogate_identity_manifest"]:
            return text.replace(
                "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present",
                "clean_release_candidate",
            )
        return text

    monkeypatch.setattr(package_gate, "_read_text", optimistic_read_text)

    artifact = package_gate.generate_package_provenance_identity_gate(
        repo_root=REPO_ROOT
    )

    blockers = artifact["blocking_conditions"]
    assert (
        artifact["status"]
        == "blocked_non_authoritative_package_provenance_identity_candidate"
    )
    assert [row["blocker_id"] for row in blockers] == [
        "BLOCK-PI-001",
        "BLOCK-PI-003",
        "BLOCK-PI-004",
    ]
    assert any("candidate-only, sanity-only or pending" in row["summary"] for row in blockers)
    assert any(
        "do not close release-grade surrogate identity" in row["summary"]
        for row in blockers
    )
    assert artifact["residual_condition_trace"][0]["blocking_condition_ids"] == [
        "BLOCK-PI-001"
    ]
    assert artifact["residual_condition_trace"][1]["blocking_condition_ids"] == [
        "BLOCK-PI-003"
    ]
    assert artifact["non_authoritative_guards"]["stock_database_authority_granted"] is False
    assert artifact["non_authoritative_guards"]["effect_scale_authority_in_stock"] is False
    assert (
        artifact["non_authoritative_guards"][
            "component_failure_probability_authority_in_stock"
        ]
        is False
    )


def test_package_provenance_identity_gate_fails_closed_on_placeholder_hits(
    monkeypatch,
) -> None:
    original_read_text = package_gate._read_text

    def placeholder_read_text(path: Path) -> str:
        text = original_read_text(path)
        if path == package_gate.DOC_REFS["validation_provenance_identity_gate"]:
            return f"{text}\n<待填>\n"
        return text

    monkeypatch.setattr(package_gate, "_read_text", placeholder_read_text)

    artifact = package_gate.generate_package_provenance_identity_gate(
        repo_root=REPO_ROOT
    )

    assert "READY-PI-001" not in [
        row["condition_id"] for row in artifact["satisfied_conditions"]
    ]
    assert artifact["blocking_conditions"][0] == {
        "blocker_id": "BLOCK-PI-000",
        "residual_id": "RES-001/002",
        "summary": (
            "placeholder text remains in package provenance or "
            "surrogate-identity documentation"
        ),
    }
    assert artifact["residual_condition_trace"][0]["blocking_condition_ids"][0] == (
        "BLOCK-PI-000"
    )
    assert artifact["residual_condition_trace"][1]["blocking_condition_ids"][0] == (
        "BLOCK-PI-000"
    )


def test_package_provenance_identity_gate_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_package_provenance_identity_gate.json"

    run_maintenance_cli(
        "a2_blastfrag_package_provenance_identity_gate.py",
        "--output",
        output_path,
        capture_output=False,
    )

    artifact = read_json(output_path)
    assert (
        artifact["status"]
        == "blocked_non_authoritative_package_provenance_identity_candidate"
    )
    assert artifact["blocking_conditions"][0]["blocker_id"] == "BLOCK-PI-001"


def test_provenance_identity_review_gate_current_repo_is_blocked(
    tmp_path: Path,
) -> None:
    artifact = review_gate.generate_provenance_identity_review_gate(
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


def test_provenance_identity_review_gate_prefers_canonical_source_pack(
    tmp_path: Path,
) -> None:
    fallback_path = tmp_path / review_gate.SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME
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

    artifact = review_gate.generate_provenance_identity_review_gate(
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


def test_provenance_identity_review_gate_fails_closed_for_optimistic_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    original_read_text = review_gate._read_text
    comparison_hash = "a" * 64

    def optimistic_read_text(path: Path) -> str:
        text = original_read_text(path)
        if path == review_gate.DOC_REFS["artifact_pin_manifest"]:
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
        if path == review_gate.DOC_REFS["surrogate_identity_manifest"]:
            text = text.replace(
                "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present",
                "clean_release_candidate",
            )
            text = text.replace("not_validated", "validated")
            return text.replace("/tmp/a2_", "retained_artifacts/a2_")
        if path == review_gate.DOC_REFS["validation_manifest"]:
            text = text.replace("unvalidated", "validated")
            return (
                f"{text}\nreviewer candidate note: comparison-output-sha256 "
                f"{comparison_hash}\n"
            )
        return text

    monkeypatch.setattr(review_gate, "_read_text", optimistic_read_text)

    artifact = review_gate.generate_provenance_identity_review_gate(
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


def test_provenance_identity_review_gate_fails_closed_when_source_evidence_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    original_read_text = review_gate._read_text

    def missing_verified_source_text(path: Path) -> str:
        text = original_read_text(path)
        if path == review_gate.DOC_REFS["artifact_pin_manifest"]:
            return text.replace("verified_candidate_artifact", "candidate_route_recorded")
        return text

    monkeypatch.setattr(review_gate, "_read_text", missing_verified_source_text)

    artifact = review_gate.generate_provenance_identity_review_gate(
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


def test_provenance_identity_review_gate_rejects_incomplete_source_pack(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        review_gate,
        "CANONICAL_SOURCE_PAYLOAD_PACK_DIR",
        tmp_path / "absent_canonical_source_payload_pack",
    )
    source_pack_path = tmp_path / review_gate.SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME
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

    artifact = review_gate.generate_provenance_identity_review_gate(
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


def test_provenance_identity_review_gate_cli_writes_retained_artifact(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "cli_output_manifest.json"
    run_maintenance_cli(
        "a2_blastfrag_provenance_identity_review_gate.py",
        "--write-retained-artifact",
        "--retained-output-dir",
        tmp_path,
        "--output",
        output_path,
        capture_output=False,
    )

    cli_payload = read_json(output_path)
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

    retained_gate_path = tmp_path / review_gate.REVIEW_ARTIFACT_FILENAME
    retained_manifest_path = tmp_path / review_gate.REVIEW_MANIFEST_FILENAME
    assert retained_gate_path.exists()
    assert retained_manifest_path.exists()
    retained_gate = read_json(retained_gate_path)
    assert retained_gate["status"] == (
        "blocked_non_authoritative_provenance_identity_review_gate"
    )
    assert retained_gate["residual_gate_results"] == {
        "RES-001": "blocked",
        "RES-002": "blocked",
    }


def test_release_provenance_closeout_gate_current_repo_is_blocked() -> None:
    artifact = closeout_gate.generate_release_provenance_closeout_gate(
        repo_root=REPO_ROOT
    )

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


def test_release_provenance_closeout_gate_fails_closed_for_optimistic_release_fields(
    monkeypatch,
) -> None:
    original_read_text = closeout_gate._read_text

    def optimistic_read_text(path: Path) -> str:
        text = original_read_text(path)
        if path == closeout_gate.DOC_REFS["artifact_pin_manifest"]:
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
        if path == closeout_gate.DOC_REFS["surrogate_identity_manifest"]:
            text = text.replace(
                "repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present",
                "clean_release_candidate",
            )
            text = text.replace("not_validated", "validated")
            return text.replace("/tmp/a2_", "retained_artifacts/a2_")
        if path == closeout_gate.DOC_REFS["validation_manifest"]:
            return f"{text}\ncomparison-output-sha256: optimistic-test-only\n"
        return text

    monkeypatch.setattr(closeout_gate, "_read_text", optimistic_read_text)

    artifact = closeout_gate.generate_release_provenance_closeout_gate(
        repo_root=REPO_ROOT
    )

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


def test_release_provenance_closeout_gate_fails_closed_when_author_side_source_evidence_missing(
    monkeypatch,
) -> None:
    original_read_text = closeout_gate._read_text

    def missing_verified_source_text(path: Path) -> str:
        text = original_read_text(path)
        if path == closeout_gate.DOC_REFS["artifact_pin_manifest"]:
            return text.replace("verified_candidate_artifact", "candidate_route_recorded")
        return text

    monkeypatch.setattr(closeout_gate, "_read_text", missing_verified_source_text)

    artifact = closeout_gate.generate_release_provenance_closeout_gate(
        repo_root=REPO_ROOT
    )

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


def test_release_provenance_closeout_gate_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_release_provenance_closeout_gate.json"
    run_maintenance_cli(
        "a2_blastfrag_release_provenance_closeout_gate.py",
        "--output",
        output_path,
        capture_output=False,
    )

    artifact = read_json(output_path)
    assert (
        artifact["status"]
        == "blocked_non_authoritative_release_provenance_closeout_candidate"
    )
    assert artifact["review_target"] == "res_001_002_release_provenance_closeout_lane"
    assert artifact["closeout_checks"][0]["check_id"] == "CLOSEOUT-RES001-001"
