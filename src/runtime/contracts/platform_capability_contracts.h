#pragma once

#include <algorithm>
#include <cctype>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace runtime::platform_capabilities {

inline constexpr std::string_view kCapabilityFamilyMobility = "mobility";
inline constexpr std::string_view kCapabilityFamilySensing = "sensing";
inline constexpr std::string_view kCapabilityFamilyCommunication = "communication";
inline constexpr std::string_view kCapabilityFamilyLaunching = "launching";
inline constexpr std::string_view kCapabilityFamilySurvivability = "survivability";
inline constexpr std::string_view kCapabilityFamilyCommand = "command";
inline constexpr std::string_view kCapabilityFamilyDoctrine = "doctrine";

inline constexpr std::string_view kPlatformSpawnRequestKindTypeNameProjection =
    "type_name_projection";
inline constexpr std::string_view kPlatformSpawnRequestKindTypedPlatformRequest =
    "typed_platform_request";

inline constexpr std::string_view kPlatformMaterializationStrategyFactoryProjection =
    "factory_projection_materialization";
inline constexpr std::string_view kPlatformMaterializationStrategyResolvedSpawnBridge =
    "resolved_spawn_plan_bridge";

inline constexpr std::string_view kPlatformCapabilityUnsupportedFamilyNotMaintained =
    "platform_capability_family_not_maintained";
inline constexpr std::string_view kPlatformCapabilityUnsupportedEffectNotMaterialized =
    "platform_capability_effect_not_materialized";
inline constexpr std::string_view kPlatformCapabilityUnsupportedTypeNameProjectionRequired =
    "platform_capability_requires_type_name_projection_path";

inline constexpr std::string_view kPlatformCapabilityRejectionMissingCapabilityId =
    "platform_capability_id_required";
inline constexpr std::string_view kPlatformCapabilityRejectionMissingCapabilityFamily =
    "platform_capability_family_required";
inline constexpr std::string_view kPlatformCapabilityRejectionUnsupportedCapabilityFamily =
    "platform_capability_family_not_maintained";
inline constexpr std::string_view kPlatformCapabilityRejectionMissingCapabilityType =
    "platform_capability_type_required";
inline constexpr std::string_view kPlatformCapabilityRejectionMissingCapabilityEvidence =
    "platform_capability_evidence_required";
inline constexpr std::string_view kPlatformCapabilityRejectionMissingUnsupportedReason =
    "unsupported_platform_capability_reason_required";

inline constexpr std::string_view kCapabilityBundleRejectionMissingBundleId =
    "platform_capability_bundle_id_required";
inline constexpr std::string_view kCapabilityBundleRejectionMissingSourceTypeName =
    "platform_capability_bundle_source_type_name_required";
inline constexpr std::string_view kCapabilityBundleRejectionMissingCapabilities =
    "platform_capability_bundle_requires_capabilities";
inline constexpr std::string_view kCapabilityBundleRejectionDuplicateCapabilityId =
    "platform_capability_bundle_duplicate_capability_id";
inline constexpr std::string_view kCapabilityBundleRejectionMissingTemplateEvidence =
    "platform_capability_bundle_template_evidence_required";
inline constexpr std::string_view kCapabilityBundleRejectionMissingBundleEvidence =
    "platform_capability_bundle_evidence_required";

inline constexpr std::string_view kResolvedPlatformSpawnPlanRejectionMissingPlanId =
    "resolved_platform_spawn_plan_id_required";
inline constexpr std::string_view kResolvedPlatformSpawnPlanRejectionMissingSourceRequestKind =
    "resolved_platform_spawn_plan_source_request_kind_required";
inline constexpr std::string_view kResolvedPlatformSpawnPlanRejectionUnsupportedSourceRequestKind =
    "resolved_platform_spawn_plan_source_request_kind_not_maintained";
inline constexpr std::string_view kResolvedPlatformSpawnPlanRejectionMissingSourceTypeName =
    "resolved_platform_spawn_plan_source_type_name_required";
inline constexpr std::string_view kResolvedPlatformSpawnPlanRejectionMissingBundleId =
    "resolved_platform_spawn_plan_bundle_id_required";
