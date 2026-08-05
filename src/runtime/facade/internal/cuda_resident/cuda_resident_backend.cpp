#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

#include "runtime/contracts/parity_budget_contracts.h"

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
#include "runtime/facade/internal/cuda_resident/cuda_world_store_device_api.h"
#endif

namespace runtime::cuda_resident {

namespace {

bool finite_in_range(double value, double minimum, double maximum) {
    return std::isfinite(value) && value >= minimum && value <= maximum;
}

bool finite_in_range(float value, float minimum, float maximum) {
    return std::isfinite(value) && value >= minimum && value <= maximum;
}

bool fixed_air_spawn_is_supported(const WorldSpawnRequest &spawn) {
    const double speed = std::sqrt(spawn.vx * spawn.vx + spawn.vy * spawn.vy + spawn.vz * spawn.vz);
    return spawn.type_name == kFixedAirFixtureTypeName && spawn.is_agent &&
           !spawn.ammo_override_enabled && spawn.missiles_remaining == 0 &&
           spawn.max_missiles == 0 && !spawn.weapon_cooldown_override_enabled &&
           spawn.weapon_cooldown_s == 2.0 && spawn.weapon_last_fire_time == -1.0 &&
           std::isfinite(spawn.x) && std::isfinite(spawn.y) && std::isfinite(spawn.z) &&
           std::isfinite(spawn.vx) && std::isfinite(spawn.vy) && std::isfinite(spawn.vz) &&
           std::isfinite(spawn.heading) && std::isfinite(spawn.pitch) &&
           std::isfinite(spawn.roll) && std::isfinite(speed) && spawn.z >= 100.0 &&
           spawn.z <= 10000.0 && speed >= 50.0 && speed <= 350.0 && std::abs(spawn.vy) <= 50.0 &&
           std::abs(spawn.vz) <= 50.0 && std::abs(spawn.pitch) <= 10.0 &&
           std::abs(spawn.roll) <= 10.0;
}

bool flight_controls_are_supported(const PilotAction &action) {
    return finite_in_range(action.stick_pitch, -1.0, 1.0) &&
           finite_in_range(action.stick_roll, -1.0, 1.0) &&
           finite_in_range(action.rudder, -1.0, 1.0) &&
           finite_in_range(action.throttle, 0.0, 1.0) &&
           finite_in_range(action.gear_handle, 0.0F, 1.0F) &&
           finite_in_range(action.flaps, 0.0F, 1.0F) &&
           finite_in_range(action.speedbrake, 0.0F, 1.0F) &&
           finite_in_range(action.brake, 0.0, 1.0) && !action.radar_active &&
           action.radar_scan_az == 0.0 && action.radar_scan_el == 0.0 && !action.tms_up &&
           !action.master_arm && !action.fire_weapon && !action.fire_gun &&
           action.weapon_select_id == 0 && !action.jettison_emergency && !action.program_chaff &&
           !action.program_flare;
}

CudaWorldKinematicsState to_cuda_kinematics(const WorldSpawnRequest &spawn) {
    return {
        .x = spawn.x,
        .y = spawn.y,
        .z = spawn.z,
        .vx = spawn.vx,
        .vy = spawn.vy,
        .vz = spawn.vz,
        .heading = spawn.heading,
        .pitch = spawn.pitch,
        .roll = spawn.roll,
    };
}

runtime::backend::EntityKinematics to_backend_kinematics(const CudaWorldKinematicsState &state) {
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

InstrumentState to_public_instrument(const CudaWorldInstrumentState &state) {
    InstrumentState result{};
    result.alt_baro_m = state.alt_baro_m;
    result.alt_radar_m = state.alt_radar_m;
    result.ias_mps = state.ias_mps;
    result.mach = state.mach;
    result.vvi_mps = state.vvi_mps;
    result.pitch_deg = state.pitch_deg;
    result.roll_deg = state.roll_deg;
    result.heading_deg = state.heading_deg;
    result.aoa_deg = state.aoa_deg;
    result.beta_deg = state.beta_deg;
    result.g_load_normal = state.g_load_normal;
    result.g_load_axial = state.g_load_axial;
    result.p_deg_s = state.p_deg_s;
    result.q_deg_s = state.q_deg_s;
    result.r_deg_s = state.r_deg_s;
    result.engine_rpm_pct = state.engine_rpm_pct;
    result.fuel_flow_kg_h = state.fuel_flow_kg_h;
    result.throttle_pos = state.throttle_pos;
    result.fuel_internal_kg = state.fuel_internal_kg;
    result.fuel_external_kg = state.fuel_external_kg;
    result.gear_pos = static_cast<float>(state.gear_pos);
    result.flaps_pos = static_cast<float>(state.flaps_pos);
    result.speedbrake_pos = static_cast<float>(state.speedbrake_pos);
    return result;
}

AgentObservation to_public_observation(const CudaWorldObservationState &state) {
    AgentObservation result{};
    result.sim_time = state.sim_time;
    result.id = state.id;
    result.x = state.x;
    result.y = state.y;
    result.z = state.z;
    result.vx = state.vx;
    result.vy = state.vy;
    result.vz = state.vz;
    result.heading = state.heading;
    result.pitch = state.pitch;
    result.roll = state.roll;
    result.speed = state.speed;
    result.health = state.health;
    result.gear_state = state.gear_state;
    result.throttle = state.throttle;
    result.total_reward = state.total_reward;
    return result;
}

CudaWorldFlightControls to_cuda_controls(const PilotAction &action) {
    return {
        .stick_pitch = action.stick_pitch,
        .stick_roll = action.stick_roll,
        .rudder = action.rudder,
        .throttle = action.throttle,
        .brake = action.brake,
        .gear_handle = action.gear_handle,
        .flaps = action.flaps,
        .speedbrake = action.speedbrake,
        .brake_left = action.brake_left,
        .brake_right = action.brake_right,
        // Match SimulationKernel::set_pilot_action: submitting an assignment
        // activates the component even if the incoming payload flag is false.
        .active = true,
    };
}

const CudaWorldResidentState &required_world(const CudaWorldStoreStateSnapshot &snapshot,
                                             std::size_t world_index) {
    if (world_index >= snapshot.worlds.size()) {
        throw std::out_of_range("CUDA resident export world_index is out of range");
    }
    return snapshot.worlds[world_index];
}

CudaResidentBarrierEvidence barrier_evidence(std::string_view barrier_id,
                                             std::vector<std::string> materialized_shards) {
    const auto &rules = runtime::parity::resident_candidate_barrier_contract();
    const auto rule = std::find_if(rules.begin(), rules.end(), [barrier_id](const auto &candidate) {
        return candidate.barrier_id == barrier_id;
    });
    if (rule == rules.end()) {
        throw std::logic_error("CUDA resident barrier is not owned by the RB2 contract");
    }
    const bool contract_satisfied = rule->enabled && materialized_shards == rule->visible_shards;
    return {
        .barrier_id = rule->barrier_id,
        .required_visible_shards = rule->visible_shards,
        .materialized_shards = std::move(materialized_shards),
        .enabled = rule->enabled,
        .contract_satisfied = contract_satisfied,
        .comparison_eligible = contract_satisfied && rule->comparison_eligible,
        .host_truth_available = contract_satisfied && rule->host_truth_available,
    };
}

} // namespace

runtime::backend::Configuration CudaResidentBackend::configuration() const noexcept {
    return {
        .world_count = store_.world_capacity(),
        .worker_threads = worker_threads_,
        .effective_worker_threads = 1,
    };
}

void CudaResidentBackend::configure(const runtime::backend::ConfigureRequest &request) {
    if (request.worker_threads.has_value()) {
        worker_threads_ = *request.worker_threads;
    }
    if (request.world_count.has_value() && !store_.configure(*request.world_count)) {
        throw std::runtime_error("CUDA resident backend configure failed: " +
                                 store_.diagnostics().last_error);
    }
}

runtime::backend::ContentResult
CudaResidentBackend::load_content(const runtime::backend::ContentRequest &) {
    reject_unimplemented_operation("load_content");
}

void CudaResidentBackend::reset(const runtime::backend::ResetRequest &request) {
    if (!store_.reset(request.seeds.get())) {
        throw std::runtime_error("CUDA resident backend reset failed: " +
                                 store_.diagnostics().last_error);
    }
}

runtime::backend::SetupResult
CudaResidentBackend::setup(const runtime::backend::SetupRequest &request) {
    if (request.kind != runtime::backend::SetupKind::Batch) {
        throw std::logic_error("CUDA RB6 supports only canonical batch setup");
    }
    const std::size_t world_count = store_.world_capacity();
    const auto &seeds = request.seeds.get();
    const auto &spawns = request.spawn_requests.get();
    const auto &time_steps = request.time_steps.get();
    if (seeds.size() != world_count || spawns.size() != world_count ||
        time_steps.size() != world_count || !request.terrain_assignments.empty() ||
        !request.wind_assignments.empty() || !request.zones.empty() ||
        !request.sun_assignments.empty()) {
        throw std::invalid_argument(
            "CUDA RB7 fixed-air setup requires one seed/spawn/time-step per world and no "
            "dynamic environment assignments");
    }

    std::vector<CudaFixedAirWorldSetup> fixed_worlds;
    fixed_worlds.reserve(world_count);
    for (std::size_t world = 0; world < world_count; ++world) {
        if (spawns[world].world_index != world || !fixed_air_spawn_is_supported(spawns[world]) ||
            !std::isfinite(time_steps[world]) || time_steps[world] < kPhaseBMinTimeStepS ||
            time_steps[world] > kPhaseBMaxTimeStepS) {
            throw std::invalid_argument(
                "CUDA RB7 setup is outside the fixed-air fixture capability");
        }
        fixed_worlds.push_back({
            .world_index = world,
            .time_step_s = time_steps[world],
            .kinematics = to_cuda_kinematics(spawns[world]),
        });
    }

    if (!store_.reset(seeds) || !store_.setup_fixed_air_fixture(&fixed_worlds)) {
        throw std::runtime_error("CUDA resident backend setup failed: " +
                                 store_.diagnostics().last_error);
    }
    runtime::backend::SetupResult result{};
    result.entity_ids.reserve(world_count);
    for (const CudaFixedAirWorldSetup &world : fixed_worlds) {
        result.entity_ids.push_back(world.entity_id);
    }
    return result;
}

runtime::backend::InputResult
CudaResidentBackend::inject(const runtime::backend::InputBatch &input) {
    if (input.kinematics_write.has_value() || !input.launch_requests.empty() ||
        !input.mission_commands.empty() || !input.task_orders.empty() ||
        !input.leader_intents.empty() || !input.pilot_reports.empty() ||
        input.clear_execution_episode_controller || input.prime_execution_episode_controller ||
        !input.execution_episode_refs.empty() || !input.execution_episode_states.empty()) {
        throw std::logic_error(
            "CUDA RB6 input injection supports only selected pilot flight controls");
    }
    const auto &actions = input.pilot_actions.get();
    if (actions.size() != store_.world_capacity()) {
        throw std::invalid_argument(
            "CUDA RB7 requires one pilot flight-control assignment per world");
    }
    std::vector<CudaWorldFlightControlAssignment> assignments;
    assignments.reserve(actions.size());
    for (std::size_t world = 0; world < actions.size(); ++world) {
        if (actions[world].world_index != world ||
            !flight_controls_are_supported(actions[world].action)) {
            throw std::invalid_argument(
                "CUDA RB7 pilot input is outside the bounded flight-control capability");
        }
        assignments.push_back({
            .world_index = actions[world].world_index,
            .entity_id = actions[world].entity_id,
            .controls = to_cuda_controls(actions[world].action),
        });
    }
    if (!store_.inject_flight_controls(assignments)) {
        throw std::runtime_error("CUDA resident backend input injection failed: " +
                                 store_.diagnostics().last_error);
    }
    return {};
}

runtime::backend::EvaluationResult
CudaResidentBackend::evaluate(const runtime::backend::EvaluationRequest &request) const {
    if (!request.execution_episode_requests.empty()) {
        throw std::logic_error(
            "CUDA resident backend evaluation supports only an empty execution request");
    }
    return {};
}

runtime::backend::AdvanceResult
CudaResidentBackend::advance(const runtime::backend::AdvanceRequest &request) {
    if (request.kind != runtime::backend::AdvanceKind::WorldBatch ||
        !request.execution_episode_requests.empty()) {
        throw std::logic_error("CUDA RB7 advances only a published Phase A/B/D device window");
    }
    if (!store_.advance_window()) {
        throw std::runtime_error("CUDA resident backend window commit failed: " +
                                 store_.diagnostics().last_error);
    }
    return {};
}

runtime::backend::ExportResult
CudaResidentBackend::export_state(const runtime::backend::ExportRequest &request) const {
    if (request.include_recent_engagement_events || request.include_execution_episode_ready ||
        request.include_execution_episode_states || request.include_mission_commands ||
        request.include_task_orders || request.include_leader_intents ||
        request.include_pilot_reports) {
        throw std::logic_error(
            "CUDA RB7 export supports only fixed-air kinematics/instruments/observation");
    }
    runtime::backend::ExportResult result{};
    if (!request.include_kinematics && !request.include_world_time_step &&
        !request.include_agent_observations && !request.include_instrument_states) {
        return result;
    }
    const CudaWorldStoreStateSnapshot snapshot = store_.state_snapshot();
    if (request.include_kinematics) {
        if (request.kinematics_ref == nullptr) {
            throw std::invalid_argument("CUDA RB6 kinematics export requires kinematics_ref");
        }
        const WorldEntityRef ref = *request.kinematics_ref;
        const CudaWorldResidentState &world =
            required_world(snapshot, static_cast<std::size_t>(ref.world_index));
        const bool found = world.setup_complete && world.entity_id == ref.entity_id;
        result.kinematics.push_back({
            .ref = ref,
            .found = found,
            .state = found ? to_backend_kinematics(world.kinematics)
                           : runtime::backend::EntityKinematics{},
        });
    }
    if (request.include_world_time_step) {
        if (!request.world_index.has_value()) {
            throw std::invalid_argument("CUDA RB6 time-step export requires world_index");
        }
        result.world_time_step = required_world(snapshot, *request.world_index).time_step_s;
    }
    if (request.include_agent_observations || request.include_instrument_states) {
        if (std::any_of(snapshot.worlds.begin(), snapshot.worlds.end(), [](const auto &world) {
                return world.barrier != CudaResidentBarrierCode::window_commit ||
                       world.shard_versions[static_cast<std::size_t>(
                           CudaResidentShard::observation)] < 1;
            })) {
            throw std::logic_error(
                "CUDA RB7 projection export requires a committed Phase-D window");
        }
        std::vector<std::size_t> worlds;
        if (!request.refs.empty()) {
            worlds.reserve(request.refs.get().size());
            for (const WorldEntityRef &ref : request.refs.get()) {
                const std::size_t world_index = static_cast<std::size_t>(ref.world_index);
                if (required_world(snapshot, world_index).entity_id != ref.entity_id) {
                    throw std::invalid_argument(
                        "CUDA RB7 projection export ref does not match resident identity");
                }
                worlds.push_back(world_index);
            }
        } else {
            worlds.resize(snapshot.worlds.size());
            for (std::size_t world = 0; world < worlds.size(); ++world)
                worlds[world] = world;
        }
        for (std::size_t world_index : worlds) {
            const CudaWorldResidentState &world = required_world(snapshot, world_index);
            if (!world.setup_complete) {
                throw std::logic_error("CUDA RB7 projection export requires completed setup");
            }
            if (request.include_agent_observations) {
                result.agent_observations.push_back(
                    to_public_observation(world.phase_d.observation));
            }
            if (request.include_instrument_states) {
                result.instrument_states.push_back(to_public_instrument(world.phase_d.instrument));
            }
        }
    }
    return result;
}

runtime::backend::Diagnostics CudaResidentBackend::diagnostics() const {
    return {
        .backend_id = std::string(kCudaResidentRb7BackendId),
        .world_count = store_.world_capacity(),
    };
}

CudaWorldStoreDiagnostics CudaResidentBackend::store_diagnostics() const {
    return store_.diagnostics();
}

void CudaResidentBackend::publish_stage() {
    if (!store_.publish_stage()) {
        throw std::runtime_error("CUDA resident backend stage publish failed: " +
                                 store_.diagnostics().last_error);
    }
}

bool CudaResidentBackend::partial_sync_commit() {
    return store_.partial_sync_commit();
}

CudaResidentExportSnapshot
CudaResidentBackend::export_snapshot(const std::string &request_id) const {
    if (request_id.empty()) {
        throw std::invalid_argument("CUDA resident snapshot export requires request_id");
    }
    const CudaWorldStoreStateSnapshot source = store_.state_snapshot();
    CudaResidentExportSnapshot result{};
    const bool phase_d_ready =
        !source.worlds.empty() &&
        std::all_of(source.worlds.begin(), source.worlds.end(), [](const auto &world) {
            return world.barrier == CudaResidentBarrierCode::window_commit &&
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::instrument)] >=
                       1 &&
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::observation)] >=
                       1 &&
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::reward)] >= 1 &&
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::termination)] >=
                       1 &&
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::events)] >= 1;
        });
    const std::vector<std::string> materialized_shards =
        phase_d_ready
            ? std::vector<std::string>{"identity",    "clock",      "snapshot",       "kinematics",
                                       "dynamics",    "instrument", "observation",    "reward",
                                       "termination", "events",     "export_envelope"}
            : std::vector<std::string>{"identity",   "clock",    "snapshot",
                                       "kinematics", "dynamics", "export_envelope"};
    result.barrier = barrier_evidence("export", materialized_shards);
    result.envelope.schema_version = std::string(
        phase_d_ready ? kCudaResidentPhaseDSnapshotSchemaV3 : kCudaResidentPhaseBSnapshotSchemaV2);
    result.envelope.field_set =
        phase_d_ready ? std::vector<std::string>{"entity_ref",       "seed",
                                                 "reset_generation", "clock",
                                                 "snapshot",         "kinematics",
                                                 "dynamics",         "instrument",
                                                 "observation",      "reward",
                                                 "termination",      "events",
                                                 "source_barrier_id"}
                      : std::vector<std::string>{
                            "entity_ref", "seed",       "reset_generation", "clock",
                            "snapshot",   "kinematics", "dynamics",         "source_barrier_id"};
    result.envelope.visibility_label = "export";
    result.envelope.provenance = std::string(phase_d_ready ? kCudaResidentPhaseDSnapshotProvenance
                                                           : kCudaResidentPhaseBSnapshotProvenance);
    result.worlds.reserve(source.worlds.size());

    std::optional<std::uint64_t> common_snapshot_version;
    std::optional<std::uint64_t> common_barrier_sequence;
    std::optional<CudaResidentBarrierCode> common_source_barrier;
    for (const CudaWorldResidentState &world : source.worlds) {
        if (!world.setup_complete) {
            throw std::logic_error("CUDA resident snapshot export requires completed setup");
        }
        if (world.barrier_sequence == std::numeric_limits<std::uint64_t>::max()) {
            throw std::overflow_error("CUDA resident export barrier sequence exhausted");
        }
        if (common_snapshot_version.has_value() &&
            *common_snapshot_version != world.global_version) {
            throw std::logic_error("CUDA resident batch snapshot versions diverged");
        }
        if ((common_barrier_sequence.has_value() &&
             *common_barrier_sequence != world.barrier_sequence) ||
            (common_source_barrier.has_value() && *common_source_barrier != world.barrier)) {
            throw std::logic_error("CUDA resident batch barrier identities diverged");
        }
        common_snapshot_version = world.global_version;
        common_barrier_sequence = world.barrier_sequence;
        common_source_barrier = world.barrier;

        CudaResidentWorldSnapshot snapshot{};
        snapshot.entity_ref = {
            .world_index = world.world_index,
            .entity_id = world.entity_id,
        };
        snapshot.seed = world.seed;
        snapshot.reset_generation = world.reset_generation;
        snapshot.clock = {
            .tick = world.clock_tick,
            .simulation_time_s = world.simulation_time_s,
        };
        snapshot.identity.world_id = world.world_index;
        snapshot.identity.global_version = world.global_version;
        snapshot.identity.barrier_id = "export";
        snapshot.identity.barrier_sequence = world.barrier_sequence + 1;
        for (std::size_t shard = 0; shard < kCudaResidentShardCount; ++shard) {
            std::uint64_t version = world.shard_versions[shard];
            if (shard == static_cast<std::size_t>(CudaResidentShard::export_envelope)) {
                version = world.global_version;
            }
            snapshot.identity.shard_versions.push_back({
                .shard_id = std::string(kCudaResidentShardIds[shard]),
                .version = version,
            });
        }
        snapshot.identity.lineage = {
            .source_snapshot_version = world.global_version,
            .source_backend_id =
                std::string(phase_d_ready ? kCudaResidentRb7BackendId : kCudaResidentRb6BackendId),
            .source_request_id = request_id,
        };
        snapshot.kinematics = world.kinematics;
        snapshot.dynamics = world.dynamics;
        snapshot.phase_d = world.phase_d;
        snapshot.source_barrier_id = std::string(cuda_resident_barrier_id(world.barrier));
        result.worlds.push_back(std::move(snapshot));
    }
    result.envelope.source_snapshot_version = common_snapshot_version.value_or(0);
    return result;
}

