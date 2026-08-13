from __future__ import annotations

import unittest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402


def public_fields(instance: object) -> tuple[str, ...]:
  return tuple(name for name in dir(instance) if not name.startswith("_"))


class BindingsRuntimeDtoSurfaceTests(unittest.TestCase):
  def test_agent_role_authority_result_binding_exposes_fail_closed_contract(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.AgentRoleAuthorizationResult()),
      (
        "authorized",
        "reason",
      ),
    )

  def test_action_hold_policy_binding_stays_contract_visible_prerequisite_only(self) -> None:
    policy = ef_py.ActionHoldPolicy()

    self.assertEqual(policy.hold_mode, "drop")
    self.assertEqual(policy.interpolation_mode, "none")
    self.assertIn("runtime_cadence_not_implemented", policy.diagnostics_reason)
    self.assertIn(
      "runtime_cadence_not_implemented",
      policy.credit_assignment_attribution_note,
    )

  def test_fidelity_profile_request_binding_admits_only_cpu_exact_baseline(self) -> None:
    request = ef_py.make_exact_evaluation_cpu_reference_fidelity_request()

    self.assertEqual(request.request_label, "exact_evaluation")
    self.assertEqual(request.backend_profile_id, "cpu_exact.reference")
    self.assertEqual(request.parity_budget_ref, "parity_budget.cpu_exact.reference.v1")
    self.assertTrue(list(request.model_family_scope))
    self.assertTrue(list(request.facade_evidence_refs))

    result = ef_py.admit_fidelity_profile_request(request)

    self.assertTrue(bool(result.admitted))
    self.assertTrue(bool(result.baseline_exact_evaluation))
    self.assertEqual(result.rejection_reason, "")
    self.assertEqual(result.backend_profile_id, "cpu_exact.reference")
    self.assertIn("RuntimeFacade.capabilities", list(result.evidence_refs))

    request.request_label = "fast_training"
    rejected = ef_py.admit_fidelity_profile_request(request)

    self.assertFalse(bool(rejected.admitted))
    self.assertEqual(rejected.rejection_reason, "fidelity_profile_label_not_maintained")

    request = ef_py.make_exact_evaluation_cpu_reference_fidelity_request()
    request.requests_adaptive_scheduling = True
    rejected = ef_py.admit_fidelity_profile_request(request)

    self.assertFalse(bool(rejected.admitted))
    self.assertEqual(
      rejected.rejection_reason,
      "adaptive_fidelity_scheduling_not_implemented",
    )

  def test_reward_term_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.RewardTerm()),
      (
        "name",
        "term_owner",
        "value",
      ),
    )

  def test_reward_report_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.RewardReport()),
      (
        "fact_snapshot_version",
        "fact_terms",
        "shaping_terms",
        "term_owner",
      ),
    )

  def test_termination_spec_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.TerminationSpec()),
      (
        "reason",
        "reason_source",
        "snapshot_version",
      ),
    )

  def test_observation_view_spec_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.ObservationViewSpec()),
      (
        "allow_minor_version_drift",
        "allow_missing_optional_fields",
        "allow_unknown_optional_fields",
        # T8/I60 additive structural-fact declaration fields (append-only).
        "information_layer_consumed",
        "information_layer_produced",
        "optional_fields",
        "reject_major_mismatch",
        "required_fields",
        "schema_version",
        "semantic_stage",
        "view_id",
      ),
    )

  def test_observation_view_compatibility_report_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.ObservationViewCompatibilityReport()),
      (
        "compatible",
        "major_compatible",
        "missing_optional_fields",
        "missing_required_fields",
        "optional_field_drift_allowed",
        "required_fields_satisfied",
        "unknown_optional_fields",
      ),
    )

  def test_tasking_request_task_order_export_uses_maintained_contract_gate_only(self) -> None:
    request = ef_py.ObservationBatchRequest()
    tasking_request = ef_py.TaskingBatchRequest()
    step_request = ef_py.ExecutionBatchStepRequest()

    self.assertFalse(hasattr(request, "include_task_orders"))
    self.assertFalse(hasattr(request, "include_task_order_contracts"))
    self.assertFalse(hasattr(request, "include_mission_commands"))
    self.assertFalse(hasattr(request, "include_leader_intents"))
    self.assertFalse(hasattr(request, "include_pilot_reports"))
    self.assertFalse(hasattr(tasking_request, "include_task_orders"))
    self.assertFalse(bool(tasking_request.include_mission_command_contracts))
    self.assertFalse(bool(tasking_request.include_task_order_contracts))
    self.assertFalse(bool(tasking_request.include_leader_intent_contracts))
    self.assertFalse(bool(tasking_request.include_pilot_report_contracts))
    self.assertFalse(hasattr(step_request, "include_task_orders"))
    self.assertFalse(hasattr(step_request, "include_task_order_contracts"))
    self.assertFalse(hasattr(step_request, "include_mission_commands"))
    self.assertFalse(hasattr(step_request, "include_leader_intents"))
    self.assertFalse(hasattr(step_request, "include_pilot_reports"))

    tasking_request.include_mission_command_contracts = True
    tasking_request.include_task_order_contracts = True
    tasking_request.include_leader_intent_contracts = True
    tasking_request.include_pilot_report_contracts = True
    self.assertTrue(bool(tasking_request.include_mission_command_contracts))
    self.assertTrue(bool(tasking_request.include_task_order_contracts))
    self.assertTrue(bool(tasking_request.include_leader_intent_contracts))
    self.assertTrue(bool(tasking_request.include_pilot_report_contracts))

  def test_task_order_whole_shell_batch_bindings_are_removed(self) -> None:
    runtime = ef_py.WorldBatchRuntime(1)
    facade = ef_py.RuntimeFacade(1)

    self.assertTrue(hasattr(runtime, "set_mission_commands_maintained_batch"))
    self.assertTrue(hasattr(runtime, "get_mission_commands_maintained_batch"))
    self.assertTrue(hasattr(runtime, "set_task_orders_maintained_batch"))
    self.assertTrue(hasattr(runtime, "get_task_orders_maintained_batch"))
    self.assertTrue(hasattr(runtime, "set_leader_intents_maintained_batch"))
    self.assertTrue(hasattr(runtime, "get_leader_intents_maintained_batch"))
    self.assertTrue(hasattr(runtime, "set_pilot_reports_maintained_batch"))
    self.assertTrue(hasattr(runtime, "get_pilot_reports_maintained_batch"))
    self.assertTrue(hasattr(facade, "set_mission_commands_maintained_batch"))
    self.assertTrue(hasattr(facade, "get_mission_commands_maintained_batch"))
    self.assertTrue(hasattr(facade, "set_task_orders_maintained_batch"))
    self.assertTrue(hasattr(facade, "get_task_orders_maintained_batch"))
    self.assertTrue(hasattr(facade, "set_leader_intents_maintained_batch"))
    self.assertTrue(hasattr(facade, "get_leader_intents_maintained_batch"))
    self.assertTrue(hasattr(facade, "set_pilot_reports_maintained_batch"))
    self.assertTrue(hasattr(facade, "get_pilot_reports_maintained_batch"))

    self.assertFalse(hasattr(runtime, "set_task_orders_batch"))
    self.assertFalse(hasattr(runtime, "get_task_orders_batch"))
    self.assertFalse(hasattr(facade, "set_task_orders_batch"))
    self.assertFalse(hasattr(facade, "get_task_orders_batch"))
    self.assertFalse(hasattr(runtime, "set_task_orders_compatibility_batch"))
    self.assertFalse(hasattr(runtime, "get_task_orders_compatibility_batch"))
    self.assertFalse(hasattr(facade, "set_task_orders_compatibility_batch"))
    self.assertFalse(hasattr(facade, "get_task_orders_compatibility_batch"))
    self.assertFalse(hasattr(ef_py, "WorldTaskOrderAssignment"))
    self.assertFalse(hasattr(ef_py, "WorldTaskOrderCompatibilityAssignment"))
    self.assertFalse(hasattr(facade, "set_mission_commands_batch"))
    self.assertFalse(hasattr(facade, "get_mission_commands_batch"))
    self.assertFalse(hasattr(facade, "set_leader_intents_batch"))
    self.assertFalse(hasattr(facade, "get_leader_intents_batch"))
    self.assertFalse(hasattr(facade, "set_pilot_reports_batch"))
    self.assertFalse(hasattr(facade, "get_pilot_reports_batch"))

  def test_observation_batch_packet_public_fields_include_metadata(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.ObservationBatchPacket()),
      (
        "agent_observations",
        "barrier_id",
        "instrument_states",
        "provenance",
        "refs",
        "snapshot_version",
        "source_time_s",
      ),
    )

  def test_tasking_batch_packet_exposes_command_and_tasking_payloads(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.TaskingBatchPacket()),
      (
        "barrier_id",
        "leader_intent_contracts",
        "mission_command_contracts",
        "pilot_report_contracts",
        "provenance",
        "refs",
        "snapshot_version",
        "source_time_s",
        "task_order_contracts",
      ),
    )

  def test_tasking_batch_packet_exposes_maintained_command_chain_contracts(self) -> None:
    packet = ef_py.TaskingBatchPacket()
    command_contract = ef_py.MissionCommandMaintainedBatchContract()
    leader_contract = ef_py.LeaderIntentMaintainedBatchContract()
    report_contract = ef_py.PilotReportMaintainedBatchContract()

    command_contract.shared_core.command_code = 31
    command_contract.shared_core.threat_state = 3
    command_contract.shared_core.assigned_target_track_id = 91001
    command_contract.shared_core.assigned_target_source_id = 92002
    command_contract.shared_core.assigned_target_snapshot_time_s = 37.5
    command_contract.air_recovery.recovery_base_id = 71
    command_contract.air_takeoff.takeoff_interval_s = 12.5
    command_contract.air_formation.formation_id = 17
    command_contract.naval_stationing.reference_entity_id = 9101
    command_contract.naval_embarked_helo.launch_helo = True
    leader_contract.shared_core.task_group_id = 8001
    leader_contract.air_formation.formation_id = 34
    leader_contract.naval_command_authority.warfare_role_code = 35
    report_contract.shared_core.sender_id = 101
    report_contract.air.element_id = 7001
    report_contract.naval_command_authority.officer_in_tactical_command = 42

    packet.mission_command_contracts = [command_contract]
    packet.leader_intent_contracts = [leader_contract]
    packet.pilot_report_contracts = [report_contract]

    self.assertIsInstance(
      packet.mission_command_contracts[0],
      ef_py.MissionCommandMaintainedBatchContract,
    )
    self.assertEqual(int(packet.mission_command_contracts[0].shared_core.command_code), 31)
    self.assertEqual(int(packet.mission_command_contracts[0].shared_core.threat_state), 3)
    self.assertEqual(
      int(packet.mission_command_contracts[0].shared_core.assigned_target_track_id),
      91001,
    )
    self.assertEqual(
      int(packet.mission_command_contracts[0].shared_core.assigned_target_source_id),
      92002,
    )
    self.assertAlmostEqual(
      float(packet.mission_command_contracts[0].shared_core.assigned_target_snapshot_time_s),
      37.5,
      places=6,
    )
    self.assertEqual(int(packet.mission_command_contracts[0].air_recovery.recovery_base_id), 71)
    self.assertAlmostEqual(
      float(packet.mission_command_contracts[0].air_takeoff.takeoff_interval_s),
      12.5,
    )
    self.assertEqual(int(packet.mission_command_contracts[0].air_formation.formation_id), 17)
    self.assertEqual(
      int(packet.mission_command_contracts[0].naval_stationing.reference_entity_id),
      9101,
    )
    self.assertTrue(bool(packet.mission_command_contracts[0].naval_embarked_helo.launch_helo))
    self.assertIsInstance(
      packet.leader_intent_contracts[0],
      ef_py.LeaderIntentMaintainedBatchContract,
    )
    self.assertEqual(int(packet.leader_intent_contracts[0].shared_core.task_group_id), 8001)
    self.assertEqual(int(packet.leader_intent_contracts[0].air_formation.formation_id), 34)
    self.assertEqual(
      int(packet.leader_intent_contracts[0].naval_command_authority.warfare_role_code),
      35,
    )
    self.assertIsInstance(
      packet.pilot_report_contracts[0],
      ef_py.PilotReportMaintainedBatchContract,
    )
    self.assertEqual(int(packet.pilot_report_contracts[0].shared_core.sender_id), 101)
    self.assertEqual(int(packet.pilot_report_contracts[0].air.element_id), 7001)
    self.assertEqual(
      int(packet.pilot_report_contracts[0].naval_command_authority.officer_in_tactical_command),
      42,
    )

  def test_tasking_batch_packet_exposes_maintained_task_order_contracts(self) -> None:
    packet = ef_py.TaskingBatchPacket()
    contract = ef_py.TaskOrderMaintainedBatchContract()
    contract.shared_core.task_id = 91
    contract.air_tasking_identity.task_type = ef_py.TaskType.CAP
    contract.air_stationing.target_speed_mps = 205.0
    contract.air_recovery.recovery_base_id = 7
    contract.air_formation.wingman_slot_id = ef_py.WingmanSlot.Left
    contract.naval_stationing.naval_station_type = ef_py.NavalStationType.Screen

    packet.task_order_contracts = [contract]

    self.assertEqual(len(packet.task_order_contracts), 1)
    self.assertIsInstance(packet.task_order_contracts[0], ef_py.TaskOrderMaintainedBatchContract)
    self.assertEqual(int(packet.task_order_contracts[0].shared_core.task_id), 91)
    self.assertEqual(
      packet.task_order_contracts[0].air_tasking_identity.task_type,
      ef_py.TaskType.CAP,
    )
    self.assertAlmostEqual(
      float(packet.task_order_contracts[0].air_stationing.target_speed_mps),
      205.0,
    )
    self.assertEqual(int(packet.task_order_contracts[0].air_recovery.recovery_base_id), 7)
    self.assertEqual(
      packet.task_order_contracts[0].air_formation.wingman_slot_id,
      ef_py.WingmanSlot.Left,
    )
    self.assertEqual(
      packet.task_order_contracts[0].naval_stationing.naval_station_type,
      ef_py.NavalStationType.Screen,
    )

  def test_observation_batch_packet_task_orders_whole_shell_export_is_removed(self) -> None:
    observation_packet = ef_py.ObservationBatchPacket()
    tasking_packet = ef_py.TaskingBatchPacket()
    maintained_contract = ef_py.TaskOrderMaintainedBatchContract()
    maintained_contract.shared_core.task_id = 91

    tasking_packet.task_order_contracts = [maintained_contract]

    self.assertIsInstance(tasking_packet.task_order_contracts[0], ef_py.TaskOrderMaintainedBatchContract)
    self.assertFalse(hasattr(observation_packet, "task_order_contracts"))
    self.assertFalse(hasattr(observation_packet, "task_orders"))
    self.assertFalse(hasattr(tasking_packet, "task_orders"))
    self.assertFalse(hasattr(tasking_packet, "mission_commands"))
    self.assertFalse(hasattr(tasking_packet, "leader_intents"))
    self.assertFalse(hasattr(tasking_packet, "pilot_reports"))

  def test_device_resident_output_descriptor_public_fields_match_additive_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.DeviceResidentOutputDescriptor()),
      (
        "consumer_constraints",
        "diagnostics_label",
        "dtype",
        "element_count",
        "host_visible_availability",
        "output_shape",
        "source_snapshot",
        "sync_or_export_barrier",
      ),
    )

  def test_device_resident_output_descriptor_defaults_stay_fail_closed(self) -> None:
    descriptor = ef_py.DeviceResidentOutputDescriptor()

    self.assertEqual(list(descriptor.output_shape), [])
    self.assertEqual(descriptor.dtype, "")
    self.assertEqual(descriptor.element_count, 0)
    self.assertEqual(descriptor.source_snapshot, 0)
    self.assertEqual(descriptor.sync_or_export_barrier, "")
    self.assertEqual(descriptor.host_visible_availability, "unavailable")
    self.assertEqual(descriptor.diagnostics_label, "diagnostics_only")
    self.assertEqual(list(descriptor.consumer_constraints), [])

  def test_device_resident_output_descriptor_fields_are_assignable(self) -> None:
    descriptor = ef_py.DeviceResidentOutputDescriptor()

    descriptor.output_shape = [4, 8, 16]
    descriptor.dtype = "float32"
    descriptor.element_count = 512
    descriptor.source_snapshot = 42
    descriptor.sync_or_export_barrier = "export"
    descriptor.host_visible_availability = "explicit_readback_required"
    descriptor.diagnostics_label = "export_only_candidate"
    descriptor.consumer_constraints = [
      "device_resident_consumer",
      "host_readback",
    ]

    self.assertEqual(list(descriptor.output_shape), [4, 8, 16])
    self.assertEqual(descriptor.dtype, "float32")
    self.assertEqual(descriptor.element_count, 512)
    self.assertEqual(descriptor.source_snapshot, 42)
    self.assertEqual(descriptor.sync_or_export_barrier, "export")
    self.assertEqual(
      descriptor.host_visible_availability,
      "explicit_readback_required",
    )
    self.assertEqual(descriptor.diagnostics_label, "export_only_candidate")
    self.assertEqual(
      list(descriptor.consumer_constraints),
      ["device_resident_consumer", "host_readback"],
    )

  def test_typed_platform_spawn_result_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.TypedPlatformSpawnResult()),
      (
        "admitted",
        "capability_bundle_id",
        "entity_id",
        "errors",
        "evidence_refs",
        "fail_closed",
        "materialized",
        "plan_id",
        "rejection_reason",
        "request_id",
        "request_index",
        "setup_surface",
        "source_type_name",
        "world_index",
      ),
    )

  def test_batch_world_setup_result_public_fields_preserve_legacy_and_typed_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.BatchWorldSetupResult()),
      (
        "entity_ids",
        "typed_platform_spawn_results",
      ),
    )

  def test_engagement_event_packet_public_fields_include_provenance(self) -> None:
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

  def test_execution_batch_step_result_public_fields_include_typed_reward_and_termination_reports(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.ExecutionBatchStepResult()),
      (
        "controller_state_changed_flags",
        "execution_episode_states",
        "observation_packet",
        "reward_breakdown_jsons",
        "reward_reports",
        "rewards",
        "status_vectors",
        "step_info_valid_flags",
        "step_infos",
        "step_results",
        "tasking_packet",
        "terminated",
        "termination_reasons",
        "termination_specs",
        "truncated",
      ),
    )

  def test_runtime_window_request_and_result_public_fields_cover_wp16_spine_evidence(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.RuntimeWindowActionRequest()),
      (
        "action_intent",
        "cadence_control",
        "input_snapshot_version",
        "source_layer",
      ),
    )
    self.assertTupleEqual(
      public_fields(ef_py.RuntimeWindowRequest()),
      (
        "action_requests",
        "cadence_config",
        "engagement_request",
        "export_diagnostics",
        "export_engagement",
        "export_observation",
        "observation_request",
        "source_time_s",
        "window_id",
        "world_id",
      ),
    )
    self.assertTupleEqual(
      public_fields(ef_py.RuntimeWindowResult()),
      (
        "barrier_trace",
        "cadence_config",
        "cadence_trace",
        "context",
        "diagnostics_traces",
        "engagement_packet",
        "executed_nodes",
        "injected_inputs",
        "observation_packet",
        "visibility_trace",
      ),
    )
    self.assertFalse(hasattr(ef_py.RuntimeWindowResult(), "identity_token_"))

  def test_packet_provenance_nested_fields_round_trip(self) -> None:
    observation_packet = ef_py.ObservationBatchPacket()
    observation_packet.snapshot_version = 12
    observation_packet.provenance.information_state_layer = "AgentObservation"
    observation_packet.provenance.source_label = "facade_observation_packet"
    observation_packet.provenance.maintained_status = "maintained"
    observation_packet.provenance.observation_packet_ids = ["obs:12"]
    observation_packet.provenance.source_observation_versions = ["global:12"]

    engagement_packet = ef_py.EngagementEventPacket()
    engagement_packet.snapshot_version = 7
    engagement_packet.packet_provenance.information_state_layer = "TrackState"
    engagement_packet.packet_provenance.source_label = "track_state_packet"
    engagement_packet.packet_provenance.maintained_status = "maintained"
    engagement_packet.diagnostics_provenance.information_state_layer = "DecisionBelief"
    engagement_packet.diagnostics_provenance.source_label = "world_truth_diagnostics"
    engagement_packet.diagnostics_provenance.maintained_status = "diagnostics_only"

    self.assertEqual(observation_packet.provenance.source_label, "facade_observation_packet")
    self.assertEqual(
      list(observation_packet.provenance.source_observation_versions),
      ["global:12"],
    )
    self.assertEqual(engagement_packet.packet_provenance.information_state_layer, "TrackState")
    self.assertEqual(
      engagement_packet.diagnostics_provenance.maintained_status,
      "diagnostics_only",
    )

  def test_observation_view_compatibility_helper_allows_minor_optional_drift(self) -> None:
    checkpoint = ef_py.ObservationViewSpec()
    checkpoint.schema_version = "1.1"
    checkpoint.required_fields = ["pose", "health"]
    checkpoint.optional_fields = ["legacy_heading_raw"]

    provider = ef_py.ObservationViewSpec()
    provider.schema_version = "1.2"
    provider.required_fields = ["pose", "health"]
    provider.optional_fields = ["radar_altitude"]

    report = ef_py.evaluate_observation_view_checkpoint_compatibility(checkpoint, provider)

    self.assertTrue(bool(report.compatible))
    self.assertTrue(bool(report.major_compatible))
    self.assertTrue(bool(report.required_fields_satisfied))
    self.assertTrue(bool(report.optional_field_drift_allowed))
    self.assertEqual(list(report.unknown_optional_fields), ["radar_altitude"])
    self.assertEqual(list(report.missing_optional_fields), ["legacy_heading_raw"])

  def test_observation_view_compatibility_helper_rejects_major_mismatch(self) -> None:
    checkpoint = ef_py.ObservationViewSpec()
    checkpoint.schema_version = "1.4"
    checkpoint.required_fields = ["pose"]

    provider = ef_py.ObservationViewSpec()
    provider.schema_version = "2.0"
    provider.required_fields = ["pose"]

    report = ef_py.evaluate_observation_view_checkpoint_compatibility(checkpoint, provider)

    self.assertFalse(bool(report.compatible))
    self.assertFalse(bool(report.major_compatible))
    self.assertTrue(bool(report.required_fields_satisfied))

  def test_agent_role_authority_helpers_preserve_role_fields_and_authorize_focused_action_slice(self) -> None:
    role = ef_py.AgentRole()
    role.role.role_id = "agent:2:17"
    role.role.role_type = "autopilot_controller"
    role.authority_scope.scope = "platform_control"
    role.authority_scope.world_index = 2
    role.authority_scope.has_world_index = True
    role.authority_scope.entity_ids = [17]
    role.information_state_source.information_state_layer = "AgentObservation"
    role.information_state_source.source_label = "facade_observation_packet"
    role.information_state_source.maintained_status = "maintained"
    role.decision_model_ref.kind = "policy"
    role.decision_model_ref.id = "blue-policy-v1"
    role.action_interface.kind = "PilotActionAssignment"
    role.action_interface.payload_type = "pilot_action"

    action = ef_py.ActionIntentPacket()
    action.source_id = "policy:blue:17"
    action.action_family = "direct_control"
    action.action_interface.kind = "PilotActionAssignment"
    action.action_interface.payload_type = "pilot_action"
    action.has_pilot_action = True
    action.has_mission_command = False

    self.assertTrue(bool(ef_py.agent_role_has_maintained_authority_shape(role)))
    self.assertTrue(bool(ef_py.agent_role_action_interface_matches_authority_scope(role)))

    result = ef_py.authorize_maintained_action_intent(role, action)

    self.assertTrue(bool(result.authorized))
    self.assertEqual(result.reason, "")
    self.assertEqual(role.role.role_id, "agent:2:17")
    self.assertEqual(role.authority_scope.scope, "platform_control")
    self.assertEqual(role.information_state_source.source_label, "facade_observation_packet")

  def test_agent_role_authority_helpers_fail_closed_for_diagnostics_source_and_interface_mismatch(self) -> None:
    role = ef_py.AgentRole()
    role.role.role_id = "director:blue"
    role.role.role_type = "flight_lead"
    role.authority_scope.scope = "formation_coordination"
    role.authority_scope.world_index = 0
    role.authority_scope.has_world_index = True
    role.authority_scope.roster_id = "blue-section"
    role.information_state_source.information_state_layer = "WorldTruth"
    role.information_state_source.source_label = "world_truth_diagnostics"
    role.information_state_source.maintained_status = "diagnostics_only"
    role.decision_model_ref.kind = "scripted_director"
    role.decision_model_ref.id = "director-v1"
    role.action_interface.kind = "PilotActionAssignment"
    role.action_interface.payload_type = "pilot_action"

    coordination = ef_py.CoordinationIntentPacket()
    coordination.source_id = "director:blue"
    produced = ef_py.ProducedIntentRef()
    produced.kind = "leader_intent"
    produced.reference_id = "leader:17"
    coordination.produced_leader_intent_refs = [produced]

    self.assertFalse(bool(ef_py.agent_role_has_maintained_authority_shape(role)))
    result = ef_py.authorize_maintained_coordination_intent(role, coordination)
    self.assertFalse(bool(result.authorized))
    self.assertIn("not full Agency Graph runtime dispatch", result.reason)


if __name__ == "__main__":
  unittest.main()
