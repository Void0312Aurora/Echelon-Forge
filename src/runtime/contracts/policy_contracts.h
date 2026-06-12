#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"

struct IntentTargetRef {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
};

struct ProducedIntentRef {
    std::string kind = "unspecified";
    std::string reference_id;
    IntentTargetRef target{};
};

struct ActionInterfaceDescriptor {
    std::string kind = "PilotActionAssignment";
    std::string payload_type = "pilot_action";
};

struct DecisionModelRef {
    std::string kind = "external_policy";
    std::string id = "caller_supplied";
};

inline constexpr std::string_view kActionInterfacePilotActionAssignment =
    "PilotActionAssignment";
inline constexpr std::string_view kActionInterfaceCommandChainAssignment =
    "CommandChainAssignment";
inline constexpr std::string_view kActionInterfacePayloadPilotAction = "pilot_action";
inline constexpr std::string_view kActionInterfacePayloadMissionCommand = "mission_command";
inline constexpr std::string_view kActionInterfacePayloadCoordinationIntent =
    "coordination_intent";

inline constexpr std::string_view kAgentAuthorityScopePlatformControl =
    "platform_control";
inline constexpr std::string_view kAgentAuthorityScopeMissionCommand =
    "mission_command";
inline constexpr std::string_view kAgentAuthorityScopeFormationCoordination =
    "formation_coordination";

inline constexpr std::string_view kActionHoldModeHoldLast = "hold_last";
inline constexpr std::string_view kActionHoldModeInterpolate = "interpolate";
inline constexpr std::string_view kActionHoldModeExpire = "expire";
inline constexpr std::string_view kActionHoldModeDrop = "drop";

inline constexpr std::string_view kActionHoldExpiryBehaviorExpire = "expire";
inline constexpr std::string_view kActionHoldExpiryBehaviorDrop = "drop";

inline constexpr std::string_view kActionHoldInterpolationModeNone = "none";
inline constexpr std::string_view kActionHoldInterpolationModeLinear = "linear";

inline constexpr std::string_view kPolicyInformationStateWorldTruth = "WorldTruth";
inline constexpr std::string_view kPolicyInformationStateSensedState = "SensedState";
inline constexpr std::string_view kPolicyInformationStateTrackState = "TrackState";
inline constexpr std::string_view kPolicyInformationStateSharedTacticalPicture =
    "SharedTacticalPicture";
inline constexpr std::string_view kPolicyInformationStateAgentObservation = "AgentObservation";
inline constexpr std::string_view kPolicyInformationStateDecisionBelief = "DecisionBelief";

inline constexpr std::string_view kPolicyMaintainedStatusMaintained = "maintained";
inline constexpr std::string_view kPolicyMaintainedStatusAdapterProjection =
    "adapter_projection";
inline constexpr std::string_view kPolicyMaintainedStatusDiagnosticsOnly =
    "diagnostics_only";

inline constexpr std::string_view kPolicySourceLabelFacadeObservationPacket =
    "facade_observation_packet";
inline constexpr std::string_view kPolicySourceLabelAgentObservationAdapterProjection =
    "agent_observation_adapter_projection";
inline constexpr std::string_view kPolicySourceLabelSensedStatePacket =
    "sensed_state_packet";
inline constexpr std::string_view kPolicySourceLabelTrackStatePacket =
    "track_state_packet";
inline constexpr std::string_view kPolicySourceLabelSharedTacticalPictureAdapterProjection =
    "shared_tactical_picture_adapter_projection";
inline constexpr std::string_view kPolicySourceLabelWorldTruthDiagnostics =
    "world_truth_diagnostics";
inline constexpr std::string_view kPolicySourceLabelObservationDerivedBelief =
    "observation_derived_belief";

struct ActionHoldPolicy {
    std::string policy_id;
    std::string action_family = "direct_control";
    std::string hold_mode = std::string(kActionHoldModeDrop);
    double validity_duration_s = 0.0;
    double refresh_cadence_s = 0.0;
    double target_control_cadence_s = 0.0;
    std::string expiry_behavior = std::string(kActionHoldExpiryBehaviorDrop);
    std::string interpolation_mode = std::string(kActionHoldInterpolationModeNone);
    double credit_assignment_latency_s = 0.0;
    std::string credit_assignment_attribution_note =
        "declarative_only_contract_runtime_cadence_not_implemented";
    std::string diagnostics_reason =
        "declarative_only_contract_runtime_cadence_not_implemented";
};

[[nodiscard]] inline bool is_supported_action_hold_mode(std::string_view hold_mode) {
    return hold_mode == kActionHoldModeHoldLast ||
        hold_mode == kActionHoldModeInterpolate ||
        hold_mode == kActionHoldModeExpire ||
        hold_mode == kActionHoldModeDrop;
}

[[nodiscard]] inline bool is_supported_action_hold_expiry_behavior(std::string_view expiry_behavior) {
    return expiry_behavior == kActionHoldExpiryBehaviorExpire ||
        expiry_behavior == kActionHoldExpiryBehaviorDrop;
}

[[nodiscard]] inline bool is_supported_action_hold_interpolation_mode(
    std::string_view interpolation_mode
) {
    return interpolation_mode == kActionHoldInterpolationModeNone ||
        interpolation_mode == kActionHoldInterpolationModeLinear;
}

[[nodiscard]] inline ActionHoldPolicy normalize_action_hold_policy(ActionHoldPolicy policy) {
    if (!is_supported_action_hold_mode(policy.hold_mode)) {
        policy.hold_mode = std::string(kActionHoldModeDrop);
        if (policy.diagnostics_reason.empty()) {
            policy.diagnostics_reason = "unsupported_action_hold_mode_fail_closed_to_drop";
        }
    }

    if (!is_supported_action_hold_expiry_behavior(policy.expiry_behavior)) {
        policy.expiry_behavior = std::string(kActionHoldExpiryBehaviorDrop);
        if (policy.diagnostics_reason.empty()) {
            policy.diagnostics_reason = "unsupported_action_hold_expiry_behavior_fail_closed_to_drop";
        }
    }

    if (!is_supported_action_hold_interpolation_mode(policy.interpolation_mode) ||
        policy.hold_mode != kActionHoldModeInterpolate) {
        policy.interpolation_mode = std::string(kActionHoldInterpolationModeNone);
    }

    if (policy.validity_duration_s < 0.0) {
        policy.validity_duration_s = 0.0;
    }
    if (policy.refresh_cadence_s < 0.0) {
        policy.refresh_cadence_s = 0.0;
    }
    if (policy.target_control_cadence_s < 0.0) {
        policy.target_control_cadence_s = 0.0;
    }
    if (policy.credit_assignment_latency_s < 0.0) {
        policy.credit_assignment_latency_s = 0.0;
    }

    return policy;
}

[[nodiscard]] inline bool is_known_policy_information_state_layer(std::string_view layer) {
    return layer == kPolicyInformationStateWorldTruth ||
        layer == kPolicyInformationStateSensedState ||
        layer == kPolicyInformationStateTrackState ||
        layer == kPolicyInformationStateSharedTacticalPicture ||
        layer == kPolicyInformationStateAgentObservation ||
        layer == kPolicyInformationStateDecisionBelief;
}

[[nodiscard]] inline bool is_known_policy_maintained_status(std::string_view status) {
    return status == kPolicyMaintainedStatusMaintained ||
        status == kPolicyMaintainedStatusAdapterProjection ||
        status == kPolicyMaintainedStatusDiagnosticsOnly;
}

[[nodiscard]] inline bool is_known_agent_action_interface_kind(std::string_view kind) {
    return kind == kActionInterfacePilotActionAssignment ||
        kind == kActionInterfaceCommandChainAssignment;
}

[[nodiscard]] inline bool is_known_agent_action_interface_payload_type(
    std::string_view payload_type
) {
    return payload_type == kActionInterfacePayloadPilotAction ||
        payload_type == kActionInterfacePayloadMissionCommand ||
        payload_type == kActionInterfacePayloadCoordinationIntent;
}

[[nodiscard]] inline bool is_known_agent_authority_scope(std::string_view scope) {
    return scope == kAgentAuthorityScopePlatformControl ||
        scope == kAgentAuthorityScopeMissionCommand ||
        scope == kAgentAuthorityScopeFormationCoordination;
}

