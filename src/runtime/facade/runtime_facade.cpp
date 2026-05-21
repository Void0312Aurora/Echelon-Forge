#include "runtime/facade/runtime_facade.h"
#include "runtime/facade/runtime_window_coordinator.h"

#include "components/basic/common.h"
#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/stage_node_manifest_registry.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <stdexcept>
#include <string>

namespace {

using runtime::scheduler::find_stage_node_manifest;

std::vector<WorldEntityRef> refs_from_step_requests(
    const std::vector<WorldExecutionEpisodeStepRequest>& requests
) {
    std::vector<WorldEntityRef> refs;
    refs.reserve(requests.size());
    for (const auto& request : requests) {
        refs.push_back(WorldEntityRef{
            .world_index = request.world_index,
            .entity_id = request.entity_id,
        });
    }
    return refs;
}

std::vector<WorldEntityRef> world_refs_from_engagement_refs(
    const std::vector<EngagementEntityRef>& refs
) {
    std::vector<WorldEntityRef> out;
    out.reserve(refs.size());
    for (const auto& ref : refs) {
        out.push_back(WorldEntityRef{
            .world_index = ref.world_index,
            .entity_id = ref.entity_id,
        });
    }
    return out;
}

bool valid_runtime_world_index(const WorldBatchRuntime& runtime, std::uint64_t world_index) {
    return world_index < runtime.world_count();
}

std::string track_source_name(int source) {
    switch (source) {
        case 1:
            return "radar";
        case 2:
            return "rwr_esm";
        case 3:
            return "data_link";
        case 4:
            return "fused";
        case 5:
            return "sonar";
        case 0:
        default:
            return "none";
    }
}

std::string track_classification_name(int classification) {
    switch (classification) {
        case 1:
            return "friendly";
        case 2:
            return "hostile";
        case 3:
            return "neutral";
        case 0:
        default:
            return "unknown";
    }
}

std::string track_status_name(int status) {
    switch (status) {
        case 1:
            return "confirmed";
        case 2:
            return "coasted";
        case 0:
        default:
            return "tentative";
    }
}

inline constexpr std::string_view kWp10ObservationExportNodeId =
    "p10.observation_export.v1";
inline constexpr std::string_view kWp10LaunchNodeId =
    "p7.fire_control_launch.v1";
inline constexpr std::string_view kWp10EffectsDamageNodeId =
    "p9.effects_damage.v1";
inline constexpr std::string_view kWp10ExportBarrierId = "export";
inline constexpr std::string_view kWp10ExportBarrierDetail =
    "maintained_facade_export";
inline constexpr std::uint64_t kWp10ExportBarrierSequence = 1;
inline constexpr std::string_view kWp11ObservationPacketIdPrefix = "obs:";
inline constexpr std::string_view kWp11EngagementPacketIdPrefix = "eng:";
inline constexpr std::string_view kWp11DiagnosticsPacketIdPrefix = "diag:";
inline constexpr std::string_view kMaintainedBaselineBackendProfileId =
    "cpu_exact.reference";
inline constexpr std::string_view kMaintainedBaselineParityBudgetRef =
    "parity_budget.cpu_exact.reference.v1";
inline constexpr std::string_view kMaintainedBaselineProfileStatus =
    "maintained_exact_baseline";
inline constexpr std::string_view kDeviceObservationViewCandidateProfileId =
    "gpu_helpers.diagnostics_only";
inline constexpr std::string_view kDeviceObservationViewRejectionReason =
    "gpu_helpers_diagnostics_only_is_not_a_maintained_device_observation_view_profile";
inline constexpr std::string_view kExactGpuBackendCandidateProfileId =
    "gpu_exact.unmaintained_candidate";
inline constexpr std::string_view kExactGpuBackendRejectionReason =
    "gpu_exact.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kResidentStateCandidateProfileId =
    "resident_state.unmaintained_candidate";
inline constexpr std::string_view kResidentStateCandidateParityBudgetRef =
    "parity_budget.resident_state.unmaintained_candidate.v1";
inline constexpr std::string_view kResidentStateRejectionReason =
    "resident_state.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kShadowCompareCandidateProfileId =
    "shadow_compare.unmaintained_candidate";
inline constexpr std::string_view kShadowCompareCandidateParityBudgetRef =
    "parity_budget.shadow_compare.unmaintained_candidate.v1";
inline constexpr std::string_view kShadowCompareRejectionReason =
    "shadow_compare.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kMultiFidelityRejectionReason =
    "multi_fidelity_profiles_require_a_maintained_registry_revision_and_acceptance_gate";
inline constexpr std::string_view kRuntimeFidelityProviderFamilyNone = "none";
inline constexpr std::string_view kRuntimeFidelityProviderFamilyReferenceCpu =
    "reference_cpu";
inline constexpr std::string_view kRuntimeCounterfactualSelectedSliceBarrierId =
    "counterfactual_selected_slice";
inline constexpr std::uint64_t kRuntimeCounterfactualSelectedSliceSnapshotVersion =
    1;
inline constexpr std::string_view kRuntimeCounterfactualRawMutationRejection =
    "counterfactual_raw_authoritative_state_mutation_forbidden";
inline constexpr std::string_view kRuntimeCounterfactualMissingReplayEnvelope =
    "counterfactual_replay_envelope_id_required";
inline constexpr std::string_view kRuntimeCounterfactualMissingBranchPoint =
    "counterfactual_branch_point_id_required";
inline constexpr std::string_view kRuntimeCounterfactualUnsupportedFidelity =
    "counterfactual_fidelity_request_not_admitted";
inline constexpr std::string_view kRuntimeCounterfactualInvalidWorld =
    "counterfactual_world_index_out_of_range";
inline constexpr std::string_view kRuntimeCounterfactualInvalidEntity =
    "counterfactual_entity_missing_transform_or_velocity";
inline constexpr std::string_view kRuntimeCounterfactualSetupMissingEntity =
    "counterfactual_baseline_setup_entity_missing";

runtime::fidelity::FidelityProfileRequest fidelity_contract_request_from_facade(
    const RuntimeFidelityRequest& request
) {
    return runtime::fidelity::FidelityProfileRequest{
        .request_label = request.request_label,
        .backend_profile_id = request.backend_profile_id,
        .parity_budget_ref = request.parity_budget_ref,
        .model_family_scope = request.model_family_scope,
        .validation_gate = request.validation_gate,
        .facade_evidence_refs = request.facade_evidence_refs,
        .requests_adaptive_scheduling = false,
        .requests_learned_model_provider = false,
        .requests_approximate_execution = false,
        .requests_exact_gpu_backend =
            request.provider_family != kRuntimeFidelityProviderFamilyNone &&
            request.provider_family != kRuntimeFidelityProviderFamilyReferenceCpu &&
            request.provider_family != "resident" &&
            request.provider_family != "resident_state" &&
            request.provider_family != "shadow",
        .requests_resident_state =
            request.provider_family == "resident" ||
            request.provider_family == "resident_state",
        .requests_shadow_compare =
            request.provider_family == "shadow",
    };
}

RuntimeFidelityAdmission runtime_fidelity_admission_from_contract(
    const RuntimeFidelityRequest& request,
    const runtime::fidelity::FidelityProfileAdmissionResult& contract_result
) {
    RuntimeFidelityAdmission admission{};
    admission.admitted = contract_result.admitted;
    admission.baseline_exact_evaluation = contract_result.baseline_exact_evaluation;
    admission.request_label = contract_result.request_label;
    admission.backend_profile_id = contract_result.backend_profile_id;
    admission.parity_budget_ref = contract_result.parity_budget_ref;
    admission.requested_provider_family = request.provider_family;
    admission.rejection_reason = contract_result.rejection_reason;
    admission.errors = contract_result.errors;
    admission.evidence_refs = contract_result.evidence_refs;
    return admission;
}

bool runtime_string_blank(const std::string& value) {
    return value.empty() || std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

void append_runtime_evidence_ref(
    std::vector<std::string>& evidence_refs,
    const std::string& ref
) {
    if (runtime_string_blank(ref)) {
        return;
    }
    if (std::find(evidence_refs.begin(), evidence_refs.end(), ref) !=
        evidence_refs.end()) {
        return;
    }
    evidence_refs.push_back(ref);
}

WorldSpawnRequest legacy_spawn_request_from_typed_request(
    const TypedPlatformSpawnRequest& request
) {
    WorldSpawnRequest legacy{};
    legacy.world_index = request.world_index;
    legacy.side = request.side;
    legacy.type_name = request.source_type_name;
    legacy.entity_name = request.entity_name;
    legacy.is_agent = request.is_agent;
    legacy.x = request.x;
    legacy.y = request.y;
    legacy.z = request.z;
    legacy.heading = request.heading;
    legacy.pitch = request.pitch;
    legacy.roll = request.roll;
    legacy.vx = request.vx;
    legacy.vy = request.vy;
    legacy.vz = request.vz;
    return legacy;
}

std::uint64_t spawn_legacy_request_through_compatibility_path(
    SimulationKernel& world,
    const WorldSpawnRequest& request
) {
    const auto entity = world.spawn_unit(
        request.side,
        request.type_name,
        request.x,
        request.y,
        request.z,
        request.heading,
        request.pitch,
        request.roll,
        request.vx,
        request.vy,
        request.vz
    );
    if (!entity.is_valid()) {
        return entity.id();
    }

    if (request.ammo_override_enabled) {
        world.set_unit_ammo(
            entity.id(),
            request.missiles_remaining,
            request.max_missiles
        );
    }
    if (request.weapon_cooldown_override_enabled) {
        world.set_weapon_cooldown(
            entity.id(),
            request.weapon_cooldown_s,
            request.weapon_last_fire_time
        );
    }
    return entity.id();
}

TypedPlatformSpawnResult materialize_typed_platform_spawn_request(
    WorldBatchRuntime& runtime,
    std::uint64_t request_index,
    const TypedPlatformSpawnRequest& request
) {
    TypedPlatformSpawnAdmission admission =
        make_typed_platform_spawn_admission(request_index, request);
    const TypedPlatformSpawnValidationResult validation =
        validate_typed_platform_spawn_request(request);

    if (!validation.valid) {
        admission.reject(
            validation.rejection_reason.empty()
                ? std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan)
                : validation.rejection_reason
        );
        admission.errors = validation.errors;
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.validation_failed"
        );
        return make_typed_platform_spawn_result(admission);
    }

