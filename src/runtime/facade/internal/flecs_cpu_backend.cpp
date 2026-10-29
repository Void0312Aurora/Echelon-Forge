#include "runtime/facade/internal/flecs_cpu_backend.h"
#include "core/engine/simulation_kernel.h"
#include "runtime/crypto/sha256.h"
#include "runtime/contracts/native_world_state_codec.h"

#include <stdexcept>
#include <utility>

namespace {

runtime::backend::EntityKinematics to_backend_kinematics(const WorldEntityKinematics &state) {
    return {
        .x = state.x,
        .y = state.y,
        .z = state.z,
        .vx = state.vx,
        .vy = state.vy,
        .vz = state.vz,
        .heading = state.heading,
        .pitch = state.pitch,
        .roll = state.roll,
    };
}

WorldEntityKinematics to_cpu_kinematics(const runtime::backend::EntityKinematics &state) {
    return {
        .x = state.x,
        .y = state.y,
        .z = state.z,
        .vx = state.vx,
        .vy = state.vy,
        .vz = state.vz,
        .heading = state.heading,
        .pitch = state.pitch,
        .roll = state.roll,
    };
}

std::size_t required_world_index(const runtime::backend::ExportRequest &request) {
    if (!request.world_index.has_value()) {
        throw std::invalid_argument("backend export requires world_index");
    }
    return *request.world_index;
}

const std::string &required_string(const std::string *value, const char *label) {
    if (value == nullptr) {
        throw std::invalid_argument(std::string("backend request requires ") + label);
    }
    return *value;
}

} // namespace

FlecsCpuBackend::FlecsCpuBackend(std::size_t world_count)
    : runtime_(world_count), native_step_sequences_(world_count, 0) {}

runtime::backend::Configuration FlecsCpuBackend::configuration() const noexcept {
    return {
        .world_count = runtime_.world_count(),
        .worker_threads = runtime_.worker_threads(),
        .effective_worker_threads = runtime_.effective_worker_threads(),
    };
}

runtime::backend::BatchFailureStatus FlecsCpuBackend::failure_status() const {
    return {
        .healthy = runtime_.batch_healthy(),
        .generation = runtime_.batch_generation(),
        .requires_host_recreate = runtime_.batch_requires_host_recreate(),
        .failure_reason = runtime_.batch_failure_reason(),
    };
}

void FlecsCpuBackend::ensure_native_branch_source_healthy() const {
    const auto status = failure_status();
    if (status.healthy) {
        return;
    }
    if (status.requires_host_recreate) {
        throw std::logic_error(
            "native branch source batch is failed-closed; recreate the host process");
    }
    throw std::logic_error(
        "native branch source batch is failed-closed; call reset_batch before branching");
}

void FlecsCpuBackend::configure(const runtime::backend::ConfigureRequest &request) {
    if (request.world_count.has_value()) {
        runtime_.resize(*request.world_count);
        native_step_sequences_.resize(*request.world_count, 0);
    }
    if (request.worker_threads.has_value()) {
        runtime_.set_worker_threads(*request.worker_threads);
    }
}

runtime::backend::ContentResult
FlecsCpuBackend::load_content(const runtime::backend::ContentRequest &request) {
    runtime::backend::ContentResult result{};
    const std::string &path = required_string(request.path, "content path");
    switch (request.kind) {
    case runtime::backend::ContentKind::Database:
        result.loaded = runtime_.load_database(path);
        return result;
    case runtime::backend::ContentKind::UnitDefinitions:
        result.loaded = runtime_.load_unit_definitions(path, &result.error);
        return result;
    }
    throw std::invalid_argument("unknown backend content kind");
}

void FlecsCpuBackend::reset(const runtime::backend::ResetRequest &request) {
    runtime_.reset_batch(request.seeds.get());
    std::fill(native_step_sequences_.begin(), native_step_sequences_.end(), 0);
}

