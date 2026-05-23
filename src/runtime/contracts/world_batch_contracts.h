#pragma once

#include <algorithm>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "components/basic/common.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"
#include "core/mission/episode/execution_episode_batch_prepare.h"
#include "runtime/contracts/platform_capability_contracts.h"

struct WorldEntityRef {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
};

struct WorldTerrainAssignment {
    std::uint64_t world_index = 0;
    std::string terrain_type = "flat";
};

struct WorldWindAssignment {
    std::uint64_t world_index = 0;
    double speed_mps = 0.0;
    double dir_from_deg = 0.0;
    double shear_mps_per_km = 0.0;
};

struct WorldZoneDefinition {
    std::uint64_t world_index = 0;
    std::string name = "Zone";
    double x = 0.0;
    double y = 0.0;
    double width = 1000.0;
    double length = 1000.0;
    double heading = 0.0;
    int surface_type = 3;
};

struct WorldSpawnRequest {
    std::uint64_t world_index = 0;
    Side side = Side::Neutral;
    std::string type_name;
    std::string entity_name;
    bool is_agent = false;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    bool ammo_override_enabled = false;
    int missiles_remaining = 0;
    int max_missiles = 0;
    bool weapon_cooldown_override_enabled = false;
    double weapon_cooldown_s = 2.0;
    double weapon_last_fire_time = -1.0;
};

inline constexpr std::string_view kTypedPlatformSpawnRejectionMissingRequestId =
    "typed_platform_spawn_request_id_required";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMissingSourceTypeName =
    "typed_platform_spawn_source_type_name_required";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMissingBundle =
    "typed_platform_spawn_requires_capability_bundle";
inline constexpr std::string_view kTypedPlatformSpawnRejectionInvalidBundle =
    "typed_platform_spawn_capability_bundle_invalid";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMissingResolvedPlan =
    "typed_platform_spawn_requires_resolved_spawn_plan";
inline constexpr std::string_view kTypedPlatformSpawnRejectionInvalidResolvedPlan =
    "typed_platform_spawn_resolved_plan_invalid";
inline constexpr std::string_view kTypedPlatformSpawnRejectionWrongRequestKind =
    "typed_platform_spawn_requires_typed_platform_request_kind";
inline constexpr std::string_view kTypedPlatformSpawnRejectionCompatibilityPathRequired =
    "typed_platform_spawn_requires_type_name_compatibility_path";
inline constexpr std::string_view
    kTypedPlatformSpawnRejectionMaintainedTypedSetupRequired =
        "typed_platform_spawn_requires_maintained_typed_setup";
inline constexpr std::string_view
    kTypedPlatformSpawnRejectionLegacyCompatibilityRequest =
        "typed_platform_spawn_legacy_compatibility_request";
inline constexpr std::string_view
    kTypedPlatformSpawnRejectionMixedSetupSurface =
        "typed_platform_spawn_mixed_typed_setup_and_compatibility_surface";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMissingEvidence =
    "typed_platform_spawn_evidence_required";
inline constexpr std::string_view kTypedPlatformSpawnRejectionWorldIndexOutOfRange =
    "typed_platform_spawn_world_index_out_of_range";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMaterializationFailed =
    "typed_platform_spawn_materialization_failed";
inline constexpr std::string_view kTypedPlatformSetupSurfaceMaintainedTypedSetup =
    "maintained_typed_setup";
inline constexpr std::string_view
    kTypedPlatformSetupSurfaceLegacyCompatibilityRequest =
        "legacy_shaped_compatibility_request";
inline constexpr std::string_view
    kTypedPlatformSetupSurfaceMixedTypedCompatibilityBridge =
        "mixed_typed_setup_compatibility_bridge";
inline constexpr std::string_view kTypedPlatformSetupSurfaceInvalid =
    "invalid_typed_setup_surface";