struct InformationStateSource {
    std::string information_state_layer = std::string(kPolicyInformationStateAgentObservation);
    std::string source_label = std::string(kPolicySourceLabelAgentObservationAdapterProjection);
    std::string maintained_status =
        std::string(kPolicyMaintainedStatusAdapterProjection);
    std::vector<std::string> observation_packet_ids;
    std::vector<std::string> source_observation_versions;
    std::string diagnostics_reason;
};

[[nodiscard]] inline InformationStateSource make_information_state_source(
    std::string_view information_state_layer,
    std::string_view source_label,
    std::string_view maintained_status
) {
    InformationStateSource source{};
    source.information_state_layer = std::string(information_state_layer);
    source.source_label = std::string(source_label);
    source.maintained_status = std::string(maintained_status);
    return source;
}

[[nodiscard]] inline bool information_state_source_label_matches_layer_and_status(
    const InformationStateSource& source
) {
    if (source.source_label == kPolicySourceLabelFacadeObservationPacket) {
        return source.information_state_layer == kPolicyInformationStateAgentObservation &&
            source.maintained_status == kPolicyMaintainedStatusMaintained;
    }

    if (source.source_label == kPolicySourceLabelAgentObservationAdapterProjection) {
        return source.information_state_layer == kPolicyInformationStateAgentObservation &&
            source.maintained_status == kPolicyMaintainedStatusAdapterProjection;
    }

    if (source.source_label == kPolicySourceLabelSensedStatePacket) {
        return source.information_state_layer == kPolicyInformationStateSensedState &&
            source.maintained_status == kPolicyMaintainedStatusMaintained;
    }

    if (source.source_label == kPolicySourceLabelTrackStatePacket) {
        return source.information_state_layer == kPolicyInformationStateTrackState &&
            source.maintained_status == kPolicyMaintainedStatusMaintained;
    }

    if (source.source_label == kPolicySourceLabelSharedTacticalPictureAdapterProjection) {
        return source.information_state_layer ==
                kPolicyInformationStateSharedTacticalPicture &&
            source.maintained_status == kPolicyMaintainedStatusAdapterProjection;
    }

    if (source.source_label == kPolicySourceLabelWorldTruthDiagnostics) {
        return source.information_state_layer == kPolicyInformationStateWorldTruth &&
            source.maintained_status == kPolicyMaintainedStatusDiagnosticsOnly;
    }

    if (source.source_label == kPolicySourceLabelObservationDerivedBelief) {
        return source.information_state_layer == kPolicyInformationStateDecisionBelief &&
            is_known_policy_maintained_status(source.maintained_status);
    }

    return false;
}

[[nodiscard]] inline bool information_state_source_has_valid_label(
    const InformationStateSource& source
) {
    return is_known_policy_information_state_layer(source.information_state_layer) &&
        !source.source_label.empty() &&
        is_known_policy_maintained_status(source.maintained_status) &&
        information_state_source_label_matches_layer_and_status(source);
}

struct ConfidenceShape {
    std::string kind = "unspecified";
    double confidence = 0.0;
    double lower_bound = 0.0;
    double upper_bound = 0.0;
};

struct RoleDescriptor {
    std::string role_id;
    std::string role_type = "unspecified";
};

struct AgentAuthorityScope {
    std::string scope = "unspecified";
    std::uint64_t world_index = 0;
    bool has_world_index = false;
    std::vector<std::uint64_t> entity_ids;
    std::string roster_id;
    std::string command_family;
};

struct ActionIntentPacket {
    std::string source_id;
    double effective_time_s = 0.0;
    double valid_until_s = 0.0;
    IntentTargetRef target{};
    std::string action_family = "direct_control";
    std::string merge_policy = "last_write_wins";
    ActionInterfaceDescriptor action_interface{};
    bool has_pilot_action = false;
    PilotAction pilot_action{};
    bool has_mission_command = false;
    MissionCommand mission_command{};
};

struct CoordinationTargetRoster {
    std::uint64_t world_index = 0;
    bool has_world_index = false;
    std::string roster_id;
    std::vector<std::uint64_t> entity_ids;
    std::vector<std::string> role_ids;
};

