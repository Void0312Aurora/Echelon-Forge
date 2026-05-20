#pragma once

#include <array>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

#include "runtime/contracts/policy_contracts.h"

namespace runtime::information {

inline constexpr std::string_view kInformationSurfaceActionIntentPacket =
    "ActionIntentPacket";

inline constexpr std::string_view kTransformationEvidenceSensorObservation =
    "sensor_observation_evidence";
inline constexpr std::string_view kTransformationEvidenceTrackFusion =
    "track_fusion_evidence";
inline constexpr std::string_view kTransformationEvidenceSharedPictureDistribution =
    "shared_picture_distribution_evidence";
inline constexpr std::string_view kTransformationEvidenceObservationView =
    "observation_view_evidence";
inline constexpr std::string_view kTransformationEvidenceDecisionInference =
    "decision_inference_evidence";
inline constexpr std::string_view kTransformationEvidenceIntentInjection =
    "intent_injection_evidence";

inline constexpr std::string_view kCanonicalTransformationWorldTruthToSensedState =
    "world_truth_to_sensed_state.v1";
inline constexpr std::string_view kCanonicalTransformationSensedStateToTrackState =
    "sensed_state_to_track_state.v1";
inline constexpr std::string_view
    kCanonicalTransformationTrackStateToSharedTacticalPicture =
        "track_state_to_shared_tactical_picture.v1";
inline constexpr std::string_view
    kCanonicalTransformationSharedTacticalPictureToAgentObservation =
        "shared_tactical_picture_to_agent_observation.v1";
inline constexpr std::string_view
    kCanonicalTransformationAgentObservationToDecisionBelief =
        "agent_observation_to_decision_belief.v1";
inline constexpr std::string_view
    kCanonicalTransformationDecisionBeliefToActionIntent =
        "decision_belief_to_action_intent.v1";

inline constexpr std::string_view
    kDiagnosticsOnlyTransformationWorldTruthToActionIntent =
        "diagnostics_only_world_truth_to_action_intent.v1";

struct InformationTransformationSpec {
    std::string_view stable_name;
    std::string_view source_layer;
    std::string_view target_layer;
    std::string_view evidence_requirement;
    bool maintained_allowed = true;
    bool diagnostics_only_allowed = true;
};

inline constexpr std::array<InformationTransformationSpec, 6>
    kCanonicalInformationTransformations{{
        InformationTransformationSpec{
            .stable_name = kCanonicalTransformationWorldTruthToSensedState,
            .source_layer = kPolicyInformationStateWorldTruth,
            .target_layer = kPolicyInformationStateSensedState,
            .evidence_requirement = kTransformationEvidenceSensorObservation,
        },
        InformationTransformationSpec{
            .stable_name = kCanonicalTransformationSensedStateToTrackState,
            .source_layer = kPolicyInformationStateSensedState,
            .target_layer = kPolicyInformationStateTrackState,
            .evidence_requirement = kTransformationEvidenceTrackFusion,
        },
        InformationTransformationSpec{
            .stable_name = kCanonicalTransformationTrackStateToSharedTacticalPicture,
            .source_layer = kPolicyInformationStateTrackState,
            .target_layer = kPolicyInformationStateSharedTacticalPicture,
            .evidence_requirement = kTransformationEvidenceSharedPictureDistribution,
        },
        InformationTransformationSpec{
            .stable_name =
                kCanonicalTransformationSharedTacticalPictureToAgentObservation,
            .source_layer = kPolicyInformationStateSharedTacticalPicture,
            .target_layer = kPolicyInformationStateAgentObservation,
            .evidence_requirement = kTransformationEvidenceObservationView,
        },
        InformationTransformationSpec{
            .stable_name =
                kCanonicalTransformationAgentObservationToDecisionBelief,
            .source_layer = kPolicyInformationStateAgentObservation,
            .target_layer = kPolicyInformationStateDecisionBelief,
            .evidence_requirement = kTransformationEvidenceDecisionInference,
        },
        InformationTransformationSpec{
            .stable_name =
                kCanonicalTransformationDecisionBeliefToActionIntent,
            .source_layer = kPolicyInformationStateDecisionBelief,
            .target_layer = kInformationSurfaceActionIntentPacket,
            .evidence_requirement = kTransformationEvidenceIntentInjection,
        },
    }};

inline constexpr std::array<InformationTransformationSpec, 1>
    kDiagnosticsOnlyInformationTransformations{{
        InformationTransformationSpec{
            .stable_name = kDiagnosticsOnlyTransformationWorldTruthToActionIntent,
            .source_layer = kPolicyInformationStateWorldTruth,
            .target_layer = kInformationSurfaceActionIntentPacket,
            .evidence_requirement = kTransformationEvidenceIntentInjection,
            .maintained_allowed = false,
            .diagnostics_only_allowed = true,
        },
    }};

struct InformationTransformationEvidence {
    std::string transformation_name;
    std::string source_layer;
    std::string target_layer;
    std::string maintained_status =
        std::string(kPolicyMaintainedStatusMaintained);
    std::vector<std::string> source_observation_versions;
    std::vector<std::string> evidence_tokens;
    std::string diagnostics_reason;
};

struct InformationTransformationValidationResult {
    bool valid = true;
    std::vector<std::string> errors;
};

struct MaintainedIntentInjectionRequestMetadata {
    std::string source_layer;
    std::string input_snapshot_version;
};

struct MaintainedActionIntentInjectionAuthorizationResult {
    bool authorized = false;
    std::string reason;
    AgentRoleAuthorizationResult authority_result{};
    InformationTransformationValidationResult transformation_result{};
    std::vector<std::string> errors;
};

[[nodiscard]] inline bool is_known_information_surface_endpoint(
    std::string_view endpoint
) {
    return endpoint == kInformationSurfaceActionIntentPacket ||
        is_known_policy_information_state_layer(endpoint);
}

[[nodiscard]] inline bool contains_transformation_token(
    const std::vector<std::string>& tokens,
    std::string_view expected_token
) {
    for (const auto& token : tokens) {
        if (token == expected_token) {
            return true;
        }
    }
    return false;
}

[[nodiscard]] inline bool contains_observation_version(
    const std::vector<std::string>& versions,
    std::string_view expected_version
) {
    for (const auto& version : versions) {
        if (version == expected_version) {
            return true;
        }
    }
    return false;
}

[[nodiscard]] inline bool contains_observation_packet_id(
    const std::vector<std::string>& packet_ids,
    std::string_view expected_packet_id
) {
    for (const auto& packet_id : packet_ids) {
        if (packet_id == expected_packet_id) {
            return true;
        }
    }
    return false;
}

[[nodiscard]] inline bool maintained_intent_injection_has_finite_time(double value) {
    return value == value &&
        value != std::numeric_limits<double>::infinity() &&
        value != -std::numeric_limits<double>::infinity();
}

[[nodiscard]] inline bool maintained_intent_injection_merge_policy_is_supported(
    std::string_view merge_policy
) {
    return merge_policy == "last_write_wins" || merge_policy == "reject_on_conflict";
}

[[nodiscard]] inline const InformationTransformationSpec*
find_information_transformation_spec(std::string_view name) {
    for (const auto& spec : kCanonicalInformationTransformations) {
        if (spec.stable_name == name) {
            return &spec;
        }
    }
    for (const auto& spec : kDiagnosticsOnlyInformationTransformations) {
        if (spec.stable_name == name) {
            return &spec;
        }
    }
    return nullptr;
}

[[nodiscard]] inline bool is_canonical_information_transformation_name(
    std::string_view name
) {
    for (const auto& spec : kCanonicalInformationTransformations) {
        if (spec.stable_name == name) {
            return true;
        }
    }
    return false;
}

[[nodiscard]] inline InformationTransformationValidationResult
validate_information_transformation_evidence(
    const InformationTransformationEvidence& evidence
) {
    InformationTransformationValidationResult result{};

    if (evidence.transformation_name.empty()) {
        result.valid = false;
        result.errors.push_back("transformation_name is required");
    }
    if (evidence.source_layer.empty()) {
        result.valid = false;
        result.errors.push_back("source_layer is required");
    }
    if (evidence.target_layer.empty()) {
        result.valid = false;
        result.errors.push_back("target_layer is required");
    }
    if (!is_known_information_surface_endpoint(evidence.source_layer)) {
        result.valid = false;
        result.errors.push_back("source_layer must name a known information surface");
    }
    if (!is_known_information_surface_endpoint(evidence.target_layer)) {
        result.valid = false;
        result.errors.push_back("target_layer must name a known information surface");
    }
    if (!is_known_policy_maintained_status(evidence.maintained_status)) {
        result.valid = false;
        result.errors.push_back("maintained_status must use the policy vocabulary");
    }

    const auto* spec =
        find_information_transformation_spec(evidence.transformation_name);
    if (spec == nullptr) {
        result.valid = false;
        result.errors.push_back(
            "transformation_name must map to a known transformation spec"
        );
        return result;
    }

    if (evidence.source_layer != spec->source_layer) {
        result.valid = false;
        result.errors.push_back(
            "source_layer does not match the declared transformation source"
        );
    }
    if (evidence.target_layer != spec->target_layer) {
        result.valid = false;
        result.errors.push_back(
            "target_layer does not match the declared transformation target"
        );
    }
    if (evidence.source_observation_versions.empty()) {
        result.valid = false;
        result.errors.push_back(
            "source_observation_versions must carry explicit transformation ancestry"
        );
    }
    if (!contains_transformation_token(
            evidence.evidence_tokens,
            spec->evidence_requirement)) {
        result.valid = false;
        result.errors.push_back(
            "evidence_tokens must include the declared evidence requirement"
        );
    }

    if (evidence.maintained_status == kPolicyMaintainedStatusMaintained &&
        !spec->maintained_allowed) {
        result.valid = false;
        result.errors.push_back(
            "this transformation is diagnostics-only and cannot authorize maintained output"
        );
    }
    if (evidence.maintained_status == kPolicyMaintainedStatusDiagnosticsOnly) {
        if (!spec->diagnostics_only_allowed) {
            result.valid = false;
            result.errors.push_back(
                "diagnostics_only output is not allowed for this transformation"
            );
        }
        if (evidence.diagnostics_reason.empty()) {
            result.valid = false;
            result.errors.push_back(
                "diagnostics_only transformation requires diagnostics_reason"
            );
        }
    }

    return result;
}

[[nodiscard]] inline InformationTransformationValidationResult
validate_information_source_transformation(
    const InformationStateSource& output_source,
    const InformationTransformationEvidence& evidence
) {
    auto result = validate_information_transformation_evidence(evidence);

    if (!information_state_source_has_valid_label(output_source)) {
        result.valid = false;
        result.errors.push_back(
            "output_source must carry a valid information-state label"
        );
    }
    if (output_source.information_state_layer != evidence.target_layer) {
        result.valid = false;
        result.errors.push_back(
            "output_source.information_state_layer must match transformation target_layer"
        );
    }
    if (output_source.maintained_status != evidence.maintained_status) {
        result.valid = false;
        result.errors.push_back(
            "output_source.maintained_status must match transformation maintained_status"
        );
    }
    if (output_source.source_observation_versions.empty()) {
        result.valid = false;
        result.errors.push_back(
            "output_source.source_observation_versions must stay explicit"
        );
    }
    if (output_source.maintained_status ==
            kPolicyMaintainedStatusDiagnosticsOnly &&
        output_source.diagnostics_reason.empty() &&
        evidence.diagnostics_reason.empty()) {
        result.valid = false;
        result.errors.push_back(
            "diagnostics_only output_source requires an explicit diagnostics reason"
        );
    }

    return result;
}

[[nodiscard]] inline InformationTransformationValidationResult
validate_decision_belief_transformation(
    const DecisionBelief& belief,
    const InformationTransformationEvidence& evidence
) {
    auto result = validate_information_transformation_evidence(evidence);

    if (!decision_belief_has_valid_provenance(belief)) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief provenance must validate before transformation promotion"
        );
    }
    if (belief.information_state_layer != evidence.target_layer) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief.information_state_layer must match transformation target_layer"
        );
    }
    if (belief.source_information_state.information_state_layer !=
        evidence.source_layer) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief.source_information_state must match transformation source_layer"
        );
    }
    if (belief.maintained_status != evidence.maintained_status) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief.maintained_status must match transformation maintained_status"
        );
    }
    if (belief.source_observation_versions.empty()) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief.source_observation_versions must stay explicit"
        );
    }

    return result;
}

