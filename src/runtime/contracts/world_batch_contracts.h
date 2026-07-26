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
#define EF_WORLD_ENTITY_REF_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_entity_ref.inc"
};

struct WorldTerrainAssignment {
#define EF_WORLD_TERRAIN_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_terrain_assignment.inc"
};

struct WorldWindAssignment {
#define EF_WORLD_WIND_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_wind_assignment.inc"
};

// Sun direction driving optical glare. Defaults preserve the historical
// fixed vector (north azimuth, 45 deg elevation).
struct WorldSunAssignment {
    std::uint64_t world_index = 0;
    double azimuth_deg = 0.0;
    double elevation_deg = 45.0;
};

struct WorldZoneDefinition {
#define EF_WORLD_ZONE_DEFINITION_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_zone_definition.inc"
};

struct WorldSpawnRequest {
#define EF_WORLD_SPAWN_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_spawn_request.inc"
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
inline constexpr std::string_view kTypedPlatformSpawnRejectionTypeNameProjectionRequired =
    "typed_platform_spawn_requires_type_name_projection_path";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMaintainedTypedSetupRequired =
    "typed_platform_spawn_requires_maintained_typed_setup";
inline constexpr std::string_view kTypedPlatformSpawnRejectionTypeNameProjectionRequest =
    "typed_platform_spawn_type_name_projection_request";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMixedSetupSurface =
    "typed_platform_spawn_mixed_typed_setup_and_type_name_projection_surface";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMissingEvidence =
    "typed_platform_spawn_evidence_required";
inline constexpr std::string_view kTypedPlatformSpawnRejectionWorldIndexOutOfRange =
    "typed_platform_spawn_world_index_out_of_range";
inline constexpr std::string_view kTypedPlatformSpawnRejectionMaterializationFailed =
    "typed_platform_spawn_materialization_failed";
inline constexpr std::string_view kTypedPlatformSetupSurfaceMaintainedTypedSetup =
    "maintained_typed_setup";
inline constexpr std::string_view kTypedPlatformSetupSurfaceTypeNameProjectionRequest =
    "type_name_projection_request";
inline constexpr std::string_view kTypedPlatformSetupSurfaceMixedTypedProjectionBridge =
    "mixed_typed_setup_type_name_projection_bridge";
inline constexpr std::string_view kTypedPlatformSetupSurfaceInvalid = "invalid_typed_setup_surface";

struct TypedPlatformSpawnRequest {
#define EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/typed_platform_spawn_request.inc"
};

struct TypedPlatformSpawnValidationResult {
#define EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/contracts/detail/typed_platform_spawn_validation_result.inc"

    void reject(std::string reason) {
        valid = false;
        fail_closed = true;
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }

    void add_error(std::string error) { errors.push_back(std::move(error)); }
};

struct TypedPlatformSetupSurfaceEvidence {
    std::string setup_surface = std::string(kTypedPlatformSetupSurfaceInvalid);
    bool maintained_typed_setup = false;
    bool type_name_projection_request = false;
    bool mixed_typed_projection_bridge = false;
    bool invalid = false;
    std::vector<std::string> reasons;
};

[[nodiscard]] inline TypedPlatformSpawnValidationResult
reject_typed_platform_spawn_request(std::string_view reason, std::string error) {
    TypedPlatformSpawnValidationResult result{};
    result.reject(std::string(reason));
    result.add_error(std::move(error));
    return result;
}

[[nodiscard]] inline TypedPlatformSpawnValidationResult
validate_typed_platform_spawn_request_common(const TypedPlatformSpawnRequest &request) {
    namespace platform = runtime::platform_capabilities;

    if (platform::is_blank(request.request_id)) {
        return reject_typed_platform_spawn_request(kTypedPlatformSpawnRejectionMissingRequestId,
                                                   "request_id is required");
    }
    if (platform::is_blank(request.source_type_name)) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMissingSourceTypeName, "source_type_name is required");
    }
    if (platform::is_blank(request.capability_bundle.bundle_id)) {
        return reject_typed_platform_spawn_request(kTypedPlatformSpawnRejectionMissingBundle,
                                                   "capability_bundle is required");
    }

    const platform::PlatformCapabilityValidationResult bundle_result =
        platform::validate_capability_bundle(request.capability_bundle);
    if (!bundle_result.valid) {
        TypedPlatformSpawnValidationResult result = reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionInvalidBundle, "capability_bundle failed validation");
        if (!bundle_result.rejection_reason.empty()) {
            result.add_error("bundle rejection: " + bundle_result.rejection_reason);
        }
        result.errors.insert(result.errors.end(), bundle_result.errors.begin(),
                             bundle_result.errors.end());
        return result;
    }

    if (platform::is_blank(request.resolved_spawn_plan.plan_id)) {
        return reject_typed_platform_spawn_request(kTypedPlatformSpawnRejectionMissingResolvedPlan,
                                                   "resolved_spawn_plan is required");
    }
    if (request.resolved_spawn_plan.source_request_kind !=
        platform::kPlatformSpawnRequestKindTypedPlatformRequest) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionWrongRequestKind,
            "resolved_spawn_plan.source_request_kind must be typed_platform_request");
    }

    const platform::PlatformCapabilityValidationResult plan_result =
        platform::validate_resolved_platform_spawn_plan(request.resolved_spawn_plan);
    if (!plan_result.valid) {
        TypedPlatformSpawnValidationResult result =
            reject_typed_platform_spawn_request(kTypedPlatformSpawnRejectionInvalidResolvedPlan,
                                                "resolved_spawn_plan failed validation");
        if (!plan_result.rejection_reason.empty()) {
            result.add_error("plan rejection: " + plan_result.rejection_reason);
        }
        result.errors.insert(result.errors.end(), plan_result.errors.begin(),
                             plan_result.errors.end());
        return result;
    }

    if (request.facade_evidence_refs.empty() ||
        platform::contains_blank_value(request.facade_evidence_refs)) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMissingEvidence,
            "facade_evidence_refs is required and cannot contain blank entries");
    }

    TypedPlatformSpawnValidationResult result{};
    result.valid = true;
    return result;
}

