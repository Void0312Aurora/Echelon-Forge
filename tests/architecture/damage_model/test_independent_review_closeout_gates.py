from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path

ensure_repo_root_on_sys_path()

from tools.maintenance.independent_review import ( # noqa: E402
  effect_scale_review as stage_b_review_gate,
  review_closeout as review_closeout_gate,
  scope_bucket_review as scope_bucket_review_gate,
  uncertainty_review as uncertainty_review_gate,
)

pytestmark = pytest.mark.governance_audit


# Independent review may close bounded review surfaces, but never release authority.
def test_independent_review_gate_passes_review_without_release_authority() -> None:
  artifact = stage_b_review_gate.generate_stage_b_independent_review_gate(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.stage_b_independent_review_gate.v1"
  assert artifact["status"] == "independent_review_passed_release_blocked"
  assert artifact["reviewer_role"] == "A2-RC-STAGE-B-INDEPENDENT-REVIEW"
  assert artifact["review_target"] == "stage_b_effect_scale_independent_review_only"
  assert artifact["release_target"] == "effect_scale_authority_only"
  assert artifact["focused_residual_ids"] == [
    "RES-007",
    "RES-008",
    "RES-010",
    "RES-011",
    "RES-012",
  ]

  review = artifact["review_decision"]
  assert review["independent_review_complete"] is True
  assert review["focused_review_passed"] is True
  assert review["review_passed_residual_ids"] == [
    "RES-007",
    "RES-008",
    "RES-010",
    "RES-011",
    "RES-012",
  ]
  assert review["review_blocked_residual_ids"] == []
  assert review["hard_gate_pass_is_release"] is False
  assert review["formal_validation_manifest_promoted"] is False
  assert review["stock_runtime_authority_granted"] is False

  release = artifact["release_decision"]
  assert release["release_ready"] is False
  assert release["release_blocked"] is True
  assert release["current_hard_gate_snapshot_pass"] is True
  assert release["hard_gate_pass_is_release"] is False
  assert release["blocked_even_when_hard_gates_pass"] is True
  assert release["release_blocked_by_residual_ids"] == [
    "RES-001",
    "RES-002",
    "RES-003",
    "RES-004",
    "RES-005",
    "RES-006",
    "RES-013/014-boundary",
  ]
  assert release["stage_c_component_probability_release_included"] is False
  assert release["stock_runtime_authority_granted"] is False

  residuals = {
    row["residual_id"]: row
    for row in artifact["residual_review_gate_results"]
  }
  assert list(residuals) == [
    "RES-007",
    "RES-008",
    "RES-010",
    "RES-011",
    "RES-012",
  ]
  assert all(row["review_gate_result"] == "review_passed" for row in residuals.values())
  assert all(row["all_review_checks_pass"] is True for row in residuals.values())
  assert all(
    row["register_status_after_review"] == "remains_open_release_blocked"
    for row in residuals.values()
  )
  assert residuals["RES-010"]["release_gate_result"] == (
    "blocked_formal_validation_promotion"
  )
  assert residuals["RES-008"]["release_gate_result"] == (
    "blocked_by_mechanism_source_residuals"
  )

  blockers = artifact["release_blocking_conditions"]
  assert [row["blocker_id"] for row in blockers] == [
    "BLOCK-IR-001",
    "BLOCK-IR-002",
    "BLOCK-IR-003",
    "BLOCK-IR-004",
    "BLOCK-IR-005",
    "BLOCK-IR-006",
    "BLOCK-IR-007",
  ]
  assert any("source provenance" in row["summary"] for row in blockers)
  assert any("surrogate identity" in row["summary"] for row in blockers)
  assert any("target geometry" in row["summary"] for row in blockers)
  assert any("warhead class" in row["summary"] for row in blockers)
  assert any("fragment mechanism" in row["summary"] for row in blockers)
  assert any("blast mechanism" in row["summary"] for row in blockers)
  assert any("stock runtime" in row["summary"] for row in blockers)


def test_independent_review_gate_audits_effect_scale_surfaces() -> None:
  artifact = stage_b_review_gate.generate_stage_b_independent_review_gate(repo_root=REPO_ROOT)

  near_miss = artifact["near_miss_bucket_review"]
  assert near_miss["review_gate_result"] == "review_passed"
  assert near_miss["release_gate_result"] == "blocked_by_upstream_release_dependencies"
  assert near_miss["standoff_probe_m"] == [0.25, 0.35, 0.45]
  assert near_miss["runtime_bucket"] == "near_miss"
  assert [row["check_id"] for row in near_miss["checks"]] == [
    "IR-RES007-001",
    "IR-RES007-002",
    "IR-RES007-003",
    "IR-RES007-004",
    "IR-RES007-005",
    "IR-RES007-006",
    "IR-RES007-007",
  ]
  assert all(row["pass"] for row in near_miss["checks"])

  beam_high = artifact["beam_high_scope_leakage_review"]
  assert beam_high["review_gate_result"] == "review_passed"
  assert beam_high["release_gate_result"] == "blocked_by_mechanism_source_residuals"
  assert beam_high["closure_probe_mps"] == [700.0, 900.0, 1100.0]
  assert beam_high["accepted_scope_labels"] == ["beam"]
  assert "direct_hit" in beam_high["rejected_scope_labels"]
  assert "closure_bucket != high" in beam_high["rejected_scope_labels"]
  assert all(row["pass"] for row in beam_high["checks"])

  validation = artifact["validation_result_promotion_review"]
  assert validation["review_gate_result"] == "review_passed"
  assert validation["release_gate_result"] == "blocked_formal_validation_promotion"
  assert validation["criteria_counts"]["criteria_count"] == 18
  assert validation["criteria_counts"]["failed_criteria_ids"] == []
  assert validation["artifact_hash_count"] == 3
  assert validation["validation_manifest_status"] == "not_promoted_to_validated"
  assert validation["formal_validation_promotion_result"] == "blocked"
  assert validation["formal_validation_promotion_blocked_by"] == [
    "RES-001",
    "RES-002",
    "RES-003",
    "RES-004",
    "RES-005",
    "RES-006",
  ]

  uncertainty = artifact["uncertainty_review"]
  assert uncertainty["review_gate_result"] == "review_passed"
  assert uncertainty["release_gate_result"] == "blocked_uncertainty_coverage_release"
  assert uncertainty["seed_window_cv_pass"] is True
  assert all(row["pass"] for row in uncertainty["cv_rows"])
  assert uncertainty["coverage_release_result"] == "blocked"
  assert uncertainty["coverage_release_blocked_by"] == [
    "RES-001",
    "RES-002",
    "RES-003",
    "RES-004",
    "RES-005",
    "RES-006",
  ]

  independence = artifact["benchmark_input_independence_review"]
  assert independence["review_gate_result"] == "review_passed"
  assert independence["release_gate_result"] == (
    "blocked_by_provenance_identity_and_source_residuals"
  )
  bm005 = next(
    row
    for row in independence["benchmark_independence_rows"]
    if row["benchmark_id"] == "BFM-BM-005"
  )
  assert bm005["independence_class"] == "not_independent_real_validation"
  assert bm005["audit_outcome"] == "candidate_hygiene_only_not_independent_validation"
  assert "authority release" in bm005["forbidden_claim"]
  assert all(row["pass"] for row in independence["checks"])

  readiness = artifact["readiness_gate_snapshot"]
  assert readiness["status"] == "blocked_non_authoritative_stage_b_release_candidate"
  assert readiness["hard_gate_pass_is_release"] is False
  assert "RES-001" in readiness["blocking_residual_ids"]
  assert "RES-002" in readiness["blocking_residual_ids"]
  assert "RES-010" in readiness["blocking_residual_ids"]

  guards = artifact["non_authoritative_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["effect_scale_authority_in_stock"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["component_failure_probability_authority_in_stock"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False


def test_independent_review_gate_cli_writes_json(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "a2_stage_b_independent_review_gate.json"
  subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "independent-review",
      "effect-scale-review",
      "--output",
      str(output_path),
    ],
    cwd=REPO_ROOT,
    check=True,
  )

  artifact = json.loads(output_path.read_text(encoding="utf-8"))
  assert artifact["status"] == "independent_review_passed_release_blocked"
  assert artifact["release_decision"]["hard_gate_pass_is_release"] is False
  assert artifact["residual_review_gate_results"][0]["residual_id"] == "RES-007"



# Bounded RES-011/012 review closeout keeps probability and release blocked.
def test_review_closeout_gate_closes_effect_scale_only() -> None:
  artifact = review_closeout_gate.generate_res011012_independent_review_closeout_gate(
    repo_root=REPO_ROOT
  )

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == (
    "a2.res011012_independent_review_closeout_gate.v1"
  )
  assert artifact["status"] == (
    "res011012_stage_b_effect_scale_closeout_pass_stage_c_blocked_release_blocked"
  )
  assert artifact["review_target"] == (
    "RES-011_RES-012_independent_review_closeout_gate"
  )
  assert artifact["release_target"] == "stage_b_effect_scale_review_closeout_only"
  assert artifact["missing_evidence"] == []
  assert len(artifact["consumed_evidence"]) == 14

  reviewer = artifact["reviewer_identity"]
  assert reviewer["worker_id"] == "A2-RES011012-INDEPENDENT-REVIEW-CLOSEOUT"
  assert reviewer["nickname"] == "res011012-closeout-reviewer"
  assert reviewer["independence_class"] == "project_internal_independent_review_worker"
  assert reviewer["external_validation_claimed"] is False

  stage_b = artifact["stage_b_effect_scale_closeout"]
  assert stage_b["decision"] == (
    "closeable_for_stage_b_effect_scale_independent_review_only"
  )
  assert stage_b["closeout_allowed"] is True
  assert stage_b["res011_stage_b_effect_scale_closeout"] is True
  assert stage_b["res012_stage_b_effect_scale_closeout"] is True
  assert stage_b["res011_basis"]["seed_window_cv_pass"] is True
  assert stage_b["res011_basis"]["release_grade_uncertainty_complete"] is False
  assert stage_b["res012_basis"]["review_gate_result"] == "review_passed"
  assert stage_b["res012_basis"]["external_validation_claimed"] is False
  assert stage_b["stage_c_component_probability_included"] is False
  assert all(row["pass"] for row in stage_b["checks"])
  assert "external validation claim" in stage_b["forbidden_promotions"]

  closeout = artifact["closeout_decision"]
  assert closeout["stage_b_effect_scale_res011012_closeout_complete"] is True
  assert closeout["stage_b_effect_scale_closeout_is_release_authority"] is False
  assert closeout["stage_c_res011012_closeout_complete"] is False
  assert closeout["res011012_package_release_grade_complete"] is False
  assert closeout["release_ready"] is False
  assert closeout["release_blocked"] is True

  residuals = artifact["residual_closeout_decisions"]
  assert residuals["RES-011"]["stage_b_effect_scale"] == (
    "closed_for_bounded_independent_review_closeout"
  )
  assert residuals["RES-012"]["stage_b_effect_scale"] == (
    "closed_for_bounded_independent_review_closeout"
  )
  assert residuals["RES-011"]["stage_c_component_probability"] == "blocked"
  assert residuals["RES-012"]["stage_c_component_probability"] == "blocked"
  assert residuals["RES-011"]["package_release_grade"] == (
    "remains_open_release_blocked"
  )
  assert residuals["RES-012"]["residual_register_edit_required_by_this_gate"] is False


def test_review_closeout_gate_keeps_probability_and_provenance_blocked() -> None:
  artifact = review_closeout_gate.generate_res011012_independent_review_closeout_gate(
    repo_root=REPO_ROOT
  )

  stage_c = artifact["stage_c_component_probability_closeout"]
  assert stage_c["decision"] == (
    "blocked_probability_uncertainty_fragility_truth_and_independence_missing"
  )
  assert stage_c["closeout_allowed"] is False
  assert stage_c["res011_stage_c_closeout"] is False
  assert stage_c["res012_stage_c_closeout"] is False
  assert stage_c["blocked_residual_ids"] == [
    "RES-009",
    "RES-010",
    "RES-011",
    "RES-012",
  ]
  blocking = stage_c["blocking_evidence"]
  assert blocking["probability_uncertainty_release_grade_complete"] is False
  assert blocking["author_repeatability_present"] is True
  assert blocking["component_failure_probability_cv"] == 0.0
  assert blocking["independent_fragility_truth_present"] is False
  assert blocking["replacement_allowed"] is False
  assert blocking["result_level_independence_audit_complete"] is False
  assert all(row["pass"] for row in stage_c["checks"])
  assert "probability uncertainty coverage with reviewer-accepted bounds" in (
    stage_c["minimum_evidence_to_unblock"]
  )

  provenance = artifact["provenance_interlock"]
  assert provenance["decision"] == "provenance_interlocks_preserved_release_blocked"
  assert provenance["release_ready"] is False
  assert provenance["release_blocked"] is True
  assert provenance["blocking_residual_ids"] == [
    "RES-001",
    "RES-002",
    "RES-003",
    "RES-004",
    "RES-005",
    "RES-006",
  ]
  assert all(row["pass"] for row in provenance["checks"])

  guards = artifact["authority_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["component_failure_probability_authority_in_stock"] is False
  assert guards["stock_component_probability_authority"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False
  assert guards["replacement_allowed"] is False


def test_review_closeout_gate_fails_closed_without_evidence(
  tmp_path: Path,
) -> None:
  artifact = review_closeout_gate.generate_res011012_independent_review_closeout_gate(
    repo_root=REPO_ROOT,
    package_dir=tmp_path,
  )

  assert artifact["status"] == "res011012_independent_review_closeout_fail_closed"
  assert artifact["stage_b_effect_scale_closeout"]["decision"] == (
    "fail_closed_stage_b_res011012_evidence_incomplete"
  )
  assert artifact["stage_b_effect_scale_closeout"]["closeout_allowed"] is False
  assert artifact["closeout_decision"][
    "stage_b_effect_scale_res011012_closeout_complete"
  ] is False
  assert artifact["residual_closeout_decisions"]["RES-011"]["stage_b_effect_scale"] == (
    "fail_closed"
  )
  assert [row["evidence_id"] for row in artifact["missing_evidence"]] == [
    "stage_b_independent_review_gate",
    "stage_b_independent_review_manifest",
    "stage_b_release_closeout",
    "uncertainty_review_gate",
    "uncertainty_review_manifest",
    "stage_c_fragility_review_gate",
    "stage_c_fragility_review_manifest",
    "stage_c_fragility_validation_prep",
    "stage_c_fragility_validation_prep_manifest",
    "stage_c_fragility_benchmark",
    "provenance_identity_review_gate",
    "geometry_warhead_row_provenance_gate",
    "mechanism_source_closeout_gate",
    "source_rights_output_policy_gate",
  ]
  assert artifact["authority_guards"]["pk_authority_granted"] is False
  assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_review_closeout_gate_cli_writes_retained_json(
  tmp_path: Path,
) -> None:
  output_dir = tmp_path / "res011012_independent_review_closeout_20260531"
  result = subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "independent-review",
      "review-closeout",
      "--output-dir",
      str(output_dir),
    ],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )

  command_summary = json.loads(result.stdout)
  assert command_summary["status"] == (
    "res011012_stage_b_effect_scale_closeout_pass_stage_c_blocked_release_blocked"
  )
  gate_path = output_dir / "res011012_independent_review_closeout_gate.json"
  manifest_path = output_dir / "manifest.json"
  assert gate_path.is_file()
  assert manifest_path.is_file()

  artifact = json.loads(gate_path.read_text(encoding="utf-8"))
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert artifact["closeout_decision"][
    "stage_b_effect_scale_res011012_closeout_complete"
  ] is True
  assert artifact["closeout_decision"]["stage_c_res011012_closeout_complete"] is False
  assert manifest["schema_version"] == (
    "a2.res011012_independent_review_closeout_retained_manifest.v1"
  )
  assert manifest["status"] == (
    "res011012_independent_review_closeout_retained_release_blocked"
  )
  assert manifest["artifacts"][0]["artifact_key"] == (
    "res011012_independent_review_closeout_gate"
  )
  assert manifest["artifacts"][0]["content_sha256"]
  assert manifest["reviewer_identity"]["external_validation_claimed"] is False
  assert manifest["authority_guards"][
    "component_failure_probability_authority_granted"
  ] is False



# Scope bucket review is a bounded review record, not a release gate.
def _scope_residuals_by_id(
  artifact: dict[str, object],
) -> dict[str, dict[str, object]]:
  return {
    row["residual_id"]: row
    for row in artifact["residual_statuses"] # type: ignore[index]
  }


def test_scope_bucket_review_gate_narrow_passes_only() -> None:
  artifact, probe = scope_bucket_review_gate.generate_scope_bucket_independent_review_gate(
    repo_root=REPO_ROOT
  )

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.scope_bucket_independent_review_gate.v1"
  assert artifact["status"] == "scope_bucket_independent_review_passed_release_blocked"
  assert artifact["review_target"] == "RES-007_RES-008_scope_bucket_independent_review_only"
  assert artifact["release_target"] == "none_review_gate_record_only"
  assert probe["status"] == "candidate_non_authoritative_scope_probe_results"

  decision = artifact["review_decision"]
  assert decision["res007_scope_bucket_review_complete"] is True
  assert decision["res008_scope_bucket_review_complete"] is True
  assert decision["narrow_stage_b_scope_only_acceptance"] is True
  assert decision["release_ready"] is False
  assert decision["release_blocked"] is True
  assert decision["release_blocked_by_residual_ids"] == [
    "RES-001",
    "RES-002",
    "RES-003",
    "RES-004",
    "RES-005",
    "RES-006",
    "RES-013/014-boundary",
  ]
  assert decision["missing_review_evidence_count"] == 0
  assert artifact["missing_review_evidence"] == []
  assert artifact["fail_closed_blockers"] == []

  residuals = _scope_residuals_by_id(artifact)
  assert list(residuals) == ["RES-007", "RES-008"]
  assert residuals["RES-007"]["scope_bucket_review_status"] == (
    "narrow_stage_b_scope_review_complete"
  )
  assert residuals["RES-007"]["decision"] == "narrow_pass_stage_b_scope_only"
  assert residuals["RES-007"]["residual_register_status_after_gate"] == (
    "remains_open_release_blocked"
  )
  assert residuals["RES-008"]["scope_bucket_review_status"] == (
    "narrow_stage_b_scope_review_complete"
  )
  assert residuals["RES-008"]["decision"] == "narrow_pass_stage_b_scope_only"
  assert residuals["RES-008"]["residual_register_status_after_gate"] == (
    "remains_open_release_blocked"
  )
  assert all(row["pass"] for row in residuals["RES-007"]["checks"])
  assert all(row["pass"] for row in residuals["RES-008"]["checks"])

  coverage = artifact["probe_coverage_summary"]
  assert coverage["standoff_rows_m"] == [0.25, 0.35, 0.45]
  assert coverage["miss_distance_row_count"] == 3
  assert coverage["miss_distance_anchor_present"] is True
  assert coverage["runtime_bucket_consistent"] is True
  assert coverage["closure_rows_mps"] == [700.0, 900.0, 1100.0]
  assert coverage["closure_row_count"] == 3
  assert coverage["closure_response_active"] is True

  rejection = artifact["boundary_rejection_coverage"]
  assert rejection["accepted_scope_labels"] == ["beam"]
  assert rejection["all_required_rejections_observed"] is True
  assert rejection["missing_rejected_scope_labels"] == []
  assert rejection["required_rejected_scope_labels"] == [
    "head_on",
    "tail_chase",
    "high_off_boresight",
    "direct_hit",
    "closure_bucket != high",
    "weapon_family != blast_fragmentation",
  ]

  closure_review = artifact["closure_response_review_status"]
  assert closure_review["probe_response_active"] is True
  assert closure_review["probe_self_review_complete"] is False
  assert closure_review["independent_review_complete"] is True
  assert closure_review["decision"] == "review_complete_for_stage_b_scope_only"

  guards = artifact["authority_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["effect_scale_authority_in_stock"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["component_failure_probability_authority_in_stock"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False
  assert guards["formal_validation_manifest_promoted"] is False
  assert guards["hard_gate_pass_is_release"] is False


def test_scope_bucket_review_gate_fails_closed_without_evidence(
  tmp_path: Path,
) -> None:
  artifact, _ = scope_bucket_review_gate.generate_scope_bucket_independent_review_gate(
    repo_root=REPO_ROOT,
    package_dir=tmp_path,
  )

  assert artifact["status"] == "scope_bucket_independent_review_fail_closed"
  assert artifact["review_decision"]["narrow_stage_b_scope_only_acceptance"] is False
  assert artifact["review_decision"]["res007_scope_bucket_review_complete"] is False
  assert artifact["review_decision"]["res008_scope_bucket_review_complete"] is False
  assert artifact["review_decision"]["release_ready"] is False
  assert artifact["review_decision"]["release_blocked"] is True

  missing = artifact["missing_review_evidence"]
  assert [row["evidence_id"] for row in missing] == [
    "EVID-SCOPE-MANIFEST-001",
    "EVID-RESULT-PACK-001",
    "EVID-INDEPENDENT-REVIEW-001",
    "EVID-INDEPENDENT-REVIEW-MANIFEST-001",
    "EVID-INDEPENDENT-REVIEW-DOC-001",
  ]
  assert all("missing" in row["blocker"] for row in missing)

  blockers = artifact["fail_closed_blockers"]
  blocker_ids = {row["check_id"] for row in blockers}
  assert "RESULT-PACK-001" in blocker_ids
  assert "INDEPENDENT-REVIEW-001" in blocker_ids
  assert "REVIEW-DOC-001" in blocker_ids
  assert "REVIEW-MANIFEST-001" in blocker_ids

  residuals = _scope_residuals_by_id(artifact)
  assert residuals["RES-007"]["decision"] == "fail_closed"
  assert residuals["RES-008"]["decision"] == "fail_closed"
  assert residuals["RES-007"]["residual_register_status_after_gate"] == (
    "remains_open_release_blocked"
  )
  assert residuals["RES-008"]["residual_register_status_after_gate"] == (
    "remains_open_release_blocked"
  )
  assert artifact["authority_guards"]["stock_runtime_authority_granted"] is False
  assert artifact["authority_guards"]["pk_authority_granted"] is False
  assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_scope_bucket_review_gate_cli_writes_retained_json(
  tmp_path: Path,
) -> None:
  output_dir = tmp_path / "scope_bucket_independent_review_20260531"
  result = subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "independent-review",
      "scope-bucket-review",
      "--output-dir",
      str(output_dir),
    ],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )

  command_summary = json.loads(result.stdout)
  assert command_summary["status"] == (
    "scope_bucket_independent_review_passed_release_blocked"
  )
  gate_path = output_dir / "scope_bucket_independent_review_gate.json"
  probe_path = output_dir / "scope_boundary_probe_rerun.json"
  manifest_path = output_dir / "manifest.json"
  assert gate_path.is_file()
  assert probe_path.is_file()
  assert manifest_path.is_file()

  artifact = json.loads(gate_path.read_text(encoding="utf-8"))
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert artifact["review_decision"]["narrow_stage_b_scope_only_acceptance"] is True
  assert manifest["schema_version"] == (
    "a2.scope_bucket_independent_review_retained_artifacts.v1"
  )
  assert manifest["status"] == "scope_bucket_independent_review_retained_release_blocked"
  assert [row["artifact_key"] for row in manifest["artifacts"]] == [
    "scope_bucket_independent_review_gate",
    "scope_boundary_probe_rerun",
  ]
  assert all(row["content_sha256"] for row in manifest["artifacts"])
  assert manifest["authority_guards"]["component_failure_probability_authority_granted"] is False