runtime::backend::SetupResult
FlecsCpuBackend::setup(const runtime::backend::SetupRequest &request) {
    runtime::backend::SetupResult result{};
    if (const auto *batch = std::get_if<runtime::backend::BatchSetup>(&request.operation)) {
        result.entity_ids = runtime_.apply_world_setup_batch(
            batch->seeds.get(), batch->terrain_assignments.get(), batch->wind_assignments.get(),
            batch->zones.get(), batch->spawn_requests.get(), batch->time_steps.get(),
            batch->sun_assignments.get(), batch->geodetic_anchor_assignments.get(),
            batch->maritime_assignments.get());
        return result;
    }
    if (const auto *layout = std::get_if<runtime::backend::LayoutSetup>(&request.operation)) {
        result.entity_ids = runtime_.apply_world_layout(
            layout->world_index, layout->seed,
            required_string(layout->terrain_type, "layout terrain_type"), layout->wind_speed_mps,
            layout->wind_dir_from_deg, layout->wind_shear_mps_per_km, layout->maritime_configured,
            layout->sea_state, layout->wave_heading_deg, layout->wave_period_s, layout->zones.get(),
            layout->spawn_requests.get(), layout->time_steps.get(), layout->sun_azimuth_deg,
            layout->sun_elevation_deg,
            WorldGeodeticAnchorAssignment{layout->world_index, layout->anchor_latitude_deg,
                                          layout->anchor_longitude_deg, layout->anchor_height_m});
        return result;
    }
    if (const auto *world_spawn =
            std::get_if<runtime::backend::WorldSpawnSetup>(&request.operation)) {
        if (world_spawn->request == nullptr) {
            throw std::invalid_argument("backend world spawn request is missing");
        }
        result.entity_ids.push_back(
            runtime_.spawn_unit_from_world_spawn_request(*world_spawn->request));
        return result;
    }
    if (const auto *typed_spawn =
            std::get_if<runtime::backend::TypedPlatformSpawnSetup>(&request.operation)) {
        if (typed_spawn->request == nullptr) {
            throw std::invalid_argument("backend typed platform spawn request is missing");
        }
        result.entity_ids.push_back(runtime_.spawn_typed_platform_unit(*typed_spawn->request));
        return result;
    }
    throw std::invalid_argument("unknown backend setup operation");
}

runtime::backend::InputResult FlecsCpuBackend::inject(const runtime::backend::InputBatch &input) {
    runtime::backend::InputResult result{};
    if (input.kinematics_write.has_value()) {
        const auto &write = *input.kinematics_write;
        result.kinematics_write_result =
            runtime_.try_set_entity_kinematics(write.ref, to_cpu_kinematics(write.state));
    }
    if (!input.pilot_actions.empty()) {
        runtime_.set_pilot_actions_batch(input.pilot_actions.get());
    }
    if (!input.command_links.empty()) {
        runtime_.set_command_links_batch(input.command_links.get());
    }
    if (!input.launch_requests.empty()) {
        result.launch_events = runtime_.apply_launch_requests_batch(input.launch_requests.get());
    }
    if (!input.mission_commands.empty()) {
        runtime_.set_mission_commands_maintained_batch(input.mission_commands.get());
    }
    if (!input.task_orders.empty()) {
        runtime_.set_task_orders_maintained_batch(input.task_orders.get());
    }
    if (!input.leader_intents.empty()) {
        runtime_.set_leader_intents_maintained_batch(input.leader_intents.get());
    }
    if (!input.pilot_reports.empty()) {
        runtime_.set_pilot_reports_maintained_batch(input.pilot_reports.get());
    }
    return result;
}

runtime::backend::EvaluationResult
FlecsCpuBackend::evaluate(const runtime::backend::EvaluationRequest &request) const {
    (void)request;
    return {};
}

runtime::backend::AdvanceResult
FlecsCpuBackend::advance(const runtime::backend::AdvanceRequest &request) {
    runtime::backend::AdvanceResult result{};
    switch (request.kind) {
    case runtime::backend::AdvanceKind::WorldBatch:
        runtime_.step_batch();
        for (auto &step : native_step_sequences_) {
            ++step;
        }
        return result;
    }
    throw std::invalid_argument("unknown backend advance kind");
}