CudaResidentDeviceObservationView
CudaResidentBackend::export_device_observation_view(const std::string &request_id) const {
    if (request_id.empty()) {
        throw std::invalid_argument("CUDA device observation view requires request_id");
    }
    const CudaWorldStoreStateSnapshot state = store_.state_snapshot();
    if (state.worlds.empty() ||
        std::any_of(state.worlds.begin(), state.worlds.end(), [](const auto &world) {
            return world.barrier != CudaResidentBarrierCode::window_commit ||
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::instrument)] <
                       1 ||
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::observation)] <
                       1 ||
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::reward)] < 1 ||
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::termination)] <
                       1 ||
                   world.shard_versions[static_cast<std::size_t>(CudaResidentShard::events)] < 1;
        })) {
        throw std::logic_error("CUDA device observation view requires a committed Phase-D window");
    }
    CudaWorldStoreDeviceObservationRaw raw{};
    std::string error;
    if (!store_.export_device_observation_raw(&raw, &error)) {
        throw std::runtime_error("CUDA device observation view export failed: " + error);
    }
    CudaResidentDeviceObservationView view{};
    // The shared_ptr constructor owns the raw allocations on both success and
    // constructor failure; subsequent descriptor exceptions unwind through the
    // shared_ptr and invoke the deleter exactly once.
    view.lifetime = std::shared_ptr<void>(raw.values, [ids = raw.ids](void *values) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
        detail::release_cuda_world_store_device_observation(values, ids);
#else
            (void)values;
            (void)ids;
#endif
    });
    view.values = static_cast<const float *>(raw.values);
    view.ids = static_cast<const std::uint64_t *>(raw.ids);
    view.descriptor.output_shape = {static_cast<std::uint64_t>(raw.world_count),
                                    static_cast<std::uint64_t>(raw.values_per_world)};
    view.descriptor.element_count = raw.world_count * raw.values_per_world;
    view.descriptor.source_snapshot = raw.source_snapshot;
    view.descriptor.consumer_constraints = {
        "retain_lease_for_entire_device_consumer_call",
        "ids_are_in_a_separate_device_buffer",
        "ownership_copy_d2d",
        "not_zero_copy",
        "source_request_id:" + request_id,
    };
    return view;
}