# Uncertainty review separates effect-scale review from probability authority.
def test_uncertainty_review_gate_splits_effect_scale_and_probability_closeout() -> None:
  artifact = uncertainty_review_gate.generate_uncertainty_review_gate(repo_root=REPO_ROOT)

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.uncertainty_review_gate.v1"
  assert artifact["status"] == (
    "uncertainty_review_stage_b_narrow_pass_stage_c_blocked_release_blocked"
  )
  assert artifact["review_target"] == "RES-011_uncertainty_review_only"
  assert artifact["missing_evidence"] == []

  stage_b = artifact["stage_b_uncertainty_review"]
  assert stage_b["review_result"] == (
    "narrow_author_side_uncertainty_closeout_complete_release_blocked"
  )
  assert stage_b["author_side_closeout_complete"] is True
  assert stage_b["seed_window_cv_pass"] is True
  assert [row["metric"] for row in stage_b["cv_rows"]] == [
    "fragment_areal_density_per_m2.cv",
    "blast_impulse_kpa_ms_proxy.cv",
    "fragment_energy_j_proxy.cv",
    "penetration_margin_proxy.cv",
  ]
  assert all(row["pass"] for row in stage_b["cv_rows"])
  assert stage_b["release_uncertainty_review_status"] == (
    "blocked_pending_independent_coverage_review"
  )
  assert "independent uncertainty reviewer signoff is absent" in (
    stage_b["not_release_grade_because"]
  )

  stage_c = artifact["stage_c_uncertainty_review"]
  assert stage_c["review_result"] == (
    "blocked_probability_uncertainty_coverage_missing"
  )
  assert stage_c["author_repeatability_review_result"] == "review_passed"
  assert stage_c["uncertainty_closeout_result"] == "blocked"
  assert stage_c["anchor_probe_label"] == "middle"
  assert stage_c["seed_values"] == [20260526, 20260527, 20260528]
  assert stage_c["component_failure_probability_cv"] == 0.0
  assert stage_c["component_result_pack_anchor_cv"] == 0.0
  assert stage_c["blocking_condition_ids"] == ["BLOCK-CP-004"]
  assert "reviewer-accepted confidence or coverage interval" in (
    stage_c["missing_evidence"]
  )
  assert stage_c["closeout_doc_is_review_package_only"] is True


def test_uncertainty_review_gate_keeps_release_authority_blocked() -> None:
  artifact = uncertainty_review_gate.generate_uncertainty_review_gate(repo_root=REPO_ROOT)

  residual = artifact["residual_status"]
  assert residual["residual_id"] == "RES-011"
  assert residual["combined_decision"] == "blocked_release_grade_uncertainty_review"
  assert residual["stage_b_decision"] == "narrow_author_side_pass_release_blocked"
  assert residual["stage_c_decision"] == (
    "blocked_probability_uncertainty_coverage_missing"
  )
  assert residual["residual_register_status_after_gate"] == (
    "remains_open_release_blocked"
  )
  assert "Stage B seed-window CV rows pass current author-side thresholds" in (
    residual["review_passed_items"]
  )
  assert "Stage C calibration or coverage scoring" in (
    residual["missing_release_grade_items"]
  )

  decision = artifact["review_decision"]
  assert decision["stage_b_author_side_uncertainty_closeout_complete"] is True
  assert decision["stage_b_release_grade_uncertainty_complete"] is False
  assert decision["stage_c_author_repeatability_present"] is True
  assert decision["stage_c_release_grade_uncertainty_complete"] is False
  assert decision["res011_release_grade_complete"] is False
  assert decision["release_ready"] is False
  assert decision["release_blocked"] is True

  guards = artifact["authority_guards"]
  assert guards["stock_descriptor_created"] is False
  assert guards["stock_database_authority_granted"] is False
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False
  assert guards["formal_validation_manifest_promoted"] is False