inline constexpr std::string_view kResolvedPlatformSpawnPlanRejectionMissingDefinitionRef =
    "resolved_platform_spawn_plan_definition_ref_required";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionMissingMaterializationStrategy =
        "resolved_platform_spawn_plan_materialization_strategy_required";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionUnsupportedMaterializationStrategy =
        "resolved_platform_spawn_plan_materialization_strategy_not_maintained";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionMissingTemplateEvidence =
        "resolved_platform_spawn_plan_template_evidence_required";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionMissingResolutionEvidence =
        "resolved_platform_spawn_plan_resolution_evidence_required";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionMissingMaterializationEvidence =
        "resolved_platform_spawn_plan_materialization_evidence_required";
inline constexpr std::string_view kResolvedPlatformSpawnPlanRejectionMissingPlanEvidence =
    "resolved_platform_spawn_plan_evidence_required";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionMissingResolvedCapabilities =
        "resolved_platform_spawn_plan_requires_resolved_capabilities";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionUnsupportedRequiredCapability =
        "resolved_spawn_plan_contains_unsupported_required_capability";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionTypeNameProjectionRequired =
        "resolved_spawn_plan_requires_type_name_projection_path";
inline constexpr std::string_view
    kResolvedPlatformSpawnPlanRejectionMissingRejectionReason =
        "rejected_resolved_spawn_plan_requires_reason";

struct Capability {
#define EF_PLATFORM_CAPABILITY_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/platform_capability.inc"
};

struct CapabilityBundle {
#define EF_CAPABILITY_BUNDLE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/capability_bundle.inc"
};

struct ResolvedPlatformSpawnPlan {
#define EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/resolved_platform_spawn_plan.inc"
};

struct PlatformCapabilityValidationResult {
    bool valid = false;
    bool fail_closed = false;
    std::string rejection_reason;
    std::vector<std::string> errors;

    void reject(std::string reason) {
        valid = false;
        fail_closed = true;
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }

    void add_error(std::string error) {
        errors.push_back(std::move(error));
    }
};

[[nodiscard]] inline bool is_blank(std::string_view value) {
    return value.empty() ||
        std::all_of(value.begin(), value.end(), [](unsigned char ch) {
            return std::isspace(ch) != 0;
        });
}

[[nodiscard]] inline bool contains_blank_value(const std::vector<std::string>& values) {
    return std::any_of(values.begin(), values.end(), [](const std::string& value) {
        return is_blank(value);
    });
}

[[nodiscard]] inline std::vector<std::string_view> platform_capability_family_vocabulary() {
    return {
        kCapabilityFamilyMobility,
        kCapabilityFamilySensing,
        kCapabilityFamilyCommunication,
        kCapabilityFamilyLaunching,
        kCapabilityFamilySurvivability,
        kCapabilityFamilyCommand,
        kCapabilityFamilyDoctrine,
    };
}

[[nodiscard]] inline bool is_known_platform_capability_family(std::string_view family) {
    const auto vocabulary = platform_capability_family_vocabulary();
    return std::find(vocabulary.begin(), vocabulary.end(), family) != vocabulary.end();
}

[[nodiscard]] inline bool is_known_platform_spawn_request_kind(std::string_view kind) {
    return kind == kPlatformSpawnRequestKindTypeNameProjection ||
        kind == kPlatformSpawnRequestKindTypedPlatformRequest;
}

[[nodiscard]] inline bool is_known_platform_materialization_strategy(
    std::string_view strategy
) {
    return strategy == kPlatformMaterializationStrategyFactoryProjection ||
        strategy == kPlatformMaterializationStrategyResolvedSpawnBridge;
}

[[nodiscard]] inline bool capability_ids_are_unique(
    const std::vector<Capability>& capabilities
) {
    std::vector<std::string> ids;
    ids.reserve(capabilities.size());
    for (const auto& capability : capabilities) {
        if (!is_blank(capability.capability_id)) {
            ids.push_back(capability.capability_id);
        }
    }

    std::sort(ids.begin(), ids.end());
    return std::adjacent_find(ids.begin(), ids.end()) == ids.end();
}

[[nodiscard]] inline Capability make_unsupported_capability(
    Capability capability,
    std::string_view reason
) {
    capability.supported = false;
    capability.unsupported_reason = std::string(reason);
    return capability;
}

[[nodiscard]] inline ResolvedPlatformSpawnPlan make_rejected_resolved_platform_spawn_plan(
    ResolvedPlatformSpawnPlan plan,
    std::string_view rejection_reason,
    std::string diagnostics_reason = {}
) {
    plan.admitted = false;
    plan.rejection_reason = std::string(rejection_reason);
    if (plan.diagnostics_reason.empty()) {
        plan.diagnostics_reason = std::move(diagnostics_reason);
    }
    return plan;
}