    if (!valid_runtime_world_index(runtime, request.world_index)) {
        admission.reject(
            std::string(kTypedPlatformSpawnRejectionWorldIndexOutOfRange)
        );
        admission.add_error("typed platform spawn world_index is outside the configured runtime batch");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.world_index_guard"
        );
        return make_typed_platform_spawn_result(admission);
    }

    if (!request.resolved_spawn_plan.admitted) {
        admission.reject(
            std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan)
        );
        if (!request.resolved_spawn_plan.rejection_reason.empty()) {
            admission.add_error(
                "resolved_spawn_plan rejected bridge admission: " +
                request.resolved_spawn_plan.rejection_reason
            );
        }
        if (!request.resolved_spawn_plan.diagnostics_reason.empty()) {
            admission.add_error(
                "resolved_spawn_plan diagnostics: " +
                request.resolved_spawn_plan.diagnostics_reason
            );
        }
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.plan_admission_guard"
        );
        return make_typed_platform_spawn_result(admission);
    }

    if (!request.compatibility_path_preserved ||
        !request.capability_bundle.compatibility_path_preserved ||
        !request.resolved_spawn_plan.compatibility_path_preserved) {
        admission.reject(
            std::string(kTypedPlatformSpawnRejectionCompatibilityPathRequired)
        );
        admission.add_error(
            "typed platform setup must preserve compatibility_path_preserved across request, bundle, and plan"
        );
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.compatibility_path_guard"
        );
        return make_typed_platform_spawn_result(admission);
    }

    if (request.capability_bundle.source_type_name != request.source_type_name) {
        admission.reject(
            std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan)
        );
        admission.add_error(
            "capability_bundle.source_type_name must match request.source_type_name"
        );
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.bundle_identity_guard"
        );
        return make_typed_platform_spawn_result(admission);
    }

    if (request.resolved_spawn_plan.source_type_name != request.source_type_name) {
        admission.reject(
            std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan)
        );
        admission.add_error(
            "resolved_spawn_plan.source_type_name must match request.source_type_name"
        );
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.source_type_name_guard"
        );
        return make_typed_platform_spawn_result(admission);
    }

    if (request.resolved_spawn_plan.capability_bundle_id !=
        request.capability_bundle.bundle_id) {
        admission.reject(
            std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan)
        );
        admission.add_error(
            "resolved_spawn_plan.capability_bundle_id must match capability_bundle.bundle_id"
        );
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.plan_identity_guard"
        );
        return make_typed_platform_spawn_result(admission);
    }

    admission.admitted = true;
    append_runtime_evidence_ref(
        admission.evidence_refs,
        "RuntimeFacade.apply_world_setup.typed_platform_spawn_bridge"
    );
    append_runtime_evidence_ref(
        admission.evidence_refs,
        "RuntimeFacade.apply_world_setup.compatibility_type_name_materialization"
    );

    TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
    WorldSpawnRequest legacy_request = legacy_spawn_request_from_typed_request(request);
    legacy_request.type_name = request.resolved_spawn_plan.source_type_name;
    auto& world = runtime.world(static_cast<std::size_t>(request.world_index));
    const std::uint64_t entity_id =
        spawn_legacy_request_through_compatibility_path(world, legacy_request);
    if (entity_id == 0U) {
        result.admitted = true;
        result.materialized = false;
        result.fail_closed = true;
        result.rejection_reason =
            std::string(kTypedPlatformSpawnRejectionMaterializationFailed);
        result.add_error(
            "compatibility path materialization returned null entity for source_type_name=" +
            request.resolved_spawn_plan.source_type_name
        );
        append_runtime_evidence_ref(
            result.evidence_refs,
            "RuntimeFacade.apply_world_setup.materialization_failed"
        );
        return result;
    }

    result.admitted = true;
    result.materialized = true;
    result.entity_id = entity_id;
    append_runtime_evidence_ref(
        result.evidence_refs,
        "RuntimeFacade.apply_world_setup.materialized"
    );
    return result;
}

BatchWorldSetupRequest single_world_counterfactual_setup(
    BatchWorldSetupRequest setup,
    std::uint32_t seed
) {
    if (seed != 0U) {
        setup.seeds = {seed};
    } else if (setup.seeds.empty()) {
        setup.seeds = {0U};
    } else {
        setup.seeds = {setup.seeds.front()};
    }
    for (auto& assignment : setup.terrain_assignments) {
        assignment.world_index = 0;
    }
    for (auto& assignment : setup.wind_assignments) {
        assignment.world_index = 0;
    }
    for (auto& zone : setup.zones) {
        zone.world_index = 0;
    }
    for (auto& spawn : setup.spawn_requests) {
        spawn.world_index = 0;
    }
    for (auto& spawn : setup.typed_platform_spawn_requests) {
        spawn.world_index = 0;
    }
    if (setup.time_steps.size() > 1U) {
        setup.time_steps = {setup.time_steps.front()};
    }
    return setup;
}

std::uint64_t counterfactual_spawned_entity_id(
    const BatchWorldSetupResult& setup_result,
    const WorldEntityRef& requested_ref
) {
    if (requested_ref.entity_id != 0U) {
        return requested_ref.entity_id;
    }
    if (!setup_result.entity_ids.empty()) {
        return setup_result.entity_ids.front();
    }
    return 0U;
}

RuntimeCounterfactualSnapshot counterfactual_snapshot_from_runtime(
    WorldBatchRuntime& runtime,
    const WorldEntityRef& ref,
    const RuntimeFidelityAdmission& fidelity_admission,
    const std::string& cadence_reason,
    std::vector<std::string> evidence_refs
) {
    if (!valid_runtime_world_index(runtime, ref.world_index)) {
        throw std::out_of_range(std::string(kRuntimeCounterfactualInvalidWorld));
    }

    auto& world = runtime.world(static_cast<std::size_t>(ref.world_index));
    const auto position = world.get_unit_position(ref.entity_id);
    const auto velocity = world.get_unit_velocity(ref.entity_id);
    const auto observation = world.get_agent_observation(ref.entity_id);

    if (position.size() < 3U || velocity.size() < 3U) {
        throw std::runtime_error(std::string(kRuntimeCounterfactualInvalidEntity));
    }

    evidence_refs.push_back("RuntimeFacade.snapshot_counterfactual_entity");
    evidence_refs.push_back("RuntimeFacade.admit_fidelity_request");
    if (!fidelity_admission.selected_stage_node_id.empty()) {
        evidence_refs.push_back(
            "selected_stage_node_id=" + fidelity_admission.selected_stage_node_id
        );
    }
    if (!cadence_reason.empty()) {
        evidence_refs.push_back("cadence_reason=" + cadence_reason);
    }

    return RuntimeCounterfactualSnapshot{
        .world_index = ref.world_index,
        .entity_id = ref.entity_id,
        .x = position[0],
        .y = position[1],
        .z = position[2],
        .vx = velocity[0],
        .vy = velocity[1],
        .vz = velocity[2],
        .heading = observation.heading,
        .pitch = observation.pitch,
        .roll = observation.roll,
        .snapshot_version = kRuntimeCounterfactualSelectedSliceSnapshotVersion,
        .barrier_id = std::string(kRuntimeCounterfactualSelectedSliceBarrierId),
        .fidelity_profile_id = fidelity_admission.backend_profile_id,
        .provider_family = fidelity_admission.selected_provider_family,
        .selected_stage_node_id = fidelity_admission.selected_stage_node_id,
        .cadence_reason = cadence_reason,
        .evidence_refs = std::move(evidence_refs),
    };
}

