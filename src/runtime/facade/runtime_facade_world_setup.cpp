#include "runtime/facade/runtime_facade_internal.h"

#include <cstdint>
#include <string>

namespace {

using namespace runtime_facade_internal;

WorldSpawnRequest
world_spawn_request_from_type_name_projection(const TypedPlatformSpawnRequest &request) {
    WorldSpawnRequest projection{};
    projection.world_index = request.world_index;
    projection.side = request.side;
    projection.type_name = request.source_type_name;
    projection.entity_name = request.entity_name;
    projection.is_agent = request.is_agent;
    projection.x = request.x;
    projection.y = request.y;
    projection.z = request.z;
    projection.heading = request.heading;
    projection.pitch = request.pitch;
    projection.roll = request.roll;
    projection.vx = request.vx;
    projection.vy = request.vy;
    projection.vz = request.vz;
    return projection;
}

std::uint64_t spawn_world_request_through_type_name_projection(IWorldBatchBackend &runtime,
                                                               const WorldSpawnRequest &request) {
    const ::runtime::backend::SetupResult result = runtime.setup(::runtime::backend::SetupRequest{
        .kind = ::runtime::backend::SetupKind::WorldSpawn,
        .world_spawn_request = &request,
    });
    return result.entity_ids.empty() ? 0U : result.entity_ids.front();
}

std::uint64_t
spawn_typed_request_through_maintained_path(IWorldBatchBackend &runtime,
                                            const TypedPlatformSpawnRequest &request) {
    const ::runtime::backend::SetupResult result = runtime.setup(::runtime::backend::SetupRequest{
        .kind = ::runtime::backend::SetupKind::TypedPlatformSpawn,
        .typed_platform_spawn_request = &request,
    });
    return result.entity_ids.empty() ? 0U : result.entity_ids.front();
}

TypedPlatformSpawnResult materialize_type_name_projection_typed_platform_spawn_request(
    IWorldBatchBackend &runtime, std::uint64_t request_index,
    const TypedPlatformSpawnRequest &request) {
    TypedPlatformSpawnAdmission admission =
        make_typed_platform_spawn_admission(request_index, request);
    const TypedPlatformSpawnValidationResult validation =
        validate_typed_platform_spawn_request(request);
    const TypedPlatformSetupSurfaceEvidence surface =
        classify_typed_platform_spawn_setup_surface(request);

    if (!validation.valid) {
        admission.reject(validation.rejection_reason.empty()
                             ? std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan)
                             : validation.rejection_reason);
        admission.errors = validation.errors;
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.type_name_projection_validation_failed");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (!valid_runtime_world_index(runtime, request.world_index)) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionWorldIndexOutOfRange));
        admission.add_error(
            "typed platform spawn world_index is outside the configured runtime batch");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.type_name_projection_world_index_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (!request.resolved_spawn_plan.admitted) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan));
        if (!request.resolved_spawn_plan.rejection_reason.empty()) {
            admission.add_error("resolved_spawn_plan rejected type_name projection admission: " +
                                request.resolved_spawn_plan.rejection_reason);
        }
        if (!request.resolved_spawn_plan.diagnostics_reason.empty()) {
            admission.add_error("resolved_spawn_plan diagnostics: " +
                                request.resolved_spawn_plan.diagnostics_reason);
        }
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.type_name_projection_plan_admission_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (!request.type_name_projection_preserved ||
        !request.capability_bundle.type_name_projection_preserved ||
        !request.resolved_spawn_plan.type_name_projection_preserved) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionTypeNameProjectionRequired));
        admission.add_error("typed platform setup must preserve type_name_projection_preserved "
                            "across request, bundle, and plan");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.type_name_projection_required_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (request.capability_bundle.source_type_name != request.source_type_name) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan));
        admission.add_error(
            "capability_bundle.source_type_name must match request.source_type_name");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.type_name_projection_bundle_identity_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (request.resolved_spawn_plan.source_type_name != request.source_type_name) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan));
        admission.add_error(
            "resolved_spawn_plan.source_type_name must match request.source_type_name");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.type_name_projection_source_type_name_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (request.resolved_spawn_plan.capability_bundle_id != request.capability_bundle.bundle_id) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan));
        admission.add_error(
            "resolved_spawn_plan.capability_bundle_id must match capability_bundle.bundle_id");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.type_name_projection_plan_identity_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    admission.admitted = true;
    append_runtime_evidence_ref(
        admission.evidence_refs,
        "RuntimeFacade.apply_world_setup.type_name_projection_typed_platform_spawn_bridge");
    append_runtime_evidence_ref(
        admission.evidence_refs,
        "RuntimeFacade.apply_world_setup.type_name_projection_materialization");

    TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
    result.setup_surface = surface.setup_surface;
    WorldSpawnRequest projection_request = world_spawn_request_from_type_name_projection(request);
    projection_request.type_name = request.resolved_spawn_plan.source_type_name;
    const std::uint64_t entity_id =
        spawn_world_request_through_type_name_projection(runtime, projection_request);
    if (entity_id == 0U) {
        result.admitted = true;
        result.materialized = false;
        result.fail_closed = true;
        result.rejection_reason = std::string(kTypedPlatformSpawnRejectionMaterializationFailed);
        result.add_error(
            "type_name projection materialization returned null entity for source_type_name=" +
            request.resolved_spawn_plan.source_type_name);
        append_runtime_evidence_ref(
            result.evidence_refs,
            "RuntimeFacade.apply_world_setup.type_name_projection_materialization_failed");
        return result;
    }

    result.admitted = true;
    result.materialized = true;
    result.entity_id = entity_id;
    append_runtime_evidence_ref(
        result.evidence_refs, "RuntimeFacade.apply_world_setup.type_name_projection_materialized");
    return result;
}