[[nodiscard]] inline bool
typed_platform_spawn_preserves_type_name_projection(const TypedPlatformSpawnRequest &request) {
    return request.type_name_projection_preserved ||
           request.capability_bundle.type_name_projection_preserved ||
           request.resolved_spawn_plan.type_name_projection_preserved;
}

[[nodiscard]] inline TypedPlatformSetupSurfaceEvidence
classify_typed_platform_spawn_setup_surface(const TypedPlatformSpawnRequest &request) {
    namespace platform = runtime::platform_capabilities;

    TypedPlatformSetupSurfaceEvidence evidence{};
    const bool typed_request_kind = request.resolved_spawn_plan.source_request_kind ==
                                    platform::kPlatformSpawnRequestKindTypedPlatformRequest;
    const bool type_name_projection_request_kind =
        request.resolved_spawn_plan.source_request_kind ==
        platform::kPlatformSpawnRequestKindTypeNameProjection;
    const bool resolved_spawn_bridge =
        request.resolved_spawn_plan.materialization_strategy ==
        platform::kPlatformMaterializationStrategyResolvedSpawnBridge;
    const bool factory_projection_materialization =
        request.resolved_spawn_plan.materialization_strategy ==
        platform::kPlatformMaterializationStrategyFactoryProjection;
    const bool type_name_projection_preserved =
        typed_platform_spawn_preserves_type_name_projection(request);

    if (typed_request_kind) {
        evidence.reasons.push_back("typed_platform_request");
    }
    if (type_name_projection_request_kind) {
        evidence.reasons.push_back("type_name_projection");
    }
    if (resolved_spawn_bridge) {
        evidence.reasons.push_back("resolved_spawn_plan_bridge");
    }
    if (factory_projection_materialization) {
        evidence.reasons.push_back("factory_projection_materialization");
    }
    if (type_name_projection_preserved) {
        evidence.reasons.push_back("type_name_projection_preserved");
    }

    if (typed_request_kind && resolved_spawn_bridge && !factory_projection_materialization &&
        !type_name_projection_request_kind && !type_name_projection_preserved) {
        evidence.setup_surface = std::string(kTypedPlatformSetupSurfaceMaintainedTypedSetup);
        evidence.maintained_typed_setup = true;
        return evidence;
    }

    if (!typed_request_kind && type_name_projection_request_kind &&
        factory_projection_materialization && type_name_projection_preserved) {
        evidence.setup_surface = std::string(kTypedPlatformSetupSurfaceTypeNameProjectionRequest);
        evidence.type_name_projection_request = true;
        return evidence;
    }

    if ((typed_request_kind || resolved_spawn_bridge) &&
        (type_name_projection_request_kind || factory_projection_materialization ||
         type_name_projection_preserved)) {
        evidence.setup_surface = std::string(kTypedPlatformSetupSurfaceMixedTypedProjectionBridge);
        evidence.mixed_typed_projection_bridge = true;
        return evidence;
    }

    evidence.invalid = true;
    return evidence;
}

[[nodiscard]] inline TypedPlatformSpawnValidationResult
validate_typed_platform_spawn_request(const TypedPlatformSpawnRequest &request) {
    TypedPlatformSpawnValidationResult result =
        validate_typed_platform_spawn_request_common(request);
    if (!result.valid) {
        return result;
    }

    if (!request.type_name_projection_preserved ||
        !request.capability_bundle.type_name_projection_preserved ||
        !request.resolved_spawn_plan.type_name_projection_preserved) {
        return reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionTypeNameProjectionRequired,
            "typed platform setup must preserve the type_name projection path");
    }

    result.valid = true;
    return result;
}

[[nodiscard]] inline TypedPlatformSpawnValidationResult
validate_maintained_typed_platform_spawn_request(const TypedPlatformSpawnRequest &request) {
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
    if (surface.type_name_projection_request) {
        rejection = reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionTypeNameProjectionRequest,
            "typed platform setup remains a type_name projection request");
    } else if (surface.mixed_typed_projection_bridge) {
        rejection =
            reject_typed_platform_spawn_request(kTypedPlatformSpawnRejectionMixedSetupSurface,
                                                "typed platform setup mixes maintained typed setup "
                                                "with type_name projection preservation");
    } else {
        rejection = reject_typed_platform_spawn_request(
            kTypedPlatformSpawnRejectionMaintainedTypedSetupRequired,
            "typed platform setup must declare maintained typed setup semantics");
    }

    rejection.errors.insert(rejection.errors.end(), surface.reasons.begin(), surface.reasons.end());
    return rejection;
}

