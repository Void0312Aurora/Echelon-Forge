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
    std::string kind = "PilotActionAssignmentCompat";
    std::string payload_type = "pilot_action";
};

struct DecisionModelRef {
    std::string kind = "external_policy";
    std::string id = "caller_supplied";
};

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
inline constexpr std::string_view kPolicyMaintainedStatusCompatibilityAdapter =
    "compatibility_adapter";
inline constexpr std::string_view kPolicyMaintainedStatusDiagnosticsOnly =
    "diagnostics_only";

inline constexpr std::string_view kPolicySourceLabelFacadeObservationPacket =
    "facade_observation_packet";
inline constexpr std::string_view kPolicySourceLabelAgentObservationCompat =
    "agent_observation_compat";
inline constexpr std::string_view kPolicySourceLabelSensedStatePacket =
    "sensed_state_packet";
inline constexpr std::string_view kPolicySourceLabelTrackStatePacket =
    "track_state_packet";
inline constexpr std::string_view kPolicySourceLabelSharedTacticalPictureCompat =
    "shared_tactical_picture_compat";
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
        status == kPolicyMaintainedStatusCompatibilityAdapter ||
        status == kPolicyMaintainedStatusDiagnosticsOnly;
}

struct InformationStateSource {
    std::string information_state_layer = std::string(kPolicyInformationStateAgentObservation);
    std::string source_label = std::string(kPolicySourceLabelAgentObservationCompat);
    std::string maintained_status =
        std::string(kPolicyMaintainedStatusCompatibilityAdapter);
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

[[nodiscard]] inline bool information_state_source_has_valid_label(
    const InformationStateSource& source
) {
    return is_known_policy_information_state_layer(source.information_state_layer) &&
        !source.source_label.empty() &&
        is_known_policy_maintained_status(source.maintained_status);
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

struct DecisionBelief {
    std::string belief_id;
    std::string information_state_layer = std::string(kPolicyInformationStateDecisionBelief);
    InformationStateSource source_information_state = make_information_state_source(
        kPolicyInformationStateAgentObservation,
        kPolicySourceLabelObservationDerivedBelief,
        kPolicyMaintainedStatusCompatibilityAdapter
    );
    std::vector<std::string> source_observation_versions;
    std::string memory_or_estimator_ref;
    ConfidenceShape confidence_shape{};
    std::string maintained_status =
        std::string(kPolicyMaintainedStatusCompatibilityAdapter);
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