runtime::backend::ExportResult
FlecsCpuBackend::export_state(const runtime::backend::ExportRequest &request) const {
    runtime::backend::ExportResult result{};
    const std::vector<WorldEntityRef> &refs = request.refs.get();
    if (request.include_kinematics) {
        if (request.kinematics_ref == nullptr) {
            throw std::invalid_argument("backend kinematics export requires kinematics_ref");
        }
        WorldEntityKinematics state{};
        const bool found = runtime_.try_get_entity_kinematics(*request.kinematics_ref, &state);
        result.kinematics.push_back({
            .ref = *request.kinematics_ref,
            .found = found,
            .state = found ? to_backend_kinematics(state) : runtime::backend::EntityKinematics{},
        });
    }
    if (request.include_recent_engagement_events) {
        result.recent_engagement_events =
            runtime_.export_recent_engagement_events(required_world_index(request));
    }
    if (request.include_world_time_step) {
        result.world_time_step = runtime_.world_time_step(required_world_index(request));
    }
    if (request.include_agent_observations) {
        result.agent_observations = runtime_.get_agent_observations_batch(refs);
    }
    if (request.include_instrument_states) {
        result.instrument_states = runtime_.get_instrument_states_batch(refs);
    }
    if (request.include_mission_commands) {
        result.mission_commands = runtime_.get_mission_commands_maintained_batch(refs);
    }
    if (request.include_task_orders) {
        result.task_orders = runtime_.get_task_orders_maintained_batch(refs);
    }
    if (request.include_leader_intents) {
        result.leader_intents = runtime_.get_leader_intents_maintained_batch(refs);
    }
    if (request.include_pilot_reports) {
        result.pilot_reports = runtime_.get_pilot_reports_maintained_batch(refs);
    }
    if (request.include_unit_messages) {
        result.unit_messages = runtime_.get_unit_messages_batch(refs);
    }
    return result;
}

runtime::backend::Diagnostics FlecsCpuBackend::diagnostics() const {
    runtime::backend::Diagnostics diagnostics{
        .backend_id = "flecs_cpu_reference",
        .world_count = runtime_.world_count(),
    };
    for (const auto &world : runtime_.composition_diagnostics()) {
        diagnostics.world_compositions.push_back({
            .world_index = world.world_index,
            .requested_manifest_sha256 = world.requested_manifest_sha256,
            .resolved_manifest_sha256 = world.resolved_manifest_sha256,
            .executable_graph_sha256 = world.executable_graph_sha256,
            .cpu_scheduler_topology_json = world.cpu_scheduler_topology_json,
            .scope_generations = world.scope_generations,
        });
    }
    return diagnostics;
}

RuntimeNativeSnapshotFacts FlecsCpuBackend::native_snapshot_facts(std::size_t world_index) const {
    ensure_native_branch_source_healthy();
    if (world_index >= runtime_.world_count()) {
        throw std::out_of_range("native identity world index out of range");
    }
    auto &world = const_cast<SimulationKernel &>(runtime_.world_raw_quarantine(world_index));
    const auto facts = [&]() {
        const std::string world_payload = runtime::contracts::serialize_native_world_state(world);
        const std::string rng_payload = runtime::contracts::serialize_native_rng_state(world);
        return RuntimeNativeSnapshotFacts{
            .step = native_step_sequences_[world_index],
            .state_digest = runtime::crypto::sha256_hex(world_payload),
            .event_cursor = native_step_sequences_[world_index],
            .rng_digest = runtime::crypto::sha256_hex(rng_payload),
            .terminated = false,
        };
    }();
    if (!facts.well_formed()) {
        throw std::runtime_error("native identity owner produced malformed snapshot facts");
    }
    return facts;
}

std::unique_ptr<RuntimeFacadeNativeBranch>
FlecsCpuBackend::fork_native_branch(std::size_t world_index, std::string intervention_digest,
                                    std::uint64_t horizon) {
    ensure_native_branch_source_healthy();
    if (world_index >= runtime_.world_count()) {
        throw std::out_of_range("native branch world index out of range");
    }
    auto &world = runtime_.world_raw_quarantine(world_index);
    return make_runtime_facade_native_branch(world, native_step_sequences_[world_index],
                                             std::move(intervention_digest), horizon);
}

std::vector<std::vector<std::uint64_t>>
FlecsCpuBackend::get_sensor_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                                bool use_gpu) const {
    return runtime_.get_sensor_candidate_ids_batch(refs, use_gpu);
}

std::vector<std::vector<std::uint64_t>>
FlecsCpuBackend::get_visual_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                                double range_m, bool use_gpu) const {
    return runtime_.get_visual_candidate_ids_batch(refs, range_m, use_gpu);
}

std::vector<std::vector<std::uint64_t>>
FlecsCpuBackend::get_comm_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                              bool use_gpu) const {
    return runtime_.get_comm_candidate_ids_batch(refs, use_gpu);
}

std::vector<WorldBatchVisualBindingCompatibilityScene>
FlecsCpuBackend::collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
    const std::vector<WorldEntityRef> &refs, int downsample,
    const std::vector<std::vector<std::uint64_t>> &candidate_ids_batch) const {
    return runtime_.collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        refs, downsample, candidate_ids_batch);
}
