#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_policy(nb::module_ &m) {
    nb::class_<IntentTargetRef>(m, "IntentTargetRef")
        .def(nb::init<>())
        .def_rw("world_index", &IntentTargetRef::world_index)
        .def_rw("entity_id", &IntentTargetRef::entity_id);

    nb::class_<ProducedIntentRef>(m, "ProducedIntentRef")
        .def(nb::init<>())
        .def_rw("kind", &ProducedIntentRef::kind)
        .def_rw("reference_id", &ProducedIntentRef::reference_id)
        .def_rw("target", &ProducedIntentRef::target);

    nb::class_<ActionInterfaceDescriptor>(m, "ActionInterfaceDescriptor")
        .def(nb::init<>())
        .def_rw("kind", &ActionInterfaceDescriptor::kind)
        .def_rw("payload_type", &ActionInterfaceDescriptor::payload_type);

    nb::class_<DecisionModelRef>(m, "DecisionModelRef")
        .def(nb::init<>())
        .def_rw("kind", &DecisionModelRef::kind)
        .def_rw("id", &DecisionModelRef::id);

    nb::class_<ActionHoldPolicy>(m, "ActionHoldPolicy")
        .def(nb::init<>())
        .def_rw("policy_id", &ActionHoldPolicy::policy_id)
        .def_rw("action_family", &ActionHoldPolicy::action_family)
        .def_rw("hold_mode", &ActionHoldPolicy::hold_mode)
        .def_rw("validity_duration_s", &ActionHoldPolicy::validity_duration_s)
        .def_rw("refresh_cadence_s", &ActionHoldPolicy::refresh_cadence_s)
        .def_rw("target_control_cadence_s", &ActionHoldPolicy::target_control_cadence_s)
        .def_rw("expiry_behavior", &ActionHoldPolicy::expiry_behavior)
        .def_rw("interpolation_mode", &ActionHoldPolicy::interpolation_mode)
        .def_rw("credit_assignment_latency_s", &ActionHoldPolicy::credit_assignment_latency_s)
        .def_rw("credit_assignment_attribution_note",
                &ActionHoldPolicy::credit_assignment_attribution_note)
        .def_rw("diagnostics_reason", &ActionHoldPolicy::diagnostics_reason);

    nb::class_<InformationStateSource>(m, "InformationStateSource")
        .def(nb::init<>())
        .def_rw("information_state_layer", &InformationStateSource::information_state_layer)
        .def_rw("source_label", &InformationStateSource::source_label)
        .def_rw("maintained_status", &InformationStateSource::maintained_status)
        .def_rw("observation_packet_ids", &InformationStateSource::observation_packet_ids)
        .def_rw("source_observation_versions", &InformationStateSource::source_observation_versions)
        .def_rw("diagnostics_reason", &InformationStateSource::diagnostics_reason);

    nb::class_<ConfidenceShape>(m, "ConfidenceShape")
        .def(nb::init<>())
        .def_rw("kind", &ConfidenceShape::kind)
        .def_rw("confidence", &ConfidenceShape::confidence)
        .def_rw("lower_bound", &ConfidenceShape::lower_bound)
        .def_rw("upper_bound", &ConfidenceShape::upper_bound);

    nb::class_<RoleDescriptor>(m, "RoleDescriptor")
        .def(nb::init<>())
        .def_rw("role_id", &RoleDescriptor::role_id)
        .def_rw("role_type", &RoleDescriptor::role_type);

    nb::class_<AgentAuthorityScope>(m, "AgentAuthorityScope")
        .def(nb::init<>())
        .def_rw("scope", &AgentAuthorityScope::scope)
        .def_rw("world_index", &AgentAuthorityScope::world_index)
        .def_rw("has_world_index", &AgentAuthorityScope::has_world_index)
        .def_rw("entity_ids", &AgentAuthorityScope::entity_ids)
        .def_rw("roster_id", &AgentAuthorityScope::roster_id)
        .def_rw("command_family", &AgentAuthorityScope::command_family);

    nb::class_<ActionIntentPacket>(m, "ActionIntentPacket")
        .def(nb::init<>())
        .def_rw("source_id", &ActionIntentPacket::source_id)
        .def_rw("effective_time_s", &ActionIntentPacket::effective_time_s)
        .def_rw("valid_until_s", &ActionIntentPacket::valid_until_s)
        .def_rw("target", &ActionIntentPacket::target)
        .def_rw("action_family", &ActionIntentPacket::action_family)
        .def_rw("merge_policy", &ActionIntentPacket::merge_policy)
        .def_rw("action_interface", &ActionIntentPacket::action_interface)
        .def_rw("has_pilot_action", &ActionIntentPacket::has_pilot_action)
        .def_rw("pilot_action", &ActionIntentPacket::pilot_action)
        .def_rw("has_mission_command", &ActionIntentPacket::has_mission_command)
        .def_rw("mission_command", &ActionIntentPacket::mission_command);

    nb::class_<CoordinationTargetRoster>(m, "CoordinationTargetRoster")
        .def(nb::init<>())
        .def_rw("world_index", &CoordinationTargetRoster::world_index)
        .def_rw("has_world_index", &CoordinationTargetRoster::has_world_index)
        .def_rw("roster_id", &CoordinationTargetRoster::roster_id)
        .def_rw("entity_ids", &CoordinationTargetRoster::entity_ids)
        .def_rw("role_ids", &CoordinationTargetRoster::role_ids);

    nb::class_<CoordinationIntentPacket>(m, "CoordinationIntentPacket")
        .def(nb::init<>())
        .def_rw("source_type", &CoordinationIntentPacket::source_type)
        .def_rw("source_id", &CoordinationIntentPacket::source_id)
        .def_rw("target_roster", &CoordinationIntentPacket::target_roster)
        .def_rw("update_clock", &CoordinationIntentPacket::update_clock)
        .def_rw("merge_policy", &CoordinationIntentPacket::merge_policy)
        .def_rw("produced_tasking_refs", &CoordinationIntentPacket::produced_tasking_refs)
        .def_rw("produced_leader_intent_refs",
                &CoordinationIntentPacket::produced_leader_intent_refs);

    nb::class_<AgentRole>(m, "AgentRole")
        .def(nb::init<>())
        .def_rw("role", &AgentRole::role)
        .def_rw("authority_scope", &AgentRole::authority_scope)
        .def_rw("information_state_source", &AgentRole::information_state_source)
        .def_rw("decision_model_ref", &AgentRole::decision_model_ref)
        .def_rw("action_interface", &AgentRole::action_interface);

    nb::class_<AgentRoleAuthorizationResult>(m, "AgentRoleAuthorizationResult")
        .def(nb::init<>())
        .def_rw("authorized", &AgentRoleAuthorizationResult::authorized)
        .def_rw("reason", &AgentRoleAuthorizationResult::reason);

    nb::class_<DecisionBelief>(m, "DecisionBelief")
        .def(nb::init<>())
        .def_rw("belief_id", &DecisionBelief::belief_id)
        .def_rw("information_state_layer", &DecisionBelief::information_state_layer)
        .def_rw("source_information_state", &DecisionBelief::source_information_state)
        .def_rw("source_observation_versions", &DecisionBelief::source_observation_versions)
        .def_rw("memory_or_estimator_ref", &DecisionBelief::memory_or_estimator_ref)
        .def_rw("confidence_shape", &DecisionBelief::confidence_shape)
        .def_rw("maintained_status", &DecisionBelief::maintained_status)
        .def_rw("diagnostics_reason", &DecisionBelief::diagnostics_reason)
        .def_rw("uses_truth_state", &DecisionBelief::uses_truth_state)
        .def_rw("uses_raw_ecs", &DecisionBelief::uses_raw_ecs);
}
