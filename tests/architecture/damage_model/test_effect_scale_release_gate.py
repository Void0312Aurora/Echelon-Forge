from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path

ensure_repo_root_on_sys_path()

from tools.maintenance.release_governance import (  # noqa: E402
  effect_scale_release_closeout,
  effect_scale_release_readiness,
)

pytestmark = pytest.mark.governance_audit


@pytest.fixture(scope="module")
def effect_scale_readiness_artifact() -> dict[str, Any]:
  return effect_scale_release_readiness.generate_stage_b_release_readiness_gate(
    repo_root=REPO_ROOT
  )


@pytest.fixture(scope="module")
def effect_scale_closeout_artifact() -> dict[str, Any]:
  return effect_scale_release_closeout.generate_stage_b_release_closeout(
    repo_root=REPO_ROOT
  )


def test_effect_scale_release_readiness_gate_records_blocked_decision(
  effect_scale_readiness_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_readiness_artifact

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


def test_effect_scale_release_readiness_gate_records_scope_and_conditions(
  effect_scale_readiness_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_readiness_artifact

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


def test_effect_scale_release_readiness_gate_records_blocking_evidence(
  effect_scale_readiness_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_readiness_artifact
  blockers = artifact["blocking_conditions"]

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


def test_effect_scale_release_readiness_gate_records_provenance_boundaries(
  effect_scale_readiness_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_readiness_artifact

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
   "tools/maintenance/damage_model.py",
      "release-governance",
      "effect-scale-readiness",
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


def test_effect_scale_release_closeout_records_blocked_decision(
  effect_scale_closeout_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_closeout_artifact

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


def test_effect_scale_release_closeout_records_validation_execution(
  effect_scale_closeout_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_closeout_artifact

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


def test_effect_scale_release_closeout_records_residual_gate_results(
  effect_scale_closeout_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_closeout_artifact

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


def test_effect_scale_release_closeout_records_scope_closeout_outputs(
  effect_scale_closeout_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_closeout_artifact

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


def test_effect_scale_release_closeout_records_remaining_dependencies_and_guards(
  effect_scale_closeout_artifact: dict[str, Any],
) -> None:
  artifact = effect_scale_closeout_artifact

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
   "tools/maintenance/damage_model.py",
      "release-governance",
      "effect-scale-closeout",
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
