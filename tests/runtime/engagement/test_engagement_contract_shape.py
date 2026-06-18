from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ENGAGEMENT_HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "engagement_contracts.h"


def _header_text() -> str:
  return ENGAGEMENT_HEADER.read_text(encoding="utf-8")


def _struct_body(header: str, struct_name: str) -> str:
  pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
  match = re.search(pattern, header, flags=re.DOTALL)
  assert match is not None, f"{struct_name} is missing from {ENGAGEMENT_HEADER}"
  return match.group("body")


def _assert_fields_present(body: str, fields: tuple[str, ...]) -> None:
  missing = [
    field
    for field in fields
    if re.search(rf"\b{re.escape(field)}\b", body) is None
  ]
  assert not missing, f"missing fields: {', '.join(missing)}"


def test_engagement_contract_header_exists_at_stable_runtime_contract_path() -> None:
  assert ENGAGEMENT_HEADER.is_file()


def test_engagement_contract_header_does_not_include_core_or_engine_layers() -> None:
  header = _header_text()
  include_lines = re.findall(r"^\s*#\s*include\s+[<\"]([^>\"]+)[>\"]", header, flags=re.MULTILINE)

  forbidden = [
    include_path
    for include_path in include_lines
    if "core/" in include_path or "engine/" in include_path
  ]

  assert forbidden == []


def test_engagement_contract_header_exposes_cross_domain_launch_surface() -> None:
  header = _header_text()

  launch_request = _struct_body(header, "LaunchRequest")
  launch_event = _struct_body(header, "LaunchEvent")

  _assert_fields_present(
    launch_request,
    (
      "request_id",
      "shooter",
      "target_entity",
      "target_track_id",
      "station_id",
      "mount_id",
      "requested_munition_family",
      "authority",
      "requested_time_s",
      "merge_policy",
    ),
  )
  _assert_fields_present(
    launch_event,
    (
      "event_id",
      "request_id",
      "accepted",
      "rejection_reason",
      "selected_launcher",
      "selected_munition",
      "ammo_delta",
      "cooldown_delta_s",
      "spawned_munition",
      "event_time_s",
    ),
  )


def test_engagement_contract_header_exposes_mlf1b_lethality_chain_surface() -> None:
  header = _header_text()

  for marker in (
    "kLethalityChainContractSchemaVersion",
    "kLethalityChainCanonicalStages",
    "kLethalityChainTerminalNegativeReasons",
    "kLethalityObservationModeSampledRuntime",
    "kLethalityObservationModeExpectedProjection",
    "kLethalityConsumerVisibilityDiagnosticsAndTraining",
    "kLethalityReasonFuzeNoDetonation",
    "kLethalityReasonMissOutsideTriggerRadius",
    "kLethalityReasonMissileTimeout",
  ):
    assert marker in header

  common_header_fields = (
    "schema_version",
    "chain_id",
    "event_id",
    "parent_event_id",
    "stage",
    "status",
    "reason",
    "source_time_s",
    "source_frame",
    "munition",
    "shooter",
    "target",
    "producer_node_id",
    "fidelity_mode",
    "evidence_level",
    "observation_mode",
    "consumer_visibility",
    "confidence",
  )
  _assert_fields_present(_struct_body(header, "LethalityChainHeader"), common_header_fields)

  event_fields = {
    "NearestApproachEvent": (
      "header",
      "miss_distance_m",
      "nearest_approach_time_s",
      "local_forward_m",
      "local_right_m",
      "local_up_m",
      "closure_mps",
      "aspect_bucket",
    ),
    "FuzeEvaluationEvent": (
      "header",
      "fuze_type",
      "armed",
      "triggered",
      "failure_reason",
      "delay_s",
      "reliability",
      "sample",
      "expected_detonation_probability",
      "sampled_outcome",
    ),
    "WarheadMechanismEvent": (
      "header",
      "mechanism_family",
      "fragment_energy_j",
      "fragment_density_per_m2",
      "blast_overpressure_kpa",
      "rod_cut_margin",
    ),
    "SpatialCoverageEvent": (
      "header",
      "projected_hitbox_count",
      "sample_count",
      "hit_estimate",
      "hit_fraction",
      "energy_scale",
      "pattern_scale",
    ),
    "ComponentLoadEvent": (
      "header",
      "component_name",
      "component_system",
      "direct_hit",
      "distance_m",
      "effect_scale",
      "load_source",
    ),
    "ComponentDamageEvent": (
      "header",
      "component_name",
      "integrity_before",
      "integrity_after",
      "failure_mode",
      "failure_probability",
    ),
    "PlatformConsequenceEvent": (
      "header",
      "mission_capability_before",
      "mission_capability_after",
      "mobility_capability_before",
      "mobility_capability_after",
      "control_delta",
      "engine_delta",
      "fuel_leak_delta",
      "fire_state",
      "aircraft_damage_state_before",
      "aircraft_damage_state_after",
      "aircraft_damage_state_delta",
      "air_system_hit_flags",
      "air_system_spatial_scales",
      "vulnerability_scale_trace",
      "loss_state_to",
    ),
    "StructuralBreakupEvent": (
      "header",
      "breakup_state",
      "break_mode",
      "detached_part_count",
      "airframe_breakup",
      "cause_event_id",
    ),
    "LifecycleTransitionEvent": (
      "header",
      "lifecycle_from",
      "lifecycle_to",
      "ground_lifecycle",
      "wreck_entity",
      "debris_count",
      "terminal",
      "terminal_projection_id",
    ),
    "TrainingProjectionEvent": (
      "header",
      "consumed_event_ids",
      "consumer_node_id",
      "consumer_version",
      "projection_kind",
      "reward_term",
      "fact_source",
    ),
  }
  for struct_name, fields in event_fields.items():
    _assert_fields_present(_struct_body(header, struct_name), fields)