[[nodiscard]] inline PlatformCapabilityValidationResult validate_capability(
    const Capability& capability
) {
    PlatformCapabilityValidationResult result{};

    if (is_blank(capability.capability_id)) {
        result.reject(std::string(kPlatformCapabilityRejectionMissingCapabilityId));
        result.add_error("capability_id is required");
        return result;
    }
    if (is_blank(capability.family)) {
        result.reject(std::string(kPlatformCapabilityRejectionMissingCapabilityFamily));
        result.add_error("family is required");
        return result;
    }
    if (!is_known_platform_capability_family(capability.family)) {
        result.reject(std::string(kPlatformCapabilityRejectionUnsupportedCapabilityFamily));
        result.add_error("family must be one of the maintained platform capability families");
        return result;
    }
    if (is_blank(capability.capability_type)) {
        result.reject(std::string(kPlatformCapabilityRejectionMissingCapabilityType));
        result.add_error("capability_type is required");
        return result;
    }
    if (capability.evidence_refs.empty() || contains_blank_value(capability.evidence_refs)) {
        result.reject(std::string(kPlatformCapabilityRejectionMissingCapabilityEvidence));
        result.add_error("evidence_refs is required and cannot contain blank entries");
        return result;
    }
    if (!capability.supported && is_blank(capability.unsupported_reason)) {
        result.reject(std::string(kPlatformCapabilityRejectionMissingUnsupportedReason));
        result.add_error("unsupported capabilities must declare unsupported_reason");
        return result;
    }

    result.valid = true;
    return result;
}

[[nodiscard]] inline PlatformCapabilityValidationResult validate_capability_bundle(
    const CapabilityBundle& bundle
) {
    PlatformCapabilityValidationResult result{};

    if (is_blank(bundle.bundle_id)) {
        result.reject(std::string(kCapabilityBundleRejectionMissingBundleId));
        result.add_error("bundle_id is required");
        return result;
    }
    if (is_blank(bundle.source_type_name)) {
        result.reject(std::string(kCapabilityBundleRejectionMissingSourceTypeName));
        result.add_error("source_type_name is required");
        return result;
    }
    if (bundle.capabilities.empty()) {
        result.reject(std::string(kCapabilityBundleRejectionMissingCapabilities));
        result.add_error("capabilities cannot be empty");
        return result;
    }
    if (!capability_ids_are_unique(bundle.capabilities)) {
        result.reject(std::string(kCapabilityBundleRejectionDuplicateCapabilityId));
        result.add_error("capability identifiers must be unique within a bundle");
        return result;
    }
    if (is_blank(bundle.template_evidence_ref)) {
        result.reject(std::string(kCapabilityBundleRejectionMissingTemplateEvidence));
        result.add_error("template_evidence_ref is required");
        return result;
    }
    if (bundle.evidence_refs.empty() || contains_blank_value(bundle.evidence_refs)) {
        result.reject(std::string(kCapabilityBundleRejectionMissingBundleEvidence));
        result.add_error("evidence_refs is required and cannot contain blank entries");
        return result;
    }

    for (const auto& capability : bundle.capabilities) {
        const auto capability_result = validate_capability(capability);
        if (!capability_result.valid) {
            result.reject(capability_result.rejection_reason);
            for (const auto& error : capability_result.errors) {
                result.add_error("capability[" + capability.capability_id + "]: " + error);
            }
            return result;
        }
    }

    result.valid = true;
    return result;
}

