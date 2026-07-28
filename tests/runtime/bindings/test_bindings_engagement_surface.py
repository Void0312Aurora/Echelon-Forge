from __future__ import annotations

import unittest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402


def public_fields(instance: object) -> tuple[str, ...]:
  return tuple(name for name in dir(instance) if not name.startswith("_"))


def _engagement_ref(entity_id: int, *, world_index: int = 0) -> ef_py.EngagementEntityRef:
  ref = ef_py.EngagementEntityRef()
  ref.world_index = int(world_index)
  ref.entity_id = int(entity_id)
  return ref


def _make_launch_damage_packet() -> tuple[ef_py.EngagementEventPacket, int, int, int]:
  shooter_id = 101
  target_id = 202
  missile_id = 303
  snapshot_version = 11

  packet = ef_py.EngagementEventPacket()
  packet.snapshot_version = snapshot_version
  packet.barrier_id = "export"
  packet.barrier_sequence = 4
  packet.barrier_detail = "maintained_facade_export"
  packet.source_time_s = 10.0
  packet.producer_node_id = "observation_export.v1"
  packet.refs = [_engagement_ref(shooter_id)]
  packet.trace_ids = [77, 78]
  packet.packet_provenance.information_state_layer = "TrackState"
  packet.packet_provenance.source_label = "track_state_packet"
  packet.packet_provenance.maintained_status = "maintained"
  packet.packet_provenance.observation_packet_ids = [f"eng:{snapshot_version}"]
  packet.packet_provenance.source_observation_versions = [f"track:{snapshot_version}"]
  packet.diagnostics_provenance.information_state_layer = "DecisionBelief"
  packet.diagnostics_provenance.source_label = "world_truth_diagnostics"
  packet.diagnostics_provenance.maintained_status = "diagnostics_only"
  packet.diagnostics_provenance.observation_packet_ids = [f"diag:{snapshot_version}"]

  launch = ef_py.LaunchEvent()
  launch.event_id = 701
  launch.accepted = True
  launch.event_time_s = 10.0
  launch.spawned_munition = _engagement_ref(missile_id)
  launch.has_spawned_munition = True
  launch.producer_node_id = "fire_control_launch.v1"
  packet.launch_events = [launch]

  effect = ef_py.EffectsEvent()
  effect.event_id = 702
  effect.munition = _engagement_ref(missile_id)
  effect.target = _engagement_ref(target_id)
  effect.detonation_time_s = 10.2
  effect.component_hit_count = 1
  effect.component_primary_name = "left_wing_fuel_cell"
  effect.component_primary_system = "fuel"
  effect.component_primary_redundancy_group = 1.0
  effect.component_primary_critical = True
  effect.component_primary_redundancy_group_id = "wing_fuel_cells"
  effect.component_primary_integrity = 0.71
  effect.component_primary_mechanism_fragment_energy_j = 540.0
  effect.component_primary_mechanism_fragment_areal_density_per_m2 = 17.0
  effect.component_primary_mechanism_penetration_margin = 0.42
  effect.component_primary_mechanism_blast_overpressure_kpa = 18.0
  effect.component_primary_mechanism_blast_impulse_kpa_ms = 44.0
  effect.component_primary_mechanism_rod_cut_margin = 0.0
  effect.component_primary_mechanism_surface_incidence_cos = 0.67
  component_load = ef_py.ComponentMechanismLoadRow()
  component_load.component_name = "left_wing_fuel_cell"
  component_load.component_system = "fuel"
  component_load.component_redundancy_group_id = "wing_fuel_cells"
  component_load.direct_hit = True
  component_load.distance_m = 0.0
  component_load.effect_scale = 0.82
  component_load.component_dependency_propagation_count = 1
  component_load.component_dependency_target_system = "fuel"
  component_load.component_dependency_edge_type = "fuel_feed"
  component_load.component_dependency_threshold = 0.95
  component_load.component_dependency_delay_s = 0.0
  component_load.component_dependency_direction = "one_way"
  component_load.component_dependency_provenance = "unit-test typed dependency"
  component_load.component_dependency_source_availability = 0.71
  component_load.component_dependency_effective_scale = 0.80
  component_load.component_dependency_propagated = True
  component_load.mechanism_fragment_energy_j = 540.0
  component_load.mechanism_fragment_areal_density_per_m2 = 17.0
  component_load.mechanism_penetration_margin = 0.42
  component_load.mechanism_blast_overpressure_kpa = 18.0
  component_load.mechanism_blast_impulse_kpa_ms = 44.0
  component_load.mechanism_rod_cut_margin = 0.0
  component_load.mechanism_surface_incidence_cos = 0.67
  effect.component_mechanism_load_rows = [component_load]
  component_response = ef_py.ComponentResponseRow()
  component_response.source_row_index = 0
  component_response.component_name = "left_wing_fuel_cell"
  component_response.component_system = "fuel"
  component_response.component_redundancy_group_id = "wing_fuel_cells"
  component_response.threshold_scale = 1.15
  component_response.failure_probability = 0.37
  component_response.failure_probability_source = "vulnerability_evidence_row"
  component_response.failure_probability_calibrated = True
  component_response.failure_probability_evidence_dataset_ref = "unit_test_rows"
  component_response.failure_probability_evidence_row_id = "row-wing-fuel-high-rod"
  component_response.failure_probability_evidence_source_ref = (
    "fixture://unit-test-rows#row-wing-fuel-high-rod"
  )
  component_response.failure_probability_evidence_provenance = "unit-test row fixture"
  component_response.failure_sample = 0.21
  component_response.failure_probability_authority = True
  component_response.failure_probability_component_specific = True
  component_response.failure_probability_weapon_family = "continuous_rod"
  component_response.failure_probability_aspect_bucket = "beam"
  component_response.failure_probability_closure_bucket = "high"
  component_response.failure_probability_miss_distance_bucket = "direct_hit"
  component_response.failure_probability_evidence_component_name = "left_wing_fuel_cell"
  component_response.failure_probability_evidence_component_system = "fuel"
  component_response.failure_probability_evidence_component_redundancy_group_id = (
    "wing_fuel_cells"
  )
  effect.component_response_rows = [component_response]
  effect.component_failure_probability_source = "vulnerability_evidence_row"
  effect.component_failure_probability_calibrated = True
  effect.component_failure_probability_evidence_dataset_ref = "unit_test_rows"
  effect.component_failure_probability_evidence_row_id = "row-wing-fuel-high-rod"
  effect.component_failure_probability_evidence_source_ref = "fixture://unit-test-rows#row-wing-fuel-high-rod"
  effect.component_failure_probability_evidence_provenance = "unit-test row fixture"
  effect.vulnerability_evidence_validation_manifest_schema_version = (
    "a2.vulnerability_surrogate_validation.v1"
  )
  effect.vulnerability_evidence_validation_status = "validated"
  effect.vulnerability_evidence_validation_artifact_sha256 = "abc123"
  effect.vulnerability_evidence_validated_surrogate_model_ref = "fixture://surrogate/model"
  effect.vulnerability_evidence_validation_benchmark_ref = "fixture://surrogate/benchmark"
  effect.vulnerability_evidence_validation_metrics_ref = "fixture://surrogate/metrics"
  effect.vulnerability_evidence_validation_acceptance_criteria_ref = "fixture://surrogate/acceptance"
  effect.component_redundancy_group_availability = 0.86
  effect.component_redundancy_group_member_count = 2
  effect.component_redundancy_group_failed_count = 0
  effect.mechanism_fragment_energy_j = 540.0
  effect.mechanism_fragment_areal_density_per_m2 = 17.0
  effect.mechanism_penetration_margin = 0.42
  effect.mechanism_blast_overpressure_kpa = 18.0
  effect.mechanism_blast_impulse_kpa_ms = 44.0
  effect.mechanism_surface_incidence_cos = 0.67
  effect.producer_node_id = "effects_damage.v1"
  packet.effects_events = [effect]

  report = ef_py.DamageReport()
  report.report_id = 703
  report.target = _engagement_ref(target_id)
  report.source_event_id = effect.event_id
  report.report_time_s = 10.2
  report.producer_node_id = "effects_damage.v1"
  packet.damage_reports = [report]

  launch_trace = ef_py.DiagnosticsTrace()
  launch_trace.trace_id = 77
  launch_trace.launch_event_id = launch.event_id
  launch_trace.munition = _engagement_ref(missile_id)
  launch_trace.source_snapshot_version = snapshot_version
  launch_trace.barrier_id = "export"
  launch_trace.barrier_detail = "maintained_facade_export"
  launch_trace.source_time_s = 10.0
  launch_trace.source_node_id = "fire_control_launch.v1"
  launch_trace.export_node_id = "observation_export.v1"

  damage_trace = ef_py.DiagnosticsTrace()
  damage_trace.trace_id = 78
  damage_trace.launch_event_id = launch.event_id
  damage_trace.effects_event_id = effect.event_id
  damage_trace.damage_report_id = report.report_id
  damage_trace.munition = _engagement_ref(missile_id)
  damage_trace.source_snapshot_version = snapshot_version
  damage_trace.barrier_id = "export"
  damage_trace.barrier_detail = "maintained_facade_export"
  damage_trace.source_time_s = 10.2
  damage_trace.source_node_id = "effects_damage.v1"
  damage_trace.export_node_id = "observation_export.v1"
  packet.diagnostics_traces = [launch_trace, damage_trace]
  return packet, shooter_id, target_id, missile_id