bool apply_counterfactual_delta(
    RuntimeFacade* facade,
    const WorldEntityRef& ref,
    const RuntimeCounterfactualBranchRequest& request,
    std::string* rejection_reason
) {
    if (facade == nullptr || !valid_runtime_world_index(facade->runtime(), ref.world_index)) {
        if (rejection_reason != nullptr) {
            *rejection_reason = std::string(kRuntimeCounterfactualInvalidWorld);
        }
        return false;
    }

    auto& world = facade->runtime().world(static_cast<std::size_t>(ref.world_index));
    auto entity = world.get_world().entity(ref.entity_id);
    const Transform* transform = entity.get<Transform>();
    const Velocity* velocity = entity.get<Velocity>();
    if (transform == nullptr || velocity == nullptr) {
        if (rejection_reason != nullptr) {
            *rejection_reason = std::string(kRuntimeCounterfactualInvalidEntity);
        }
        return false;
    }

    entity.set<Transform>(Transform{
        .x = transform->x + request.mutation_dx,
        .y = transform->y + request.mutation_dy,
        .z = transform->z + request.mutation_dz,
        .heading = Math::normalize_heading_deg(
            transform->heading + request.mutation_dheading
        ),
        .pitch = transform->pitch,
        .roll = transform->roll,
    });
    entity.set<Velocity>(Velocity{
        .vx = velocity->vx + request.mutation_dvx,
        .vy = velocity->vy + request.mutation_dvy,
        .vz = velocity->vz + request.mutation_dvz,
    });
    return true;
}

RuntimeWorldlineComparison compare_counterfactual_snapshots(
    const RuntimeCounterfactualSnapshot& parent,
    const RuntimeCounterfactualSnapshot& branch,
    const RuntimeCounterfactualBranchRequest& request
) {
    RuntimeWorldlineComparison comparison{};
    comparison.comparable = parent.entity_id != 0U &&
        parent.entity_id == branch.entity_id &&
        parent.world_index == branch.world_index;
    comparison.comparison_id = request.branch_point_id.empty()
        ? "counterfactual:selected_slice"
        : "counterfactual:selected_slice:" + request.branch_point_id;
    comparison.barrier_id = std::string(kRuntimeCounterfactualSelectedSliceBarrierId);
    comparison.dx = branch.x - parent.x;
    comparison.dy = branch.y - parent.y;
    comparison.dz = branch.z - parent.z;
    comparison.dvx = branch.vx - parent.vx;
    comparison.dvy = branch.vy - parent.vy;
    comparison.dvz = branch.vz - parent.vz;
    comparison.dheading = branch.heading - parent.heading;
    comparison.evidence_refs = {
        "RuntimeFacade.run_counterfactual_branch",
        "RuntimeFacade.compare_counterfactual_snapshots",
        "replay_envelope_id=" + request.replay_envelope_id,
        "branch_point_id=" + request.branch_point_id,
    };
    return comparison;
}

int launch_event_priority(const LaunchEvent&) {
    return 10;
}

int effects_event_priority(const EffectsEvent&) {
    return 20;
}

int damage_report_priority(const DamageReport&) {
    return 30;
}

int diagnostics_trace_priority(const DiagnosticsTrace&) {
    return 40;
}

template <typename Event>
const std::string& ensure_manifest_node_id(
    Event& event,
    std::string Event::* field,
    std::string_view fallback_node_id
) {
    auto& node_id = event.*field;
    if (node_id.empty() && find_stage_node_manifest(fallback_node_id) != nullptr) {
        node_id = std::string(fallback_node_id);
    }
    return node_id;
}

void stable_sort_track_packets(std::vector<TrackPacket>* tracks) {
    if (tracks == nullptr) {
        return;
    }
    std::stable_sort(
        tracks->begin(),
        tracks->end(),
        [](const TrackPacket& lhs, const TrackPacket& rhs) {
            if (lhs.source_time_s != rhs.source_time_s) {
                return lhs.source_time_s < rhs.source_time_s;
            }
            if (lhs.update_age_s != rhs.update_age_s) {
                return lhs.update_age_s < rhs.update_age_s;
            }
            return lhs.track_id < rhs.track_id;
        }
    );
}

void stable_sort_launch_events(std::vector<LaunchEvent>* events) {
    if (events == nullptr) {
        return;
    }
    std::stable_sort(
        events->begin(),
        events->end(),
        [](const LaunchEvent& lhs, const LaunchEvent& rhs) {
            if (lhs.event_time_s != rhs.event_time_s) {
                return lhs.event_time_s < rhs.event_time_s;
            }
            if (launch_event_priority(lhs) != launch_event_priority(rhs)) {
                return launch_event_priority(lhs) < launch_event_priority(rhs);
            }
            return lhs.event_id < rhs.event_id;
        }
    );
}

void stable_sort_effects_events(std::vector<EffectsEvent>* events) {
    if (events == nullptr) {
        return;
    }
    std::stable_sort(
        events->begin(),
        events->end(),
        [](const EffectsEvent& lhs, const EffectsEvent& rhs) {
            if (lhs.detonation_time_s != rhs.detonation_time_s) {
                return lhs.detonation_time_s < rhs.detonation_time_s;
            }
            if (effects_event_priority(lhs) != effects_event_priority(rhs)) {
                return effects_event_priority(lhs) < effects_event_priority(rhs);
            }
            return lhs.event_id < rhs.event_id;
        }
    );
}

void stable_sort_damage_reports(std::vector<DamageReport>* reports) {
    if (reports == nullptr) {
        return;
    }
    std::stable_sort(
        reports->begin(),
        reports->end(),
        [](const DamageReport& lhs, const DamageReport& rhs) {
            if (lhs.report_time_s != rhs.report_time_s) {
                return lhs.report_time_s < rhs.report_time_s;
            }
            if (damage_report_priority(lhs) != damage_report_priority(rhs)) {
                return damage_report_priority(lhs) < damage_report_priority(rhs);
            }
            return lhs.report_id < rhs.report_id;
        }
    );
}

void stable_sort_diagnostics_traces(std::vector<DiagnosticsTrace>* traces) {
    if (traces == nullptr) {
        return;
    }
    std::stable_sort(
        traces->begin(),
        traces->end(),
        [](const DiagnosticsTrace& lhs, const DiagnosticsTrace& rhs) {
            if (lhs.source_time_s != rhs.source_time_s) {
                return lhs.source_time_s < rhs.source_time_s;
            }
            if (diagnostics_trace_priority(lhs) != diagnostics_trace_priority(rhs)) {
                return diagnostics_trace_priority(lhs) < diagnostics_trace_priority(rhs);
            }
            return lhs.trace_id < rhs.trace_id;
        }
    );
}

void apply_export_packet_metadata(
    EngagementEventPacket* packet,
    std::uint64_t snapshot_version,
    double source_time_s
) {
    if (packet == nullptr) {
        return;
    }
    packet->snapshot_version = snapshot_version;
    packet->barrier_id = std::string(kWp10ExportBarrierId);
    packet->barrier_sequence = kWp10ExportBarrierSequence;
    packet->barrier_detail = std::string(kWp10ExportBarrierDetail);
    packet->source_time_s = source_time_s;
    if (find_stage_node_manifest(kWp10ObservationExportNodeId) != nullptr) {
        packet->producer_node_id = std::string(kWp10ObservationExportNodeId);
    }
    packet->packet_provenance.observation_packet_ids = {
        std::string(kWp11EngagementPacketIdPrefix) + std::to_string(snapshot_version)
    };
    packet->packet_provenance.source_observation_versions = {
        "track:" + std::to_string(snapshot_version)
    };
    packet->diagnostics_provenance.observation_packet_ids = {
        std::string(kWp11DiagnosticsPacketIdPrefix) + std::to_string(snapshot_version)
    };
    packet->diagnostics_provenance.source_observation_versions = {
        "diag:" + std::to_string(snapshot_version)
    };
    packet->diagnostics_provenance.diagnostics_reason =
        "diagnostics_trace_surface_not_maintained_decision_path";
}