def test_uncertainty_review_gate_fails_closed_without_evidence(
  tmp_path: Path,
) -> None:
  artifact = uncertainty_review_gate.generate_uncertainty_review_gate(
    repo_root=REPO_ROOT,
    package_dir=tmp_path,
  )

  assert artifact["status"] == "uncertainty_review_fail_closed"
  assert artifact["stage_b_uncertainty_review"]["review_result"] == (
    "fail_closed_missing_result_pack"
  )
  assert artifact["residual_status"]["combined_decision"] == (
    "fail_closed_missing_or_incomplete_uncertainty_evidence"
  )
  assert [row["evidence_id"] for row in artifact["missing_evidence"]] == [
    "UNC-STAGE-B-RESULT-PACK",
    "UNC-STAGE-B-CLOSEOUT-DOC",
    "UNC-STAGE-C-RESULT-PACK",
    "UNC-STAGE-C-FRAGILITY-REVIEW",
    "UNC-STAGE-C-FRAGILITY-BENCHMARK",
    "UNC-STAGE-C-CLOSEOUT-DOC",
  ]
  assert artifact["authority_guards"]["pk_authority_granted"] is False
  assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_uncertainty_review_gate_cli_writes_retained_json(
  tmp_path: Path,
) -> None:
  output_dir = tmp_path / "uncertainty_review_20260531"
  result = subprocess.run(
    [
      sys.executable,
   "tools/maintenance/damage_model.py",
      "independent-review",
      "uncertainty-review",
      "--output-dir",
      str(output_dir),
    ],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )

  command_summary = json.loads(result.stdout)
  assert command_summary["status"] == (
    "uncertainty_review_stage_b_narrow_pass_stage_c_blocked_release_blocked"
  )
  gate_path = output_dir / "uncertainty_review_gate.json"
  manifest_path = output_dir / "manifest.json"
  assert gate_path.is_file()
  assert manifest_path.is_file()

  artifact = json.loads(gate_path.read_text(encoding="utf-8"))
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert artifact["review_decision"]["res011_release_grade_complete"] is False
  assert manifest["schema_version"] == (
    "a2.uncertainty_review_retained_artifacts.v1"
  )
  assert manifest["status"] == "uncertainty_review_retained_release_blocked"
  assert manifest["artifacts"][0]["artifact_key"] == "uncertainty_review_gate"
  assert manifest["artifacts"][0]["content_sha256"]
  assert manifest["authority_guards"]["component_failure_probability_authority_granted"] is False