device_consumer::AcquireResult
CudaResidentBackend::acquire_device_observation_lease(const std::string &request_id) const {
    device_consumer::AcquireResult result{};
    if (request_id.empty()) {
        result.failure = device_consumer::FailureCode::invalid_request;
        result.detail = "CUDA device observation lease requires request_id";
        return result;
    }
    CudaWorldStoreDeviceObservationLeaseRaw raw{};
    if (!store_.acquire_device_observation_lease_raw(&raw, &result.failure, &result.detail)) {
        return result;
    }
    auto &lease = result.lease;
    lease.lifetime = std::shared_ptr<void>(raw.values, [ids = raw.ids, event = raw.ready_event,
                                                        device = raw.device_ordinal](void *values) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
        detail::release_cuda_world_store_device_observation_lease(values, ids, event, device);
#else
            (void)values;
            (void)ids;
            (void)event;
            (void)device;
#endif
    });
    lease.values = static_cast<const float *>(raw.values);
    lease.ids = static_cast<const std::uint64_t *>(raw.ids);
    lease.ready_event = raw.ready_event;
    lease.device_ordinal = raw.device_ordinal;
    lease.producer_stream = raw.producer_stream;
    lease.epoch = raw.epoch;
    lease.observations = {
        .shape = {static_cast<std::uint64_t>(raw.world_count),
                  static_cast<std::uint64_t>(raw.values_per_world)},
        .strides = {static_cast<std::uint64_t>(raw.values_per_world), 1},
        .dtype = "float32",
        .element_count = raw.world_count * raw.values_per_world,
    };
    lease.ids_tensor = {
        .shape = {static_cast<std::uint64_t>(raw.world_count)},
        .strides = {1},
        .dtype = "uint64",
        .element_count = raw.world_count,
    };
    lease.source_request_id = request_id;
    result.failure = device_consumer::FailureCode::none;
    result.detail.clear();
    return result;
}

void CudaResidentBackend::reject_unimplemented_operation(const char *operation) {
    throw std::logic_error(std::string("CUDA resident backend ") + operation +
                           " is outside the RB7 Phase A/B/D shell");
}

CudaWorldStore &
testing::CudaResidentBackendTestAccess::world_store(CudaResidentBackend &backend) noexcept {
    return backend.store_;
}

} // namespace runtime::cuda_resident