void apply_export_trace_metadata(
    DiagnosticsTrace* trace,
    std::uint64_t snapshot_version,
    double source_time_s,
    std::string_view source_node_id
) {
    if (trace == nullptr) {
        return;
    }
    trace->source_snapshot_version = snapshot_version;
    trace->barrier_id = std::string(kWp10ExportBarrierId);
    trace->barrier_detail = std::string(kWp10ExportBarrierDetail);
    trace->source_time_s = source_time_s;
    if (find_stage_node_manifest(source_node_id) != nullptr) {
        trace->source_node_id = std::string(source_node_id);
    }
    if (find_stage_node_manifest(kWp10ObservationExportNodeId) != nullptr) {
        trace->export_node_id = std::string(kWp10ObservationExportNodeId);
    }
}

void finalize_recent_event_metadata(
    EngagementEventPacket* packet
) {
    if (packet == nullptr) {
        return;
    }
    for (auto& event : packet->launch_events) {
        ensure_manifest_node_id(event, &LaunchEvent::producer_node_id, kWp10LaunchNodeId);
    }
    for (auto& event : packet->effects_events) {
        ensure_manifest_node_id(event, &EffectsEvent::producer_node_id, kWp10EffectsDamageNodeId);
    }
    for (auto& report : packet->damage_reports) {
        ensure_manifest_node_id(report, &DamageReport::producer_node_id, kWp10EffectsDamageNodeId);
    }
}

void finalize_diagnostics_ancestry(
    EngagementEventPacket* packet
) {
    if (packet == nullptr) {
        return;
    }
    for (auto& trace : packet->diagnostics_traces) {
        if (trace.launch_event_id != 0) {
            const auto match = std::find_if(
                packet->launch_events.begin(),
                packet->launch_events.end(),
                [&trace](const LaunchEvent& event) {
                    return event.event_id == trace.launch_event_id;
                }
            );
            if (match != packet->launch_events.end()) {
                apply_export_trace_metadata(
                    &trace,
                    packet->snapshot_version,
                    match->event_time_s,
                    match->producer_node_id.empty() ? kWp10LaunchNodeId : match->producer_node_id
                );
                continue;
            }
        }
        if (trace.effects_event_id != 0) {
            const auto match = std::find_if(
                packet->effects_events.begin(),
                packet->effects_events.end(),
                [&trace](const EffectsEvent& event) {
                    return event.event_id == trace.effects_event_id;
                }
            );
            if (match != packet->effects_events.end()) {
                apply_export_trace_metadata(
                    &trace,
                    packet->snapshot_version,
                    match->detonation_time_s,
                    match->producer_node_id.empty() ? kWp10EffectsDamageNodeId : match->producer_node_id
                );
                continue;
            }
        }
        if (trace.damage_report_id != 0) {
            const auto match = std::find_if(
                packet->damage_reports.begin(),
                packet->damage_reports.end(),
                [&trace](const DamageReport& report) {
                    return report.report_id == trace.damage_report_id;
                }
            );
            if (match != packet->damage_reports.end()) {
                apply_export_trace_metadata(
                    &trace,
                    packet->snapshot_version,
                    match->report_time_s,
                    match->producer_node_id.empty() ? kWp10EffectsDamageNodeId : match->producer_node_id
                );
                continue;
            }
        }
        apply_export_trace_metadata(
            &trace,
            trace.source_snapshot_version != 0 ? trace.source_snapshot_version : packet->snapshot_version,
            trace.source_time_s,
            trace.source_node_id.empty() ? kWp10ObservationExportNodeId : trace.source_node_id
        );
    }
}

void apply_observation_packet_provenance(ObservationBatchPacket* packet) {
    if (packet == nullptr) {
        return;
    }
    packet->provenance.information_state_layer =
        std::string(kPolicyInformationStateAgentObservation);
    packet->provenance.source_label = std::string(kPolicySourceLabelFacadeObservationPacket);
    packet->provenance.maintained_status =
        std::string(kPolicyMaintainedStatusMaintained);
    packet->provenance.observation_packet_ids = {
        std::string(kWp11ObservationPacketIdPrefix) + std::to_string(packet->snapshot_version)
    };
    packet->provenance.source_observation_versions = {
        "global:" + std::to_string(packet->snapshot_version)
    };
    packet->provenance.diagnostics_reason.clear();
}

TrackPacket track_packet_from_observation_contact(
    const EngagementEntityRef& observer,
    const TrackData& contact,
    double source_time_s,
    std::uint64_t snapshot_version
) {
    return TrackPacket{
        .track_id = contact.id,
        .correlated_entity = EngagementEntityRef{
            .world_index = observer.world_index,
            .entity_id = contact.id,
        },
        .has_correlated_entity = contact.id != 0,
        .correlation_policy = contact.id != 0 ? "entity_id" : "unresolved",
        .source = track_source_name(contact.source),
        .classification = track_classification_name(contact.classification),
        .status = track_status_name(contact.status),
        .quality = contact.quality,
        .confidence = contact.confidence,
        .usable = contact.usability > 0,
        .iff = contact.iff_known ? "known" : "unknown",
        .source_time_s = source_time_s,
        .update_age_s = contact.time_since_update,
        .snapshot_version = snapshot_version,
    };
}

DiagnosticsTrace diagnostics_trace_from_track_packet(
    std::uint64_t trace_id,
    const TrackPacket& track,
    std::uint64_t observation_packet_version
) {
    return DiagnosticsTrace{
        .trace_id = trace_id,
        .parent_trace_id = 0,
        .chain_id = trace_id,
        .track_id = track.track_id,
        .observation_packet_version = observation_packet_version,
        .source_snapshot_version = track.snapshot_version,
        .barrier_id = std::string(kWp10ExportBarrierId),
        .barrier_detail = std::string(kWp10ExportBarrierDetail),
        .source_time_s = track.source_time_s,
        .source_node_id = std::string(kWp10ObservationExportNodeId),
        .export_node_id = std::string(kWp10ObservationExportNodeId),
    };
}

bool contains_world_index(const std::vector<std::uint64_t>& world_indices, std::uint64_t world_index) {
    return std::find(world_indices.begin(), world_indices.end(), world_index) != world_indices.end();
}

void assign_world_index(EngagementEntityRef& ref, std::uint64_t world_index) {
    if (ref.entity_id != 0) {
        ref.world_index = world_index;
    }
}

RecentEngagementEvents with_world_index(
    RecentEngagementEvents recent,
    std::uint64_t world_index
) {
    for (auto& event : recent.launch_events) {
        assign_world_index(event.spawned_munition, world_index);
    }
    for (auto& event : recent.effects_events) {
        assign_world_index(event.munition, world_index);
        assign_world_index(event.target, world_index);
    }
    for (auto& report : recent.damage_reports) {
        assign_world_index(report.target, world_index);
    }
    for (auto& trace : recent.diagnostics_traces) {
        assign_world_index(trace.munition, world_index);
    }
    return recent;
}

