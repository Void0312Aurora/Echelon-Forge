from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.architecture.damage_model.helpers import (
  assert_authority_guards_false,
  assert_hex64,
  run_maintenance_cli,
  run_maintenance_json_cli,
)
from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path, read_json

ensure_repo_root_on_sys_path()

from tools.maintenance.candidate_artifacts import ( # noqa: E402
  component_probability_result_pack as result_pack,
  component_probability_retained_pack as retained_pack,
  component_probability_snapshot as snapshot,
  component_probability_surface_probe as surface_probe,
)


@pytest.fixture(scope="module")
def surface_probe_artifact() -> dict[str, Any]:
  return surface_probe.generate_stage_c_component_probability_surface_probe(
    repo_root=REPO_ROOT
  )


@pytest.fixture(scope="module")
def snapshot_artifact() -> dict[str, Any]:
  return snapshot.generate_stage_c_component_probability_snapshot(repo_root=REPO_ROOT)


@pytest.fixture(scope="module")
def result_pack_artifact() -> dict[str, Any]:
  return result_pack.generate_stage_c_component_probability_result_pack(
    repo_root=REPO_ROOT
  )


# Component probability surface probe

def test_component_probability_surface_probe_records_candidate_identity(
  surface_probe_artifact: dict[str, Any],
) -> None:
  artifact = surface_probe_artifact

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert (
    artifact["schema_version"]
    == "a2.stage_c_component_probability_surface_probe.v1"
  )
  assert (
    artifact["status"]
    == "candidate_non_authoritative_stage_c_component_probability_surface_probe"
  )


def test_component_probability_surface_probe_records_scope_and_descriptor(
  surface_probe_artifact: dict[str, Any],
) -> None:
  artifact = surface_probe_artifact
  scope = artifact["scope"]

  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["aspect_bucket"] == "beam"
  assert scope["closure_bucket"] == "high"
  assert scope["runtime_miss_distance_bucket"] == "near_miss"
  assert scope["component_name"] == "right_aileron_actuator"
  assert scope["component_system"] == "flight_control"
  assert scope["component_redundancy_group_id"] == "lateral_flight_control_actuators"

  descriptor = artifact["descriptor_candidate_summary"]
  assert descriptor["dataset_id"] == (
    "unit_test_a2_blastfrag_runtime_aligned_component_probability_surface_probe"
  )
  assert descriptor["source_kind"] == "validated_physics_surrogate"
  assert descriptor["calibration_status"] == "calibrated"
  assert descriptor["component_failure_probability_authority"] is True
  assert descriptor["row_count"] == 4
  assert descriptor["component_specific_row_count"] == 3
  assert descriptor["global_fallback_row_id"] == "global-fallback"


def test_component_probability_surface_probe_is_deterministic_against_stock_baseline(
  surface_probe_artifact: dict[str, Any],
) -> None:
  artifact = surface_probe_artifact
  determinism = artifact["determinism_summary"]

  assert determinism["probe_labels_are_fixed"] == ["inner", "middle", "outer"]
  assert determinism["probe_local_points_are_fixed"] == [
    [-0.753, 5.5, 0.0],
    [-0.753, 5.8, 0.0],
    [-0.753, 6.0, 0.0],
  ]
  assert determinism["runtime_seed_values_are_fixed"] == [
    20260526,
    20260527,
    20260528,
  ]
  assert determinism["descriptor_gate_bands_use_stock_seed"] == 20260526
  assert determinism["json_output_uses_sort_keys"] is True
  assert determinism["runtime_database_copy_is_temporary"] is True

  stock_baseline = artifact["stock_baseline_probe_summary"]
  assert stock_baseline["source_database"] == "examples/config/database"
  assert stock_baseline["probe_labels"] == ["inner", "middle", "outer"]
  assert stock_baseline["component_primary_names"] == [
    "right_aileron_actuator",
    "right_aileron_actuator",
    "right_aileron_actuator",
  ]
  assert stock_baseline["component_probability_sources"] == [
    "synthetic_sigmoid",
    "synthetic_sigmoid",
    "synthetic_sigmoid",
  ]
  assert stock_baseline["all_probability_sources_are_synthetic_sigmoid"] is True
  assert stock_baseline["any_calibrated_component_probability"] is False