[[nodiscard]] inline InformationTransformationValidationResult
validate_decision_belief_to_action_intent_transformation(
    const DecisionBelief& belief,
    const ActionIntentPacket& intent,
    const InformationTransformationEvidence& evidence
) {
    auto result = validate_information_transformation_evidence(evidence);

    if (!decision_belief_has_valid_provenance(belief)) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief provenance must validate before action-intent transformation"
        );
    }
    if (belief.source_observation_versions.empty()) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief.source_observation_versions must stay explicit before action-intent transformation"
        );
    }
    if (belief.information_state_layer != evidence.source_layer) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief source layer must match the action-intent transformation source"
        );
    }
    if (belief.maintained_status != evidence.maintained_status) {
        result.valid = false;
        result.errors.push_back(
            "DecisionBelief maintained_status must match the action-intent transformation"
        );
    }
    if (intent.source_id.empty()) {
        result.valid = false;
        result.errors.push_back(
            "ActionIntentPacket.source_id is required for transformation evidence"
        );
    }
    if (intent.action_family.empty()) {
        result.valid = false;
        result.errors.push_back(
            "ActionIntentPacket.action_family is required for transformation evidence"
        );
    }
    if (intent.action_interface.kind.empty()) {
        result.valid = false;
        result.errors.push_back(
            "ActionIntentPacket.action_interface.kind is required for transformation evidence"
        );
    }

    return result;
}