void append_recent_diagnostics_traces(
    std::vector<DiagnosticsTrace>& traces,
    const RecentEngagementEvents& recent
) {
    for (const auto& trace : recent.diagnostics_traces) {
        DiagnosticsTrace copy = trace;
        std::uint64_t snapshot_version = copy.observation_packet_version;
        double source_time_s = copy.source_time_s;
        if (copy.launch_event_id != 0) {
            const auto match = std::find_if(
                recent.launch_events.begin(),
                recent.launch_events.end(),
                [&copy](const LaunchEvent& event) {
                    return event.event_id == copy.launch_event_id;
                }
            );
            if (match != recent.launch_events.end()) {
                source_time_s = match->event_time_s;
            }
            apply_export_trace_metadata(
                &copy,
                snapshot_version,
                source_time_s,
                kWp10LaunchNodeId
            );
        } else if (copy.effects_event_id != 0 || copy.damage_report_id != 0) {
            const auto effects_match = std::find_if(
                recent.effects_events.begin(),
                recent.effects_events.end(),
                [&copy](const EffectsEvent& event) {
                    return event.event_id == copy.effects_event_id;
                }
            );
            const auto damage_match = std::find_if(
                recent.damage_reports.begin(),
                recent.damage_reports.end(),
                [&copy](const DamageReport& report) {
                    return report.report_id == copy.damage_report_id;
                }
            );
            if (effects_match != recent.effects_events.end()) {
                source_time_s = effects_match->detonation_time_s;
            } else if (damage_match != recent.damage_reports.end()) {
                source_time_s = damage_match->report_time_s;
            }
            apply_export_trace_metadata(
                &copy,
                snapshot_version,
                source_time_s,
                kWp10EffectsDamageNodeId
            );
        } else {
            if (source_time_s == 0.0 && snapshot_version != 0) {
                source_time_s = static_cast<double>(snapshot_version - 1);
            }
            apply_export_trace_metadata(
                &copy,
                snapshot_version,
                source_time_s,
                kWp10ObservationExportNodeId
            );
        }
        traces.push_back(std::move(copy));
    }
}

void append_recent_engagement_events(
    EngagementEventPacket& packet,
    const RecentEngagementEvents& recent,
    const EngagementBatchRequest& request
) {
    if (request.include_launch_events) {
        packet.launch_events.insert(
            packet.launch_events.end(),
            recent.launch_events.begin(),
            recent.launch_events.end()
        );
    }
    if (request.include_effects_events) {
        packet.effects_events.insert(
            packet.effects_events.end(),
            recent.effects_events.begin(),
            recent.effects_events.end()
        );
    }
    if (request.include_damage_reports) {
        packet.damage_reports.insert(
            packet.damage_reports.end(),
            recent.damage_reports.begin(),
            recent.damage_reports.end()
        );
    }
    if (request.include_diagnostics_traces) {
        append_recent_diagnostics_traces(packet.diagnostics_traces, recent);
    }
}

ObservationBatchRequest observation_request_from_step_request(
    const ExecutionBatchStepRequest& request
) {
    return ObservationBatchRequest{
        .refs = refs_from_step_requests(request.step_requests),
        .include_agent_observations = request.include_agent_observations,
        .include_instrument_states = request.include_instrument_states,
        .include_mission_commands = request.include_mission_commands,
        .include_task_orders = request.include_task_orders,
        .include_leader_intents = request.include_leader_intents,
        .include_pilot_reports = request.include_pilot_reports,
    };
}

std::uint64_t next_snapshot_version(std::size_t index) {
    return static_cast<std::uint64_t>(index + 1);
}

double resolve_observation_source_time(
    const std::vector<AgentObservation>& observations,
    std::size_t fallback_count
) {
    if (observations.empty()) {
        return fallback_count == 0 ? 0.0 : static_cast<double>(fallback_count - 1);
    }

    double latest = 0.0;
    for (const auto& observation : observations) {
        latest = std::max(latest, observation.sim_time);
    }
    return latest;
}

double resolve_engagement_source_time(const EngagementEventPacket& packet) {
    double latest = 0.0;
    for (const auto& track : packet.track_packets) {
        latest = std::max(latest, track.source_time_s);
    }
    for (const auto& event : packet.launch_events) {
        latest = std::max(latest, event.event_time_s);
    }
    for (const auto& event : packet.effects_events) {
        latest = std::max(latest, event.detonation_time_s);
    }
    for (const auto& report : packet.damage_reports) {
        latest = std::max(latest, report.report_time_s);
    }
    for (const auto& trace : packet.diagnostics_traces) {
        latest = std::max(latest, trace.source_time_s);
    }
    if (latest == 0.0 && !packet.refs.empty()) {
        return static_cast<double>(packet.refs.size() - 1);
    }
    return latest;
}

std::uint64_t resolve_engagement_snapshot_version(const EngagementEventPacket& packet) {
    std::uint64_t latest = 0;
    for (const auto& track : packet.track_packets) {
        latest = std::max(latest, track.snapshot_version);
    }
    for (const auto& trace : packet.diagnostics_traces) {
        latest = std::max(latest, trace.observation_packet_version);
        latest = std::max(latest, trace.source_snapshot_version);
    }
    if (latest == 0 && !packet.refs.empty()) {
        return next_snapshot_version(packet.refs.size() - 1);
    }
    return latest;
}

void stable_sort_engagement_packet(EngagementEventPacket* packet) {
    if (packet == nullptr) {
        return;
    }
    stable_sort_track_packets(&packet->track_packets);
    stable_sort_launch_events(&packet->launch_events);
    stable_sort_effects_events(&packet->effects_events);
    stable_sort_damage_reports(&packet->damage_reports);
    stable_sort_diagnostics_traces(&packet->diagnostics_traces);
}

void add_reward_term_if_nonzero(
    std::vector<RewardTerm>* terms,
    const char* name,
    double value,
    const char* owner = "simulation"
) {
    if (terms == nullptr || value == 0.0) {
        return;
    }
    terms->push_back(RewardTerm{
        .name = name,
        .value = value,
        .term_owner = owner,
    });
}

RewardReport reward_report_from_step_result(
    const ExecutionEpisodeControllerStepResult& step_result,
    std::uint64_t fact_snapshot_version
) {
    RewardReport report{};
    report.fact_snapshot_version = fact_snapshot_version;
    report.fact_terms.push_back(RewardTerm{
        .name = "fact_snapshot_version",
        .value = static_cast<double>(fact_snapshot_version),
        .term_owner = "simulation",
    });

    if (!step_result.valid) {
        return report;
    }

    report.shaping_terms.push_back(RewardTerm{
        .name = "compiled_reward_total",
        .value = step_result.reward_total,
        .term_owner = "experiment",
    });

    if (step_result.controller_state.last_reward_total != step_result.reward_total) {
        add_reward_term_if_nonzero(
            &report.shaping_terms,
            "controller_reward_total",
            step_result.controller_state.last_reward_total,
            "experiment"
        );
    }

    if (step_result.step_info_valid) {
        const auto& info = step_result.step_info;
        add_reward_term_if_nonzero(&report.fact_terms, "runway_cross_m", info.runway_cross_m);
        add_reward_term_if_nonzero(&report.fact_terms, "runway_along_m", info.runway_along_m);
        if (info.on_runway) {
            add_reward_term_if_nonzero(&report.fact_terms, "on_runway", 1.0);
        }
        if (info.airborne) {
            add_reward_term_if_nonzero(&report.fact_terms, "airborne", 1.0);
        }
        if (info.gear_collapsed) {
            add_reward_term_if_nonzero(&report.fact_terms, "gear_collapsed", 1.0);
        }
        add_reward_term_if_nonzero(&report.fact_terms, "gear_stress", info.gear_stress);
    }

    const auto& state = step_result.controller_state;
    add_reward_term_if_nonzero(
        &report.fact_terms,
        "termination_state_active",
        state.last_termination_reason == "running" ? 0.0 : 1.0
    );
    add_reward_term_if_nonzero(&report.shaping_terms, "step_count", static_cast<double>(state.step_count), "experiment");
    add_reward_term_if_nonzero(&report.shaping_terms, "reward_total", state.last_reward_total, "experiment");
    if (step_result.structural_state_changed) {
        add_reward_term_if_nonzero(
            &report.shaping_terms,
            "structural_state_changed",
            1.0,
            "orchestration"
        );
    }

    return report;
}

TerminationSpec termination_spec_from_step_result(
    const ExecutionEpisodeControllerStepResult& step_result,
    bool truncated,
    std::uint64_t snapshot_version
) {
    TerminationSpec spec{};
    spec.reason = step_result.controller_state.last_termination_reason;
    spec.snapshot_version = snapshot_version;
    if (truncated) {
        spec.reason_source = "orchestration";
    } else if (step_result.terminated) {
        spec.reason_source = "simulation";
    } else {
        spec.reason_source = "policy";
    }
    return spec;
}

}  // namespace

RuntimeFacade::RuntimeFacade(std::size_t world_count)
    : runtime_(std::make_unique<WorldBatchRuntime>(world_count)) {}

RuntimeFacade::RuntimeFacade(const RuntimeBatchConfig& config)
    : runtime_(std::make_unique<WorldBatchRuntime>(config.world_count)) {
    configure_batch(config);
}

RuntimeFacade::RuntimeFacade(RuntimeFacade&&) noexcept = default;