[[nodiscard]] inline std::vector<std::string>
collect_typed_platform_spawn_evidence_refs(const TypedPlatformSpawnRequest &request) {
    namespace platform = runtime::platform_capabilities;

    std::vector<std::string> evidence_refs{};
    evidence_refs.reserve(request.facade_evidence_refs.size() +
                          request.capability_bundle.evidence_refs.size() +
                          request.resolved_spawn_plan.evidence_refs.size() + 4);

    const auto append_if_present = [&](const std::string &ref) {
        if (platform::is_blank(ref)) {
            return;
        }
        if (std::find(evidence_refs.begin(), evidence_refs.end(), ref) != evidence_refs.end()) {
            return;
        }
        evidence_refs.push_back(ref);
    };

    const auto append_many = [&](const std::vector<std::string> &refs) {
        for (const std::string &ref : refs) {
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

    void add_error(std::string error) { errors.push_back(std::move(error)); }
};

struct TypedPlatformSpawnResult {
#define EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/typed_platform_spawn_result.inc"

    void reject(std::string reason) {
        admitted = false;
        materialized = false;
        fail_closed = true;
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }

    void add_error(std::string error) { errors.push_back(std::move(error)); }
};

[[nodiscard]] inline TypedPlatformSpawnAdmission
make_typed_platform_spawn_admission(std::uint64_t request_index,
                                    const TypedPlatformSpawnRequest &request) {
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
make_typed_platform_spawn_result(const TypedPlatformSpawnAdmission &admission) {
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
#define EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_pilot_action_assignment.inc"
};

struct WorldMissionCommandAssignment {
    using shell_type = MissionCommandCompatibilityTransportShell;
    static constexpr bool kCompatibilityTransportShell = kMissionCommandCompatibilityTransportShell;
    static_assert(
        kCompatibilityTransportShell,
        "WorldMissionCommandAssignment transports only the MissionCommand compatibility shell.");

#define EF_WORLD_MISSION_COMMAND_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_mission_command_assignment.inc"
};

struct MissionCommandMaintainedBatchContract {
    using shared_core_owner_slice = MissionCommandSharedCoreOwnerSlice;
    using air_owner_slice = MissionCommandAirOwnerSlice;
    using naval_owner_slice = MissionCommandNavalOwnerSlice;
    using ground_owner_slice = MissionCommandGroundOwnerSlice;
    using shared_core_type = MissionCommandSharedCoreDirective;
    using air_recovery_type = MissionCommandAir::RecoveryDirective;
    using air_takeoff_type = MissionCommandAir::TakeoffDirective;
    using air_formation_type = MissionCommandAir::FormationDirective;
    using naval_stationing_type = MissionCommandNaval::StationingDirective;
    using naval_embarked_helo_type = MissionCommandNaval::EmbarkedHeloDirective;
    using ground_static_task_type = MissionCommandGround::StaticTaskDirective;
    static constexpr bool kMaintainedBatchTruth = true;

#define EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/mission_command_maintained_batch_contract.inc"

    static_assert(kMaintainedBatchTruth, "MissionCommandMaintainedBatchContract is the controlled "
                                         "MissionCommand maintained batch read/write shape.");
};

[[nodiscard]] inline MissionCommandMaintainedBatchContract
mission_command_maintained_batch_contract(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return {
        .shared_core = mission_command_shared_core_directive(command),
        .air_recovery = mission_command_air_recovery_directive(command),
        .air_takeoff = mission_command_air_takeoff_directive(command),
        .air_formation = mission_command_air_formation_directive(command),
        .naval_stationing = mission_command_naval_stationing_directive(command),
        .naval_embarked_helo = mission_command_naval_embarked_helo_directive(command),
        .ground_static_task = mission_command_ground_static_task_directive(command),
    };
}

inline void apply_mission_command_maintained_batch_contract_to_compatibility_shell(
    MissionCommandCompatibilityTransportShell &command,
    const MissionCommandMaintainedBatchContract &contract) noexcept {
    mission_command_shared_core(command) = contract.shared_core;

    auto &air = mission_command_air_owner_slice(command);
    air.recovery_base_id = contract.air_recovery.recovery_base_id;
    air.recovery_runway_id = contract.air_recovery.recovery_runway_id;
    air.recovery_approach_type = contract.air_recovery.recovery_approach_type;
    air.takeoff_procedure_id = contract.air_takeoff.takeoff_procedure_id;
    air.takeoff_clearance_id = contract.air_takeoff.takeoff_clearance_id;
    air.takeoff_interval_s = contract.air_takeoff.takeoff_interval_s;
    air.runway_slot_id = contract.air_takeoff.runway_slot_id;
    air.formation_id = contract.air_formation.formation_id;
    air.form_offset_x = contract.air_formation.form_offset_x;
    air.form_offset_y = contract.air_formation.form_offset_y;
    air.form_offset_z = contract.air_formation.form_offset_z;

    auto &naval = mission_command_naval_owner_slice(command);
    naval.reference_entity_id = contract.naval_stationing.reference_entity_id;
    naval.station_radius_m = contract.naval_stationing.station_radius_m;
    naval.station_bearing_deg = contract.naval_stationing.station_bearing_deg;
    naval.embarked_helo_entity_id = contract.naval_embarked_helo.embarked_helo_entity_id;
    naval.launch_helo = contract.naval_embarked_helo.launch_helo;
    naval.recover_helo = contract.naval_embarked_helo.recover_helo;
    naval.relay_oth_targeting = contract.naval_embarked_helo.relay_oth_targeting;

    auto &ground = mission_command_ground_owner_slice(command);
    ground.ground_task_mode = contract.ground_static_task.ground_task_mode;
    ground.objective_area_id = contract.ground_static_task.objective_area_id;
    ground.objective_node_id = contract.ground_static_task.objective_node_id;
    ground.ground_commander_id = contract.ground_static_task.ground_commander_id;
    ground.tactical_cadence_hz = contract.ground_static_task.tactical_cadence_hz;
}

[[nodiscard]] inline MissionCommandCompatibilityTransportShell
mission_command_compatibility_shell_from_maintained_batch_contract(
    const MissionCommandMaintainedBatchContract &contract) noexcept {
    MissionCommandCompatibilityTransportShell compatibility_shell{};
    apply_mission_command_maintained_batch_contract_to_compatibility_shell(compatibility_shell,
                                                                           contract);
    return compatibility_shell;
}

struct WorldMissionCommandMaintainedAssignment {
    using contract_type = MissionCommandMaintainedBatchContract;
    static constexpr bool kMaintainedBatchTruth = contract_type::kMaintainedBatchTruth;
    static_assert(kMaintainedBatchTruth,
                  "WorldMissionCommandMaintainedAssignment transports only the controlled "
                  "MissionCommand maintained batch contract.");

#define EF_WORLD_MISSION_COMMAND_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_mission_command_maintained_assignment.inc"
};

struct TaskOrderAirTaskingIdentityDirective {
#define EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/task_order_air_tasking_identity_directive.inc"

    bool operator==(const TaskOrderAirTaskingIdentityDirective &) const = default;
};

struct TaskOrderAirStationingDirective {
#define EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/task_order_air_stationing_directive.inc"

    bool operator==(const TaskOrderAirStationingDirective &) const = default;
};

struct TaskOrderAirFormationDirective {
#define EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/task_order_air_formation_directive.inc"

    bool operator==(const TaskOrderAirFormationDirective &) const = default;
};

struct TaskOrderNavalStationingDirective {
#define EF_TASK_ORDER_NAVAL_STATIONING_DIRECTIVE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/task_order_naval_stationing_directive.inc"

    bool operator==(const TaskOrderNavalStationingDirective &) const = default;
};

[[nodiscard]] inline TaskOrderAirTaskingIdentityDirective
task_order_air_tasking_identity_directive(const TaskOrderAirOwnerSlice &air) noexcept {
    return {
        .task_type = air.task_type,
        .element_id = air.element_id,
        .package_id = air.package_id,
        .lead_aircraft_id = air.lead_aircraft_id,
    };
}

[[nodiscard]] inline TaskOrderAirTaskingIdentityDirective task_order_air_tasking_identity_directive(
    const TaskOrderCompatibilityTransportShell &order) noexcept {
    return task_order_air_tasking_identity_directive(task_order_air_owner_slice(order));
}

[[nodiscard]] inline TaskOrderAirStationingDirective
task_order_air_stationing_directive(const TaskOrderAirOwnerSlice &air) noexcept {
    return {
        .anchor_x_m = air.anchor_x_m,
        .anchor_y_m = air.anchor_y_m,
        .anchor_z_m = air.anchor_z_m,
        .station_type = air.station_type,
        .station_radius_m = air.station_radius_m,
        .station_leg_length_m = air.station_leg_length_m,
        .station_heading_deg = air.station_heading_deg,
        .altitude_block_min_m = air.altitude_block_min_m,
        .altitude_block_max_m = air.altitude_block_max_m,
        .target_altitude_m = air.target_altitude_m,
        .speed_min_mps = air.speed_min_mps,
        .speed_max_mps = air.speed_max_mps,
        .target_speed_mps = air.target_speed_mps,
        .entry_condition_code = air.entry_condition_code,
        .exit_condition_code = air.exit_condition_code,
        .on_station_time_s = air.on_station_time_s,
        .fuel_bingo_override_kg = air.fuel_bingo_override_kg,
    };
}

[[nodiscard]] inline TaskOrderAirStationingDirective
task_order_air_stationing_directive(const TaskOrderCompatibilityTransportShell &order) noexcept {
    return task_order_air_stationing_directive(task_order_air_owner_slice(order));
}

[[nodiscard]] inline TaskOrderAirFormationDirective
task_order_air_formation_directive(const TaskOrderAirOwnerSlice &air) noexcept {
    return {
        .formation_template_id = air.formation_template_id,
        .formation_contract_id = air.formation_contract_id,
        .formation_role_id = air.formation_role_id,
        .wingman_slot_id = air.wingman_slot_id,
        .join_policy_id = air.join_policy_id,
        .rejoin_policy_id = air.rejoin_policy_id,
        .mutual_support_mode = air.mutual_support_mode,
        .support_sector_id = air.support_sector_id,
    };
}

[[nodiscard]] inline TaskOrderAirFormationDirective
task_order_air_formation_directive(const TaskOrderCompatibilityTransportShell &order) noexcept {
    return task_order_air_formation_directive(task_order_air_owner_slice(order));
}

[[nodiscard]] inline TaskOrderNavalStationingDirective
task_order_naval_stationing_directive(const TaskOrderNavalOwnerSlice &naval) noexcept {
    return {
        .naval_station_type = naval.naval_station_type,
    };
}

[[nodiscard]] inline TaskOrderNavalStationingDirective
task_order_naval_stationing_directive(const TaskOrderCompatibilityTransportShell &order) noexcept {
    return task_order_naval_stationing_directive(task_order_naval_owner_slice(order));
}

inline void apply_task_order_air_tasking_identity_directive(
    TaskOrderAirOwnerSlice &air, const TaskOrderAirTaskingIdentityDirective &directive) noexcept {
    air.task_type = directive.task_type;
    air.element_id = directive.element_id;
    air.package_id = directive.package_id;
    air.lead_aircraft_id = directive.lead_aircraft_id;
}

inline void apply_task_order_air_stationing_directive(
    TaskOrderAirOwnerSlice &air, const TaskOrderAirStationingDirective &directive) noexcept {
    air.anchor_x_m = directive.anchor_x_m;
    air.anchor_y_m = directive.anchor_y_m;
    air.anchor_z_m = directive.anchor_z_m;
    air.station_type = directive.station_type;
    air.station_radius_m = directive.station_radius_m;
    air.station_leg_length_m = directive.station_leg_length_m;
    air.station_heading_deg = directive.station_heading_deg;
    air.altitude_block_min_m = directive.altitude_block_min_m;
    air.altitude_block_max_m = directive.altitude_block_max_m;
    air.target_altitude_m = directive.target_altitude_m;
    air.speed_min_mps = directive.speed_min_mps;
    air.speed_max_mps = directive.speed_max_mps;
    air.target_speed_mps = directive.target_speed_mps;
    air.entry_condition_code = directive.entry_condition_code;
    air.exit_condition_code = directive.exit_condition_code;
    air.on_station_time_s = directive.on_station_time_s;
    air.fuel_bingo_override_kg = directive.fuel_bingo_override_kg;
}

inline void
apply_task_order_air_recovery_directive(TaskOrderAirOwnerSlice &air,
                                        const TaskOrderAir::RecoveryDirective &directive) noexcept {
    air.recovery_base_id = directive.recovery_base_id;
    air.recovery_runway_id = directive.recovery_runway_id;
    air.recovery_approach_type = directive.recovery_approach_type;
}

inline void
apply_task_order_air_takeoff_directive(TaskOrderAirOwnerSlice &air,
                                       const TaskOrderAir::TakeoffDirective &directive) noexcept {
    air.takeoff_procedure_id = directive.takeoff_procedure_id;
    air.takeoff_clearance_id = directive.takeoff_clearance_id;
    air.takeoff_interval_s = directive.takeoff_interval_s;
    air.runway_slot_id = directive.runway_slot_id;
}

inline void
apply_task_order_air_formation_directive(TaskOrderAirOwnerSlice &air,
                                         const TaskOrderAirFormationDirective &directive) noexcept {
    air.formation_template_id = directive.formation_template_id;
    air.formation_contract_id = directive.formation_contract_id;
    air.formation_role_id = directive.formation_role_id;
    air.wingman_slot_id = directive.wingman_slot_id;
    air.join_policy_id = directive.join_policy_id;
    air.rejoin_policy_id = directive.rejoin_policy_id;
    air.mutual_support_mode = directive.mutual_support_mode;
    air.support_sector_id = directive.support_sector_id;
}

inline void apply_task_order_naval_command_authority_directive(
    TaskOrderNavalOwnerSlice &naval,
    const TaskOrderNaval::CommandAuthorityDirective &directive) noexcept {
    naval.warfare_role_code = directive.warfare_role_code;
    naval.officer_in_tactical_command = directive.officer_in_tactical_command;
}

inline void apply_task_order_naval_stationing_directive(
    TaskOrderNavalOwnerSlice &naval, const TaskOrderNavalStationingDirective &directive) noexcept {
    naval.naval_station_type = directive.naval_station_type;
}

inline void apply_task_order_ground_static_task_directive(
    TaskOrderGroundOwnerSlice &ground,
    const TaskOrderGround::StaticTaskDirective &directive) noexcept {
    ground.ground_task_mode = directive.ground_task_mode;
    ground.objective_area_id = directive.objective_area_id;
    ground.objective_node_id = directive.objective_node_id;
    ground.ground_commander_id = directive.ground_commander_id;
    ground.tactical_cadence_hz = directive.tactical_cadence_hz;
}

struct TaskOrderMaintainedBatchContract {
    using shared_core_owner_slice = TaskOrderSharedCoreOwnerSlice;
    using air_owner_slice = TaskOrderAirOwnerSlice;
    using naval_owner_slice = TaskOrderNavalOwnerSlice;
    using ground_owner_slice = TaskOrderGroundOwnerSlice;
    using shared_core_type = TaskOrderSharedCoreDirective;
    using air_tasking_identity_type = TaskOrderAirTaskingIdentityDirective;
    using air_stationing_type = TaskOrderAirStationingDirective;
    using air_recovery_type = TaskOrderAir::RecoveryDirective;
    using air_takeoff_type = TaskOrderAir::TakeoffDirective;
    using air_formation_type = TaskOrderAirFormationDirective;
    using naval_command_authority_type = TaskOrderNaval::CommandAuthorityDirective;
    using naval_stationing_type = TaskOrderNavalStationingDirective;
    using ground_static_task_type = TaskOrderGround::StaticTaskDirective;
    static constexpr bool kMaintainedBatchTruth = true;

#define EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/task_order_maintained_batch_contract.inc"

    static_assert(kMaintainedBatchTruth, "TaskOrderMaintainedBatchContract is the controlled "
                                         "TaskOrder maintained batch read/write shape.");
};

[[nodiscard]] inline TaskOrderMaintainedBatchContract
task_order_maintained_batch_contract(const TaskOrderCompatibilityTransportShell &order) noexcept {
    return {
        .shared_core = task_order_shared_core_directive(order),
        .air_tasking_identity = task_order_air_tasking_identity_directive(order),
        .air_stationing = task_order_air_stationing_directive(order),
        .air_recovery = task_order_air_recovery_directive(order),
        .air_takeoff = task_order_air_takeoff_directive(order),
        .air_formation = task_order_air_formation_directive(order),
        .naval_command_authority = task_order_naval_command_authority(order),
        .naval_stationing = task_order_naval_stationing_directive(order),
        .ground_static_task = task_order_ground_static_task_directive(order),
    };
}

inline void apply_task_order_maintained_batch_contract_to_compatibility_shell(
    TaskOrderCompatibilityTransportShell &order,
    const TaskOrderMaintainedBatchContract &contract) noexcept {
    task_order_shared_core(order) = contract.shared_core;
    auto &air = task_order_air_owner_slice(order);
    apply_task_order_air_tasking_identity_directive(air, contract.air_tasking_identity);
    apply_task_order_air_stationing_directive(air, contract.air_stationing);
    apply_task_order_air_recovery_directive(air, contract.air_recovery);
    apply_task_order_air_takeoff_directive(air, contract.air_takeoff);
    apply_task_order_air_formation_directive(air, contract.air_formation);
    auto &naval = task_order_naval_owner_slice(order);
    apply_task_order_naval_command_authority_directive(naval, contract.naval_command_authority);
    apply_task_order_naval_stationing_directive(naval, contract.naval_stationing);
    auto &ground = task_order_ground_owner_slice(order);
    apply_task_order_ground_static_task_directive(ground, contract.ground_static_task);
}

[[nodiscard]] inline TaskOrderCompatibilityTransportShell
task_order_compatibility_shell_from_maintained_batch_contract(
    const TaskOrderMaintainedBatchContract &contract) noexcept {
    TaskOrderCompatibilityTransportShell compatibility_shell{};
    apply_task_order_maintained_batch_contract_to_compatibility_shell(compatibility_shell,
                                                                      contract);
    return compatibility_shell;
}

struct WorldTaskOrderMaintainedAssignment {
    using contract_type = TaskOrderMaintainedBatchContract;
    static constexpr bool kMaintainedBatchTruth = contract_type::kMaintainedBatchTruth;
    static_assert(kMaintainedBatchTruth, "WorldTaskOrderMaintainedAssignment transports only the "
                                         "controlled TaskOrder maintained batch contract.");

#define EF_WORLD_TASK_ORDER_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_task_order_maintained_assignment.inc"
};

struct WorldLeaderIntentAssignment {
    using shell_type = LeaderIntentCompatibilityTransportShell;
    static constexpr bool kCompatibilityTransportShell = kLeaderIntentCompatibilityTransportShell;
    static_assert(
        kCompatibilityTransportShell,
        "WorldLeaderIntentAssignment transports only the LeaderIntent compatibility shell.");

#define EF_WORLD_LEADER_INTENT_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_leader_intent_assignment.inc"
};

struct LeaderIntentMaintainedBatchContract {
    using shared_core_owner_slice = LeaderIntentCore;
    using air_owner_slice = LeaderIntentAirOwnerSlice;
    using naval_owner_slice = LeaderIntentNavalOwnerSlice;
    using ground_owner_slice = LeaderIntentGroundOwnerSlice;
    using shared_core_type = LeaderIntentCore;
    using air_recovery_type = LeaderIntentAir::RecoveryDirective;
    using air_takeoff_type = LeaderIntentAir::TakeoffDirective;
    using air_formation_type = LeaderIntentAir::FormationDirective;
    using naval_command_authority_type = LeaderIntentNaval::CommandAuthorityDirective;
    using ground_static_status_type = LeaderIntentGround::StaticStatusDirective;
    static constexpr bool kMaintainedBatchTruth = true;

#define EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/leader_intent_maintained_batch_contract.inc"

    static_assert(kMaintainedBatchTruth, "LeaderIntentMaintainedBatchContract is the controlled "
                                         "LeaderIntent maintained batch read/write shape.");
};

[[nodiscard]] inline LeaderIntentMaintainedBatchContract leader_intent_maintained_batch_contract(
    const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return {
        .shared_core = leader_intent_shared_core(intent),
        .phase_id = leader_intent_air_owner_slice(intent).phase_id,
        .element_phase_id = leader_intent_air_owner_slice(intent).element_phase_id,
        .air_recovery = leader_intent_air_recovery_directive(intent),
        .formation_mode_id = leader_intent_air_owner_slice(intent).formation_mode_id,
        .join_required_flag = leader_intent_air_owner_slice(intent).join_required_flag,
        .rejoin_required_flag = leader_intent_air_owner_slice(intent).rejoin_required_flag,
        .air_takeoff = leader_intent_air_takeoff_directive(intent),
        .air_formation = leader_intent_air_formation_directive(intent),
        .naval_command_authority = leader_intent_naval_command_authority(intent),
        .ground_static_status = leader_intent_ground_static_status_directive(intent),
    };
}

inline void apply_leader_intent_maintained_batch_contract_to_compatibility_shell(
    LeaderIntentCompatibilityTransportShell &intent,
    const LeaderIntentMaintainedBatchContract &contract) noexcept {
    leader_intent_shared_core(intent) = contract.shared_core;
    auto &air = leader_intent_air_owner_slice(intent);
    air.phase_id = contract.phase_id;
    air.element_phase_id = contract.element_phase_id;
    air.formation_mode_id = contract.formation_mode_id;
    air.join_required_flag = contract.join_required_flag;
    air.rejoin_required_flag = contract.rejoin_required_flag;
    air.recovery_base_id = contract.air_recovery.recovery_base_id;
    air.recovery_runway_id = contract.air_recovery.recovery_runway_id;
    air.recovery_approach_type = contract.air_recovery.recovery_approach_type;
    air.takeoff_procedure_id = contract.air_takeoff.takeoff_procedure_id;
    air.takeoff_clearance_id = contract.air_takeoff.takeoff_clearance_id;
    air.takeoff_interval_s = contract.air_takeoff.takeoff_interval_s;
    air.runway_slot_id = contract.air_takeoff.runway_slot_id;
    air.formation_id = contract.air_formation.formation_id;
    air.form_offset_x = contract.air_formation.form_offset_x;
    air.form_offset_y = contract.air_formation.form_offset_y;
    air.form_offset_z = contract.air_formation.form_offset_z;

    auto &naval = leader_intent_naval_owner_slice(intent);
    naval.warfare_role_code = contract.naval_command_authority.warfare_role_code;
    naval.officer_in_tactical_command =
        contract.naval_command_authority.officer_in_tactical_command;

    auto &ground = leader_intent_ground_owner_slice(intent);
    ground.ground_status_phase = contract.ground_static_status.ground_status_phase;
    ground.ground_task_mode = contract.ground_static_status.ground_task_mode;
    ground.objective_area_id = contract.ground_static_status.objective_area_id;
    ground.objective_node_id = contract.ground_static_status.objective_node_id;
    ground.ground_commander_id = contract.ground_static_status.ground_commander_id;
    ground.tactical_cadence_hz = contract.ground_static_status.tactical_cadence_hz;
}

[[nodiscard]] inline LeaderIntentCompatibilityTransportShell
leader_intent_compatibility_shell_from_maintained_batch_contract(
    const LeaderIntentMaintainedBatchContract &contract) noexcept {
    LeaderIntentCompatibilityTransportShell compatibility_shell{};
    apply_leader_intent_maintained_batch_contract_to_compatibility_shell(compatibility_shell,
                                                                         contract);
    return compatibility_shell;
}

struct WorldLeaderIntentMaintainedAssignment {
    using contract_type = LeaderIntentMaintainedBatchContract;
    static constexpr bool kMaintainedBatchTruth = contract_type::kMaintainedBatchTruth;
    static_assert(kMaintainedBatchTruth, "WorldLeaderIntentMaintainedAssignment transports only "
                                         "the controlled LeaderIntent maintained batch contract.");

#define EF_WORLD_LEADER_INTENT_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_leader_intent_maintained_assignment.inc"
};

struct WorldPilotReportAssignment {
    using shell_type = PilotReportCompatibilityTransportShell;
    static constexpr bool kCompatibilityTransportShell = kPilotReportCompatibilityTransportShell;
    static_assert(
        kCompatibilityTransportShell,
        "WorldPilotReportAssignment transports only the PilotReport compatibility shell.");

#define EF_WORLD_PILOT_REPORT_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_pilot_report_assignment.inc"
};

struct PilotReportMaintainedBatchContract {
    using shared_core_owner_slice = PilotReportCore;
    using air_owner_slice = PilotReportAirOwnerSlice;
    using naval_owner_slice = PilotReportNavalOwnerSlice;
    using ground_owner_slice = PilotReportGroundOwnerSlice;
    using shared_core_type = PilotReportCore;
    using air_owner_slice_type = PilotReportAirOwnerSlice;
    using naval_command_authority_type = PilotReportNaval::CommandAuthorityDirective;
    using ground_static_status_type = PilotReportGround::StaticStatusDirective;
    static constexpr bool kMaintainedBatchTruth = true;

#define EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/pilot_report_maintained_batch_contract.inc"

    static_assert(kMaintainedBatchTruth, "PilotReportMaintainedBatchContract is the controlled "
                                         "PilotReport maintained batch read/write shape.");
};

[[nodiscard]] inline PilotReportMaintainedBatchContract pilot_report_maintained_batch_contract(
    const PilotReportCompatibilityTransportShell &report) noexcept {
    return {
        .shared_core = pilot_report_shared_core(report),
        .air = pilot_report_air_owner_slice(report),
        .naval_command_authority = pilot_report_naval_command_authority(report),
        .ground_static_status = pilot_report_ground_static_status_directive(report),
    };
}

inline void apply_pilot_report_maintained_batch_contract_to_compatibility_shell(
    PilotReportCompatibilityTransportShell &report,
    const PilotReportMaintainedBatchContract &contract) noexcept {
    pilot_report_shared_core(report) = contract.shared_core;
    pilot_report_air_owner_slice(report) = contract.air;
    auto &naval = pilot_report_naval_owner_slice(report);
    naval.warfare_role_code = contract.naval_command_authority.warfare_role_code;
    naval.officer_in_tactical_command =
        contract.naval_command_authority.officer_in_tactical_command;
    auto &ground = pilot_report_ground_owner_slice(report);
    ground.ground_status_phase = contract.ground_static_status.ground_status_phase;
    ground.ground_task_mode = contract.ground_static_status.ground_task_mode;
    ground.objective_area_id = contract.ground_static_status.objective_area_id;
    ground.objective_node_id = contract.ground_static_status.objective_node_id;
    ground.ground_commander_id = contract.ground_static_status.ground_commander_id;
    ground.tactical_cadence_hz = contract.ground_static_status.tactical_cadence_hz;
    ground.readiness_ratio = contract.ground_static_status.readiness_ratio;
}

[[nodiscard]] inline PilotReportCompatibilityTransportShell
pilot_report_compatibility_shell_from_maintained_batch_contract(
    const PilotReportMaintainedBatchContract &contract) noexcept {
    PilotReportCompatibilityTransportShell compatibility_shell{};
    apply_pilot_report_maintained_batch_contract_to_compatibility_shell(compatibility_shell,
                                                                        contract);
    return compatibility_shell;
}

struct WorldPilotReportMaintainedAssignment {
    using contract_type = PilotReportMaintainedBatchContract;
    static constexpr bool kMaintainedBatchTruth = contract_type::kMaintainedBatchTruth;
    static_assert(kMaintainedBatchTruth, "WorldPilotReportMaintainedAssignment transports only the "
                                         "controlled PilotReport maintained batch contract.");

#define EF_WORLD_PILOT_REPORT_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/world_pilot_report_maintained_assignment.inc"
};

[[nodiscard]] inline const MissionCommandCompatibilityTransportShell &
world_batch_assignment_compatibility_shell(
    const WorldMissionCommandAssignment &assignment) noexcept {
    return assignment.command;
}

[[nodiscard]] inline MissionCommandCompatibilityTransportShell &
world_batch_assignment_compatibility_shell(WorldMissionCommandAssignment &assignment) noexcept {
    return assignment.command;
}

[[nodiscard]] inline const MissionCommandMaintainedBatchContract &
world_mission_command_maintained_batch_contract(
    const WorldMissionCommandMaintainedAssignment &assignment) noexcept {
    return assignment.mission_command;
}

[[nodiscard]] inline MissionCommandMaintainedBatchContract &
world_mission_command_maintained_batch_contract(
    WorldMissionCommandMaintainedAssignment &assignment) noexcept {
    return assignment.mission_command;
}

[[nodiscard]] inline const TaskOrderMaintainedBatchContract &
world_task_order_maintained_batch_contract(
    const WorldTaskOrderMaintainedAssignment &assignment) noexcept {
    return assignment.task_order;
}

[[nodiscard]] inline TaskOrderMaintainedBatchContract &world_task_order_maintained_batch_contract(
    WorldTaskOrderMaintainedAssignment &assignment) noexcept {
    return assignment.task_order;
}

[[nodiscard]] inline WorldTaskOrderMaintainedAssignment
project_world_task_order_maintained_batch_assignment(
    std::uint64_t world_index, std::uint64_t entity_id,
    const TaskOrderCompatibilityTransportShell &order) noexcept {
    return {
        .world_index = world_index,
        .entity_id = entity_id,
        .task_order = task_order_maintained_batch_contract(order),
    };
}

[[nodiscard]] inline const LeaderIntentCompatibilityTransportShell &
world_batch_assignment_compatibility_shell(const WorldLeaderIntentAssignment &assignment) noexcept {
    return assignment.intent;
}

[[nodiscard]] inline LeaderIntentCompatibilityTransportShell &
world_batch_assignment_compatibility_shell(WorldLeaderIntentAssignment &assignment) noexcept {
    return assignment.intent;
}

[[nodiscard]] inline const LeaderIntentMaintainedBatchContract &
world_leader_intent_maintained_batch_contract(
    const WorldLeaderIntentMaintainedAssignment &assignment) noexcept {
    return assignment.leader_intent;
}

[[nodiscard]] inline LeaderIntentMaintainedBatchContract &
world_leader_intent_maintained_batch_contract(
    WorldLeaderIntentMaintainedAssignment &assignment) noexcept {
    return assignment.leader_intent;
}

[[nodiscard]] inline const PilotReportCompatibilityTransportShell &
world_batch_assignment_compatibility_shell(const WorldPilotReportAssignment &assignment) noexcept {
    return assignment.report;
}

[[nodiscard]] inline PilotReportCompatibilityTransportShell &
world_batch_assignment_compatibility_shell(WorldPilotReportAssignment &assignment) noexcept {
    return assignment.report;
}

[[nodiscard]] inline const PilotReportMaintainedBatchContract &
world_pilot_report_maintained_batch_contract(
    const WorldPilotReportMaintainedAssignment &assignment) noexcept {
    return assignment.pilot_report;
}

[[nodiscard]] inline PilotReportMaintainedBatchContract &
world_pilot_report_maintained_batch_contract(
    WorldPilotReportMaintainedAssignment &assignment) noexcept {
    return assignment.pilot_report;
}

struct WorldExecutionEpisodeStepRequest {
#define EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/contracts/detail/world_execution_episode_step_request.inc"
};