[[nodiscard]] inline InformationTransformationValidationResult
validate_information_source_to_action_intent_transformation(
    const InformationStateSource& source,
    const ActionIntentPacket& intent,
    const InformationTransformationEvidence& evidence
) {
    auto result = validate_information_transformation_evidence(evidence);

    if (!information_state_source_has_valid_label(source)) {
        result.valid = false;
        result.errors.push_back(
            "source information_state_source must carry a valid label"
        );
    }
    if (source.information_state_layer != evidence.source_layer) {
        result.valid = false;
        result.errors.push_back(
            "source information_state_layer must match the action-intent transformation source"
        );
    }
    if (source.maintained_status != evidence.maintained_status) {
        result.valid = false;
        result.errors.push_back(
            "source maintained_status must match the action-intent transformation"
        );
    }
    if (source.maintained_status ==
            kPolicyMaintainedStatusDiagnosticsOnly &&
        source.diagnostics_reason.empty() &&
        evidence.diagnostics_reason.empty()) {
        result.valid = false;
        result.errors.push_back(
            "diagnostics_only action-intent shortcut requires explicit diagnostics reason"
        );
    }
    if (intent.source_id.empty()) {
        result.valid = false;
        result.errors.push_back(
            "ActionIntentPacket.source_id is required for transformation evidence"
        );
    }

    return result;
}