RuntimeFacade& RuntimeFacade::operator=(RuntimeFacade&&) noexcept = default;

RuntimeFacade::~RuntimeFacade() = default;

void RuntimeFacade::configure_batch(const RuntimeBatchConfig& config) {
    runtime_->resize(config.world_count);
    runtime_->set_worker_threads(config.worker_threads);
}

RuntimeBatchConfig RuntimeFacade::batch_config() const noexcept {
    return RuntimeBatchConfig{
        .world_count = runtime_->world_count(),
        .worker_threads = runtime_->worker_threads(),
    };
}

RuntimeCapabilities RuntimeFacade::capabilities() const noexcept {
    return RuntimeCapabilities{
        .supports_batch_runtime = runtime_ != nullptr,
        .supports_compiled_episode_controller = true,
        .supports_compiled_execution_step = true,
        .supports_gpu_visual = false,
        .supports_gpu_observation = false,
        .supports_gpu_flight_shaping = false,
        .supports_device_observation_view = false,
        .supports_resident_state = false,
        .supports_exact_gpu_backend = false,
        .supports_shadow_compare = false,
        .maintained_baseline_backend_profile_id =
            std::string(kMaintainedBaselineBackendProfileId),
        .maintained_baseline_parity_budget_ref =
            std::string(kMaintainedBaselineParityBudgetRef),
        .maintained_baseline_profile_status =
            std::string(kMaintainedBaselineProfileStatus),
        .device_observation_view_candidate_profile_id =
            std::string(kDeviceObservationViewCandidateProfileId),
        .device_observation_view_rejection_reason =
            std::string(kDeviceObservationViewRejectionReason),
        .exact_gpu_backend_candidate_profile_id =
            std::string(kExactGpuBackendCandidateProfileId),
        .exact_gpu_backend_rejection_reason =
            std::string(kExactGpuBackendRejectionReason),
        .resident_state_candidate_profile_id =
            std::string(kResidentStateCandidateProfileId),
        .resident_state_candidate_parity_budget_ref =
            std::string(kResidentStateCandidateParityBudgetRef),
        .resident_state_rejection_reason =
            std::string(kResidentStateRejectionReason),
        .shadow_compare_candidate_profile_id =
            std::string(kShadowCompareCandidateProfileId),
        .shadow_compare_candidate_parity_budget_ref =
            std::string(kShadowCompareCandidateParityBudgetRef),
        .shadow_compare_rejection_reason =
            std::string(kShadowCompareRejectionReason),
        .multi_fidelity_rejection_reason =
            std::string(kMultiFidelityRejectionReason),
    };
}

RuntimeFidelityAdmission RuntimeFacade::admit_fidelity_request(
    const RuntimeFidelityRequest& request
) const {
    RuntimeFidelityRequest normalized = request;
    if (normalized.provider_family.empty()) {
        normalized.provider_family =
            std::string(kRuntimeFidelityProviderFamilyNone);
    }

    const runtime::fidelity::FidelityProfileAdmissionResult contract_result =
        runtime::fidelity::admit_fidelity_profile_request(
            fidelity_contract_request_from_facade(normalized)
        );
    RuntimeFidelityAdmission admission =
        runtime_fidelity_admission_from_contract(normalized, contract_result);

    if (!contract_result.admitted) {
        return admission;
    }

    if (normalized.provider_family ==
        kRuntimeFidelityProviderFamilyNone) {
        admission.selected_provider_family =
            std::string(kRuntimeFidelityProviderFamilyNone);
        if (find_stage_node_manifest(kWp10ObservationExportNodeId) != nullptr) {
            admission.selected_stage_node_id =
                std::string(kWp10ObservationExportNodeId);
        }
        return admission;
    }

    if (normalized.provider_family ==
        kRuntimeFidelityProviderFamilyReferenceCpu) {
        admission.selected_provider_family =
            std::string(kRuntimeFidelityProviderFamilyReferenceCpu);
        if (find_stage_node_manifest(kWp10ObservationExportNodeId) != nullptr) {
            admission.selected_stage_node_id =
                std::string(kWp10ObservationExportNodeId);
        }
        return admission;
    }

    admission.admitted = false;
    admission.baseline_exact_evaluation = false;
    admission.selected_provider_family =
        std::string(kRuntimeFidelityProviderFamilyNone);
    admission.selected_stage_node_id.clear();
    if (normalized.provider_family == "resident" ||
        normalized.provider_family == "resident_state") {
        admission.rejection_reason =
            std::string(runtime::fidelity::kFidelityProfileRejectionResidentState);
    } else if (normalized.provider_family == "shadow") {
        admission.rejection_reason =
            std::string(runtime::fidelity::kFidelityProfileRejectionShadowCompare);
    } else {
        admission.rejection_reason =
            std::string(runtime::fidelity::kFidelityProfileRejectionExactGpu);
    }
    if (admission.errors.empty()) {
        admission.errors.push_back(
            "requested provider_family is not maintained by the facade-owned baseline"
        );
    }
    return admission;
}

RuntimeCounterfactualSnapshot RuntimeFacade::snapshot_counterfactual_entity(
    const WorldEntityRef& ref,
    const RuntimeFidelityAdmission& fidelity_admission,
    const std::string& cadence_reason,
    const std::vector<std::string>& evidence_refs
) const {
    return counterfactual_snapshot_from_runtime(
        *runtime_,
        ref,
        fidelity_admission,
        cadence_reason,
        evidence_refs
    );
}

RuntimeCounterfactualBranchResult RuntimeFacade::run_counterfactual_branch(
    const RuntimeCounterfactualBranchRequest& request
) const {
    RuntimeCounterfactualBranchResult result{};
    result.evidence_refs = request.evidence_refs;
    result.evidence_refs.push_back("RuntimeFacade.run_counterfactual_branch");

    if (request.allow_raw_authoritative_state_mutation) {
        result.rejection_reason =
            std::string(kRuntimeCounterfactualRawMutationRejection);
        return result;
    }
    if (runtime_string_blank(request.replay_envelope_id)) {
        result.rejection_reason =
            std::string(kRuntimeCounterfactualMissingReplayEnvelope);
        return result;
    }
    if (runtime_string_blank(request.branch_point_id)) {
        result.rejection_reason =
            std::string(kRuntimeCounterfactualMissingBranchPoint);
        return result;
    }

    result.fidelity_admission = admit_fidelity_request(request.fidelity_request);
    if (!result.fidelity_admission.admitted) {
        result.rejection_reason =
            std::string(kRuntimeCounterfactualUnsupportedFidelity);
        if (!result.fidelity_admission.rejection_reason.empty()) {
            result.evidence_refs.push_back(
                "fidelity_rejection=" + result.fidelity_admission.rejection_reason
            );
        }
        return result;
    }

    const std::uint32_t seed =
        request.deterministic_seed == 0U
            ? 0U
            : static_cast<std::uint32_t>(
                request.deterministic_seed & 0xffffffffULL
            );
    BatchWorldSetupRequest setup =
        single_world_counterfactual_setup(request.baseline_setup, seed);

    RuntimeFacade parent(1);
    RuntimeFacade branch(1);
    const BatchWorldSetupResult parent_setup = parent.apply_world_setup(setup);
    const BatchWorldSetupResult branch_setup = branch.apply_world_setup(setup);

    WorldEntityRef selected_ref{
        .world_index = 0,
        .entity_id = counterfactual_spawned_entity_id(
            parent_setup,
            request.entity_ref
        ),
    };
    if (selected_ref.entity_id == 0U || branch_setup.entity_ids.empty()) {
        result.rejection_reason =
            std::string(kRuntimeCounterfactualSetupMissingEntity);
        return result;
    }

    std::string mutation_rejection;
    if (!apply_counterfactual_delta(&branch, selected_ref, request, &mutation_rejection)) {
        result.rejection_reason = mutation_rejection;
        return result;
    }

    std::vector<std::string> snapshot_evidence = result.evidence_refs;
    snapshot_evidence.push_back("replay_envelope_id=" + request.replay_envelope_id);
    snapshot_evidence.push_back("branch_point_id=" + request.branch_point_id);
    if (!request.branch_worldline_id.empty()) {
        snapshot_evidence.push_back("branch_worldline_id=" + request.branch_worldline_id);
    }

    result.parent_snapshot = parent.snapshot_counterfactual_entity(
        selected_ref,
        result.fidelity_admission,
        request.cadence_reason,
        snapshot_evidence
    );
    result.branch_snapshot = branch.snapshot_counterfactual_entity(
        selected_ref,
        result.fidelity_admission,
        request.cadence_reason,
        snapshot_evidence
    );
    result.comparison = compare_counterfactual_snapshots(
        result.parent_snapshot,
        result.branch_snapshot,
        request
    );
    result.admitted = result.comparison.comparable;
    if (!result.admitted) {
        result.rejection_reason = "counterfactual_worldline_comparison_not_comparable";
    }
    result.evidence_refs.insert(
        result.evidence_refs.end(),
        result.comparison.evidence_refs.begin(),
        result.comparison.evidence_refs.end()
    );
    return result;
}

