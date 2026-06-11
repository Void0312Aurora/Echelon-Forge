from __future__ import annotations

import textwrap

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

POLICY_HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "policy_contracts.h"


def _compile_and_run(source: str):
  return compile_cpp_snippet(source, binary_prefix="policy_agent_role_authority")


def test_wp12_agent_role_authority_header_exists_at_stable_contract_path() -> None:
  assert POLICY_HEADER.is_file()


def test_wp12_agent_role_authority_slice_is_explicitly_not_full_agency_graph_runtime() -> None:
  header = POLICY_HEADER.read_text(encoding="utf-8")

  assert "authorize_maintained_action_intent" in header
  assert "authorize_maintained_coordination_intent" in header
  assert "This is not full Agency Graph runtime dispatch." in header


def test_valid_maintained_agent_role_authorizes_focused_action_and_coordination_paths() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include "runtime/contracts/policy_contracts.h"

    int main() {
      AgentRole action_role{};
      action_role.role.role_id = "agent:2:17";
      action_role.role.role_type = "autopilot_controller";
      action_role.authority_scope.scope = "platform_control";
      action_role.authority_scope.world_index = 2;
      action_role.authority_scope.has_world_index = true;
      action_role.authority_scope.entity_ids = {17};
      action_role.information_state_source.information_state_layer =
        "AgentObservation";
      action_role.information_state_source.source_label =
        "facade_observation_packet";
      action_role.information_state_source.maintained_status = "maintained";
      action_role.decision_model_ref.kind = "policy";
      action_role.decision_model_ref.id = "blue-policy-v1";
      action_role.action_interface.kind = "PilotActionAssignmentCompat";
      action_role.action_interface.payload_type = "pilot_action";

      ActionIntentPacket action{};
      action.source_id = "policy:blue:17";
      action.action_family = "direct_control";
      action.action_interface.kind = "PilotActionAssignmentCompat";
      action.action_interface.payload_type = "pilot_action";
      action.has_pilot_action = true;

      const auto action_result =
        authorize_maintained_action_intent(action_role, action);
      if (!action_result.authorized) {
        std::cerr << "valid maintained action role should authorize\n";
        return 1;
      }

      AgentRole coordination_role{};
      coordination_role.role.role_id = "director:blue";
      coordination_role.role.role_type = "flight_lead";
      coordination_role.authority_scope.scope = "formation_coordination";
      coordination_role.authority_scope.world_index = 2;
      coordination_role.authority_scope.has_world_index = true;
      coordination_role.authority_scope.roster_id = "blue-section";
      coordination_role.information_state_source.information_state_layer =
        "DecisionBelief";
      coordination_role.information_state_source.source_label =
        "observation_derived_belief";
      coordination_role.information_state_source.maintained_status =
        "maintained";
      coordination_role.decision_model_ref.kind = "scripted_director";
      coordination_role.decision_model_ref.id = "director-v1";
      coordination_role.action_interface.kind =
        "CommandChainAssignmentCompat";
      coordination_role.action_interface.payload_type =
        "coordination_intent";

      CoordinationIntentPacket coordination{};
      coordination.source_id = "director:blue";
      coordination.target_roster.world_index = 2;
      coordination.target_roster.has_world_index = true;
      coordination.target_roster.roster_id = "blue-section";
      ProducedIntentRef produced{};
      produced.kind = "leader_intent";
      produced.reference_id = "leader:17";
      coordination.produced_leader_intent_refs = {produced};

      const auto coordination_result =
        authorize_maintained_coordination_intent(
          coordination_role,
          coordination);
      if (!coordination_result.authorized) {
        std::cerr << "valid maintained coordination role should authorize\n";
        return 1;
      }

      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_missing_unknown_or_incompatible_agent_role_combinations_fail_closed() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include <string>
    #include "runtime/contracts/policy_contracts.h"

    int main() {
      AgentRole missing_scope{};
      missing_scope.role.role_id = "agent:2:17";
      missing_scope.role.role_type = "autopilot_controller";
      missing_scope.information_state_source.information_state_layer =
        "AgentObservation";
      missing_scope.information_state_source.source_label =
        "facade_observation_packet";
      missing_scope.information_state_source.maintained_status =
        "maintained";
      missing_scope.decision_model_ref.kind = "policy";
      missing_scope.decision_model_ref.id = "blue-policy-v1";
      missing_scope.action_interface.kind = "PilotActionAssignmentCompat";
      missing_scope.action_interface.payload_type = "pilot_action";

      ActionIntentPacket pilot_action{};
      pilot_action.source_id = "policy:blue:17";
      pilot_action.action_family = "direct_control";
      pilot_action.action_interface.kind = "PilotActionAssignmentCompat";
      pilot_action.action_interface.payload_type = "pilot_action";
      pilot_action.has_pilot_action = true;

      if (authorize_maintained_action_intent(missing_scope, pilot_action)
          .authorized) {
        std::cerr << "missing authority scope unexpectedly passed\n";
        return 1;
      }

      AgentRole unknown_scope = missing_scope;
      unknown_scope.authority_scope.scope = "unknown_scope";
      unknown_scope.authority_scope.world_index = 2;
      unknown_scope.authority_scope.has_world_index = true;
      unknown_scope.authority_scope.entity_ids = {17};
      if (authorize_maintained_action_intent(unknown_scope, pilot_action)
          .authorized) {
        std::cerr << "unknown authority scope unexpectedly passed\n";
        return 1;
      }

      AgentRole truth_source = missing_scope;
      truth_source.authority_scope.scope = "platform_control";
      truth_source.authority_scope.world_index = 2;
      truth_source.authority_scope.has_world_index = true;
      truth_source.authority_scope.entity_ids = {17};
      truth_source.information_state_source.information_state_layer =
        "WorldTruth";
      truth_source.information_state_source.source_label =
        "world_truth_diagnostics";
      truth_source.information_state_source.maintained_status =
        "diagnostics_only";
      const auto truth_result =
        authorize_maintained_action_intent(truth_source, pilot_action);
      if (truth_result.authorized ||
        truth_result.reason.find("not full Agency Graph runtime dispatch") ==
          std::string::npos) {
        std::cerr << "diagnostics/truth source did not fail closed\n";
        return 1;
      }

      AgentRole mismatched_interface = truth_source;
      mismatched_interface.information_state_source.information_state_layer =
        "AgentObservation";
      mismatched_interface.information_state_source.source_label =
        "facade_observation_packet";
      mismatched_interface.information_state_source.maintained_status =
        "maintained";
      mismatched_interface.action_interface.kind =
        "CommandChainAssignmentCompat";
      mismatched_interface.action_interface.payload_type =
        "mission_command";
      if (authorize_maintained_action_intent(
          mismatched_interface,
          pilot_action).authorized) {
        std::cerr << "action interface mismatch unexpectedly passed\n";
        return 1;
      }

      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout
