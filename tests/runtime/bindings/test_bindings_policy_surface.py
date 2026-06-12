from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402


def public_fields(instance: object) -> tuple[str, ...]:
  return tuple(name for name in dir(instance) if not name.startswith("_"))


class BindingsPolicySurfaceTests(unittest.TestCase):
  def test_action_hold_policy_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.ActionHoldPolicy()),
      (
        "action_family",
        "credit_assignment_attribution_note",
        "credit_assignment_latency_s",
        "diagnostics_reason",
        "expiry_behavior",
        "hold_mode",
        "interpolation_mode",
        "policy_id",
        "refresh_cadence_s",
        "target_control_cadence_s",
        "validity_duration_s",
      ),
    )

  def test_action_intent_packet_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.ActionIntentPacket()),
      (
        "action_family",
        "action_interface",
        "effective_time_s",
        "has_mission_command",
        "has_pilot_action",
        "merge_policy",
        "mission_command",
        "pilot_action",
        "source_id",
        "target",
        "valid_until_s",
      ),
    )

  def test_coordination_intent_packet_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.CoordinationIntentPacket()),
      (
        "merge_policy",
        "produced_leader_intent_refs",
        "produced_tasking_refs",
        "source_id",
        "source_type",
        "target_roster",
        "update_clock",
      ),
    )

  def test_agent_role_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.AgentRole()),
      (
        "action_interface",
        "authority_scope",
        "decision_model_ref",
        "information_state_source",
        "role",
      ),
    )

  def test_decision_belief_public_fields_match_expected_binding_surface(self) -> None:
    self.assertTupleEqual(
      public_fields(ef_py.DecisionBelief()),
      (
        "belief_id",
        "confidence_shape",
        "diagnostics_reason",
        "information_state_layer",
        "maintained_status",
        "memory_or_estimator_ref",
        "source_information_state",
        "source_observation_versions",
        "uses_raw_ecs",
        "uses_truth_state",
      ),
    )

  def test_policy_dto_defaults_are_exposed(self) -> None:
    hold = ef_py.ActionHoldPolicy()
    self.assertEqual(hold.action_family, "direct_control")
    self.assertEqual(hold.hold_mode, "drop")
    self.assertEqual(float(hold.validity_duration_s), 0.0)
    self.assertEqual(float(hold.refresh_cadence_s), 0.0)
    self.assertEqual(float(hold.target_control_cadence_s), 0.0)
    self.assertEqual(hold.expiry_behavior, "drop")
    self.assertEqual(hold.interpolation_mode, "none")
    self.assertEqual(float(hold.credit_assignment_latency_s), 0.0)
    self.assertIn("runtime_cadence_not_implemented", hold.diagnostics_reason)
    self.assertIn(
      "runtime_cadence_not_implemented",
      hold.credit_assignment_attribution_note,
    )

    action = ef_py.ActionIntentPacket()
    self.assertEqual(action.action_family, "direct_control")
    self.assertEqual(action.merge_policy, "last_write_wins")
    self.assertEqual(action.action_interface.kind, "PilotActionAssignment")
    self.assertFalse(bool(action.has_pilot_action))
    self.assertFalse(bool(action.has_mission_command))

    coordination = ef_py.CoordinationIntentPacket()
    self.assertEqual(coordination.source_type, "policy")
    self.assertEqual(coordination.update_clock, "adapter_step")
    self.assertEqual(coordination.merge_policy, "last_write_wins")

    role = ef_py.AgentRole()
    self.assertEqual(role.role.role_type, "unspecified")
    self.assertEqual(role.information_state_source.maintained_status, "compatibility_adapter")
    self.assertEqual(role.action_interface.kind, "PilotActionAssignment")

    belief = ef_py.DecisionBelief()
    self.assertEqual(belief.information_state_layer, "DecisionBelief")
    self.assertEqual(belief.maintained_status, "compatibility_adapter")
    self.assertEqual(
      belief.source_information_state.information_state_layer,
      "AgentObservation",
    )
    self.assertFalse(bool(belief.uses_truth_state))
    self.assertFalse(bool(belief.uses_raw_ecs))

  def test_nested_policy_contract_fields_round_trip(self) -> None:
    hold = ef_py.ActionHoldPolicy()
    hold.policy_id = "policy:blue:hold"
    hold.action_family = "pilot_action"
    hold.hold_mode = "interpolate"
    hold.validity_duration_s = 0.25
    hold.refresh_cadence_s = 0.1
    hold.target_control_cadence_s = 0.05
    hold.expiry_behavior = "expire"
    hold.interpolation_mode = "linear"
    hold.credit_assignment_latency_s = 0.2
    hold.credit_assignment_attribution_note = "policy_output_window_aligned"
    hold.diagnostics_reason = "declarative_contract_for_wp11a"

    action = ef_py.ActionIntentPacket()
    action.source_id = "policy:blue:7"
    action.effective_time_s = 4.0
    action.valid_until_s = 4.2
    action.target.world_index = 2
    action.target.entity_id = 17
    action.action_interface.kind = "PilotActionAssignment"
    action.action_interface.payload_type = "pilot_action"
    action.has_pilot_action = True
    action.pilot_action.stick_pitch = 0.25

    role = ef_py.AgentRole()
    role.role.role_id = "agent:2:17"
    role.role.role_type = "autopilot_controller"
    role.authority_scope.world_index = 2
    role.authority_scope.has_world_index = True
    role.authority_scope.entity_ids = [17]
    role.information_state_source.source_label = "facade_observation_packet"
    role.information_state_source.source_observation_versions = ["global:11"]
    role.decision_model_ref.kind = "policy"
    role.decision_model_ref.id = "blue-policy-v1"

    belief = ef_py.DecisionBelief()
    belief.belief_id = "belief:track:17"
    belief.information_state_layer = "DecisionBelief"
    belief.source_information_state.information_state_layer = "TrackState"
    belief.source_information_state.source_label = "track_state_packet"
    belief.source_information_state.maintained_status = "maintained"
    belief.source_information_state.source_observation_versions = ["track:7"]
    belief.source_observation_versions = ["global:11"]
    belief.memory_or_estimator_ref = "estimator:track-kf"
    belief.confidence_shape.kind = "interval"
    belief.confidence_shape.confidence = 0.88

    coordination = ef_py.CoordinationIntentPacket()
    coordination.source_id = "director:blue"
    coordination.target_roster.world_index = 2
    coordination.target_roster.has_world_index = True
    coordination.target_roster.role_ids = ["flight_lead"]
    produced = ef_py.ProducedIntentRef()
    produced.kind = "leader_intent"
    produced.reference_id = "leader:17"
    produced.target.world_index = 2
    produced.target.entity_id = 17
    coordination.produced_leader_intent_refs = [produced]

    self.assertEqual(hold.policy_id, "policy:blue:hold")
    self.assertEqual(hold.hold_mode, "interpolate")
    self.assertEqual(hold.interpolation_mode, "linear")
    self.assertAlmostEqual(float(hold.target_control_cadence_s), 0.05, places=6)
    self.assertEqual(action.target.world_index, 2)
    self.assertAlmostEqual(float(action.pilot_action.stick_pitch), 0.25, places=6)
    self.assertEqual(role.decision_model_ref.id, "blue-policy-v1")
    self.assertEqual(belief.source_information_state.source_label, "track_state_packet")
    self.assertEqual(belief.source_information_state.maintained_status, "maintained")
    self.assertEqual(list(belief.source_observation_versions), ["global:11"])
    self.assertEqual(coordination.produced_leader_intent_refs[0].target.entity_id, 17)

  def test_decision_belief_provenance_validator_exposes_diagnostics_only_boundary(self) -> None:
    belief = ef_py.DecisionBelief()
    belief.belief_id = "belief:oracle:1"
    belief.information_state_layer = "DecisionBelief"
    belief.source_information_state.information_state_layer = "WorldTruth"
    belief.source_information_state.source_label = "world_truth_diagnostics"
    belief.source_information_state.maintained_status = "diagnostics_only"
    belief.maintained_status = "diagnostics_only"
    belief.diagnostics_reason = "oracle audit"
    belief.uses_truth_state = True

    self.assertTrue(bool(ef_py.information_state_source_has_valid_label(
      belief.source_information_state
    )))
    self.assertTrue(bool(ef_py.decision_belief_requires_diagnostics_only(belief)))
    self.assertTrue(bool(ef_py.decision_belief_has_valid_provenance(belief)))

    belief.maintained_status = "maintained"
    self.assertFalse(bool(ef_py.decision_belief_has_valid_provenance(belief)))


if __name__ == "__main__":
  unittest.main()
