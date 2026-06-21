from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_HEADER = REPO_ROOT / "src" / "core" / "engine" / "weapon_launch_adapter.h"
SIMULATION_KERNEL_HEADER = REPO_ROOT / "src" / "core" / "engine" / "simulation_kernel.h"


def _text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _struct_body(header: str, struct_name: str) -> str:
  pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
  match = re.search(pattern, header, flags=re.DOTALL)
  assert match is not None, f"{struct_name} is missing from {ADAPTER_HEADER}"
  return match.group("body")


def _assert_fields_present(body: str, fields: tuple[str, ...]) -> None:
  missing = [
    field
    for field in fields
    if re.search(rf"\b{re.escape(field)}\b", body) is None
  ]
  assert not missing, f"missing fields: {', '.join(missing)}"


def _assert_fields_absent(body: str, fields: tuple[str, ...]) -> None:
  present = [
    field
    for field in fields
    if re.search(rf"\b{re.escape(field)}\b", body) is not None
  ]
  assert not present, f"unexpected fields: {', '.join(present)}"


def _assert_cpp_fragment(text: str, fragment: str) -> None:
  normalized_text = re.sub(r"\s+", " ", text)
  normalized_fragment = re.sub(r"\s+", " ", fragment)
  assert normalized_fragment in normalized_text


def test_weapon_launch_adapter_is_header_only_contract_converter() -> None:
  header = _text(ADAPTER_HEADER)

  assert '#include "runtime/contracts/engagement_contracts.h"' in header
  assert "namespace engagement_adapter" in header
  _assert_cpp_fragment(header, "inline LaunchRequest make_launch_request")
  _assert_cpp_fragment(header, "inline LaunchEvent make_launch_event")
  _assert_cpp_fragment(header, "inline MunitionLifecyclePacket make_munition_lifecycle_packet")
  _assert_cpp_fragment(header, "inline EffectsEvent make_effects_event")
  _assert_cpp_fragment(header, "inline DamageReport make_damage_report")
  _assert_cpp_fragment(header, "inline DiagnosticsTrace make_diagnostics_trace")


def test_weapon_launch_adapter_does_not_depend_on_engine_owners_or_live_fire_calls() -> None:
  header = _text(ADAPTER_HEADER)
  include_lines = re.findall(r"^\s*#\s*include\s+[<\"]([^>\"]+)[>\"]", header, flags=re.MULTILINE)

  assert "core/engine" not in "\n".join(include_lines)
  assert "simulation_kernel" not in header
  assert "SimulationKernel" not in header
  assert "WorldBatchRuntime" not in header
  assert "flecs" not in header
  assert "fire_missile" not in header
  assert "fire_naval_weapon" not in header


def test_weapon_launch_adapter_snapshots_cover_launch_contract_fields() -> None:
  header = _text(ADAPTER_HEADER)

  request_snapshot = _struct_body(header, "LaunchRequestSnapshot")
  outcome_snapshot = _struct_body(header, "LegacyLaunchOutcomeSnapshot")

  _assert_fields_present(
    request_snapshot,
    (
      "world_index",
      "request_id",
      "shooter_entity_id",
      "target_entity_id",
      "has_target_entity",
      "target_track_id",
      "has_target_track",
      "station_id",
      "mount_id",
      "requested_munition_family",
      "authority",
      "requested_time_s",
      "merge_policy",
    ),
  )
  _assert_fields_present(
    outcome_snapshot,
    (
      "world_index",
      "event_id",
      "request_id",
      "accepted",
      "rejection_reason",
      "selected_launcher",
      "selected_munition",
      "ammo_delta",
      "cooldown_delta_s",
      "spawned_munition_entity_id",
      "event_time_s",
    ),
  )