def test_component_probability_surface_probe_locks_component_scope_and_rows(
  surface_probe_artifact: dict[str, Any],
) -> None:
  artifact = surface_probe_artifact
  scope_audit = artifact["component_scope_audit"]

  assert scope_audit["candidate_component_name"] == "right_aileron_actuator"
  assert scope_audit["candidate_component_system"] == "flight_control"
  assert (
    scope_audit["candidate_component_redundancy_group_id"]
    == "lateral_flight_control_actuators"
  )
  assert scope_audit["component_specific_row_ids"] == [
    "component-inner",
    "component-middle",
    "component-outer",
  ]
  assert (
    scope_audit["component_specific_rows_scope_locked_to_primary_component"]
    is True
  )
  assert scope_audit["selected_rows_scope_locked_to_primary_component"] is True
  assert scope_audit["global_fallback_row_id"] == "global-fallback"
  assert scope_audit["global_fallback_row_has_no_component_identity"] is True

  rows = artifact["surface_probe_rows"]
  assert [row["probe_label"] for row in rows] == ["inner", "middle", "outer"]
  assert [row["selected_row_id"] for row in rows] == [
    "component-inner",
    "component-middle",
    "component-outer",
  ]
  assert [row["selected_row_probability"] for row in rows] == [0.52, 0.37, 0.21]
  assert all(row["component_primary_name"] == "right_aileron_actuator" for row in rows)
  assert all(row["selected_row_matches_component_specific_scope"] for row in rows)
  assert all(row["selected_row_covers_primary_loads"] for row in rows)


def test_component_probability_surface_probe_records_metrics_and_repeatability(
  surface_probe_artifact: dict[str, Any],
) -> None:
  artifact = surface_probe_artifact
  metrics = artifact["metrics"]

  assert metrics["primary_component_identity_stable_pass"] is True
  assert metrics["component_specific_precedence_pass"] is True
  assert metrics["selected_rows_cover_primary_loads_pass"] is True
  assert metrics["probability_monotonic_decreasing_with_standoff_pass"] is True
  assert metrics["selected_row_ids_are_distinct_pass"] is True
  assert metrics["anchor_seed_window_cv_pass"] is True

  repeatability = artifact["repeatability_summary"]
  assert repeatability["anchor_probe_label"] == "middle"
  assert repeatability["seed_values"] == [20260526, 20260527, 20260528]
  assert repeatability["selected_row_ids"] == [
    "component-middle",
    "component-middle",
    "component-middle",
  ]
  assert repeatability["component_failure_probability"]["cv"] <= 0.05
  assert repeatability["fragment_areal_density_per_m2"]["cv"] <= 0.05
  assert repeatability["fragment_energy_j"]["cv"] <= 0.05
  assert repeatability["penetration_margin"]["cv"] <= 0.05
  assert repeatability["blast_impulse_kpa_ms"]["cv"] <= 0.05


def test_component_probability_surface_probe_preserves_candidate_boundaries(
  surface_probe_artifact: dict[str, Any],
) -> None:
  artifact = surface_probe_artifact
  findings = artifact["current_findings"]

  assert "three-point component-specific surface probe" in findings[0]
  assert "decrease monotonically" in findings[1]
  assert "does not close fragility truth" in findings[2]

  guards = artifact["non_authoritative_guards"]
  assert guards["stock_runtime_authority_granted"] is False
  assert guards["effect_scale_authority_granted"] is False
  assert guards["component_failure_probability_authority_granted"] is False
  assert guards["pk_authority_granted"] is False
  assert guards["deterministic_fuze_authority_granted"] is False