struct CoordinationIntentPacket {
    std::string source_type = "policy";
    std::string source_id;
    CoordinationTargetRoster target_roster{};
    std::string update_clock = "adapter_step";
    std::string merge_policy = "last_write_wins";
    std::vector<ProducedIntentRef> produced_tasking_refs;
    std::vector<ProducedIntentRef> produced_leader_intent_refs;
};

struct AgentRole {
    RoleDescriptor role{};
    AgentAuthorityScope authority_scope{};
    InformationStateSource information_state_source{};
    DecisionModelRef decision_model_ref{};
    ActionInterfaceDescriptor action_interface{};
};

struct AgentRoleAuthorizationResult {
    bool authorized = false;
    std::string reason;
};

[[nodiscard]] inline bool action_interface_descriptor_has_valid_shape(
    const ActionInterfaceDescriptor& action_interface
) {
    return is_known_agent_action_interface_kind(action_interface.kind) &&
        is_known_agent_action_interface_payload_type(action_interface.payload_type);
}

[[nodiscard]] inline bool agent_authority_scope_has_required_shape(
    const AgentAuthorityScope& authority_scope
) {
    if (!is_known_agent_authority_scope(authority_scope.scope)) {
        return false;
    }

    if (!authority_scope.has_world_index) {
        return false;
    }

    if (authority_scope.scope == kAgentAuthorityScopePlatformControl ||
        authority_scope.scope == kAgentAuthorityScopeMissionCommand) {
        return !authority_scope.entity_ids.empty();
    }

    if (authority_scope.scope == kAgentAuthorityScopeFormationCoordination) {
        return !authority_scope.roster_id.empty() || !authority_scope.entity_ids.empty();
    }

    return false;
}

[[nodiscard]] inline bool maintained_information_state_source_is_authorized_for_agent_role(
    const InformationStateSource& source
) {
    if (!information_state_source_has_valid_label(source)) {
        return false;
    }

    if (source.maintained_status != kPolicyMaintainedStatusMaintained) {
        return false;
    }

    return source.information_state_layer == kPolicyInformationStateAgentObservation ||
        source.information_state_layer == kPolicyInformationStateDecisionBelief;
}

[[nodiscard]] inline bool decision_model_ref_has_required_shape(
    const DecisionModelRef& decision_model_ref
) {
    return !decision_model_ref.kind.empty() && !decision_model_ref.id.empty();
}

[[nodiscard]] inline bool agent_role_has_maintained_authority_shape(
    const AgentRole& role
) {
    return !role.role.role_id.empty() &&
        !role.role.role_type.empty() &&
        role.role.role_type != "unspecified" &&
        agent_authority_scope_has_required_shape(role.authority_scope) &&
        maintained_information_state_source_is_authorized_for_agent_role(
            role.information_state_source
        ) &&
        decision_model_ref_has_required_shape(role.decision_model_ref) &&
        action_interface_descriptor_has_valid_shape(role.action_interface);
}

[[nodiscard]] inline bool agent_role_action_interface_matches_authority_scope(
    const AgentRole& role
) {
    if (role.authority_scope.scope == kAgentAuthorityScopePlatformControl) {
        return role.action_interface.kind == kActionInterfacePilotActionAssignment &&
            role.action_interface.payload_type == kActionInterfacePayloadPilotAction;
    }

    if (role.authority_scope.scope == kAgentAuthorityScopeMissionCommand) {
        return role.action_interface.kind == kActionInterfaceCommandChainAssignment &&
            role.action_interface.payload_type == kActionInterfacePayloadMissionCommand;
    }

    if (role.authority_scope.scope == kAgentAuthorityScopeFormationCoordination) {
        return role.action_interface.kind == kActionInterfaceCommandChainAssignment &&
            role.action_interface.payload_type == kActionInterfacePayloadCoordinationIntent;
    }

    return false;
}

[[nodiscard]] inline bool action_intent_packet_matches_action_interface(
    const ActionIntentPacket& intent,
    const ActionInterfaceDescriptor& action_interface
) {
    if (intent.action_interface.kind != action_interface.kind ||
        intent.action_interface.payload_type != action_interface.payload_type) {
        return false;
    }

    if (action_interface.payload_type == kActionInterfacePayloadPilotAction) {
        return intent.has_pilot_action && !intent.has_mission_command;
    }

    if (action_interface.payload_type == kActionInterfacePayloadMissionCommand) {
        return intent.has_mission_command && !intent.has_pilot_action;
    }

    return false;
}