def test_weapon_launch_adapter_snapshots_cover_munition_effects_damage_trace_contract_fields() -> None:
  header = _text(ADAPTER_HEADER)

  lifecycle_snapshot = _struct_body(header, "MunitionLifecycleSnapshot")
  effects_snapshot = _struct_body(header, "EffectsEventSnapshot")
  damage_snapshot = _struct_body(header, "DamageReportSnapshot")
  diagnostics_snapshot = _struct_body(header, "DiagnosticsTraceSnapshot")

  _assert_fields_present(
    lifecycle_snapshot,
    (
      "world_index",
      "packet_id",
      "munition_entity_id",
      "attacker_entity_id",
      "target_entity_id",
      "has_target_entity",
      "target_track_id",
      "has_target_track",
      "launch_event_id",
      "active",
      "seeker_mode",
      "guidance_cadence_s",
      "track_memory_state",
      "fuel_remaining_fraction",
      "burnout",
      "max_flight_time_s",
      "fuze_state",
      "source_time_s",
    ),
  )
  _assert_fields_present(
    effects_snapshot,
    (
      "world_index",
      "event_id",
      "munition_entity_id",
      "target_entity_id",
      "trigger_type",
      "outcome_state",
      "detonation_time_s",
      "nearest_approach_time_s",
      "miss_distance_m",
      "detonation_local_forward_m",
      "detonation_local_right_m",
      "detonation_local_up_m",
      "detonation_heading_deg",
      "detonation_pitch_deg",
      "detonation_roll_deg",
      "closure_mps",
      "missile_axis_forward",
      "missile_axis_right",
      "missile_axis_up",
      "quality",
      "confidence",
      "effect_family",
      "warhead_mass_kg",
      "warhead_lethal_radius_m",
      "warhead_profile_synthetic",
      "damage_scalar_synthetic",
      "fuze_type",
      "fuze_trigger_radius_m",
      "fuze_delay_s",
      "fuze_reliability",
      "fuze_profile_synthetic",
      "fuze_signature_source",
      "fuze_target_signature",
      "fuze_signature_scale",
      "fuze_effective_reliability",
      "fuze_contact_surface_distance_m",
      "fuze_contact_penetration_depth_m",
      "fuze_contact_surface_tolerance_m",
      "fuze_contact_inside_hitbox",
      "direct_hitbox_intersection",
      "projected_hitbox_count",
      "spatial_effect_scale",
      "mechanism_armor_scale",
      "mechanism_exposure_scale",
      "mechanism_effect_scale",
      "mechanism_fragment_energy_j",
      "mechanism_fragment_areal_density_per_m2",
      "mechanism_penetration_margin",
      "mechanism_blast_overpressure_kpa",
      "mechanism_blast_impulse_kpa_ms",
      "mechanism_blast_scaled_distance_m_kg13",
      "mechanism_rod_cut_margin",
      "mechanism_surface_incidence_cos",
      "warhead_spatial_sample_count",
      "warhead_spatial_hit_estimate",
      "warhead_spatial_hit_fraction",
      "warhead_spatial_energy_scale",
      "warhead_spatial_pattern_scale",
      "warhead_orientation_axis_forward",
      "warhead_orientation_axis_right",
      "warhead_orientation_axis_up",
      "warhead_orientation_pattern_scale",
      "component_threshold_scale",
      "component_failure_probability",
      "component_failure_probability_source",
      "component_failure_probability_calibrated",
      "component_failure_probability_evidence_dataset_ref",
      "component_failure_probability_evidence_row_id",
      "component_failure_probability_evidence_source_ref",
      "component_failure_probability_evidence_provenance",
      "component_failure_sample",
      "component_failure_count",
      "component_hit_count",
      "component_mechanism_load_rows",
      "component_response_rows",
      "component_primary_name",
      "component_primary_system",
      "component_primary_redundancy_group",
      "component_primary_critical",
      "component_primary_redundancy_group_id",
      "component_primary_integrity",
      "component_primary_mechanism_fragment_energy_j",
      "component_primary_mechanism_fragment_areal_density_per_m2",
      "component_primary_mechanism_penetration_margin",
      "component_primary_mechanism_blast_overpressure_kpa",
      "component_primary_mechanism_blast_impulse_kpa_ms",
      "component_primary_mechanism_blast_scaled_distance_m_kg13",
      "component_primary_mechanism_rod_cut_margin",
      "component_primary_mechanism_surface_incidence_cos",
      "component_redundancy_group_availability",
      "component_redundancy_group_member_count",
      "component_redundancy_group_failed_count",
      "vulnerability_profile_present",
      "vulnerability_profile_synthetic",
      "vulnerability_calibrated_evidence",
      "vulnerability_pk_authority",
      "vulnerability_deterministic_fuze_authority",
      "vulnerability_evidence_dataset_valid",
      "vulnerability_evidence_dataset_ref",
      "vulnerability_calibration_status",
      "vulnerability_provenance",
      "vulnerability_evidence_schema_version",
      "vulnerability_evidence_source_kind",
      "vulnerability_evidence_source_ref",
      "vulnerability_evidence_validation_artifact_ref",
      "vulnerability_evidence_validation_manifest_schema_version",
      "vulnerability_evidence_validation_status",
      "vulnerability_evidence_validation_artifact_sha256",
      "vulnerability_evidence_validated_surrogate_model_ref",
      "vulnerability_evidence_validation_benchmark_ref",
      "vulnerability_evidence_validation_metrics_ref",
      "vulnerability_evidence_validation_acceptance_criteria_ref",
      "vulnerability_aspect_bucket",
      "vulnerability_family_scale",
      "vulnerability_aspect_scale",
      "vulnerability_closure_mps",
      "vulnerability_closure_scale",
      "vulnerability_miss_distance_scale",
      "vulnerability_effect_scale",
      "vulnerability_effect_scale_source",
      "vulnerability_effect_scale_evidence_row_id",
      "vulnerability_effect_scale_evidence_source_ref",
      "vulnerability_effect_scale_evidence_provenance",
      "air_system_hit_flags",
      "air_system_spatial_scales",
      "vulnerability_scale_trace",
    ),
  )
  _assert_fields_absent(
    effects_snapshot,
    (
      "fuze_quality_damage_multiplier_applied",
      "fuze_quality_damage_multiplier",
      "warhead_damage_scalar_before_fuze_quality",
      "warhead_damage_scalar_after_fuze_quality",
    ),
  )
  _assert_fields_present(
    damage_snapshot,
    (
      "world_index",
      "report_id",
      "target_entity_id",
      "source_event_id",
      "hp_delta",
      "system_health_delta",
      "platform_damage_state_delta",
      "mission_kill",
      "mobility_kill",
      "sensor_kill",
      "survivability_kill",
      "forced_landing",
      "flight_control_kill",
      "propulsion_kill",
      "crew_kill",
      "loss_state_from",
      "loss_state_to",
      "destroyed",
      "report_time_s",
    ),
  )
  _assert_fields_present(
    diagnostics_snapshot,
    (
      "world_index",
      "trace_id",
      "parent_trace_id",
      "chain_id",
      "track_id",
      "launch_request_id",
      "launch_event_id",
      "munition_entity_id",
      "effects_event_id",
      "damage_report_id",
      "observation_packet_version",
    ),
  )


def test_legacy_weapon_api_return_shapes_remain_unchanged_for_adapter_migration() -> None:
  header = _text(SIMULATION_KERNEL_HEADER)

  assert "flecs::entity fire_missile(uint64_t attacker_id, uint64_t target_id);" in header
  assert "bool fire_naval_weapon(uint64_t attacker_id, uint64_t target_id, int weapon_type_code);" in header