[[nodiscard]] inline MaintainedActionIntentInjectionAuthorizationResult
authorize_maintained_decision_belief_action_intent_injection(
    const AgentRole& role,
    const DecisionBelief& belief,
    const ActionIntentPacket& intent,
    const InformationTransformationEvidence& evidence,
    const MaintainedIntentInjectionRequestMetadata& request_metadata
) {
    MaintainedActionIntentInjectionAuthorizationResult result{};
    result.authority_result = authorize_maintained_action_intent(role, intent);
    result.transformation_result =
        validate_decision_belief_to_action_intent_transformation(belief, intent, evidence);

    if (!result.authority_result.authorized) {
        result.errors.push_back(result.authority_result.reason);
    }
    if (!result.transformation_result.valid) {
        result.errors.insert(
            result.errors.end(),
            result.transformation_result.errors.begin(),
            result.transformation_result.errors.end()
        );
    }

    if (role.information_state_source.information_state_layer !=
        kPolicyInformationStateDecisionBelief) {
        result.errors.push_back(
            "maintained action-intent injection requires a DecisionBelief AgentRole source"
        );
    }
    if (role.information_state_source.source_label !=
        kPolicySourceLabelObservationDerivedBelief) {
        result.errors.push_back(
            "maintained action-intent injection requires the observation_derived_belief source label"
        );
    }
    if (!belief.belief_id.empty() &&
        !role.information_state_source.observation_packet_ids.empty() &&
        !contains_observation_packet_id(
            role.information_state_source.observation_packet_ids,
            belief.belief_id
        )) {
        result.errors.push_back(
            "AgentRole DecisionBelief source must trace the injected belief_id"
        );
    }
    if (!belief.source_observation_versions.empty() &&
        role.information_state_source.source_observation_versions !=
            belief.source_observation_versions) {
        result.errors.push_back(
            "AgentRole DecisionBelief source_observation_versions must match the injected belief ancestry"
        );
    }

    if (request_metadata.source_layer.empty()) {
        result.errors.push_back("source_layer is required for facade-compatible injection");
    }
    if (request_metadata.input_snapshot_version.empty()) {
        result.errors.push_back(
            "input_snapshot_version is required for facade-compatible injection"
        );
    }
    if (request_metadata.source_layer != "policy" &&
        request_metadata.source_layer != "orchestration" &&
        request_metadata.source_layer != "adapter" &&
        request_metadata.source_layer != "human" &&
        request_metadata.source_layer != "diagnostic" &&
        request_metadata.source_layer != "facade") {
        result.errors.push_back(
            "source_layer must use the facade-compatible cross-layer request vocabulary"
        );
    }
    if (request_metadata.source_layer == "facade") {
        result.errors.push_back(
            "maintained DecisionBelief action-intent injection must not masquerade as raw facade injection"
        );
    }
    if (!request_metadata.input_snapshot_version.empty() &&
        !contains_observation_version(
            belief.source_observation_versions,
            request_metadata.input_snapshot_version
        )) {
        result.errors.push_back(
            "input_snapshot_version must match explicit DecisionBelief source_observation_versions ancestry"
        );
    }

    if (intent.source_id.empty()) {
        result.errors.push_back("source_id is required for facade-compatible injection");
    }
    if (!maintained_intent_injection_has_finite_time(intent.effective_time_s)) {
        result.errors.push_back("effective_time_s must be finite for maintained injection");
    }
    if (intent.valid_until_s != 0.0 &&
        !maintained_intent_injection_has_finite_time(intent.valid_until_s)) {
        result.errors.push_back("valid_until_s must be finite for maintained injection");
    }
    if (intent.valid_until_s != 0.0 && intent.valid_until_s < intent.effective_time_s) {
        result.errors.push_back(
            "valid_until_s must be greater than or equal to effective_time_s"
        );
    }
    if (!maintained_intent_injection_merge_policy_is_supported(intent.merge_policy)) {
        result.errors.push_back(
            "merge_policy is not supported by the maintained facade-compatible injection seam"
        );
    }

    result.authorized = result.errors.empty();
    if (!result.authorized) {
        if (!result.authority_result.authorized && !result.authority_result.reason.empty()) {
            result.reason = result.authority_result.reason;
        } else if (!result.transformation_result.valid &&
                   !result.transformation_result.errors.empty()) {
            result.reason = result.transformation_result.errors.front();
        } else {
            result.reason = result.errors.front();
        }
    }

    return result;
}

}  // namespace runtime::information