[[nodiscard]] inline PlatformCapabilityValidationResult validate_resolved_platform_spawn_plan(
    const ResolvedPlatformSpawnPlan& plan
) {
    PlatformCapabilityValidationResult result{};

    if (is_blank(plan.plan_id)) {
        result.reject(std::string(kResolvedPlatformSpawnPlanRejectionMissingPlanId));
        result.add_error("plan_id is required");
        return result;
    }
    if (is_blank(plan.source_request_kind)) {
        result.reject(
            std::string(kResolvedPlatformSpawnPlanRejectionMissingSourceRequestKind)
        );
        result.add_error("source_request_kind is required");
        return result;
    }
    if (!is_known_platform_spawn_request_kind(plan.source_request_kind)) {
        result.reject(
            std::string(kResolvedPlatformSpawnPlanRejectionUnsupportedSourceRequestKind)
        );
        result.add_error("source_request_kind is outside the maintained WP14-A vocabulary");
        return result;
    }
    if (is_blank(plan.source_type_name)) {
        result.reject(std::string(kResolvedPlatformSpawnPlanRejectionMissingSourceTypeName));
        result.add_error("source_type_name is required");
        return result;
    }
    if (is_blank(plan.capability_bundle_id)) {
        result.reject(std::string(kResolvedPlatformSpawnPlanRejectionMissingBundleId));
        result.add_error("capability_bundle_id is required");
        return result;
    }
    if (plan.source_request_kind == kPlatformSpawnRequestKindTypeNameProjection &&
        !plan.type_name_projection_preserved) {
        result.reject(
            std::string(kResolvedPlatformSpawnPlanRejectionTypeNameProjectionRequired)
        );
        result.add_error("type_name projection requests must preserve the type_name projection path");
        return result;
    }

    if (!plan.admitted) {
        if (is_blank(plan.rejection_reason)) {
            result.reject(
                std::string(kResolvedPlatformSpawnPlanRejectionMissingRejectionReason)
            );
            result.add_error("rejected plans must declare rejection_reason");
            return result;
        }

        result.valid = true;
        return result;
    }

    if (is_blank(plan.resolved_platform_definition_ref)) {
        result.reject(std::string(kResolvedPlatformSpawnPlanRejectionMissingDefinitionRef));
        result.add_error("resolved_platform_definition_ref is required for admitted plans");
        return result;
    }
    if (is_blank(plan.materialization_strategy)) {
        result.reject(
            std::string(
                kResolvedPlatformSpawnPlanRejectionMissingMaterializationStrategy
            )
        );
        result.add_error("materialization_strategy is required");
        return result;
    }
    if (!is_known_platform_materialization_strategy(plan.materialization_strategy)) {
        result.reject(
            std::string(
                kResolvedPlatformSpawnPlanRejectionUnsupportedMaterializationStrategy
            )
        );
        result.add_error(
            "materialization_strategy is outside the maintained WP14-A vocabulary"
        );
        return result;
    }
    if (is_blank(plan.template_evidence_ref)) {
        result.reject(
            std::string(kResolvedPlatformSpawnPlanRejectionMissingTemplateEvidence)
        );
        result.add_error("template_evidence_ref is required");
        return result;
    }
    if (is_blank(plan.resolution_evidence_ref)) {
        result.reject(
            std::string(kResolvedPlatformSpawnPlanRejectionMissingResolutionEvidence)
        );
        result.add_error("resolution_evidence_ref is required");
        return result;
    }
    if (is_blank(plan.materialization_evidence_ref)) {
        result.reject(
            std::string(
                kResolvedPlatformSpawnPlanRejectionMissingMaterializationEvidence
            )
        );
        result.add_error("materialization_evidence_ref is required");
        return result;
    }
    if (plan.evidence_refs.empty() || contains_blank_value(plan.evidence_refs)) {
        result.reject(std::string(kResolvedPlatformSpawnPlanRejectionMissingPlanEvidence));
        result.add_error("evidence_refs is required and cannot contain blank entries");
        return result;
    }
    if (plan.resolved_capabilities.empty()) {
        result.reject(
            std::string(
                kResolvedPlatformSpawnPlanRejectionMissingResolvedCapabilities
            )
        );
        result.add_error("resolved_capabilities cannot be empty for admitted plans");
        return result;
    }

    for (const auto& capability : plan.resolved_capabilities) {
        const auto capability_result = validate_capability(capability);
        if (!capability_result.valid) {
            result.reject(capability_result.rejection_reason);
            for (const auto& error : capability_result.errors) {
                result.add_error("resolved_capability[" + capability.capability_id + "]: " + error);
            }
            return result;
        }

        if (capability.required && !capability.supported) {
            result.reject(
                std::string(
                    kResolvedPlatformSpawnPlanRejectionUnsupportedRequiredCapability
                )
            );
            result.add_error(
                "required capability is unsupported: " + capability.capability_id +
                " (" + capability.unsupported_reason + ")"
            );
            return result;
        }
    }

    result.valid = true;
    return result;
}

}  // namespace runtime::platform_capabilities
