from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


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
                "optional_fields",
                "reject_major_mismatch",
                "required_fields",
                "schema_version",
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

    def test_observation_batch_packet_public_fields_include_metadata(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.ObservationBatchPacket()),
            (
                "agent_observations",
                "barrier_id",
                "instrument_states",
                "leader_intents",
                "mission_commands",
                "pilot_reports",
                "provenance",
                "refs",
                "snapshot_version",
                "source_time_s",
                "task_orders",
            ),
        )

    def test_engagement_event_packet_public_fields_include_provenance(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.EngagementEventPacket()),
            (
                "barrier_detail",
                "barrier_id",
                "barrier_sequence",
                "damage_reports",
                "diagnostics_provenance",
                "diagnostics_traces",
                "effects_events",
                "launch_events",
                "launch_requests",
                "munition_lifecycle_packets",
                "packet_provenance",
                "producer_node_id",
                "refs",
                "snapshot_version",
                "source_time_s",
                "trace_ids",
                "track_packets",
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
        role.action_interface.kind = "PilotActionAssignmentCompat"
        role.action_interface.payload_type = "pilot_action"

        action = ef_py.ActionIntentPacket()
        action.source_id = "policy:blue:17"
        action.action_family = "direct_control"
        action.action_interface.kind = "PilotActionAssignmentCompat"
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
        role.action_interface.kind = "PilotActionAssignmentCompat"
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