TypedPlatformSpawnResult
materialize_maintained_typed_platform_spawn_request(IWorldBatchBackend &runtime,
                                                    std::uint64_t request_index,
                                                    const TypedPlatformSpawnRequest &request) {
    TypedPlatformSpawnAdmission admission =
        make_typed_platform_spawn_admission(request_index, request);
    const TypedPlatformSetupSurfaceEvidence surface =
        classify_typed_platform_spawn_setup_surface(request);
    const TypedPlatformSpawnValidationResult validation =
        validate_maintained_typed_platform_spawn_request(request);

    if (!validation.valid) {
        admission.reject(validation.rejection_reason.empty()
                             ? std::string(kTypedPlatformSpawnRejectionMaintainedTypedSetupRequired)
                             : validation.rejection_reason);
        admission.errors = validation.errors;
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.maintained_typed_validation_failed");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (!valid_runtime_world_index(runtime, request.world_index)) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionWorldIndexOutOfRange));
        admission.add_error(
            "typed platform spawn world_index is outside the configured runtime batch");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.maintained_typed_world_index_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (!request.resolved_spawn_plan.admitted) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan));
        if (!request.resolved_spawn_plan.rejection_reason.empty()) {
            admission.add_error("resolved_spawn_plan rejected maintained typed admission: " +
                                request.resolved_spawn_plan.rejection_reason);
        }
        if (!request.resolved_spawn_plan.diagnostics_reason.empty()) {
            admission.add_error("resolved_spawn_plan diagnostics: " +
                                request.resolved_spawn_plan.diagnostics_reason);
        }
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.maintained_typed_plan_admission_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (request.capability_bundle.source_type_name != request.source_type_name) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan));
        admission.add_error(
            "capability_bundle.source_type_name must match request.source_type_name");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.maintained_typed_bundle_identity_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (request.resolved_spawn_plan.source_type_name != request.source_type_name) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan));
        admission.add_error(
            "resolved_spawn_plan.source_type_name must match request.source_type_name");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.maintained_typed_source_type_name_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    if (request.resolved_spawn_plan.capability_bundle_id != request.capability_bundle.bundle_id) {
        admission.reject(std::string(kTypedPlatformSpawnRejectionInvalidResolvedPlan));
        admission.add_error(
            "resolved_spawn_plan.capability_bundle_id must match capability_bundle.bundle_id");
        append_runtime_evidence_ref(
            admission.evidence_refs,
            "RuntimeFacade.apply_world_setup.maintained_typed_plan_identity_guard");
        TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
        result.setup_surface = surface.setup_surface;
        return result;
    }

    admission.admitted = true;
    append_runtime_evidence_ref(admission.evidence_refs,
                                "RuntimeFacade.apply_world_setup.maintained_typed_platform_spawn");
    append_runtime_evidence_ref(admission.evidence_refs,
                                "RuntimeFacade.apply_world_setup.maintained_typed_setup");

    TypedPlatformSpawnResult result = make_typed_platform_spawn_result(admission);
    result.setup_surface = surface.setup_surface;
    const std::uint64_t entity_id = spawn_typed_request_through_maintained_path(runtime, request);
    if (entity_id == 0U) {
        result.admitted = true;
        result.materialized = false;
        result.fail_closed = true;
        result.rejection_reason = std::string(kTypedPlatformSpawnRejectionMaterializationFailed);
        result.add_error(
            "maintained typed platform spawn returned null entity for source_type_name=" +
            request.source_type_name);
        append_runtime_evidence_ref(
            result.evidence_refs,
            "RuntimeFacade.apply_world_setup.maintained_typed_materialization_failed");
        return result;
    }

    result.admitted = true;
    result.materialized = true;
    result.entity_id = entity_id;
    append_runtime_evidence_ref(result.evidence_refs,
                                "RuntimeFacade.apply_world_setup.maintained_typed_materialized");
    return result;
}