[[nodiscard]] inline bool coordination_intent_packet_matches_action_interface(
    const CoordinationIntentPacket& intent,
    const ActionInterfaceDescriptor& action_interface
) {
    if (action_interface.kind != kActionInterfaceCommandChainAssignment ||
        action_interface.payload_type != kActionInterfacePayloadCoordinationIntent) {
        return false;
    }

    if (intent.source_id.empty()) {
        return false;
    }

    return !intent.produced_tasking_refs.empty() || !intent.produced_leader_intent_refs.empty();
}

[[nodiscard]] inline AgentRoleAuthorizationResult authorize_maintained_action_intent(
    const AgentRole& role,
    const ActionIntentPacket& intent
) {
    if (!agent_role_has_maintained_authority_shape(role)) {
        return {
            false,
            "WP12-B maintained AgentRole authority slice requires role, authority scope, "
            "maintained information source, decision model ref, and action interface. "
            "This is not full Agency Graph runtime dispatch."
        };
    }

    if (!agent_role_action_interface_matches_authority_scope(role)) {
        return {false, "AgentRole authority scope and action interface are incompatible"};
    }

    if (!action_intent_packet_matches_action_interface(intent, role.action_interface)) {
        return {false, "ActionIntentPacket payload does not match AgentRole action interface"};
    }

    return {true, ""};
}

[[nodiscard]] inline AgentRoleAuthorizationResult authorize_maintained_coordination_intent(
    const AgentRole& role,
    const CoordinationIntentPacket& intent
) {
    if (!agent_role_has_maintained_authority_shape(role)) {
        return {
            false,
            "WP12-B maintained AgentRole authority slice requires role, authority scope, "
            "maintained information source, decision model ref, and action interface. "
            "This is not full Agency Graph runtime dispatch."
        };
    }

    if (!agent_role_action_interface_matches_authority_scope(role)) {
        return {false, "AgentRole authority scope and action interface are incompatible"};
    }

    if (!coordination_intent_packet_matches_action_interface(intent, role.action_interface)) {
        return {
            false,
            "CoordinationIntentPacket payload does not match AgentRole action interface"
        };
    }

    return {true, ""};
}

struct DecisionBelief {
    std::string belief_id;
    std::string information_state_layer = std::string(kPolicyInformationStateDecisionBelief);
    InformationStateSource source_information_state = make_information_state_source(
        kPolicyInformationStateAgentObservation,
        kPolicySourceLabelAgentObservationAdapterProjection,
        kPolicyMaintainedStatusAdapterProjection
    );
    std::vector<std::string> source_observation_versions;
    std::string memory_or_estimator_ref;
    ConfidenceShape confidence_shape{};
    std::string maintained_status =
        std::string(kPolicyMaintainedStatusAdapterProjection);
    std::string diagnostics_reason;
    bool uses_truth_state = false;
    bool uses_raw_ecs = false;
};

[[nodiscard]] inline bool decision_belief_requires_diagnostics_only(
    const DecisionBelief& belief
) {
    return belief.uses_truth_state ||
        belief.uses_raw_ecs ||
        belief.source_information_state.information_state_layer ==
            kPolicyInformationStateWorldTruth ||
        belief.source_information_state.maintained_status ==
            kPolicyMaintainedStatusDiagnosticsOnly;
}

[[nodiscard]] inline bool decision_belief_has_valid_provenance(
    const DecisionBelief& belief
) {
    if (belief.information_state_layer != kPolicyInformationStateDecisionBelief) {
        return false;
    }
    if (!information_state_source_has_valid_label(belief.source_information_state)) {
        return false;
    }
    if (!is_known_policy_maintained_status(belief.maintained_status)) {
        return false;
    }
    if (!decision_belief_requires_diagnostics_only(belief)) {
        return true;
    }
    return belief.maintained_status == kPolicyMaintainedStatusDiagnosticsOnly &&
        belief.source_information_state.maintained_status ==
            kPolicyMaintainedStatusDiagnosticsOnly &&
        !belief.diagnostics_reason.empty();
}