class BindingsEngagementSurfaceTests(unittest.TestCase):
  def test_engagement_entity_ref_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.EngagementEntityRef()),
      (
        "entity_id",
        "world_index",
      ),
    )

  def test_track_packet_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.TrackPacket()),
      (
        "classification",
        "confidence",
        "correlated_entity",
        "correlation_policy",
        "has_correlated_entity",
        "iff",
        "quality",
        "snapshot_version",
        "source",
        "source_time_s",
        "status",
        "track_id",
        "update_age_s",
        "usable",
      ),
    )

  def test_launch_request_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.LaunchRequest()),
      (
        "authority",
        "has_target_entity",
        "has_target_track",
        "merge_policy",
        "mount_id",
        "request_id",
        "requested_munition_family",
        "requested_time_s",
        "shooter",
        "station_id",
        "target_entity",
        "target_track_id",
      ),
    )

  def test_launch_event_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.LaunchEvent()),
      (
        "accepted",
        "ammo_delta",
        "cooldown_delta_s",
        "event_id",
        "event_time_s",
        "has_spawned_munition",
        "producer_node_id",
        "rejection_reason",
        "request_id",
        "selected_launcher",
        "selected_munition",
        "spawned_munition",
      ),
    )

  def test_munition_lifecycle_packet_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.MunitionLifecyclePacket()),
      (
        "active",
        "attacker",
        "burnout",
        "fuel_remaining_fraction",
        "fuze_state",
        "guidance_cadence_s",
        "has_target_entity",
        "has_target_track",
        "launch_event_id",
        "max_flight_time_s",
        "munition",
        "packet_id",
        "seeker_mode",
        "source_time_s",
        "target_entity",
        "target_track_id",
        "track_memory_state",
      ),
    )

  def test_lethality_chain_event_public_fields_expose_mlf1b_shape(self) -> None:
    self.assertTrue(
      {
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
      }.issubset(public_fields(ef_py.LethalityChainHeader()))
    )
    self.assertTrue(
      {
        "header",
        "miss_distance_m",
        "nearest_approach_time_s",
        "local_forward_m",
        "local_right_m",
        "local_up_m",
        "closure_mps",
        "aspect_bucket",
      }.issubset(public_fields(ef_py.NearestApproachEvent()))
    )
    self.assertTrue(
      {
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
        "sensor_opportunity_source",
        "sensor_opportunity_score",
        "terminal_track_valid",
        "target_detected",
        "target_detection_source",
        "target_detection_confidence",
        "target_detection_threshold",
        "detonation_point_source",
        "mechanism_coverage_score",
      }.issubset(public_fields(ef_py.FuzeEvaluationEvent()))
    )
    self.assertTrue({"header", "mechanism_family"}.issubset(
      public_fields(ef_py.WarheadMechanismEvent())
    ))
    self.assertTrue({"header", "sample_count"}.issubset(
      public_fields(ef_py.SpatialCoverageEvent())
    ))
    self.assertTrue(
      {
        "header",
        "component_name",
        "spatial_intersection_fraction",
        "pattern_weight",
        "orientation_weight",
        "receiver_exposure_fraction",
        "armor_transmission",
        "sampling_confidence",
        "load_intensity_scale",
      }.issubset(public_fields(ef_py.ComponentLoadEvent()))
    )
    self.assertTrue({"header", "integrity_before", "integrity_after"}.issubset(
      public_fields(ef_py.ComponentDamageEvent())
    ))
    self.assertTrue(
      {
        "header",
        "mission_capability_before",
        "mission_capability_after",
        "control_delta",
        "engine_delta",
        "fuel_leak_delta",
        "aircraft_damage_state_delta",
        "air_system_hit_flags",
        "air_system_spatial_scales",
        "vulnerability_scale_trace",
        "loss_state_to",
      }.issubset(public_fields(ef_py.PlatformConsequenceEvent()))
    )
    self.assertTrue({"header", "breakup_state"}.issubset(
      public_fields(ef_py.StructuralBreakupEvent())
    ))
    self.assertTrue(
      {
        "header",
        "lifecycle_from",
        "lifecycle_to",
        "terminal",
        "terminal_projection_id",
      }.issubset(public_fields(ef_py.LifecycleTransitionEvent()))
    )
    self.assertTrue({"header", "consumed_event_ids", "fact_source"}.issubset(
      public_fields(ef_py.TrainingProjectionEvent())
    ))
    self.assertFalse(ef_py.TrainingProjectionEvent().fact_source)

  def test_component_mechanism_load_row_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.ComponentMechanismLoadRow()),
      (
        "component_dependency_delay_s",
        "component_dependency_direction",
        "component_dependency_edge_type",
        "component_dependency_effective_scale",
        "component_dependency_propagated",
        "component_dependency_propagation_count",
        "component_dependency_provenance",
        "component_dependency_source_availability",
        "component_dependency_target_system",
        "component_dependency_threshold",
        "component_name",
        "component_redundancy_group_id",
        "component_system",
        "direct_hit",
        "distance_m",
        "effect_scale",
        "mechanism_blast_impulse_kpa_ms",
        "mechanism_blast_overpressure_kpa",
        "mechanism_blast_scaled_distance_m_kg13",
        "mechanism_fragment_areal_density_per_m2",
        "mechanism_fragment_energy_j",
        "mechanism_penetration_margin",
        "mechanism_rod_cut_margin",
        "mechanism_surface_incidence_cos",
      ),
    )

  def test_component_response_row_public_fields_expose_response_owner_shape(self) -> None:
    self.assertTrue(
      {
        "owner_stage",
        "source_current_owner_stage",
        "source_row_index",
        "component_name",
        "component_system",
        "component_redundancy_group_id",
        "threshold_scale",
        "failure_probability",
        "failure_sample",
        "failure_probability_source",
        "failure_probability_calibrated",
        "failure_probability_evidence_dataset_ref",
        "failure_probability_evidence_row_id",
        "failure_probability_evidence_source_ref",
        "failure_probability_evidence_provenance",
        "failure_probability_authority",
        "failure_probability_component_specific",
        "failure_probability_weapon_family",
        "failure_probability_aspect_bucket",
        "failure_probability_closure_bucket",
        "failure_probability_miss_distance_bucket",
        "failure_probability_evidence_component_name",
        "failure_probability_evidence_component_system",
        "failure_probability_evidence_component_redundancy_group_id",
        "failure_mode",
        "failure_severity",
        "failure_mode_names",
        "failure_mode_severities",
        "failure_mode_source",
        "failure_mode_authority",
        "integrity_before",
        "integrity_after",
        "redundancy_group_availability_before",
        "redundancy_group_availability_after",
      }.issubset(public_fields(ef_py.ComponentResponseRow()))
    )
    row = ef_py.ComponentResponseRow()
    self.assertEqual(row.owner_stage, "component_response")
    self.assertEqual(row.source_current_owner_stage, "component_response_row")
    self.assertNotIn("facade_owner_projected", public_fields(row))
    self.assertNotIn("runtime_owner_migrated", public_fields(row))

  def test_effects_event_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.EffectsEvent()),
      (
        "air_system_hit_flags",
        "air_system_spatial_scales",
        "closure_mps",
        "component_failure_count",
        "component_failure_probability",
        "component_failure_probability_calibrated",
        "component_failure_probability_evidence_dataset_ref",
        "component_failure_probability_evidence_provenance",
        "component_failure_probability_evidence_row_id",
        "component_failure_probability_evidence_source_ref",
        "component_failure_probability_source",
        "component_failure_sample",
        "component_hit_count",
        "component_mechanism_load_rows",
        "component_primary_critical",
        "component_primary_integrity",
        "component_primary_mechanism_blast_impulse_kpa_ms",
        "component_primary_mechanism_blast_overpressure_kpa",
        "component_primary_mechanism_blast_scaled_distance_m_kg13",
        "component_primary_mechanism_fragment_areal_density_per_m2",
        "component_primary_mechanism_fragment_energy_j",
        "component_primary_mechanism_penetration_margin",
        "component_primary_mechanism_rod_cut_margin",
        "component_primary_mechanism_surface_incidence_cos",
        "component_primary_name",
        "component_primary_redundancy_group",
        "component_primary_redundancy_group_id",
        "component_primary_system",
        "component_redundancy_group_availability",
        "component_redundancy_group_failed_count",
        "component_redundancy_group_member_count",
        "component_response_rows",
        "component_threshold_scale",
        "confidence",
        "damage_scalar_synthetic",
        "detonation_heading_deg",
        "detonation_local_forward_m",
        "detonation_local_right_m",
        "detonation_local_up_m",
        "detonation_pitch_deg",
        "detonation_point_source",
        "detonation_roll_deg",
        "detonation_time_s",
        "direct_hitbox_intersection",
        "effect_family",
        "event_id",
        "fuze_contact_inside_hitbox",
        "fuze_contact_penetration_depth_m",
        "fuze_contact_surface_distance_m",
        "fuze_contact_surface_tolerance_m",
        "fuze_delay_s",
        "fuze_effective_reliability",
        "fuze_mechanism_coverage_score",
        "fuze_profile_synthetic",
        "fuze_reliability",
        "fuze_sensor_opportunity_score",
        "fuze_sensor_opportunity_source",
        "fuze_signature_scale",
        "fuze_signature_source",
        "fuze_target_detected",
        "fuze_target_detection_confidence",
        "fuze_target_detection_source",
        "fuze_target_detection_threshold",
        "fuze_target_signature",
        "fuze_terminal_track_valid",
        "fuze_trigger_radius_m",
        "fuze_type",
        "mechanism_armor_scale",
        "mechanism_blast_impulse_kpa_ms",
        "mechanism_blast_overpressure_kpa",
        "mechanism_blast_scaled_distance_m_kg13",
        "mechanism_effect_scale",
        "mechanism_exposure_scale",
        "mechanism_fragment_areal_density_per_m2",
        "mechanism_fragment_energy_j",
        "mechanism_penetration_margin",
        "mechanism_rod_cut_margin",
        "mechanism_surface_incidence_cos",
        "miss_distance_m",
        "missile_axis_forward",
        "missile_axis_right",
        "missile_axis_up",
        "munition",
        "nearest_approach_time_s",
        "outcome_state",
        "producer_node_id",
        "projected_hitbox_count",
        "quality",
        "spatial_effect_scale",
        "target",
        "trigger_type",
        "vulnerability_aspect_bucket",
        "vulnerability_aspect_scale",
        "vulnerability_calibrated_evidence",
        "vulnerability_calibration_status",
        "vulnerability_closure_mps",
        "vulnerability_closure_scale",
        "vulnerability_deterministic_fuze_authority",
        "vulnerability_effect_scale",
        "vulnerability_effect_scale_evidence_provenance",
        "vulnerability_effect_scale_evidence_row_id",
        "vulnerability_effect_scale_evidence_source_ref",
        "vulnerability_effect_scale_source",
        "vulnerability_evidence_dataset_ref",
        "vulnerability_evidence_dataset_valid",
        "vulnerability_evidence_schema_version",
        "vulnerability_evidence_source_kind",
        "vulnerability_evidence_source_ref",
        "vulnerability_evidence_validated_surrogate_model_ref",
        "vulnerability_evidence_validation_acceptance_criteria_ref",
        "vulnerability_evidence_validation_artifact_ref",
        "vulnerability_evidence_validation_artifact_sha256",
        "vulnerability_evidence_validation_benchmark_ref",
        "vulnerability_evidence_validation_manifest_schema_version",
        "vulnerability_evidence_validation_metrics_ref",
        "vulnerability_evidence_validation_status",
        "vulnerability_family_scale",
        "vulnerability_miss_distance_scale",
        "vulnerability_pk_authority",
        "vulnerability_profile_present",
        "vulnerability_profile_synthetic",
        "vulnerability_provenance",
        "vulnerability_scale_trace",
        "warhead_lethal_radius_m",
        "warhead_mass_kg",
        "warhead_orientation_axis_forward",
        "warhead_orientation_axis_right",
        "warhead_orientation_axis_up",
        "warhead_orientation_pattern_scale",
        "warhead_profile_synthetic",
        "warhead_spatial_energy_scale",
        "warhead_spatial_hit_estimate",
        "warhead_spatial_hit_fraction",
        "warhead_spatial_pattern_scale",
        "warhead_spatial_sample_count",
      ),
    )

  def test_damage_report_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.DamageReport()),
      (
        "crew_kill",
        "destroyed",
        "flight_control_kill",
        "forced_landing",
        "hp_delta",
        "loss_state_from",
        "loss_state_to",
        "mission_kill",
        "mobility_kill",
        "platform_damage_state_delta",
        "producer_node_id",
        "propulsion_kill",
        "report_id",
        "report_time_s",
        "sensor_kill",
        "source_event_id",
        "survivability_kill",
        "system_health_delta",
        "target",
      ),
    )

  def test_kill_chain_runtime_facade_binding_projects_effects_event(self) -> None:
    effect = ef_py.EffectsEvent()
    effect.event_id = 9001
    effect.outcome_state = "damage_applied"
    effect.miss_distance_m = 4.25
    effect.detonation_local_forward_m = 1.0
    effect.detonation_local_right_m = -2.0
    effect.detonation_local_up_m = 0.5
    effect.nearest_approach_time_s = 12.5
    effect.closure_mps = 820.0
    effect.fuze_type = "radar_proximity"
    effect.confidence = 0.91
    effect.quality = 0.73
    effect.fuze_sensor_opportunity_score = 0.88
    effect.fuze_terminal_track_valid = True
    effect.fuze_target_detected = True
    effect.fuze_target_detection_confidence = 0.84
    effect.fuze_target_detection_threshold = 0.6
    effect.detonation_point_source = "nearest_approach"
    effect.effect_family = "blast_fragmentation"
    effect.warhead_mass_kg = 18.144
    effect.warhead_lethal_radius_m = 15.0
    effect.spatial_effect_scale = 0.44
    effect.mechanism_armor_scale = 0.72
    effect.mechanism_exposure_scale = 0.81
    effect.mechanism_effect_scale = 0.66
    effect.projected_hitbox_count = 4
    effect.warhead_spatial_sample_count = 32
    effect.warhead_spatial_hit_estimate = 3.0
    effect.warhead_spatial_hit_fraction = 0.09375
    effect.warhead_spatial_energy_scale = 0.5
    effect.warhead_spatial_pattern_scale = 0.75
    effect.warhead_orientation_pattern_scale = 0.9
    effect.mechanism_fragment_energy_j = 540.0
    effect.mechanism_fragment_areal_density_per_m2 = 17.0
    effect.mechanism_penetration_margin = 0.42
    effect.mechanism_blast_overpressure_kpa = 18.0
    effect.mechanism_blast_impulse_kpa_ms = 44.0
    effect.mechanism_blast_scaled_distance_m_kg13 = 1.7
    effect.mechanism_rod_cut_margin = 0.0
    effect.mechanism_surface_incidence_cos = 0.67
    effect.vulnerability_profile_present = True
    effect.vulnerability_profile_synthetic = False
    effect.vulnerability_calibrated_evidence = True
    effect.vulnerability_pk_authority = False
    effect.vulnerability_deterministic_fuze_authority = False
    effect.vulnerability_calibration_status = "fixture"
    effect.vulnerability_aspect_bucket = "beam"
    effect.vulnerability_family_scale = 1.1
    effect.vulnerability_aspect_scale = 1.2
    effect.vulnerability_closure_scale = 1.3
    effect.vulnerability_miss_distance_scale = 0.7
    effect.vulnerability_effect_scale = 1.0
    effect.component_hit_count = 1
    effect.component_failure_count = 1
    effect.component_primary_name = "left_wing_fuel_cell"
    effect.component_primary_system = "fuel"
    effect.component_primary_integrity = 0.62
    effect.component_redundancy_group_availability = 0.86
    effect.air_system_hit_flags = "fuel"
    effect.air_system_spatial_scales = "fixture-scales"
    effect.vulnerability_scale_trace = "fixture-trace"

    component_load = ef_py.ComponentMechanismLoadRow()
    component_load.component_name = "left_wing_fuel_cell"
    component_load.component_system = "fuel"
    component_load.component_redundancy_group_id = "wing_fuel_cells"
    component_load.direct_hit = True
    component_load.distance_m = 0.0
    component_load.effect_scale = 0.82
    component_load.mechanism_fragment_energy_j = 540.0
    component_load.mechanism_fragment_areal_density_per_m2 = 17.0
    component_load.mechanism_penetration_margin = 0.42
    component_load.mechanism_blast_overpressure_kpa = 18.0
    component_load.mechanism_blast_impulse_kpa_ms = 44.0
    component_load.mechanism_blast_scaled_distance_m_kg13 = 1.7
    component_load.mechanism_rod_cut_margin = 0.0
    component_load.mechanism_surface_incidence_cos = 0.67
    effect.component_mechanism_load_rows = [component_load]

    component_response = ef_py.ComponentResponseRow()
    component_response.source_row_index = 0
    component_response.component_name = "left_wing_fuel_cell"
    component_response.component_system = "fuel"
    component_response.component_redundancy_group_id = "wing_fuel_cells"
    component_response.threshold_scale = 1.15
    component_response.failure_probability = 0.37
    component_response.failure_sample = 0.21
    component_response.failure_probability_source = "vulnerability_evidence_row"
    component_response.failure_probability_calibrated = True
    component_response.failure_probability_evidence_component_name = "left_wing_fuel_cell"
    component_response.failure_probability_evidence_component_system = "fuel"
    component_response.failure_probability_evidence_component_redundancy_group_id = (
      "wing_fuel_cells"
    )
    component_response.failure_mode = "leak"
    component_response.failure_severity = 0.64
    component_response.integrity_before = 1.0
    component_response.integrity_after = 0.62
    effect.component_response_rows = [component_response]

    facade = ef_py.make_kill_chain_runtime_facade(effect)

    self.assertEqual(facade.schema_name, "a2.kill_chain_runtime_facade.v1")
    self.assertTrue(facade.runtime_dto_authority)
    self.assertFalse(facade.runtime_parameter_retuning)
    self.assertFalse(facade.calibration_authority)
    self.assertFalse(facade.real_world_pk)
    self.assertNotIn("component_response_runtime_owner_migrated", public_fields(facade))
    self.assertNotIn("component_response_source", public_fields(facade))
    self.assertAlmostEqual(facade.approach_fact.closest_distance_m, 4.25)
    self.assertEqual(facade.approach_fact.owner_stage, "approach")
    self.assertEqual(facade.fuze_decision.owner_stage, "fuze_decision")
    self.assertTrue(facade.fuze_decision.detonated)
    self.assertNotIn("fuze_quality_damage_multiplier_applied", public_fields(facade.fuze_decision))
    self.assertNotIn("fuze_quality_damage_multiplier", public_fields(facade.fuze_decision))
    self.assertEqual(facade.warhead_load_field.owner_stage, "warhead_load_field")
    self.assertEqual(len(facade.warhead_load_field.component_loads), 1)
    load = facade.warhead_load_field.component_loads[0]
    self.assertEqual(load.owner_stage, "warhead_load_field")
    self.assertEqual(load.component_name, "left_wing_fuel_cell")
    self.assertAlmostEqual(load.fragment_energy_j, 540.0)
    self.assertAlmostEqual(load.spatial_intersection_fraction, 0.09375)
    self.assertAlmostEqual(load.pattern_weight, 0.75)
    self.assertAlmostEqual(load.orientation_weight, 0.9)
    self.assertAlmostEqual(load.receiver_exposure_fraction, 0.81)
    self.assertAlmostEqual(load.armor_transmission, 0.72)
    self.assertAlmostEqual(load.sampling_confidence, 0.91)
    self.assertAlmostEqual(load.load_intensity_scale, 0.66)
    self.assertEqual(facade.target_susceptibility.owner_stage, "target_susceptibility")
    self.assertTrue(facade.target_susceptibility.calibrated_evidence)
    self.assertEqual(len(facade.component_responses), 1)
    response = facade.component_responses[0]
    self.assertEqual(response.owner_stage, "component_response")
    self.assertEqual(response.source_current_owner_stage, "component_response_row")
    self.assertEqual(response.source_row_index, 0)
    self.assertNotIn("facade_owner_projected", public_fields(response))
    self.assertNotIn("runtime_owner_migrated", public_fields(response))
    self.assertAlmostEqual(response.failure_probability, 0.37)
    self.assertEqual(
      response.failure_probability_evidence_component_name,
      "left_wing_fuel_cell",
    )
    self.assertEqual(response.failure_probability_evidence_component_system, "fuel")
    self.assertEqual(
      response.failure_probability_evidence_component_redundancy_group_id,
      "wing_fuel_cells",
    )
    self.assertEqual(response.failure_mode, "leak")
    self.assertEqual(facade.consequence_projection.owner_stage, "consequence_projection")
    self.assertEqual(facade.consequence_projection.outcome_state, "damage_applied")

  def test_kill_chain_runtime_facade_detonation_flag_uses_positive_outcomes(self) -> None:
    for outcome in (
      "damage_applied",
      "detonated_no_effect",
      "hit",
    ):
      effect = ef_py.EffectsEvent()
      effect.outcome_state = outcome
      facade = ef_py.make_kill_chain_runtime_facade(effect)
      self.assertTrue(facade.fuze_decision.detonated, outcome)

    for outcome in (
      "fuze_no_detonation",
      "fuze_no_terminal_track",
      "miss_outside_trigger_radius",
      "outside_sensor_window",
      "target_not_detected",
      "missile_timeout",
      "unknown",
      "rejected",
    ):
      effect = ef_py.EffectsEvent()
      effect.outcome_state = outcome
      facade = ef_py.make_kill_chain_runtime_facade(effect)
      self.assertFalse(facade.fuze_decision.detonated, outcome)

  def test_diagnostics_trace_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.DiagnosticsTrace()),
      (
        "barrier_detail",
        "barrier_id",
        "chain_id",
        "damage_report_id",
        "effects_event_id",
        "export_node_id",
        "launch_event_id",
        "launch_request_id",
        "munition",
        "observation_packet_version",
        "parent_trace_id",
        "source_node_id",
        "source_snapshot_version",
        "source_time_s",
        "trace_id",
        "track_id",
      ),
    )

  def test_engagement_batch_request_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.EngagementBatchRequest()),
      (
        "include_damage_reports",
        "include_diagnostics_traces",
        "include_effects_events",
        "include_launch_events",
        "include_launch_requests",
        "include_munition_lifecycle_packets",
        "include_track_packets",
        "refs",
        "trace_ids",
      ),
    )

  def test_engagement_event_packet_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.EngagementEventPacket()),
      (
        "barrier_detail",
        "barrier_id",
        "barrier_sequence",
        "component_damage_events",
        "component_load_events",
        "damage_reports",
        "diagnostics_provenance",
        "diagnostics_traces",
        "effects_events",
        "fuze_evaluation_events",
        "launch_events",
        "launch_requests",
        "lifecycle_transition_events",
        "munition_lifecycle_packets",
        "nearest_approach_events",
        "packet_provenance",
        "platform_consequence_events",
        "producer_node_id",
        "refs",
        "snapshot_version",
        "source_time_s",
        "spatial_coverage_events",
        "structural_breakup_events",
        "trace_ids",
        "track_packets",
        "training_projection_events",
        "warhead_mechanism_events",
      ),
    )

  def test_lethality_chain_vectors_round_trip_on_python_packets(self) -> None:
    header = ef_py.LethalityChainHeader()
    header.chain_id = 7001
    header.event_id = 7002
    header.parent_event_id = 7000
    header.stage = "nearest_approach"
    header.status = "pass"
    header.reason = "shape_contract_unit_test"
    header.evidence_level = "training_synthetic"
    header.munition = _engagement_ref(303)
    header.shooter = _engagement_ref(101)
    header.target = _engagement_ref(202)

    nearest = ef_py.NearestApproachEvent()
    nearest.header = header
    nearest.miss_distance_m = 2.5

    projection = ef_py.TrainingProjectionEvent()
    projection.header = header
    projection.consumed_event_ids = [nearest.header.event_id]
    projection.consumer_node_id = "unit-test-consumer"

    packet = ef_py.EngagementEventPacket()
    packet.nearest_approach_events = [nearest]
    packet.fuze_evaluation_events = [ef_py.FuzeEvaluationEvent()]
    packet.warhead_mechanism_events = [ef_py.WarheadMechanismEvent()]
    packet.spatial_coverage_events = [ef_py.SpatialCoverageEvent()]
    packet.component_load_events = [ef_py.ComponentLoadEvent()]
    packet.component_damage_events = [ef_py.ComponentDamageEvent()]
    packet.platform_consequence_events = [ef_py.PlatformConsequenceEvent()]
    packet.structural_breakup_events = [ef_py.StructuralBreakupEvent()]
    packet.lifecycle_transition_events = [ef_py.LifecycleTransitionEvent()]
    packet.training_projection_events = [projection]

    recent = ef_py.RecentEngagementEvents()
    recent.nearest_approach_events = [nearest]
    recent.training_projection_events = [projection]

    self.assertEqual(float(packet.nearest_approach_events[0].miss_distance_m), 2.5)
    self.assertEqual(
      int(packet.training_projection_events[0].consumed_event_ids[0]),
      int(nearest.header.event_id),
    )
    self.assertFalse(packet.training_projection_events[0].fact_source)
    self.assertEqual(int(recent.nearest_approach_events[0].header.chain_id), 7001)

  def test_live_engagement_packet_binding_surface_exposes_wp11_vertical_slice_chain(self) -> None:
    packet, _, target_id, missile_id = _make_launch_damage_packet()

    self.assertEqual(packet.barrier_id, "export")
    self.assertEqual(packet.barrier_detail, "maintained_facade_export")
    self.assertEqual(packet.producer_node_id, "observation_export.v1")
    self.assertEqual(packet.packet_provenance.information_state_layer, "TrackState")
    self.assertEqual(packet.packet_provenance.source_label, "track_state_packet")
    self.assertEqual(packet.packet_provenance.maintained_status, "maintained")
    self.assertEqual(
      list(packet.packet_provenance.observation_packet_ids),
      [f"eng:{int(packet.snapshot_version)}"],
    )
    self.assertEqual(
      list(packet.packet_provenance.source_observation_versions),
      [f"track:{int(packet.snapshot_version)}"],
    )
    self.assertEqual(
      packet.diagnostics_provenance.information_state_layer,
      "DecisionBelief",
    )
    self.assertEqual(
      packet.diagnostics_provenance.source_label,
      "world_truth_diagnostics",
    )
    self.assertEqual(
      packet.diagnostics_provenance.maintained_status,
      "diagnostics_only",
    )
    self.assertEqual(
      list(packet.diagnostics_provenance.observation_packet_ids),
      [f"diag:{int(packet.snapshot_version)}"],
    )
    self.assertTrue(
      any(
        event.producer_node_id == "fire_control_launch.v1"
        and int(event.spawned_munition.entity_id) == missile_id
        for event in packet.launch_events
      )
    )
    self.assertTrue(
      any(
        event.producer_node_id == "effects_damage.v1"
        and int(event.target.entity_id) == target_id
        for event in packet.effects_events
      )
    )
    damage_event = next(
      event
      for event in packet.effects_events
      if event.producer_node_id == "effects_damage.v1"
      and int(event.target.entity_id) == target_id
    )
    component_rows = list(damage_event.component_mechanism_load_rows)
    self.assertEqual(len(component_rows), 1)
    self.assertEqual(str(component_rows[0].component_name), "left_wing_fuel_cell")
    self.assertEqual(str(component_rows[0].component_system), "fuel")
    self.assertEqual(str(component_rows[0].component_redundancy_group_id), "wing_fuel_cells")
    self.assertTrue(bool(component_rows[0].direct_hit))
    self.assertEqual(int(component_rows[0].component_dependency_propagation_count), 1)
    self.assertEqual(str(component_rows[0].component_dependency_target_system), "fuel")
    self.assertEqual(str(component_rows[0].component_dependency_edge_type), "fuel_feed")
    self.assertAlmostEqual(float(component_rows[0].component_dependency_threshold), 0.95)
    self.assertAlmostEqual(float(component_rows[0].component_dependency_delay_s), 0.0)
    self.assertEqual(str(component_rows[0].component_dependency_direction), "one_way")
    self.assertEqual(
      str(component_rows[0].component_dependency_provenance),
      "unit-test typed dependency",
    )
    self.assertAlmostEqual(
      float(component_rows[0].component_dependency_source_availability),
      0.71,
    )
    self.assertAlmostEqual(float(component_rows[0].component_dependency_effective_scale), 0.80)
    self.assertTrue(bool(component_rows[0].component_dependency_propagated))
    self.assertFalse(hasattr(component_rows[0], "component_failure_probability"))
    self.assertFalse(hasattr(component_rows[0], "component_threshold_scale"))
    response_rows = list(damage_event.component_response_rows)
    self.assertEqual(len(response_rows), 1)
    self.assertEqual(str(response_rows[0].component_name), "left_wing_fuel_cell")
    self.assertEqual(str(response_rows[0].component_system), "fuel")
    self.assertEqual(str(response_rows[0].component_redundancy_group_id), "wing_fuel_cells")
    self.assertAlmostEqual(float(response_rows[0].threshold_scale), 1.15)
    self.assertAlmostEqual(float(response_rows[0].failure_probability), 0.37)
    self.assertEqual(
      str(response_rows[0].failure_probability_source),
      "vulnerability_evidence_row",
    )
    self.assertTrue(bool(response_rows[0].failure_probability_calibrated))
    self.assertEqual(
      str(response_rows[0].failure_probability_evidence_dataset_ref),
      "unit_test_rows",
    )
    self.assertEqual(
      str(response_rows[0].failure_probability_evidence_row_id),
      "row-wing-fuel-high-rod",
    )
    self.assertEqual(
      str(response_rows[0].failure_probability_evidence_source_ref),
      "fixture://unit-test-rows#row-wing-fuel-high-rod",
    )
    self.assertEqual(
      str(response_rows[0].failure_probability_evidence_provenance),
      "unit-test row fixture",
    )
    self.assertEqual(
      str(damage_event.vulnerability_evidence_validation_manifest_schema_version),
      "a2.vulnerability_surrogate_validation.v1",
    )
    self.assertEqual(str(damage_event.vulnerability_evidence_validation_status), "validated")
    self.assertEqual(str(damage_event.vulnerability_evidence_validation_artifact_sha256), "abc123")
    self.assertEqual(
      str(damage_event.vulnerability_evidence_validated_surrogate_model_ref),
      "fixture://surrogate/model",
    )
    self.assertEqual(
      str(damage_event.vulnerability_evidence_validation_benchmark_ref),
      "fixture://surrogate/benchmark",
    )
    self.assertEqual(
      str(damage_event.vulnerability_evidence_validation_metrics_ref),
      "fixture://surrogate/metrics",
    )
    self.assertEqual(
      str(damage_event.vulnerability_evidence_validation_acceptance_criteria_ref),
      "fixture://surrogate/acceptance",
    )
    self.assertAlmostEqual(float(response_rows[0].failure_sample), 0.21)
    self.assertTrue(bool(response_rows[0].failure_probability_authority))
    self.assertTrue(bool(response_rows[0].failure_probability_component_specific))
    self.assertEqual(
      str(response_rows[0].failure_probability_weapon_family),
      "continuous_rod",
    )
    self.assertEqual(str(response_rows[0].failure_probability_aspect_bucket), "beam")
    self.assertEqual(str(response_rows[0].failure_probability_closure_bucket), "high")
    self.assertEqual(
      str(response_rows[0].failure_probability_miss_distance_bucket),
      "direct_hit",
    )
    self.assertEqual(
      str(response_rows[0].failure_probability_evidence_component_name),
      "left_wing_fuel_cell",
    )
    self.assertEqual(
      str(response_rows[0].failure_probability_evidence_component_system),
      "fuel",
    )
    self.assertEqual(
      str(response_rows[0].failure_probability_evidence_component_redundancy_group_id),
      "wing_fuel_cells",
    )
    self.assertAlmostEqual(float(component_rows[0].mechanism_fragment_energy_j), 540.0)
    self.assertAlmostEqual(
      float(component_rows[0].mechanism_fragment_areal_density_per_m2),
      17.0,
    )
    self.assertAlmostEqual(float(component_rows[0].mechanism_surface_incidence_cos), 0.67)
    self.assertTrue(
      any(
        report.producer_node_id == "effects_damage.v1"
        and int(report.target.entity_id) == target_id
        for report in packet.damage_reports
      )
    )
    self.assertTrue(
      any(
        trace.source_node_id == "fire_control_launch.v1"
        and trace.export_node_id == "observation_export.v1"
        for trace in packet.diagnostics_traces
      )
    )
    self.assertTrue(
      any(
        trace.source_node_id == "effects_damage.v1"
        and trace.export_node_id == "observation_export.v1"
        for trace in packet.diagnostics_traces
      )
    )
    self.assertTrue(all(trace.barrier_id == "export" for trace in packet.diagnostics_traces))

  def test_defaults_are_exposed_for_engagement_dtos(self) -> None:
    track = ef_py.TrackPacket()
    self.assertEqual(track.correlation_policy, "unresolved")
    self.assertEqual(track.classification, "unknown")
    self.assertEqual(track.status, "unknown")
    self.assertFalse(bool(track.usable))

    request = ef_py.LaunchRequest()
    self.assertEqual(request.authority, "unspecified")
    self.assertEqual(request.merge_policy, "reject_on_conflict")

    effects = ef_py.EffectsEvent()
    self.assertEqual(int(effects.component_hit_count), 0)
    self.assertEqual(list(effects.component_mechanism_load_rows), [])
    component_row = ef_py.ComponentMechanismLoadRow()
    self.assertEqual(int(component_row.component_dependency_propagation_count), 0)
    self.assertEqual(str(component_row.component_dependency_target_system), "")
    self.assertEqual(str(component_row.component_dependency_edge_type), "none")
    self.assertAlmostEqual(float(component_row.component_dependency_threshold), 1.0)
    self.assertAlmostEqual(float(component_row.component_dependency_delay_s), 0.0)
    self.assertEqual(str(component_row.component_dependency_direction), "one_way")
    self.assertEqual(str(component_row.component_dependency_provenance), "")
    self.assertAlmostEqual(float(component_row.component_dependency_source_availability), 1.0)
    self.assertAlmostEqual(float(component_row.component_dependency_effective_scale), 0.0)
    self.assertFalse(bool(component_row.component_dependency_propagated))
    self.assertFalse(hasattr(component_row, "component_failure_probability"))
    self.assertFalse(hasattr(component_row, "component_failure_sample"))
    response_row = ef_py.ComponentResponseRow()
    self.assertAlmostEqual(float(response_row.failure_probability), 0.0)
    self.assertEqual(str(response_row.failure_probability_source), "none")
    self.assertFalse(bool(response_row.failure_probability_calibrated))
    self.assertEqual(str(response_row.failure_probability_evidence_dataset_ref), "")
    self.assertEqual(str(response_row.failure_probability_evidence_row_id), "")
    self.assertEqual(str(response_row.failure_probability_evidence_source_ref), "")
    self.assertEqual(str(response_row.failure_probability_evidence_provenance), "")
    self.assertAlmostEqual(float(response_row.failure_sample), 1.0)
    self.assertFalse(bool(response_row.failure_probability_authority))
    self.assertFalse(bool(response_row.failure_probability_component_specific))
    self.assertEqual(str(response_row.failure_probability_weapon_family), "unknown")
    self.assertEqual(str(response_row.failure_probability_aspect_bucket), "unknown")
    self.assertEqual(str(response_row.failure_probability_closure_bucket), "unknown")
    self.assertEqual(str(response_row.failure_probability_miss_distance_bucket), "unknown")
    self.assertEqual(str(effects.component_primary_name), "")
    self.assertEqual(str(effects.component_primary_system), "")
    self.assertAlmostEqual(float(effects.component_primary_redundancy_group), 0.0)
    self.assertFalse(bool(effects.component_primary_critical))
    self.assertEqual(str(effects.component_primary_redundancy_group_id), "")
    self.assertAlmostEqual(float(effects.component_primary_integrity), 1.0)
    self.assertAlmostEqual(float(effects.component_primary_mechanism_fragment_energy_j), 0.0)
    self.assertAlmostEqual(
      float(effects.component_primary_mechanism_fragment_areal_density_per_m2),
      0.0,
    )
    self.assertAlmostEqual(float(effects.component_primary_mechanism_penetration_margin), 0.0)
    self.assertAlmostEqual(
      float(effects.component_primary_mechanism_blast_overpressure_kpa),
      0.0,
    )
    self.assertAlmostEqual(
      float(effects.component_primary_mechanism_blast_impulse_kpa_ms),
      0.0,
    )
    self.assertAlmostEqual(float(effects.component_primary_mechanism_rod_cut_margin), 0.0)
    self.assertAlmostEqual(
      float(effects.component_primary_mechanism_surface_incidence_cos),
      0.0,
    )
    self.assertAlmostEqual(float(effects.component_redundancy_group_availability), 1.0)
    self.assertEqual(int(effects.component_redundancy_group_member_count), 0)
    self.assertEqual(int(effects.component_redundancy_group_failed_count), 0)
    self.assertEqual(str(effects.component_failure_probability_source), "none")
    self.assertFalse(bool(effects.component_failure_probability_calibrated))
    self.assertEqual(str(effects.component_failure_probability_evidence_dataset_ref), "")
    self.assertEqual(str(effects.component_failure_probability_evidence_row_id), "")
    self.assertEqual(str(effects.component_failure_probability_evidence_source_ref), "")
    self.assertEqual(str(effects.component_failure_probability_evidence_provenance), "")
    self.assertAlmostEqual(float(effects.detonation_heading_deg), 0.0)
    self.assertAlmostEqual(float(effects.detonation_pitch_deg), 0.0)
    self.assertAlmostEqual(float(effects.detonation_roll_deg), 0.0)
    self.assertAlmostEqual(float(effects.warhead_orientation_axis_forward), 0.0)
    self.assertAlmostEqual(float(effects.warhead_orientation_axis_right), 0.0)
    self.assertAlmostEqual(float(effects.warhead_orientation_axis_up), 0.0)
    self.assertAlmostEqual(float(effects.warhead_orientation_pattern_scale), 1.0)
    self.assertAlmostEqual(float(effects.mechanism_fragment_energy_j), 0.0)
    self.assertAlmostEqual(float(effects.mechanism_fragment_areal_density_per_m2), 0.0)
    self.assertAlmostEqual(float(effects.mechanism_penetration_margin), 0.0)
    self.assertAlmostEqual(float(effects.mechanism_blast_overpressure_kpa), 0.0)
    self.assertAlmostEqual(float(effects.mechanism_blast_impulse_kpa_ms), 0.0)
    self.assertAlmostEqual(float(effects.mechanism_blast_scaled_distance_m_kg13), 0.0)
    self.assertAlmostEqual(float(effects.mechanism_rod_cut_margin), 0.0)
    self.assertAlmostEqual(float(effects.mechanism_surface_incidence_cos), 0.0)
    self.assertEqual(str(effects.fuze_signature_source), "none")
    self.assertAlmostEqual(float(effects.fuze_target_signature), 0.0)
    self.assertAlmostEqual(float(effects.fuze_signature_scale), 1.0)
    self.assertAlmostEqual(float(effects.fuze_effective_reliability), 1.0)
    self.assertAlmostEqual(float(effects.fuze_contact_surface_distance_m), 0.0)
    self.assertAlmostEqual(float(effects.fuze_contact_penetration_depth_m), 0.0)
    self.assertAlmostEqual(float(effects.fuze_contact_surface_tolerance_m), 0.0)
    self.assertFalse(bool(effects.fuze_contact_inside_hitbox))
    self.assertFalse(bool(effects.vulnerability_profile_present))
    self.assertTrue(bool(effects.vulnerability_profile_synthetic))
    self.assertFalse(bool(effects.vulnerability_calibrated_evidence))
    self.assertFalse(bool(effects.vulnerability_pk_authority))
    self.assertFalse(bool(effects.vulnerability_deterministic_fuze_authority))
    self.assertFalse(bool(effects.vulnerability_evidence_dataset_valid))
    self.assertEqual(str(effects.vulnerability_evidence_dataset_ref), "")
    self.assertEqual(str(effects.vulnerability_calibration_status), "none")
    self.assertEqual(str(effects.vulnerability_provenance), "")
    self.assertEqual(str(effects.vulnerability_evidence_schema_version), "")
    self.assertEqual(str(effects.vulnerability_evidence_source_kind), "")
    self.assertEqual(str(effects.vulnerability_evidence_source_ref), "")
    self.assertEqual(str(effects.vulnerability_evidence_validation_artifact_ref), "")
    self.assertEqual(str(effects.vulnerability_evidence_validation_manifest_schema_version), "")
    self.assertEqual(str(effects.vulnerability_evidence_validation_status), "")
    self.assertEqual(str(effects.vulnerability_evidence_validation_artifact_sha256), "")
    self.assertEqual(str(effects.vulnerability_evidence_validated_surrogate_model_ref), "")
    self.assertEqual(str(effects.vulnerability_evidence_validation_benchmark_ref), "")
    self.assertEqual(str(effects.vulnerability_evidence_validation_metrics_ref), "")
    self.assertEqual(str(effects.vulnerability_evidence_validation_acceptance_criteria_ref), "")
    self.assertEqual(str(effects.vulnerability_aspect_bucket), "unknown")
    self.assertAlmostEqual(float(effects.vulnerability_family_scale), 1.0)
    self.assertAlmostEqual(float(effects.vulnerability_aspect_scale), 1.0)
    self.assertAlmostEqual(float(effects.vulnerability_closure_mps), 0.0)
    self.assertAlmostEqual(float(effects.vulnerability_closure_scale), 1.0)
    self.assertAlmostEqual(float(effects.vulnerability_miss_distance_scale), 1.0)
    self.assertAlmostEqual(float(effects.vulnerability_effect_scale), 1.0)
    self.assertEqual(str(effects.vulnerability_effect_scale_source), "profile_scale")
    self.assertEqual(str(effects.vulnerability_effect_scale_evidence_row_id), "")
    self.assertEqual(str(effects.vulnerability_effect_scale_evidence_source_ref), "")
    self.assertEqual(str(effects.vulnerability_effect_scale_evidence_provenance), "")
    self.assertEqual(str(effects.air_system_hit_flags), "")
    self.assertEqual(str(effects.air_system_spatial_scales), "")
    self.assertEqual(str(effects.vulnerability_scale_trace), "")

  def test_nested_entity_ref_round_trips_through_dto_fields(self) -> None:
    ref = ef_py.EngagementEntityRef()
    ref.world_index = 3
    ref.entity_id = 42

    event = ef_py.LaunchEvent()
    event.event_id = 7
    event.accepted = True
    event.spawned_munition = ref
    event.has_spawned_munition = True

    self.assertEqual(event.event_id, 7)
    self.assertTrue(bool(event.accepted))
    self.assertTrue(bool(event.has_spawned_munition))
    self.assertEqual(event.spawned_munition.world_index, 3)
    self.assertEqual(event.spawned_munition.entity_id, 42)

  def test_runtime_facade_exports_empty_engagement_packet_shell_default_world_index(self) -> None:
    ref = ef_py.EngagementEntityRef()

    request = ef_py.EngagementBatchRequest()
    request.refs = [ref]
    request.include_track_packets = False
    request.include_launch_requests = False
    request.include_launch_events = False
    request.include_munition_lifecycle_packets = False
    request.include_effects_events = False
    request.include_damage_reports = False
    request.include_diagnostics_traces = False

    packet = ef_py.RuntimeFacade(1).export_engagement_event_packet(request)

    self.assertEqual(len(packet.refs), 1)
    self.assertEqual(packet.refs[0].world_index, 0)
    self.assertEqual(packet.refs[0].entity_id, 0)
    self.assertEqual(list(packet.trace_ids), [])
    self.assertEqual(list(packet.track_packets), [])
    self.assertEqual(list(packet.launch_requests), [])
    self.assertEqual(list(packet.launch_events), [])
    self.assertEqual(list(packet.munition_lifecycle_packets), [])
    self.assertEqual(list(packet.effects_events), [])
    self.assertEqual(list(packet.damage_reports), [])
    self.assertEqual(list(packet.diagnostics_traces), [])
    self.assertEqual(int(packet.snapshot_version), 1)
    self.assertEqual(packet.barrier_id, "export")
    self.assertEqual(int(packet.barrier_sequence), 1)
    self.assertEqual(packet.barrier_detail, "maintained_facade_export")
    self.assertEqual(packet.producer_node_id, "observation_export.v1")

  def test_runtime_facade_exposes_dedicated_diagnostics_trace_export(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    self.assertTrue(hasattr(facade, "export_diagnostics_traces"))


if __name__ == "__main__":
  unittest.main()