struct TypedPlatformSpawnRequest {
    std::uint64_t world_index = 0;
    Side side = Side::Neutral;
    std::string request_id;
    std::string source_type_name;
    std::string entity_name;
    bool is_agent = false;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    runtime::platform_capabilities::CapabilityBundle capability_bundle;
    runtime::platform_capabilities::ResolvedPlatformSpawnPlan resolved_spawn_plan;
    std::vector<std::string> facade_evidence_refs;
    bool compatibility_path_preserved = true;
};

struct TypedPlatformSpawnValidationResult {
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

struct TypedPlatformSetupSurfaceEvidence {
    std::string setup_surface = std::string(kTypedPlatformSetupSurfaceInvalid);
    bool maintained_typed_setup = false;
    bool legacy_compatibility_request = false;
    bool mixed_typed_compatibility_bridge = false;
    bool invalid = false;
    std::vector<std::string> reasons;
};

[[nodiscard]] inline TypedPlatformSpawnValidationResult
reject_typed_platform_spawn_request(
    std::string_view reason,
    std::string error
) {
    TypedPlatformSpawnValidationResult result{};
    result.reject(std::string(reason));
    result.add_error(std::move(error));
    return result;
}

[[nodiscard]] inline TypedPlatformSpawnValidationResult
validate_typed_platform_spawn_request_common(
    const TypedPlatformSpawnRequest& request
) {
    namespace platform = runtime::platform_capabilities;

    if (platform::is_blank(request.request_id)) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMissingRequestId,
            "request_id is required"
        );
    }
    if (platform::is_blank(request.source_type_name)) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMissingSourceTypeName,
            "source_type_name is required"
        );
    }
    if (platform::is_blank(request.capability_bundle.bundle_id)) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMissingBundle,
            "capability_bundle is required"
        );
    }

    const platform::PlatformCapabilityValidationResult bundle_result =
        platform::validate_capability_bundle(request.capability_bundle);
    if (!bundle_result.valid) {
        TypedPlatformSpawnValidationResult result =
            reject_typed_platform_spawn_request(
                kTypedPlatformSpawnRejectionInvalidBundle,
                "capability_bundle failed validation"
            );
        if (!bundle_result.rejection_reason.empty()) {
            result.add_error(
                "bundle rejection: " + bundle_result.rejection_reason
            );
        }
        result.errors.insert(
            result.errors.end(),
            bundle_result.errors.begin(),
            bundle_result.errors.end()
        );
        return result;
    }

    if (platform::is_blank(request.resolved_spawn_plan.plan_id)) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMissingResolvedPlan,
            "resolved_spawn_plan is required"
        );
    }
    if (request.resolved_spawn_plan.source_request_kind !=
        platform::kPlatformSpawnRequestKindTypedPlatformRequest) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionWrongRequestKind,
            "resolved_spawn_plan.source_request_kind must be typed_platform_request"
        );
    }

    const platform::PlatformCapabilityValidationResult plan_result =
        platform::validate_resolved_platform_spawn_plan(request.resolved_spawn_plan);
    if (!plan_result.valid) {
        TypedPlatformSpawnValidationResult result =
            reject_typed_platform_spawn_request(
                kTypedPlatformSpawnRejectionInvalidResolvedPlan,
                "resolved_spawn_plan failed validation"
            );
        if (!plan_result.rejection_reason.empty()) {
            result.add_error("plan rejection: " + plan_result.rejection_reason);
        }
        result.errors.insert(
            result.errors.end(),
            plan_result.errors.begin(),
            plan_result.errors.end()
        );
        return result;
    }

    if (request.facade_evidence_refs.empty() ||
        platform::contains_blank_value(request.facade_evidence_refs)) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMissingEvidence,
            "facade_evidence_refs is required and cannot contain blank entries"
        );
    }

    TypedPlatformSpawnValidationResult result{};
    result.valid = true;
    return result;
}

[[nodiscard]] inline bool typed_platform_spawn_preserves_compatibility_path(
    const TypedPlatformSpawnRequest& request
) {
    return request.compatibility_path_preserved ||
        request.capability_bundle.compatibility_path_preserved ||
        request.resolved_spawn_plan.compatibility_path_preserved;
}

[[nodiscard]] inline TypedPlatformSetupSurfaceEvidence
classify_typed_platform_spawn_setup_surface(
    const TypedPlatformSpawnRequest& request
) {
    namespace platform = runtime::platform_capabilities;

    TypedPlatformSetupSurfaceEvidence evidence{};
    const bool typed_request_kind =
        request.resolved_spawn_plan.source_request_kind ==
        platform::kPlatformSpawnRequestKindTypedPlatformRequest;
    const bool compatibility_request_kind =
        request.resolved_spawn_plan.source_request_kind ==
        platform::kPlatformSpawnRequestKindTypeNameCompatibility;
    const bool resolved_spawn_bridge =
        request.resolved_spawn_plan.materialization_strategy ==
        platform::kPlatformMaterializationStrategyResolvedSpawnBridge;
    const bool factory_compatibility_materialization =
        request.resolved_spawn_plan.materialization_strategy ==
        platform::kPlatformMaterializationStrategyFactoryCompatibility;
    const bool compatibility_path_preserved =
        typed_platform_spawn_preserves_compatibility_path(request);

    if (typed_request_kind) {
        evidence.reasons.push_back("typed_platform_request");
    }
    if (compatibility_request_kind) {
        evidence.reasons.push_back("type_name_compatibility");
    }
    if (resolved_spawn_bridge) {
        evidence.reasons.push_back("resolved_spawn_plan_bridge");
    }
    if (factory_compatibility_materialization) {
        evidence.reasons.push_back("factory_compatibility_materialization");
    }
    if (compatibility_path_preserved) {
        evidence.reasons.push_back("compatibility_path_preserved");
    }

    if (typed_request_kind && resolved_spawn_bridge &&
        !factory_compatibility_materialization &&
        !compatibility_request_kind &&
        !compatibility_path_preserved) {
        evidence.setup_surface =
            std::string(kTypedPlatformSetupSurfaceMaintainedTypedSetup);
        evidence.maintained_typed_setup = true;
        return evidence;
    }

    if (!typed_request_kind &&
        compatibility_request_kind &&
        factory_compatibility_materialization &&
        compatibility_path_preserved) {
        evidence.setup_surface = std::string(
            kTypedPlatformSetupSurfaceLegacyCompatibilityRequest
        );
        evidence.legacy_compatibility_request = true;
        return evidence;
    }

    if ((typed_request_kind || resolved_spawn_bridge) &&
        (compatibility_request_kind ||
         factory_compatibility_materialization ||
         compatibility_path_preserved)) {
        evidence.setup_surface = std::string(
            kTypedPlatformSetupSurfaceMixedTypedCompatibilityBridge
        );
        evidence.mixed_typed_compatibility_bridge = true;
        return evidence;
    }

    evidence.invalid = true;
    return evidence;
}

[[nodiscard]] inline TypedPlatformSpawnValidationResult
validate_typed_platform_spawn_request(const TypedPlatformSpawnRequest& request) {
    TypedPlatformSpawnValidationResult result =
        validate_typed_platform_spawn_request_common(request);
    if (!result.valid) {
        return result;
    }

    if (!request.compatibility_path_preserved ||
        !request.capability_bundle.compatibility_path_preserved ||
        !request.resolved_spawn_plan.compatibility_path_preserved) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionCompatibilityPathRequired,
            "typed platform setup must preserve the type_name compatibility path"
        );
    }

    result.valid = true;
    return result;
}

[[nodiscard]] inline TypedPlatformSpawnValidationResult
validate_maintained_typed_platform_spawn_request(
    const TypedPlatformSpawnRequest& request
) {
    TypedPlatformSpawnValidationResult result =
        validate_typed_platform_spawn_request_common(request);
    if (!result.valid) {
        return result;
    }

    const TypedPlatformSetupSurfaceEvidence surface =
        classify_typed_platform_spawn_setup_surface(request);
    if (surface.maintained_typed_setup) {
        result.valid = true;
        return result;
    }

    TypedPlatformSpawnValidationResult rejection{};
    if (surface.legacy_compatibility_request) {
        rejection = reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionLegacyCompatibilityRequest,
            "typed platform setup remains a legacy-shaped compatibility request"
        );
    } else if (surface.mixed_typed_compatibility_bridge) {
        rejection = reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMixedSetupSurface,
            "typed platform setup mixes maintained typed setup with compatibility preservation"
        );
    } else {
        rejection = reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMaintainedTypedSetupRequired,
            "typed platform setup must declare maintained typed setup semantics"
        );
    }

    rejection.errors.insert(
        rejection.errors.end(),
        surface.reasons.begin(),
        surface.reasons.end()
    );
    return rejection;
}

[[nodiscard]] inline std::vector<std::string>
collect_typed_platform_spawn_evidence_refs(
    const TypedPlatformSpawnRequest& request
) {
    namespace platform = runtime::platform_capabilities;

    std::vector<std::string> evidence_refs{};
    evidence_refs.reserve(
        request.facade_evidence_refs.size() +
        request.capability_bundle.evidence_refs.size() +
        request.resolved_spawn_plan.evidence_refs.size() + 4
    );

    const auto append_if_present = [&](const std::string& ref) {
        if (platform::is_blank(ref)) {
            return;
        }
        if (std::find(evidence_refs.begin(), evidence_refs.end(), ref) !=
            evidence_refs.end()) {
            return;
        }
        evidence_refs.push_back(ref);
    };

    const auto append_many = [&](const std::vector<std::string>& refs) {
        for (const std::string& ref : refs) {
            append_if_present(ref);
        }
    };

    append_many(request.facade_evidence_refs);
    append_if_present(request.capability_bundle.template_evidence_ref);
    append_many(request.capability_bundle.evidence_refs);
    append_if_present(request.resolved_spawn_plan.template_evidence_ref);
    append_if_present(request.resolved_spawn_plan.resolution_evidence_ref);
    append_if_present(request.resolved_spawn_plan.materialization_evidence_ref);
    append_many(request.resolved_spawn_plan.evidence_refs);
    return evidence_refs;
}

struct TypedPlatformSpawnAdmission {
    std::uint64_t request_index = 0;
    std::uint64_t world_index = 0;
    bool admitted = false;
    bool fail_closed = false;
    std::string request_id;
    std::string source_type_name;
    std::string plan_id;
    std::string capability_bundle_id;
    std::string rejection_reason;
    std::vector<std::string> errors;
    std::vector<std::string> evidence_refs;

    void reject(std::string reason) {
        admitted = false;
        fail_closed = true;
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }

    void add_error(std::string error) {
        errors.push_back(std::move(error));
    }
};

struct TypedPlatformSpawnResult {
    std::uint64_t request_index = 0;
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    bool admitted = false;
    bool materialized = false;
    bool fail_closed = false;
    std::string request_id;
    std::string source_type_name;
    std::string plan_id;
    std::string capability_bundle_id;
    std::string setup_surface;
    std::string rejection_reason;
    std::vector<std::string> errors;
    std::vector<std::string> evidence_refs;

    void reject(std::string reason) {
        admitted = false;
        materialized = false;
        fail_closed = true;
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }

    void add_error(std::string error) {
        errors.push_back(std::move(error));
    }
};

[[nodiscard]] inline TypedPlatformSpawnAdmission
make_typed_platform_spawn_admission(
    std::uint64_t request_index,
    const TypedPlatformSpawnRequest& request
) {
    TypedPlatformSpawnAdmission admission{};
    admission.request_index = request_index;
    admission.world_index = request.world_index;
    admission.request_id = request.request_id;
    admission.source_type_name = request.source_type_name;
    admission.plan_id = request.resolved_spawn_plan.plan_id;
    admission.capability_bundle_id = request.capability_bundle.bundle_id;
    admission.evidence_refs = collect_typed_platform_spawn_evidence_refs(request);
    return admission;
}

[[nodiscard]] inline TypedPlatformSpawnResult
make_typed_platform_spawn_result(
    const TypedPlatformSpawnAdmission& admission
) {
    TypedPlatformSpawnResult result{};
    result.request_index = admission.request_index;
    result.world_index = admission.world_index;
    result.admitted = admission.admitted;
    result.fail_closed = admission.fail_closed;
    result.request_id = admission.request_id;
    result.source_type_name = admission.source_type_name;
    result.plan_id = admission.plan_id;
    result.capability_bundle_id = admission.capability_bundle_id;
    result.setup_surface = std::string(kTypedPlatformSetupSurfaceInvalid);
    result.rejection_reason = admission.rejection_reason;
    result.errors = admission.errors;
    result.evidence_refs = admission.evidence_refs;
    return result;
}

struct WorldPilotActionAssignment {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    PilotAction action{};
};

struct WorldMissionCommandAssignment {
    using shell_type = MissionCommandCompatibilityTransportShell;
    static constexpr bool kCompatibilityTransportShell =
        kMissionCommandCompatibilityTransportShell;
    static_assert(
        kCompatibilityTransportShell,
        "WorldMissionCommandAssignment transports only the MissionCommand compatibility shell."
    );

    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    shell_type command{};
};

struct WorldTaskOrderAssignment {
    using shell_type = TaskOrderCompatibilityTransportShell;
    static constexpr bool kCompatibilityTransportShell =
        kTaskOrderCompatibilityTransportShell;
    static_assert(
        kCompatibilityTransportShell,
        "WorldTaskOrderAssignment transports only the TaskOrder compatibility shell."
    );

    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    shell_type order{};
};

struct WorldLeaderIntentAssignment {
    using shell_type = LeaderIntentCompatibilityTransportShell;
    static constexpr bool kCompatibilityTransportShell =
        kLeaderIntentCompatibilityTransportShell;
    static_assert(
        kCompatibilityTransportShell,
        "WorldLeaderIntentAssignment transports only the LeaderIntent compatibility shell."
    );

    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    shell_type intent{};
};

struct WorldPilotReportAssignment {
    using shell_type = PilotReportCompatibilityTransportShell;
    static constexpr bool kCompatibilityTransportShell =
        kPilotReportCompatibilityTransportShell;
    static_assert(
        kCompatibilityTransportShell,
        "WorldPilotReportAssignment transports only the PilotReport compatibility shell."
    );

    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    shell_type report{};
};

[[nodiscard]] inline const MissionCommandCompatibilityTransportShell&
world_batch_assignment_compatibility_shell(
    const WorldMissionCommandAssignment& assignment
) noexcept {
    return assignment.command;
}

[[nodiscard]] inline MissionCommandCompatibilityTransportShell&
world_batch_assignment_compatibility_shell(
    WorldMissionCommandAssignment& assignment
) noexcept {
    return assignment.command;
}

[[nodiscard]] inline const TaskOrderCompatibilityTransportShell&
world_batch_assignment_compatibility_shell(
    const WorldTaskOrderAssignment& assignment
) noexcept {
    return assignment.order;
}

[[nodiscard]] inline TaskOrderCompatibilityTransportShell&
world_batch_assignment_compatibility_shell(WorldTaskOrderAssignment& assignment) noexcept {
    return assignment.order;
}

[[nodiscard]] inline const LeaderIntentCompatibilityTransportShell&
world_batch_assignment_compatibility_shell(
    const WorldLeaderIntentAssignment& assignment
) noexcept {
    return assignment.intent;
}

[[nodiscard]] inline LeaderIntentCompatibilityTransportShell&
world_batch_assignment_compatibility_shell(
    WorldLeaderIntentAssignment& assignment
) noexcept {
    return assignment.intent;
}

[[nodiscard]] inline const PilotReportCompatibilityTransportShell&
world_batch_assignment_compatibility_shell(
    const WorldPilotReportAssignment& assignment
) noexcept {
    return assignment.report;
}

[[nodiscard]] inline PilotReportCompatibilityTransportShell&
world_batch_assignment_compatibility_shell(
    WorldPilotReportAssignment& assignment
) noexcept {
    return assignment.report;
}

struct WorldExecutionEpisodeStepRequest {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    StepEvaluationBatchConfig config{};
    StepEvaluationBatchEnvState env_state{};
};