std::size_t RuntimeFacade::world_count() const noexcept {
    return runtime_->world_count();
}

void RuntimeFacade::resize(std::size_t world_count) {
    runtime_->resize(world_count);
}

void RuntimeFacade::set_worker_threads(std::size_t worker_threads) noexcept {
    runtime_->set_worker_threads(worker_threads);
}

std::size_t RuntimeFacade::worker_threads() const noexcept {
    return runtime_->worker_threads();
}

std::size_t RuntimeFacade::effective_worker_threads() const noexcept {
    return runtime_->effective_worker_threads();
}

WorldBatchRuntime& RuntimeFacade::runtime() noexcept {
    return *runtime_;
}

const WorldBatchRuntime& RuntimeFacade::runtime() const noexcept {
    return *runtime_;
}

bool RuntimeFacade::load_database(const std::string& path) {
    return runtime_->load_database(path);
}

bool RuntimeFacade::load_unit_definitions(const std::string& path, std::string* error) {
    return runtime_->load_unit_definitions(path, error);
}

void RuntimeFacade::reset_batch(const BatchResetRequest& request) {
    runtime_->reset_batch(request.seeds);
}

std::vector<uint64_t> RuntimeFacade::apply_world_setup_batch(
    const std::vector<uint32_t>& seeds,
    const std::vector<WorldTerrainAssignment>& terrain_assignments,
    const std::vector<WorldWindAssignment>& wind_assignments,
    const std::vector<WorldZoneDefinition>& zones,
    const std::vector<WorldSpawnRequest>& requests,
    const std::vector<double>& time_steps
) {
    return runtime_->apply_world_setup_batch(
        seeds,
        terrain_assignments,
        wind_assignments,
        zones,
        requests,
        time_steps
    );
}

BatchWorldSetupResult RuntimeFacade::apply_world_setup(const BatchWorldSetupRequest& request) {
    BatchWorldSetupResult result{};
    result.entity_ids = runtime_->apply_world_setup_batch(
        request.seeds,
        request.terrain_assignments,
        request.wind_assignments,
        request.zones,
        request.spawn_requests,
        request.time_steps
    );
    result.typed_platform_spawn_results.reserve(
        request.typed_platform_spawn_requests.size()
    );
    for (std::size_t request_index = 0;
         request_index < request.typed_platform_spawn_requests.size();
         ++request_index) {
        result.typed_platform_spawn_results.push_back(
            materialize_typed_platform_spawn_request(
                *runtime_,
                static_cast<std::uint64_t>(request_index),
                request.typed_platform_spawn_requests[request_index]
            )
        );
    }
    return result;
}

void RuntimeFacade::set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment>& assignments) {
    runtime_->set_pilot_actions_batch(assignments);
}

void RuntimeFacade::set_mission_commands_batch(const std::vector<WorldMissionCommandAssignment>& assignments) {
    runtime_->set_mission_commands_batch(assignments);
}

void RuntimeFacade::set_task_orders_batch(const std::vector<WorldTaskOrderAssignment>& assignments) {
    runtime_->set_task_orders_batch(assignments);
}

void RuntimeFacade::set_leader_intents_batch(const std::vector<WorldLeaderIntentAssignment>& assignments) {
    runtime_->set_leader_intents_batch(assignments);
}

void RuntimeFacade::set_pilot_reports_batch(const std::vector<WorldPilotReportAssignment>& assignments) {
    runtime_->set_pilot_reports_batch(assignments);
}

void RuntimeFacade::step_batch() {
    runtime_->step_batch();
}

void RuntimeFacade::clear_execution_episode_batch() noexcept {
    runtime_->clear_execution_episode_controller_batch();
}

void RuntimeFacade::prime_execution_episode_batch(
    const std::vector<WorldEntityRef>& refs,
    const std::vector<ExecutionEpisodeState>& states
) {
    runtime_->prime_execution_episode_controller_batch(refs, states);
}

bool RuntimeFacade::execution_episode_ready(std::size_t world_index) const noexcept {
    return runtime_->execution_episode_controller_ready(world_index);
}

std::vector<ExecutionEpisodeState> RuntimeFacade::export_execution_episode_states(
    const std::vector<WorldEntityRef>& refs
) const {
    return runtime_->export_execution_episode_states_batch(refs);
}

std::vector<ExecutionEpisodeRuntimeProducts> RuntimeFacade::evaluate_execution_batch(
    const std::vector<WorldExecutionEpisodeStepRequest>& requests
) const {
    return runtime_->evaluate_execution_episode_batch(requests);
}

std::vector<ExecutionEpisodeRuntimeProducts> RuntimeFacade::step_execution_products_batch(
    const std::vector<WorldExecutionEpisodeStepRequest>& requests
) {
    return runtime_->step_execution_episode_batch(requests);
}

ExecutionBatchStepResult RuntimeFacade::step_execution_batch(const ExecutionBatchStepRequest& request) {
    ExecutionBatchStepResult result{};
    result.step_results = runtime_->step_execution_episode_results_batch(request.step_requests);
    result.execution_episode_states =
        runtime_->export_execution_episode_states_batch(refs_from_step_requests(request.step_requests));
    result.rewards.reserve(result.step_results.size());
    result.terminated.reserve(result.step_results.size());
    result.truncated.reserve(result.step_results.size());
    result.status_vectors.reserve(result.step_results.size());
    result.termination_reasons.reserve(result.step_results.size());
    result.termination_specs.reserve(result.step_results.size());
    result.reward_breakdown_jsons.reserve(result.step_results.size());
    result.reward_reports.reserve(result.step_results.size());
    result.step_infos.reserve(result.step_results.size());
    result.step_info_valid_flags.reserve(result.step_results.size());
    result.controller_state_changed_flags.reserve(result.step_results.size());
    for (std::size_t step_index = 0; step_index < result.step_results.size(); ++step_index) {
        const auto& step_result = result.step_results[step_index];
        const std::uint64_t snapshot_version = next_snapshot_version(step_index);
        result.rewards.push_back(step_result.reward_total);
        result.terminated.push_back(step_result.terminated);
        result.truncated.push_back(step_result.truncated);
        result.status_vectors.push_back(std::array<double, 4>{
            step_result.status0,
            step_result.status1,
            step_result.status2,
            step_result.status3,
        });
        result.termination_reasons.push_back(step_result.controller_state.last_termination_reason);
        result.termination_specs.push_back(termination_spec_from_step_result(
            step_result,
            step_result.truncated,
            snapshot_version
        ));
        result.reward_breakdown_jsons.push_back(step_result.controller_state.last_reward_breakdown_json);
        result.reward_reports.push_back(reward_report_from_step_result(step_result, snapshot_version));
        result.step_infos.push_back(step_result.step_info);
        result.step_info_valid_flags.push_back(step_result.step_info_valid);
        result.controller_state_changed_flags.push_back(step_result.structural_state_changed);
    }
    result.observation_packet = build_observation_packet(observation_request_from_step_request(request));
    return result;
}

std::vector<AgentObservation> RuntimeFacade::get_agent_observations_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_agent_observations_batch(refs);
}

std::vector<InstrumentState> RuntimeFacade::get_instrument_states_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_instrument_states_batch(refs);
}

std::vector<MissionCommand> RuntimeFacade::get_mission_commands_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_mission_commands_batch(refs);
}

std::vector<TaskOrder> RuntimeFacade::get_task_orders_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_task_orders_batch(refs);
}

std::vector<LeaderIntent> RuntimeFacade::get_leader_intents_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_leader_intents_batch(refs);
}

std::vector<PilotReport> RuntimeFacade::get_pilot_reports_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_pilot_reports_batch(refs);
}

ObservationBatchPacket RuntimeFacade::export_observation_packet(const std::vector<WorldEntityRef>& refs) const {
    return build_observation_packet(ObservationBatchRequest{
        .refs = refs,
        .include_agent_observations = true,
        .include_instrument_states = true,
        .include_mission_commands = true,
        .include_task_orders = true,
        .include_leader_intents = true,
        .include_pilot_reports = true,
    });
}