def test_engagement_contract_header_exposes_lifecycle_effects_and_damage_surface() -> None:
  header = _header_text()

  component_mechanism_load_row = _struct_body(header, "ComponentMechanismLoadRow")
  lifecycle_packet = _struct_body(header, "MunitionLifecyclePacket")
  effects_event = _struct_body(header, "EffectsEvent")
  damage_report = _struct_body(header, "DamageReport")

  _assert_fields_present(
    component_mechanism_load_row,
    (
      "component_failure_probability",
      "component_failure_probability_aspect_bucket",
      "component_failure_probability_authority",
      "component_failure_probability_source",
      "component_failure_probability_calibrated",
      "component_failure_probability_closure_bucket",
      "component_failure_probability_component_specific",
      "component_failure_probability_evidence_dataset_ref",
      "component_failure_probability_evidence_component_name",
      "component_failure_probability_evidence_component_system",
      "component_failure_probability_evidence_component_redundancy_group_id",
      "component_failure_probability_miss_distance_bucket",
      "component_failure_probability_evidence_row_id",
      "component_failure_probability_evidence_source_ref",
      "component_failure_probability_evidence_provenance",
      "component_failure_sample",
      "component_failure_probability_weapon_family",
      "component_name",
      "component_system",
      "component_redundancy_group_id",
      "direct_hit",
      "distance_m",
      "effect_scale",
      "component_threshold_scale",
      "component_dependency_propagation_count",
      "component_dependency_target_system",
      "component_dependency_edge_type",
      "component_dependency_threshold",
      "component_dependency_delay_s",
      "component_dependency_direction",
      "component_dependency_provenance",
      "component_dependency_source_availability",
      "component_dependency_effective_scale",
      "component_dependency_propagated",
      "mechanism_fragment_energy_j",
      "mechanism_fragment_areal_density_per_m2",
      "mechanism_penetration_margin",
      "mechanism_blast_overpressure_kpa",
      "mechanism_blast_impulse_kpa_ms",
      "mechanism_blast_scaled_distance_m_kg13",
      "mechanism_rod_cut_margin",
      "mechanism_surface_incidence_cos",
    ),
  )
  _assert_fields_present(
    lifecycle_packet,
    (
      "packet_id",
      "munition",
      "attacker",
      "target_entity",
      "target_track_id",
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
    effects_event,
    (
      "event_id",
      "munition",
      "target",
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
  _assert_fields_present(
    damage_report,
    (
      "report_id",
      "target",
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
      "destroyed",
      "report_time_s",
    ),
  )