def test_component_probability_surface_probe_cli_writes_json(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "a2_stage_c_component_probability_surface_probe.json"
  run_maintenance_cli(
    "damage_model.py candidate-artifacts",
    "component-probability-surface-probe",
    "--output",
    output_path,
  )

  artifact = read_json(output_path)
  assert (
    artifact["status"]
    == "candidate_non_authoritative_stage_c_component_probability_surface_probe"
  )
  assert artifact["metrics"]["probability_monotonic_decreasing_with_standoff_pass"] is True
  assert artifact["repeatability_summary"]["component_failure_probability"]["cv"] <= 0.05

# Component probability snapshot and result pack

def test_component_probability_snapshot_records_candidate_identity(
  snapshot_artifact: dict[str, Any],
) -> None:
  artifact = snapshot_artifact

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.stage_c_component_probability_snapshot.v1"
  assert (
    artifact["status"]
    == "candidate_non_authoritative_stage_c_component_probability_snapshot"
  )


def test_component_probability_snapshot_records_scope_and_summary(
  snapshot_artifact: dict[str, Any],
) -> None:
  artifact = snapshot_artifact
  scope = artifact["scope"]

  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["aspect_bucket"] == "beam"
  assert scope["closure_bucket"] == "high"
  assert scope["candidate_scope_label"] == "near_miss_0_35m"
  assert scope["runtime_miss_distance_bucket"] == "near_miss"
  assert scope["component_name"] == "right_aileron_actuator"
  assert scope["component_system"] == "flight_control"
  assert scope["component_redundancy_group_id"] == "lateral_flight_control_actuators"

  summary = artifact["summary"]
  assert summary["all_hard_gates_pass_in_current_snapshot"]
  assert summary["failed_criteria_ids"] == []
  assert summary["reviewed_checks"] == [
    "runtime_projected_component_row_present",
    "descriptor_authority_flags",
    "component_provenance_fields",
    "mechanism_load_gate_band_contains_primary_row",
    "component_probability_surface_probe",
  ]
  assert summary["primary_release_scope"] == "component_failure_probability_authority_only"
  assert summary["review_status"] == "author_snapshot_only_pending_independent_review"


def test_component_probability_snapshot_records_criteria_and_baseline_event(
  snapshot_artifact: dict[str, Any],
) -> None:
  artifact = snapshot_artifact
  criteria_rows = artifact["criteria_evaluation"]

  assert len(criteria_rows) == 23
  assert all(row["pass"] for row in criteria_rows)
  assert criteria_rows[0]["criteria_id"] == "BFM-CRIT-CP-001"
  assert criteria_rows[-1]["criteria_id"] == "BFM-CRIT-CP-023"

  baseline = artifact["baseline_event_summary"]
  assert baseline["component_primary_name"] == "right_aileron_actuator"
  assert baseline["component_failure_probability_source"] == "synthetic_sigmoid"
  assert baseline["component_primary_mechanism_fragment_energy_j"] > 0.0
  assert baseline["component_primary_mechanism_penetration_margin"] > 0.0
  assert baseline["component_primary_mechanism_blast_impulse_kpa_ms"] > 0.0


def test_component_probability_snapshot_records_candidate_probability_row(
  snapshot_artifact: dict[str, Any],
) -> None:
  artifact = snapshot_artifact
  component_snapshot = artifact["component_probability_snapshot"]

  assert component_snapshot["descriptor_status"] == (
    "test_local_component_specific_probability_candidate"
  )
  assert component_snapshot["source_kind"] == "validated_physics_surrogate"
  assert component_snapshot["calibration_status"] == "calibrated"
  assert component_snapshot["component_failure_probability_authority"] is True
  assert component_snapshot["row"]["component_name"] == "right_aileron_actuator"
  assert component_snapshot["row"]["component_failure_probability"] == 0.67
  assert component_snapshot["row"]["min_fragment_energy_j"] > 0.0
  assert component_snapshot["row"]["min_blast_impulse_kpa_ms"] > 0.0


def test_component_probability_snapshot_embeds_surface_probe_summary(
  snapshot_artifact: dict[str, Any],
) -> None:
  artifact = snapshot_artifact
  surface_probe = artifact["surface_probe_summary"]

  assert surface_probe["status"] == (
    "candidate_non_authoritative_stage_c_component_probability_surface_probe"
  )
  assert surface_probe["probe_labels"] == ["inner", "middle", "outer"]
  assert surface_probe["runtime_seed_values_are_fixed"] == [
    20260526,
    20260527,
    20260528,
  ]
  assert surface_probe["json_output_uses_sort_keys"] is True
  assert surface_probe["selected_row_ids"] == [
    "component-inner",
    "component-middle",
    "component-outer",
  ]
  assert surface_probe["primary_component_identity_stable_pass"] is True
  assert surface_probe["component_specific_precedence_pass"] is True
  assert surface_probe["selected_rows_cover_primary_loads_pass"] is True
  assert surface_probe["probability_monotonic_decreasing_with_standoff_pass"] is True
  assert surface_probe["anchor_seed_window_probability_cv"] <= 0.05
  assert surface_probe["stock_baseline_sources_are_synthetic_sigmoid"] is True
  assert surface_probe["stock_baseline_calibrated_probability_present"] is False
  assert (
    surface_probe[
      "component_specific_rows_scope_locked_to_right_aileron_actuator"
    ]
    is True
  )
  assert (
    surface_probe["selected_rows_scope_locked_to_right_aileron_actuator"]
    is True
  )


def test_component_probability_snapshot_preserves_candidate_boundaries(
  snapshot_artifact: dict[str, Any],
) -> None:
  artifact = snapshot_artifact
  findings = artifact["current_findings"]

  assert "bind a component-specific probability row" in findings[0]
  assert "three-point candidate component-probability surface probe" in findings[1]
  assert "synthetic component probability" in findings[2]
  assert "does not validate fragility truth" in findings[3]

  assert_authority_guards_false(artifact, guards_key="non_authoritative_guards")


def test_component_probability_snapshot_cli_writes_json(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "a2_stage_c_component_probability_snapshot.json"
  run_maintenance_cli(
    "damage_model.py candidate-artifacts",
    "component-probability-snapshot",
    "--output",
    output_path,
  )

  artifact = read_json(output_path)
  assert (
    artifact["status"]
    == "candidate_non_authoritative_stage_c_component_probability_snapshot"
  )
  assert artifact["summary"]["all_hard_gates_pass_in_current_snapshot"] is True
  assert_authority_guards_false(artifact, guards_key="non_authoritative_guards")


def test_component_probability_result_pack_records_candidate_identity(
  result_pack_artifact: dict[str, Any],
) -> None:
  artifact = result_pack_artifact

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert artifact["schema_version"] == "a2.stage_c_component_probability_result_pack.v1"
  assert (
    artifact["status"]
    == "candidate_non_authoritative_stage_c_component_probability_result_pack"
  )


def test_component_probability_result_pack_records_scope_and_hashes(
  result_pack_artifact: dict[str, Any],
) -> None:
  artifact = result_pack_artifact
  scope = artifact["scope"]

  assert scope["target_type"] == "F-16C_Block50"
  assert scope["weapon_class"] == "AIM-120C-class"
  assert scope["weapon_family"] == "blast_fragmentation"
  assert scope["component_name"] == "right_aileron_actuator"

  artifact_hashes = artifact["artifact_hashes"]
  assert len(artifact_hashes) == 3
  assert [row["artifact_id"] for row in artifact_hashes] == [
    "ART-RUNTIME-AUTH-001",
    "ART-STAGE-C-SNAPSHOT-001",
    "ART-STAGE-C-SURFACE-001",
  ]
  assert all(len(row["sha256"]) == 64 for row in artifact_hashes)


def test_component_probability_result_pack_records_result_table_summary(
  result_pack_artifact: dict[str, Any],
) -> None:
  artifact = result_pack_artifact
  result_summary = artifact["result_table_summary"]

  assert result_summary["all_hard_gates_pass_in_current_snapshot"] is True
  assert result_summary["failed_criteria_ids"] == []
  assert result_summary["reviewed_checks"] == [
    "runtime_projected_component_row_present",
    "descriptor_authority_flags",
    "component_provenance_fields",
    "mechanism_load_gate_band_contains_primary_row",
    "component_probability_surface_probe",
  ]
  assert (
    result_summary["primary_release_scope"]
    == "component_failure_probability_authority_only"
  )
  assert (
    result_summary["review_status"]
    == "author_result_pack_only_pending_independent_review"
  )


def test_component_probability_result_pack_records_probability_and_scope_audit(
  result_pack_artifact: dict[str, Any],
) -> None:
  artifact = result_pack_artifact
  probability = artifact["component_probability_result_summary"]

  assert probability["baseline_component_probability_source"] == "synthetic_sigmoid"
  assert probability["candidate_component_name"] == "right_aileron_actuator"
  assert probability["candidate_component_system"] == "flight_control"
  assert (
    probability["candidate_component_redundancy_group_id"]
    == "lateral_flight_control_actuators"
  )
  assert probability["candidate_component_failure_probability"] == 0.67
  assert "candidate component-specific probability snapshot only" in probability[
    "result_interpretation"
  ]

  scope_audit = artifact["scope_audit_summary"]
  assert scope_audit["projected_component_row_count"] >= 1
  assert scope_audit["primary_component_name"] == "right_aileron_actuator"
  assert scope_audit["gate_band_contains_primary_blast_scaled_distance"] is True
  assert scope_audit["gate_band_contains_primary_fragment_density"] is True
  assert scope_audit["gate_band_contains_primary_fragment_energy"] is True
  assert scope_audit["gate_band_contains_primary_penetration_margin"] is True
  assert scope_audit["gate_band_contains_primary_blast_impulse"] is True
  assert scope_audit["gate_band_contains_primary_surface_incidence"] is True
  assert "one component-specific candidate row" in scope_audit[
    "scope_guard_interpretation"
  ]


def test_component_probability_result_pack_records_fragility_surface_summary(
  result_pack_artifact: dict[str, Any],
) -> None:
  artifact = result_pack_artifact
  fragility_surface = artifact["fragility_surface_summary"]

  assert (
    fragility_surface["surface_probe_status"]
    == "candidate_non_authoritative_stage_c_component_probability_surface_probe"
  )
  assert fragility_surface["probe_row_count"] == 3
  assert fragility_surface["probe_labels"] == ["inner", "middle", "outer"]
  assert fragility_surface["runtime_seed_values_are_fixed"] == [
    20260526,
    20260527,
    20260528,
  ]
  assert fragility_surface["json_output_uses_sort_keys"] is True
  assert fragility_surface["primary_component_identity_stable_pass"] is True
  assert fragility_surface["component_specific_precedence_pass"] is True
  assert fragility_surface["selected_rows_cover_primary_loads_pass"] is True
  assert fragility_surface["probability_monotonic_decreasing_with_standoff_pass"] is True
  assert fragility_surface["anchor_seed_window_probability_cv"] <= 0.05
  assert "candidate fragility-surface" in fragility_surface["result_interpretation"]
  assert fragility_surface["stock_baseline_sources_are_synthetic_sigmoid"] is True
  assert (
    fragility_surface["component_scope_locked_to_right_aileron_actuator"]
    is True
  )


def test_component_probability_result_pack_preserves_stage_b_and_independence_boundaries(
  result_pack_artifact: dict[str, Any],
) -> None:
  artifact = result_pack_artifact
  upstream = artifact["upstream_stage_b_dependency_summary"]

  assert upstream["dependency_role"] == (
    "separate_upstream_effect_scale_authority_track"
  )
  assert upstream["status"] == "blocked_non_authoritative_stage_b_release_candidate"
  assert upstream["release_target"] == "effect_scale_authority_only"
  assert upstream["dependency_preserved_as_blocked"] is True
  assert "RES-010" in upstream["blocking_residual_ids"]
  assert "Stage C component-probability packaging remains candidate" in upstream[
    "stage_c_interlock"
  ]

  independence = artifact["independence_audit"]
  assert [row["artifact_id"] for row in independence] == [
    "ART-RUNTIME-AUTH-001",
    "ART-STAGE-C-SNAPSHOT-001",
    "ROW-COMPONENT-001",
  ]
  assert independence[0]["audit_outcome"] == "test_local_positive_path_only"
  assert (
    independence[1]["audit_outcome"]
    == "candidate_snapshot_only_not_independent_validation"
  )
  assert independence[2]["audit_outcome"] == "candidate_component_specific_only"

  findings = artifact["current_findings"]
  assert "surface probe" in findings[0]
  assert "synthetic component probability" in findings[1]
  assert "lacks independent fragility validation" in findings[2]

  assert_authority_guards_false(artifact, guards_key="non_authoritative_guards")


def test_component_probability_result_pack_cli_writes_json(
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "a2_stage_c_component_probability_result_pack.json"
  run_maintenance_cli(
    "damage_model.py candidate-artifacts",
    "component-probability-result-pack",
    "--output",
    output_path,
  )

  artifact = read_json(output_path)
  assert (
    artifact["status"]
    == "candidate_non_authoritative_stage_c_component_probability_result_pack"
  )
  assert artifact["result_table_summary"]["all_hard_gates_pass_in_current_snapshot"] is True
  assert artifact["scope_audit_summary"]["gate_band_contains_primary_surface_incidence"]
  assert artifact["scope_audit_summary"]["gate_band_contains_primary_blast_impulse"]
  assert artifact["fragility_surface_summary"]["probe_row_count"] == 3
  assert (
    artifact["upstream_stage_b_dependency_summary"]["dependency_preserved_as_blocked"]
    is True
  )

# Component probability retained artifact pack

def test_component_probability_retained_artifact_pack_writes_retained_files(
  tmp_path: Path,
) -> None:
  artifact = retained_pack.generate_retained_artifact_pack(
    repo_root=REPO_ROOT,
    output_dir=tmp_path / "retained_pack",
  )

  assert artifact["package_id"] == (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
  )
  assert (
    artifact["schema_version"]
    == "a2.stage_c_component_probability_retained_artifact_pack.v1"
  )
  assert (
    artifact["status"]
    == "author_retained_stage_c_component_probability_candidate_artifacts_only"
  )
  assert (
    artifact["retention_scope"]
    == "stage_c_component_probability_author_side_candidate_only"
  )
  assert artifact["retained_artifact_count"] == 4
  assert_hex64(artifact["manifest_sha256"])

  origin = artifact["retained_origin_summary"]
  assert origin["runtime_origin"] == "test_local_runtime_authority_exercise_only"
  assert (
    origin["review_surface"]
    == "author_side_candidate_snapshot_and_result_pack_only"
  )
  assert origin["independent_release_artifact_present"] is False
  assert origin["stock_runtime_authority_present"] is False

  rows = artifact["artifacts"]
  assert [row["artifact_key"] for row in rows] == [
    "runtime_aligned_authority_pack",
    "stage_c_component_probability_snapshot",
    "stage_c_component_probability_surface_probe",
    "stage_c_component_probability_result_pack",
  ]
  assert [row["origin_class"] for row in rows] == [
    "test_local_runtime_exercise_only",
    "author_side_candidate_snapshot_only",
    "author_side_candidate_surface_probe_only",
    "author_side_candidate_result_pack_only",
  ]
  for row in rows:
    path = REPO_ROOT / row["relative_path"]
    assert path.exists()
    assert_hex64(row["sha256"])
    assert_hex64(row["content_sha256"])
    assert "stock runtime authority" in row["forbidden_claim"]
    assert "Pk authority" in row["forbidden_claim"]
    assert "deterministic-fuze authority" in row["forbidden_claim"]
    payload = read_json(path)
    assert payload.get("status", payload.get("validation_status")) == row["status"]
    assert payload["schema_version"] == row["schema_version"]

  assert_authority_guards_false(artifact, guards_key="non_authoritative_guards")

  loaded = retained_pack.load_retained_artifact_pack_manifest(
    repo_root=REPO_ROOT,
    output_dir=tmp_path / "retained_pack",
  )
  assert loaded["manifest_exists"] is True
  assert loaded["retained_artifact_count"] == 4
  assert loaded["all_artifacts_exist"] is True
  assert loaded["manifest_relative_path"].endswith("retained_pack/manifest.json")


def test_component_probability_retained_artifact_pack_cli_writes_manifest(
  tmp_path: Path,
) -> None:
  output_dir = tmp_path / "retained_pack_cli"
  artifact = run_maintenance_json_cli(
    "damage_model.py candidate-artifacts",
    "component-probability-retained-pack",
    "--output-dir",
    output_dir,
  )
  assert (
    artifact["status"]
    == "author_retained_stage_c_component_probability_candidate_artifacts_only"
  )
  assert artifact["retained_artifact_count"] == 4
  assert artifact["retained_origin_summary"]["runtime_origin"] == (
    "test_local_runtime_authority_exercise_only"
  )
  assert (output_dir / "manifest.json").exists()