ObservationBatchPacket RuntimeFacade::export_observation_packet(const ObservationBatchRequest& request) const {
    return build_observation_packet(request);
}

std::vector<DiagnosticsTrace> RuntimeFacade::export_diagnostics_traces(
    const EngagementBatchRequest& request
) const {
    std::vector<DiagnosticsTrace> traces;

    std::vector<std::uint64_t> exported_world_indices;
    for (const auto& ref : request.refs) {
        if (!valid_runtime_world_index(*runtime_, ref.world_index)) {
            continue;
        }
        if (contains_world_index(exported_world_indices, ref.world_index)) {
            continue;
        }
        exported_world_indices.push_back(ref.world_index);
        append_recent_diagnostics_traces(
            traces,
            with_world_index(
                runtime_->world(static_cast<std::size_t>(ref.world_index)).export_recent_engagement_events(),
                ref.world_index
            )
        );
    }

    const bool needs_observations =
        request.include_track_packets || request.include_diagnostics_traces;
    if (!needs_observations || request.refs.empty() || request.trace_ids.empty()) {
        return traces;
    }

    std::vector<EngagementEntityRef> valid_refs;
    valid_refs.reserve(request.refs.size());
    for (const auto& ref : request.refs) {
        if (valid_runtime_world_index(*runtime_, ref.world_index)) {
            valid_refs.push_back(ref);
        }
    }
    if (valid_refs.empty()) {
        return traces;
    }

    const auto observations = runtime_->get_agent_observations_batch(
        world_refs_from_engagement_refs(valid_refs)
    );

    std::uint64_t next_snapshot_version = 1;
    for (std::size_t ref_index = 0; ref_index < valid_refs.size(); ++ref_index) {
        const auto& ref = valid_refs[ref_index];
        const auto& observation = observations[ref_index];
        const std::uint64_t snapshot_version = next_snapshot_version++;
        for (const auto& contact : observation.contacts) {
            const auto trace_id = request.trace_ids[traces.size() % request.trace_ids.size()];
            traces.push_back(diagnostics_trace_from_track_packet(
                trace_id,
                track_packet_from_observation_contact(
                    ref,
                    contact,
                    observation.sim_time,
                    snapshot_version
                ),
                snapshot_version
            ));
        }
    }
    stable_sort_diagnostics_traces(&traces);
    return traces;
}

RuntimeWindowResult RuntimeFacade::run_wp10_window(
    const RuntimeWindowRequest& request
) {
    return execute_runtime_window(
        request,
        RuntimeWindowCoordinatorCallbacks{
            .apply_pilot_actions =
                [this](const std::vector<WorldPilotActionAssignment>& assignments) {
                    set_pilot_actions_batch(assignments);
                },
            .apply_mission_commands =
                [this](const std::vector<WorldMissionCommandAssignment>& assignments) {
                    set_mission_commands_batch(assignments);
                },
            .step_window = [this]() {
                step_batch();
            },
            .export_observation_packet =
                [this](const ObservationBatchRequest& observation_request) {
                    return export_observation_packet(observation_request);
                },
            .export_engagement_event_packet =
                [this](const EngagementBatchRequest& engagement_request) {
                    return export_engagement_event_packet(engagement_request);
                },
            .export_diagnostics_traces =
                [this](const EngagementBatchRequest& engagement_request) {
                    return export_diagnostics_traces(engagement_request);
                },
        }
    );
}

EngagementEventPacket RuntimeFacade::export_engagement_event_packet(
    const EngagementBatchRequest& request
) const {
    EngagementEventPacket packet{};
    packet.refs = request.refs;
    packet.trace_ids = request.trace_ids;
    packet.barrier_id = std::string(kWp10ExportBarrierId);
    packet.barrier_sequence = kWp10ExportBarrierSequence;
    packet.barrier_detail = std::string(kWp10ExportBarrierDetail);

    std::vector<std::uint64_t> exported_world_indices;
    for (const auto& ref : request.refs) {
        if (!valid_runtime_world_index(*runtime_, ref.world_index)) {
            continue;
        }
        if (contains_world_index(exported_world_indices, ref.world_index)) {
            continue;
        }
        exported_world_indices.push_back(ref.world_index);
        append_recent_engagement_events(
            packet,
            with_world_index(
                runtime_->world(static_cast<std::size_t>(ref.world_index)).export_recent_engagement_events(),
                ref.world_index
            ),
            request
        );
    }

    const bool needs_observations =
        request.include_track_packets || request.include_diagnostics_traces;
    if (!needs_observations || request.refs.empty()) {
        finalize_recent_event_metadata(&packet);
        stable_sort_engagement_packet(&packet);
        apply_export_packet_metadata(
            &packet,
            resolve_engagement_snapshot_version(packet),
            resolve_engagement_source_time(packet)
        );
        finalize_diagnostics_ancestry(&packet);
        stable_sort_diagnostics_traces(&packet.diagnostics_traces);
        return packet;
    }

    std::vector<EngagementEntityRef> valid_refs;
    valid_refs.reserve(request.refs.size());
    for (const auto& ref : request.refs) {
        if (valid_runtime_world_index(*runtime_, ref.world_index)) {
            valid_refs.push_back(ref);
        }
    }
    if (valid_refs.empty()) {
        apply_export_packet_metadata(
            &packet,
            resolve_engagement_snapshot_version(packet),
            resolve_engagement_source_time(packet)
        );
        return packet;
    }

    const auto observations = runtime_->get_agent_observations_batch(
        world_refs_from_engagement_refs(valid_refs)
    );

    std::size_t observation_trace_index = packet.diagnostics_traces.size();
    std::uint64_t next_snapshot_version = 1;
    for (std::size_t ref_index = 0; ref_index < valid_refs.size(); ++ref_index) {
        const auto& ref = valid_refs[ref_index];
        const auto& observation = observations[ref_index];
        const std::uint64_t snapshot_version = next_snapshot_version++;
        for (const auto& contact : observation.contacts) {
            if (request.include_track_packets) {
                packet.track_packets.push_back(track_packet_from_observation_contact(
                    ref,
                    contact,
                    observation.sim_time,
                    snapshot_version
                ));
            }
            if (request.include_diagnostics_traces && !request.trace_ids.empty()) {
                const auto trace_id = request.trace_ids[
                    observation_trace_index % request.trace_ids.size()
                ];
                packet.diagnostics_traces.push_back(diagnostics_trace_from_track_packet(
                    trace_id,
                    track_packet_from_observation_contact(
                        ref,
                        contact,
                        observation.sim_time,
                        snapshot_version
                    ),
                    snapshot_version
                ));
                ++observation_trace_index;
            }
        }
    }
    stable_sort_engagement_packet(&packet);
    apply_export_packet_metadata(
        &packet,
        resolve_engagement_snapshot_version(packet),
        resolve_engagement_source_time(packet)
    );
    finalize_recent_event_metadata(&packet);
    finalize_diagnostics_ancestry(&packet);
    stable_sort_diagnostics_traces(&packet.diagnostics_traces);
    return packet;
}

ObservationBatchPacket RuntimeFacade::build_observation_packet(
    const ObservationBatchRequest& request
) const {
    ObservationBatchPacket packet{};
    packet.refs = request.refs;
    packet.barrier_id = "export";

    if (request.refs.empty()) {
        apply_observation_packet_provenance(&packet);
        return packet;
    }

    if (request.include_agent_observations) {
        packet.agent_observations = runtime_->get_agent_observations_batch(request.refs);
    }
    if (request.include_instrument_states) {
        packet.instrument_states = runtime_->get_instrument_states_batch(request.refs);
    }
    if (request.include_mission_commands) {
        packet.mission_commands = runtime_->get_mission_commands_batch(request.refs);
    }
    if (request.include_task_orders) {
        packet.task_orders = runtime_->get_task_orders_batch(request.refs);
    }
    if (request.include_leader_intents) {
        packet.leader_intents = runtime_->get_leader_intents_batch(request.refs);
    }
    if (request.include_pilot_reports) {
        packet.pilot_reports = runtime_->get_pilot_reports_batch(request.refs);
    }
    packet.snapshot_version = next_snapshot_version(packet.refs.size() - 1);
    packet.source_time_s = resolve_observation_source_time(packet.agent_observations, packet.refs.size());
    apply_observation_packet_provenance(&packet);
    return packet;
}