TypedPlatformSpawnResult
materialize_typed_platform_spawn_request(IWorldBatchBackend &runtime, std::uint64_t request_index,
                                         const TypedPlatformSpawnRequest &request) {
    const TypedPlatformSetupSurfaceEvidence surface =
        classify_typed_platform_spawn_setup_surface(request);
    if (surface.maintained_typed_setup) {
        return materialize_maintained_typed_platform_spawn_request(runtime, request_index, request);
    }
    return materialize_type_name_projection_typed_platform_spawn_request(runtime, request_index,
                                                                         request);
}

} // namespace

void RuntimeFacade::reset_batch(const BatchResetRequest &request) {
    runtime_->reset(runtime::backend::ResetRequest{.seeds = request.seeds});
}

std::vector<uint64_t> RuntimeFacade::apply_world_setup_batch(
    const std::vector<uint32_t> &seeds,
    const std::vector<WorldTerrainAssignment> &terrain_assignments,
    const std::vector<WorldWindAssignment> &wind_assignments,
    const std::vector<WorldZoneDefinition> &zones, const std::vector<WorldSpawnRequest> &requests,
    const std::vector<double> &time_steps, const std::vector<WorldSunAssignment> &sun_assignments) {
    return runtime_
        ->setup(runtime::backend::SetupRequest{
            .kind = runtime::backend::SetupKind::Batch,
            .seeds = seeds,
            .terrain_assignments = terrain_assignments,
            .wind_assignments = wind_assignments,
            .zones = zones,
            .spawn_requests = requests,
            .time_steps = time_steps,
            .sun_assignments = sun_assignments,
        })
        .entity_ids;
}

BatchWorldSetupResult RuntimeFacade::apply_world_setup(const BatchWorldSetupRequest &request) {
    BatchWorldSetupResult result{};
    result.entity_ids = runtime_
                            ->setup(runtime::backend::SetupRequest{
                                .kind = runtime::backend::SetupKind::Batch,
                                .seeds = request.seeds,
                                .terrain_assignments = request.terrain_assignments,
                                .wind_assignments = request.wind_assignments,
                                .zones = request.zones,
                                .spawn_requests = request.spawn_requests,
                                .time_steps = request.time_steps,
                                .sun_assignments = request.sun_assignments,
                            })
                            .entity_ids;
    result.typed_platform_spawn_results.reserve(request.typed_platform_spawn_requests.size());
    for (std::size_t request_index = 0;
         request_index < request.typed_platform_spawn_requests.size(); ++request_index) {
        result.typed_platform_spawn_results.push_back(materialize_typed_platform_spawn_request(
            *runtime_, static_cast<std::uint64_t>(request_index),
            request.typed_platform_spawn_requests[request_index]));
    }
    return result;
}

RuntimeWorldLayoutResult
RuntimeFacade::apply_world_layout(const RuntimeWorldLayoutRequest &request) {
    RuntimeWorldLayoutResult result{};
    result.world_index = request.world_index;
    result.entity_ids = runtime_
                            ->setup(runtime::backend::SetupRequest{
                                .kind = runtime::backend::SetupKind::Layout,
                                .zones = request.zones,
                                .spawn_requests = request.spawn_requests,
                                .time_steps = request.time_steps,
                                .world_index = static_cast<std::size_t>(request.world_index),
                                .seed = request.seed,
                                .terrain_type = &request.terrain_type,
                                .wind_speed_mps = request.wind_speed_mps,
                                .wind_dir_from_deg = request.wind_dir_from_deg,
                                .wind_shear_mps_per_km = request.wind_shear_mps_per_km,
                                .maritime_configured = request.maritime_configured,
                                .sea_state = request.sea_state,
                                .wave_heading_deg = request.wave_heading_deg,
                                .wave_period_s = request.wave_period_s,
                                .sun_azimuth_deg = request.sun_azimuth_deg,
                                .sun_elevation_deg = request.sun_elevation_deg,
                            })
                            .entity_ids;
    return result;
}

double RuntimeFacade::world_time_step(std::size_t world_index) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .world_index = world_index,
            .include_world_time_step = true,
        })
        .world_time_step;
}
