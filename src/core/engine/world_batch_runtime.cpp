#include "core/engine/world_batch_runtime.h"

#include "components/systems/data_link.h"
#include "components/systems/sensor.h"
#include "components/visual/visual_sensor.h"
#include "core/engine/simulation_kernel_command_surface.h"
#include "core/engine/world_batch_setup_helper.h"
#include "core/engine/world_batch_visual_binding_compatibility_helper.h"
#include "gpu/gpu_interaction_broadphase_runtime.h"

#include <algorithm>
#include <atomic>
#include <cmath>
#include <exception>
#include <mutex>
#include <stdexcept>
#include <thread>

namespace {

size_t hardware_thread_count() noexcept {
    const unsigned int hc = std::thread::hardware_concurrency();
    return hc == 0U ? 1U : static_cast<size_t>(hc);
}

template <typename Fn>
void parallel_for_index(size_t task_count, size_t requested_threads, Fn &&fn) {
    if (task_count == 0) {
        return;
    }
    const size_t thread_count =
        std::min(task_count, requested_threads == 0 ? hardware_thread_count()
                                                    : std::max<size_t>(1, requested_threads));
    if (thread_count <= 1) {
        for (size_t i = 0; i < task_count; ++i) {
            fn(i);
        }
        return;
    }

    const size_t chunk_size = (task_count + thread_count - 1) / thread_count;
    std::vector<std::thread> workers;
    workers.reserve(thread_count - 1);

    std::exception_ptr first_exception;
    std::mutex exception_mutex;

    auto run_range = [&](size_t begin, size_t end) {
        for (size_t i = begin; i < end; ++i) {
            try {
                fn(i);
            } catch (...) {
                std::lock_guard<std::mutex> lock(exception_mutex);
                if (first_exception == nullptr) {
                    first_exception = std::current_exception();
                }
                break;
            }
        }
    };

    size_t begin = 0;
    for (size_t worker_idx = 1; worker_idx < thread_count; ++worker_idx) {
        const size_t end = std::min(task_count, begin + chunk_size);
        workers.emplace_back(run_range, begin, end);
        begin = end;
    }
    run_range(begin, task_count);
    for (auto &worker : workers) {
        worker.join();
    }
    if (first_exception != nullptr) {
        std::rethrow_exception(first_exception);
    }
}

template <typename Item>
std::vector<std::vector<size_t>> group_item_indices_by_world(size_t world_count,
                                                             const std::vector<Item> &items) {
    std::vector<std::vector<size_t>> grouped(world_count);
    for (size_t item_index = 0; item_index < items.size(); ++item_index) {
        const size_t world_index = static_cast<size_t>(items[item_index].world_index);
        if (world_index >= world_count) {
            throw std::out_of_range("world index out of range");
        }
        grouped[world_index].push_back(item_index);
    }
    return grouped;
}

void validate_unique_world_indices(size_t world_count, const std::vector<uint64_t> &world_indices,
                                   const char *operation) {
    std::vector<bool> seen(world_count, false);
    for (const uint64_t raw_index : world_indices) {
        const auto world_index = static_cast<size_t>(raw_index);
        if (world_index >= world_count) {
            throw std::out_of_range("world index out of range");
        }
        if (seen[world_index]) {
            throw std::invalid_argument(std::string(operation) +
                                        " received a duplicate world index");
        }
        seen[world_index] = true;
    }
}

double default_bounding_radius_m(UnitType type) {
    switch (type) {
    case UnitType::Aircraft:
        return 10.0;
    case UnitType::Ship:
        return 50.0;
    case UnitType::Submarine:
        return 40.0;
    case UnitType::Missile:
        return 2.0;
    case UnitType::Facility:
    case UnitType::C2Node:
        return 20.0;
    default:
        return 5.0;
    }
}

double entity_bounding_radius_m(flecs::entity entity, UnitType fallback_type) {
    if (const auto *sig = entity.get<VisualSignature>()) {
        if (std::isfinite(sig->bounding_radius) && sig->bounding_radius > 0.0) {
            return sig->bounding_radius;
        }
    }
    return default_bounding_radius_m(fallback_type);
}

gpu::InteractionBroadphaseConfig
make_interaction_broadphase_config(std::size_t max_entities_per_world, double range_hint_m) {
    gpu::InteractionBroadphaseConfig config{};
    config.entities_per_world = static_cast<int>(std::max<std::size_t>(1, max_entities_per_world));
    config.cell_size_m = std::clamp(range_hint_m, 1000.0, 10000.0);
    config.max_entity_radius_m = 250.0;

    std::size_t bucket_count = 256;
    const std::size_t target = std::max<std::size_t>(512, max_entities_per_world * 8);
    while (bucket_count < target) {
        bucket_count <<= 1u;
    }
    config.hash_bucket_count = static_cast<int>(bucket_count);
    config.bucket_capacity = 64;
    return config;
}

std::vector<std::vector<uint64_t>>
decode_broadphase_candidate_ids(const std::vector<std::uint32_t> &words,
                                const std::vector<gpu::InteractionQueryPacked> &queries,
                                const std::vector<std::vector<uint64_t>> &ids_by_world,
                                int entities_per_world) {
    const std::size_t words_per_query = gpu::interaction_broadphase_word_count(entities_per_world);
    std::vector<std::vector<uint64_t>> out(queries.size());
    if (queries.empty() || words.empty()) {
        return out;
    }

    for (std::size_t query_index = 0; query_index < queries.size(); ++query_index) {
        const int world_index = queries[query_index].world_index;
        if (world_index < 0 || static_cast<std::size_t>(world_index) >= ids_by_world.size()) {
            continue;
        }
        const auto &ids = ids_by_world[static_cast<std::size_t>(world_index)];
        auto &dst = out[query_index];
        const auto *src = words.data() + query_index * words_per_query;
        for (std::size_t word_index = 0; word_index < words_per_query; ++word_index) {
            std::uint32_t mask = src[word_index];
            while (mask != 0u) {
                const std::uint32_t bit = mask & (~mask + 1u);
                const int bit_index = static_cast<int>(__builtin_ctz(mask));
                const int local_index = static_cast<int>(word_index * 32u) + bit_index;
                if (local_index >= 0 && static_cast<std::size_t>(local_index) < ids.size()) {
                    dst.push_back(ids[static_cast<std::size_t>(local_index)]);
                }
                mask ^= bit;
            }
        }
    }
    return out;
}

std::vector<std::vector<uint64_t>>
run_interaction_broadphase_candidate_ids(const std::vector<gpu::InteractionEntityPacked> &entities,
                                         const std::vector<gpu::InteractionQueryPacked> &queries,
                                         const std::vector<std::vector<uint64_t>> &ids_by_world,
                                         const gpu::InteractionBroadphaseConfig &config,
                                         bool use_gpu) {
    auto words =
        use_gpu ? gpu::build_interaction_broadphase_experiment_batch(entities, queries, config)
                : gpu::build_interaction_broadphase_reference_cpu_batch(entities, queries, config);
    return decode_broadphase_candidate_ids(words, queries, ids_by_world, config.entities_per_world);
}

uint64_t spawn_from_request(SimulationKernel &world, const WorldSpawnRequest &request) {
    const auto entity = world.spawn_unit(request.side, request.type_name, request.x, request.y,
                                         request.z, request.heading, request.pitch, request.roll,
                                         request.vx, request.vy, request.vz);
    if (!entity.is_valid()) {
        return entity.id();
    }

    if (request.ammo_override_enabled) {
        world.set_unit_ammo(entity.id(), request.missiles_remaining, request.max_missiles);
    }
    if (request.weapon_cooldown_override_enabled) {
        world.set_weapon_cooldown(entity.id(), request.weapon_cooldown_s,
                                  request.weapon_last_fire_time);
    }
    return entity.id();
}

} // namespace

WorldBatchRuntime::WorldBatchRuntime(size_t world_count) {
    resize(world_count);
}

void WorldBatchRuntime::resize(size_t world_count) {
    const size_t existing_count = worlds_.size();
    if (world_count < existing_count) {
        worlds_.resize(world_count);
    } else if (world_count > existing_count) {
        worlds_.reserve(world_count);
        for (size_t i = existing_count; i < world_count; ++i) {
            worlds_.push_back(std::make_unique<SimulationKernel>());
        }
    }
    execution_episode_controllers_.resize(world_count);
    execution_episode_controller_entity_ids_.resize(world_count, 0);
    execution_episode_controller_active_.resize(world_count, false);
}

SimulationKernel &WorldBatchRuntime::checked_world(size_t index) {
    if (index >= worlds_.size()) {
        throw std::out_of_range("world index out of range");
    }
    return *worlds_[index];
}

const SimulationKernel &WorldBatchRuntime::checked_world(size_t index) const {
    if (index >= worlds_.size()) {
        throw std::out_of_range("world index out of range");
    }
    return *worlds_[index];
}

SimulationKernel &WorldBatchRuntime::world_raw_quarantine(size_t index) {
    return checked_world(index);
}

const SimulationKernel &WorldBatchRuntime::world_raw_quarantine(size_t index) const {
    return checked_world(index);
}

size_t WorldBatchRuntime::resolve_worker_threads(size_t task_count) const noexcept {
    if (task_count == 0) {
        return 1;
    }
    const size_t configured =
        worker_threads_ == 0 ? hardware_thread_count() : std::max<size_t>(1, worker_threads_);
    return std::min(task_count, configured);
}

size_t WorldBatchRuntime::effective_worker_threads() const noexcept {
    return resolve_worker_threads(worlds_.size());
}

std::uint64_t
WorldBatchRuntime::spawn_unit_from_world_spawn_request(const WorldSpawnRequest &request) {
    const auto world_index = static_cast<size_t>(request.world_index);
    return spawn_from_request(checked_world(world_index), request);
}

std::uint64_t
WorldBatchRuntime::spawn_typed_platform_unit(const TypedPlatformSpawnRequest &request) {
    const auto world_index = static_cast<size_t>(request.world_index);
    auto &world = checked_world(world_index);
    const auto entity = world.spawn_unit(request.side, request.source_type_name, request.x,
                                         request.y, request.z, request.heading, request.pitch,
                                         request.roll, request.vx, request.vy, request.vz);
    return entity.id();
}

bool WorldBatchRuntime::try_get_entity_kinematics(const WorldEntityRef &ref,
                                                  WorldEntityKinematics *state) const {
    if (state == nullptr) {
        return false;
    }

    const auto world_index = static_cast<size_t>(ref.world_index);
    const auto &world = checked_world(world_index);
    const auto entity = world.get_world().entity(ref.entity_id);
    if (!entity.is_valid()) {
        return false;
    }

    const Transform *transform = entity.get<Transform>();
    const Velocity *velocity = entity.get<Velocity>();
    if (transform == nullptr || velocity == nullptr) {
        return false;
    }

    state->x = transform->x;
    state->y = transform->y;
    state->z = transform->z;
    state->vx = velocity->vx;
    state->vy = velocity->vy;
    state->vz = velocity->vz;
    state->heading = transform->heading;
    state->pitch = transform->pitch;
    state->roll = transform->roll;
    return true;
}

bool WorldBatchRuntime::try_set_entity_kinematics(const WorldEntityRef &ref,
                                                  const WorldEntityKinematics &state) {
    const auto world_index = static_cast<size_t>(ref.world_index);
    auto &world = checked_world(world_index);
    const auto entity = world.get_world().entity(ref.entity_id);
    if (!entity.is_valid()) {
        return false;
    }

    const Transform *transform = entity.get<Transform>();
    const Velocity *velocity = entity.get<Velocity>();
    if (transform == nullptr || velocity == nullptr) {
        return false;
    }

    entity.set<Transform>(Transform{
        .x = state.x,
        .y = state.y,
        .z = state.z,
        .heading = state.heading,
        .pitch = state.pitch,
        .roll = state.roll,
    });
    entity.set<Velocity>(Velocity{
        .vx = state.vx,
        .vy = state.vy,
        .vz = state.vz,
    });
    return true;
}

RecentEngagementEvents
WorldBatchRuntime::export_recent_engagement_events(size_t world_index) const {
    return checked_world(world_index).export_recent_engagement_events();
}

void WorldBatchRuntime::reset_batch(const std::vector<uint32_t> &seeds) {
    clear_execution_episode_controller_batch();
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        uint32_t seed = static_cast<uint32_t>(42 + i);
        if (seeds.size() == worlds_.size()) {
            seed = seeds[i];
        } else if (seeds.size() == 1) {
            seed = static_cast<uint32_t>(seeds[0] + static_cast<uint32_t>(i));
        }
        worlds_[i]->reset(seed);
    });
}

void WorldBatchRuntime::clear_execution_episode_controller_batch() noexcept {
    for (std::size_t world_index = 0; world_index < worlds_.size(); ++world_index) {
        clear_execution_episode_controller(world_index);
    }
}

void WorldBatchRuntime::clear_execution_episode_controller(std::size_t world_index) noexcept {
    execution_episode_controllers_[world_index].clear_state();
    execution_episode_controller_entity_ids_[world_index] = 0;
    execution_episode_controller_active_[world_index] = false;
}

void WorldBatchRuntime::prime_execution_episode_controller_batch(
    const std::vector<WorldEntityRef> &refs, const std::vector<ExecutionEpisodeState> &states) {
    if (refs.size() != states.size()) {
        throw std::invalid_argument(
            "prime_execution_episode_controller_batch refs/states size mismatch");
    }
    for (std::size_t i = 0; i < refs.size(); ++i) {
        const auto world_index = static_cast<std::size_t>(refs[i].world_index);
        if (world_index >= worlds_.size()) {
            throw std::out_of_range("world index out of range");
        }
        execution_episode_controllers_[world_index].import_state(states[i]);
        execution_episode_controller_entity_ids_[world_index] = refs[i].entity_id;
        execution_episode_controller_active_[world_index] = true;
    }
}

bool WorldBatchRuntime::execution_episode_controller_ready(size_t world_index) const noexcept {
    return world_index < execution_episode_controller_active_.size() &&
           execution_episode_controller_active_[world_index] &&
           execution_episode_controllers_[world_index].has_state();
}

ExecutionEpisodeController &
WorldBatchRuntime::checked_execution_episode_controller(size_t world_index, uint64_t entity_id) {
    if (!execution_episode_controller_ready(world_index)) {
        throw std::runtime_error("execution episode controller is not primed for world");
    }
    if (execution_episode_controller_entity_ids_[world_index] != entity_id) {
        throw std::runtime_error("execution episode controller entity_id mismatch");
    }
    return execution_episode_controllers_[world_index];
}

const ExecutionEpisodeController &
WorldBatchRuntime::checked_execution_episode_controller(size_t world_index,
                                                        uint64_t entity_id) const {
    if (!execution_episode_controller_ready(world_index)) {
        throw std::runtime_error("execution episode controller is not primed for world");
    }
    if (execution_episode_controller_entity_ids_[world_index] != entity_id) {
        throw std::runtime_error("execution episode controller entity_id mismatch");
    }
    return execution_episode_controllers_[world_index];
}

void WorldBatchRuntime::validate_execution_episode_step_requests(
    const std::vector<WorldExecutionEpisodeStepRequest> &requests) const {
    std::vector<bool> seen(worlds_.size(), false);
    for (const auto &request : requests) {
        const auto world_index = static_cast<std::size_t>(request.world_index);
        if (world_index >= worlds_.size()) {
            throw std::out_of_range("world index out of range");
        }
        if (seen[world_index]) {
            throw std::invalid_argument("duplicate world_index in execution episode step batch");
        }
        seen[world_index] = true;
        static_cast<void>(checked_execution_episode_controller(world_index, request.entity_id));
    }
}

std::vector<ExecutionEpisodeState> WorldBatchRuntime::export_execution_episode_states_batch(
    const std::vector<WorldEntityRef> &refs) const {
    std::vector<ExecutionEpisodeState> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](std::size_t i) {
        const auto &ref = refs[i];
        out[i] = checked_execution_episode_controller(static_cast<std::size_t>(ref.world_index),
                                                      ref.entity_id)
                     .export_state();
    });
    return out;
}

std::vector<ExecutionEpisodeRuntimeProducts> WorldBatchRuntime::evaluate_execution_episode_batch(
    const std::vector<WorldExecutionEpisodeStepRequest> &requests) const {
    validate_execution_episode_step_requests(requests);
    std::vector<ExecutionEpisodeRuntimeProducts> out(requests.size());
    parallel_for_index(requests.size(), worker_threads_, [&](std::size_t i) {
        const auto &request = requests[i];
        out[i] = checked_execution_episode_controller(static_cast<std::size_t>(request.world_index),
                                                      request.entity_id)
                     .evaluate(request.config, request.env_state);
    });
    return out;
}

std::vector<ExecutionEpisodeRuntimeProducts> WorldBatchRuntime::step_execution_episode_batch(
    const std::vector<WorldExecutionEpisodeStepRequest> &requests) {
    validate_execution_episode_step_requests(requests);
    std::vector<ExecutionEpisodeRuntimeProducts> out(requests.size());
    parallel_for_index(requests.size(), worker_threads_, [&](std::size_t i) {
        const auto &request = requests[i];
        out[i] = checked_execution_episode_controller(static_cast<std::size_t>(request.world_index),
                                                      request.entity_id)
                     .step(request.config, request.env_state);
    });
    return out;
}

std::vector<ExecutionEpisodeControllerStepResult>
WorldBatchRuntime::step_execution_episode_results_batch(
    const std::vector<WorldExecutionEpisodeStepRequest> &requests) {
    validate_execution_episode_step_requests(requests);
    std::vector<ExecutionEpisodeControllerStepResult> out(requests.size());
    parallel_for_index(requests.size(), worker_threads_, [&](std::size_t i) {
        const auto &request = requests[i];
        out[i] = checked_execution_episode_controller(static_cast<std::size_t>(request.world_index),
                                                      request.entity_id)
                     .step_result(request.config, request.env_state);
    });
    return out;
}

void WorldBatchRuntime::step_batch() {
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) { worlds_[i]->step(); });
}

void WorldBatchRuntime::step_worlds(const std::vector<uint64_t> &world_indices) {
    if (world_indices.empty()) {
        return;
    }
    validate_unique_world_indices(worlds_.size(), world_indices, "step_worlds");
    parallel_for_index(world_indices.size(), worker_threads_, [&](size_t i) {
        checked_world(static_cast<size_t>(world_indices[i])).step();
    });
}

bool WorldBatchRuntime::load_database(const std::string &path) {
    std::atomic<bool> ok{true};
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        if (!worlds_[i]->load_database(path)) {
            ok.store(false, std::memory_order_relaxed);
        }
    });
    return ok.load(std::memory_order_relaxed);
}

bool WorldBatchRuntime::load_unit_definitions(const std::string &path, std::string *error) {
    std::atomic<bool> ok{true};
    std::string first_error;
    std::mutex error_mutex;
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        std::string local_error;
        const bool local_ok = worlds_[i]->load_unit_definitions(path, &local_error);
        if (!local_ok) {
            ok.store(false, std::memory_order_relaxed);
            if (!local_error.empty()) {
                std::lock_guard<std::mutex> lock(error_mutex);
                if (first_error.empty()) {
                    first_error = local_error;
                }
            }
        }
    });
    if (error != nullptr) {
        *error = first_error;
    }
    return ok.load(std::memory_order_relaxed);
}

void WorldBatchRuntime::set_time_step(double dt) {
    parallel_for_index(worlds_.size(), worker_threads_,
                       [&](size_t i) { worlds_[i]->set_time_step(dt); });
}

void WorldBatchRuntime::set_terrain_types_batch(
    const std::vector<WorldTerrainAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        world_batch_setup::apply_terrain_assignments(world, assignments, grouped[world_index]);
    });
}

void WorldBatchRuntime::set_winds_batch(const std::vector<WorldWindAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        world_batch_setup::apply_wind_assignments(world, assignments, grouped[world_index]);
    });
}

void WorldBatchRuntime::set_suns_batch(const std::vector<WorldSunAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        world_batch_setup::apply_sun_assignments(world, assignments, grouped[world_index]);
    });
}

void WorldBatchRuntime::clear_zones_batch(const std::vector<uint64_t> &world_indices) {
    if (world_indices.empty()) {
        parallel_for_index(worlds_.size(), worker_threads_,
                           [&](size_t i) { worlds_[i]->clear_zones(); });
        return;
    }
    validate_unique_world_indices(worlds_.size(), world_indices, "clear_zones_batch");
    parallel_for_index(world_indices.size(), worker_threads_, [&](size_t i) {
        checked_world(static_cast<size_t>(world_indices[i])).clear_zones();
    });
}

void WorldBatchRuntime::add_zones_batch(const std::vector<WorldZoneDefinition> &zones) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), zones);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        world_batch_setup::append_zones(world, zones, grouped[world_index]);
    });
}

std::vector<uint64_t>
WorldBatchRuntime::spawn_units_batch(const std::vector<WorldSpawnRequest> &requests) {
    std::vector<uint64_t> out(requests.size(), 0);
    const auto grouped = group_item_indices_by_world(worlds_.size(), requests);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            out[item_index] = spawn_from_request(world, requests[item_index]);
        }
    });
    return out;
}

std::vector<uint64_t> WorldBatchRuntime::apply_world_setup_batch(
    const std::vector<uint32_t> &seeds,
    const std::vector<WorldTerrainAssignment> &terrain_assignments,
    const std::vector<WorldWindAssignment> &wind_assignments,
    const std::vector<WorldZoneDefinition> &zones, const std::vector<WorldSpawnRequest> &requests,
    const std::vector<double> &time_steps, const std::vector<WorldSunAssignment> &sun_assignments) {
    if (!time_steps.empty() && time_steps.size() != 1 && time_steps.size() != worlds_.size()) {
        throw std::invalid_argument("time_steps must have size 0, 1, or world_count");
    }

    std::vector<uint64_t> out(requests.size(), 0);
    const auto terrain_grouped = group_item_indices_by_world(worlds_.size(), terrain_assignments);
    const auto wind_grouped = group_item_indices_by_world(worlds_.size(), wind_assignments);
    const auto sun_grouped = group_item_indices_by_world(worlds_.size(), sun_assignments);
    const auto zone_grouped = group_item_indices_by_world(worlds_.size(), zones);
    const auto spawn_grouped = group_item_indices_by_world(worlds_.size(), requests);
    clear_execution_episode_controller_batch();

    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        world_batch_setup::apply_world_setup(
            world, world_index, worlds_.size(), seeds, terrain_assignments,
            terrain_grouped[world_index], wind_assignments, wind_grouped[world_index],
            sun_assignments, sun_grouped[world_index], zones, zone_grouped[world_index], requests,
            spawn_grouped[world_index], time_steps, &out, spawn_from_request);
    });
    return out;
}

std::vector<uint64_t> WorldBatchRuntime::apply_world_layout(
    std::size_t world_index, std::uint32_t seed, const std::string &terrain_type,
    double wind_speed_mps, double wind_dir_from_deg, double wind_shear_mps_per_km,
    bool maritime_configured, double sea_state, double wave_heading_deg, double wave_period_s,
    const std::vector<WorldZoneDefinition> &zones, const std::vector<WorldSpawnRequest> &requests,
    const std::vector<double> &time_steps, double sun_azimuth_deg, double sun_elevation_deg) {
    if (!time_steps.empty() && time_steps.size() != 1 && time_steps.size() != worlds_.size()) {
        throw std::invalid_argument("time_steps must have size 0, 1, or world_count");
    }
    auto &world = checked_world(world_index);
    clear_execution_episode_controller(world_index);
    world_batch_setup::maybe_apply_time_step(world, world_index, time_steps);
    world.set_terrain_type(terrain_type.empty() ? WorldTerrainAssignment{}.terrain_type
                                                : terrain_type);
    world.set_wind(wind_speed_mps, wind_dir_from_deg, wind_shear_mps_per_km);
    world.set_sun_direction(sun_azimuth_deg, sun_elevation_deg);
    if (maritime_configured) {
        world.set_maritime_state(sea_state, wave_heading_deg, wave_period_s);
    } else {
        world.clear_maritime_state();
    }
    world_batch_setup::replace_zones(world, zones, [&]() {
        std::vector<std::size_t> grouped;
        grouped.reserve(zones.size());
        for (std::size_t item_index = 0; item_index < zones.size(); ++item_index) {
            if (static_cast<std::size_t>(zones[item_index].world_index) == world_index) {
                grouped.push_back(item_index);
            }
        }
        return grouped;
    }());
    world.reset(seed);

    std::vector<uint64_t> out;
    out.reserve(requests.size());
    for (const auto &request : requests) {
        if (static_cast<std::size_t>(request.world_index) != world_index) {
            continue;
        }
        out.push_back(spawn_from_request(world, request));
    }
    return out;
}

double WorldBatchRuntime::world_time_step(std::size_t world_index) const {
    return checked_world(world_index).get_time_step();
}

void WorldBatchRuntime::set_pilot_actions_batch(
    const std::vector<WorldPilotActionAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        SimulationKernelCommandSurface commands(world);
        for (const size_t item_index : grouped[world_index]) {
            const auto &item = assignments[item_index];
            commands.set_pilot_action(item.entity_id, item.action);
        }
    });
}

std::vector<LaunchEvent>
WorldBatchRuntime::apply_launch_requests_batch(const std::vector<LaunchRequest> &requests) {
    std::vector<LaunchEvent> events(requests.size());
    std::vector<std::vector<size_t>> grouped(worlds_.size());
    for (size_t item_index = 0; item_index < requests.size(); ++item_index) {
        const size_t world_index = static_cast<size_t>(requests[item_index].shooter.world_index);
        if (world_index >= worlds_.size()) {
            throw std::out_of_range("world index out of range");
        }
        grouped[world_index].push_back(item_index);
    }
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto &request = requests[item_index];
            LaunchEvent event{};
            event.request_id = request.request_id;
            event.event_id = request.request_id;
            event.event_time_s = request.requested_time_s;
            event.producer_node_id = "fire_control_launch.v1";
            event.selected_launcher = request.station_id;
            event.selected_munition = request.requested_munition_family.empty()
                                          ? "missile"
                                          : request.requested_munition_family;

            if (!request.has_target_entity || request.target_entity.entity_id == 0) {
                event.rejection_reason = "target_entity_required";
                events[item_index] = event;
                continue;
            }
            if (request.target_entity.world_index != request.shooter.world_index) {
                event.rejection_reason = "cross_world_launch_not_supported";
                events[item_index] = event;
                continue;
            }

            const flecs::entity munition =
                world.fire_missile(request.shooter.entity_id, request.target_entity.entity_id);
            if (!munition.is_valid()) {
                event.rejection_reason = "launch_rejected";
                events[item_index] = event;
                continue;
            }

            event.accepted = true;
            event.rejection_reason.clear();
            event.ammo_delta = -1;
            if (const auto recent = world.export_recent_engagement_events();
                !recent.launch_events.empty()) {
                const LaunchEvent &recorded = recent.launch_events.back();
                event.event_id = recorded.event_id;
                event.event_time_s = recorded.event_time_s;
                event.selected_launcher = recorded.selected_launcher;
                event.selected_munition = recorded.selected_munition;
                event.cooldown_delta_s = recorded.cooldown_delta_s;
            }
            event.spawned_munition = EngagementEntityRef{
                .world_index = request.shooter.world_index,
                .entity_id = static_cast<std::uint64_t>(munition.id()),
            };
            event.has_spawned_munition = true;
            if (event.event_id == 0) {
                event.event_id = static_cast<std::uint64_t>(munition.id());
            }
            events[item_index] = event;
        }
    });
    return events;
}

void WorldBatchRuntime::set_mission_commands_batch(
    const std::vector<WorldMissionCommandAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        SimulationKernelCommandSurface commands(world);
        for (const size_t item_index : grouped[world_index]) {
            const auto &item = assignments[item_index];
            commands.set_mission_command(item.entity_id, item.command);
        }
    });
}

void WorldBatchRuntime::set_mission_commands_maintained_batch(
    const std::vector<WorldMissionCommandMaintainedAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        SimulationKernelCommandSurface commands(world);
        for (const size_t item_index : grouped[world_index]) {
            const auto &item = assignments[item_index];
            commands.set_mission_command(
                item.entity_id, mission_command_compatibility_shell_from_maintained_batch_contract(
                                    item.mission_command));
        }
    });
}

void WorldBatchRuntime::set_task_orders_maintained_batch(
    const std::vector<WorldTaskOrderMaintainedAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        SimulationKernelCommandSurface commands(world);
        for (const size_t item_index : grouped[world_index]) {
            const auto &item = assignments[item_index];
            commands.set_task_order(
                item.entity_id,
                task_order_compatibility_shell_from_maintained_batch_contract(item.task_order));
        }
    });
}

void WorldBatchRuntime::set_leader_intents_batch(
    const std::vector<WorldLeaderIntentAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        SimulationKernelCommandSurface commands(world);
        for (const size_t item_index : grouped[world_index]) {
            const auto &item = assignments[item_index];
            commands.set_leader_intent(item.entity_id, item.intent);
        }
    });
}

void WorldBatchRuntime::set_leader_intents_maintained_batch(
    const std::vector<WorldLeaderIntentMaintainedAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        SimulationKernelCommandSurface commands(world);
        for (const size_t item_index : grouped[world_index]) {
            const auto &item = assignments[item_index];
            commands.set_leader_intent(
                item.entity_id, leader_intent_compatibility_shell_from_maintained_batch_contract(
                                    item.leader_intent));
        }
    });
}

void WorldBatchRuntime::set_pilot_reports_batch(
    const std::vector<WorldPilotReportAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        SimulationKernelCommandSurface commands(world);
        for (const size_t item_index : grouped[world_index]) {
            const auto &item = assignments[item_index];
            commands.set_pilot_report(item.entity_id, item.report);
        }
    });
}

void WorldBatchRuntime::set_pilot_reports_maintained_batch(
    const std::vector<WorldPilotReportMaintainedAssignment> &assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto &world = checked_world(world_index);
        SimulationKernelCommandSurface commands(world);
        for (const size_t item_index : grouped[world_index]) {
            const auto &item = assignments[item_index];
            commands.set_pilot_report(
                item.entity_id,
                pilot_report_compatibility_shell_from_maintained_batch_contract(item.pilot_report));
        }
    });
}

std::vector<AgentObservation>
WorldBatchRuntime::get_agent_observations_batch(const std::vector<WorldEntityRef> &refs) const {
    std::vector<AgentObservation> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index))
                     .get_agent_observation(ref.entity_id);
    });
    return out;
}

InstrumentState WorldBatchRuntime::safe_get_instrument_state(const SimulationKernel &world,
                                                             uint64_t entity_id) {
    auto e = world.get_world().entity(entity_id);
    if (e.is_valid()) {
        const InstrumentState *inst = e.get<InstrumentState>();
        if (inst != nullptr) {
            return *inst;
        }
    }
    return InstrumentState{};
}

std::vector<InstrumentState>
WorldBatchRuntime::get_instrument_states_batch(const std::vector<WorldEntityRef> &refs) const {
    std::vector<InstrumentState> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        out[i] = safe_get_instrument_state(checked_world(static_cast<size_t>(ref.world_index)),
                                           ref.entity_id);
    });
    return out;
}

std::vector<MissionCommand>
WorldBatchRuntime::get_mission_commands_batch(const std::vector<WorldEntityRef> &refs) const {
    std::vector<MissionCommand> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        const SimulationKernelCommandReadSurface commands(
            checked_world(static_cast<size_t>(ref.world_index)));
        out[i] = commands.get_mission_command(ref.entity_id);
    });
    return out;
}

std::vector<MissionCommandMaintainedBatchContract>
WorldBatchRuntime::get_mission_commands_maintained_batch(
    const std::vector<WorldEntityRef> &refs) const {
    std::vector<MissionCommandMaintainedBatchContract> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        const SimulationKernelCommandReadSurface commands(
            checked_world(static_cast<size_t>(ref.world_index)));
        out[i] =
            mission_command_maintained_batch_contract(commands.get_mission_command(ref.entity_id));
    });
    return out;
}

std::vector<TaskOrderMaintainedBatchContract>
WorldBatchRuntime::get_task_orders_maintained_batch(const std::vector<WorldEntityRef> &refs) const {
    std::vector<TaskOrderMaintainedBatchContract> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        const SimulationKernelCommandReadSurface commands(
            checked_world(static_cast<size_t>(ref.world_index)));
        out[i] = task_order_maintained_batch_contract(commands.get_task_order(ref.entity_id));
    });
    return out;
}

std::vector<LeaderIntent>
WorldBatchRuntime::get_leader_intents_batch(const std::vector<WorldEntityRef> &refs) const {
    std::vector<LeaderIntent> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        const SimulationKernelCommandReadSurface commands(
            checked_world(static_cast<size_t>(ref.world_index)));
        out[i] = commands.get_leader_intent(ref.entity_id);
    });
    return out;
}

std::vector<LeaderIntentMaintainedBatchContract>
WorldBatchRuntime::get_leader_intents_maintained_batch(
    const std::vector<WorldEntityRef> &refs) const {
    std::vector<LeaderIntentMaintainedBatchContract> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        const SimulationKernelCommandReadSurface commands(
            checked_world(static_cast<size_t>(ref.world_index)));
        out[i] = leader_intent_maintained_batch_contract(commands.get_leader_intent(ref.entity_id));
    });
    return out;
}

std::vector<PilotReport>
WorldBatchRuntime::get_pilot_reports_batch(const std::vector<WorldEntityRef> &refs) const {
    std::vector<PilotReport> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        const SimulationKernelCommandReadSurface commands(
            checked_world(static_cast<size_t>(ref.world_index)));
        out[i] = commands.get_pilot_report(ref.entity_id);
    });
    return out;
}

std::vector<PilotReportMaintainedBatchContract>
WorldBatchRuntime::get_pilot_reports_maintained_batch(
    const std::vector<WorldEntityRef> &refs) const {
    std::vector<PilotReportMaintainedBatchContract> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto &ref = refs[i];
        const SimulationKernelCommandReadSurface commands(
            checked_world(static_cast<size_t>(ref.world_index)));
        out[i] = pilot_report_maintained_batch_contract(commands.get_pilot_report(ref.entity_id));
    });
    return out;
}

std::vector<std::vector<uint64_t>>
WorldBatchRuntime::get_sensor_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                                  bool use_gpu) const {
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<std::vector<uint64_t>> ids_by_world(worlds_.size());
    std::vector<gpu::InteractionQueryPacked> queries;
    queries.reserve(refs.size());

    double range_hint_m = 5000.0;
    std::size_t max_entities_per_world = 0;
    for (std::size_t world_index = 0; world_index < worlds_.size(); ++world_index) {
        const auto &world = checked_world(world_index);
        auto query = world.get_world().query<const KeyEntity, const Transform>();
        int local_index = 0;
        query.each([&](flecs::entity entity, const KeyEntity &key, const Transform &transform) {
            gpu::InteractionEntityPacked packed{};
            packed.world_index = static_cast<int>(world_index);
            packed.local_index = local_index++;
            packed.x = transform.x;
            packed.y = transform.y;
            packed.z = transform.z;
            packed.bounding_radius_m = entity_bounding_radius_m(entity, key.type);
            entities.push_back(packed);
            ids_by_world[world_index].push_back(entity.id());
        });
        max_entities_per_world = std::max(max_entities_per_world, ids_by_world[world_index].size());
    }

    for (const auto &ref : refs) {
        gpu::InteractionQueryPacked query{};
        query.world_index = static_cast<int>(ref.world_index);
        const auto &world = checked_world(static_cast<size_t>(ref.world_index));
        auto entity = world.get_world().entity(ref.entity_id);
        if (entity.is_valid()) {
            if (const auto *transform = entity.get<Transform>()) {
                query.x = transform->x;
                query.y = transform->y;
                query.z = transform->z;
            }
            if (const auto *sensor = entity.get<Sensor>()) {
                query.range_m = std::max(0.0, sensor->max_range);
                range_hint_m = std::max(range_hint_m, query.range_m);
            }
        }
        queries.push_back(query);
    }

    const auto config = make_interaction_broadphase_config(max_entities_per_world, range_hint_m);
    auto out =
        run_interaction_broadphase_candidate_ids(entities, queries, ids_by_world, config, use_gpu);
    for (std::size_t idx = 0; idx < refs.size(); ++idx) {
        auto &ids = out[idx];
        ids.erase(std::remove(ids.begin(), ids.end(), refs[idx].entity_id), ids.end());
        std::sort(ids.begin(), ids.end());
    }
    return out;
}

std::vector<std::vector<uint64_t>>
WorldBatchRuntime::get_visual_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                                  double range_m, bool use_gpu) const {
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<std::vector<uint64_t>> ids_by_world(worlds_.size());
    std::vector<gpu::InteractionQueryPacked> queries;
    queries.reserve(refs.size());

    const double range_hint_m = std::max(1000.0, range_m);
    std::size_t max_entities_per_world = 0;
    for (std::size_t world_index = 0; world_index < worlds_.size(); ++world_index) {
        const auto &world = checked_world(world_index);
        auto query = world.get_world().query<const KeyEntity, const Transform>();
        int local_index = 0;
        query.each([&](flecs::entity entity, const KeyEntity &key, const Transform &transform) {
            gpu::InteractionEntityPacked packed{};
            packed.world_index = static_cast<int>(world_index);
            packed.local_index = local_index++;
            packed.x = transform.x;
            packed.y = transform.y;
            packed.z = transform.z;
            packed.bounding_radius_m = entity_bounding_radius_m(entity, key.type);
            entities.push_back(packed);
            ids_by_world[world_index].push_back(entity.id());
        });
        max_entities_per_world = std::max(max_entities_per_world, ids_by_world[world_index].size());
    }

    for (const auto &ref : refs) {
        gpu::InteractionQueryPacked query{};
        query.world_index = static_cast<int>(ref.world_index);
        const auto &world = checked_world(static_cast<size_t>(ref.world_index));
        auto entity = world.get_world().entity(ref.entity_id);
        if (entity.is_valid()) {
            if (const auto *transform = entity.get<Transform>()) {
                query.x = transform->x;
                query.y = transform->y;
                query.z = transform->z;
            }
        }
        query.range_m = std::max(0.0, range_m);
        queries.push_back(query);
    }

    const auto config = make_interaction_broadphase_config(max_entities_per_world, range_hint_m);
    auto out =
        run_interaction_broadphase_candidate_ids(entities, queries, ids_by_world, config, use_gpu);
    for (std::size_t idx = 0; idx < refs.size(); ++idx) {
        auto &ids = out[idx];
        ids.erase(std::remove(ids.begin(), ids.end(), refs[idx].entity_id), ids.end());
        std::sort(ids.begin(), ids.end());
    }
    return out;
}

std::vector<std::vector<uint64_t>>
WorldBatchRuntime::get_comm_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                                bool use_gpu) const {
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<std::vector<uint64_t>> ids_by_world(worlds_.size());
    std::vector<gpu::InteractionQueryPacked> queries;
    queries.reserve(refs.size());

    double range_hint_m = 10000.0;
    std::size_t max_entities_per_world = 0;
    for (std::size_t world_index = 0; world_index < worlds_.size(); ++world_index) {
        const auto &world = checked_world(world_index);
        auto query = world.get_world().query<const Transform, const DataLink>();
        int local_index = 0;
        query.each([&](flecs::entity entity, const Transform &transform, const DataLink &link) {
            if (!link.active) {
                return;
            }
            gpu::InteractionEntityPacked packed{};
            packed.world_index = static_cast<int>(world_index);
            packed.local_index = local_index++;
            packed.x = transform.x;
            packed.y = transform.y;
            packed.z = transform.z;
            packed.bounding_radius_m = 0.0;
            entities.push_back(packed);
            ids_by_world[world_index].push_back(entity.id());
            range_hint_m = std::max(range_hint_m, link.max_range_km * 1000.0);
        });
        max_entities_per_world = std::max(max_entities_per_world, ids_by_world[world_index].size());
    }

    for (const auto &ref : refs) {
        gpu::InteractionQueryPacked query{};
        query.world_index = static_cast<int>(ref.world_index);
        const auto &world = checked_world(static_cast<size_t>(ref.world_index));
        auto entity = world.get_world().entity(ref.entity_id);
        if (entity.is_valid()) {
            if (const auto *transform = entity.get<Transform>()) {
                query.x = transform->x;
                query.y = transform->y;
                query.z = transform->z;
            }
            if (const auto *link = entity.get<DataLink>()) {
                query.range_m = std::max(0.0, link->max_range_km * 1000.0);
            }
        }
        queries.push_back(query);
    }

    const auto config = make_interaction_broadphase_config(max_entities_per_world, range_hint_m);
    auto out =
        run_interaction_broadphase_candidate_ids(entities, queries, ids_by_world, config, use_gpu);
    for (std::size_t idx = 0; idx < refs.size(); ++idx) {
        const auto &world = checked_world(static_cast<size_t>(refs[idx].world_index));
        const auto owner = world.get_world().entity(refs[idx].entity_id);
        const auto *owner_link = owner.is_valid() ? owner.get<DataLink>() : nullptr;
        const auto *owner_alliance = owner.is_valid() ? owner.get<Alliance>() : nullptr;
        auto &ids = out[idx];
        ids.erase(std::remove(ids.begin(), ids.end(), refs[idx].entity_id), ids.end());
        ids.erase(std::remove_if(ids.begin(), ids.end(),
                                 [&](uint64_t candidate_id) {
                                     if (owner_link == nullptr || owner_alliance == nullptr) {
                                         return true;
                                     }
                                     const auto candidate = world.get_world().entity(candidate_id);
                                     const auto *candidate_link =
                                         candidate.is_valid() ? candidate.get<DataLink>() : nullptr;
                                     const auto *candidate_alliance =
                                         candidate.is_valid() ? candidate.get<Alliance>() : nullptr;
                                     if (candidate_link == nullptr ||
                                         candidate_alliance == nullptr) {
                                         return true;
                                     }
                                     return (!candidate_link->active) ||
                                            candidate_link->network_id != owner_link->network_id ||
                                            candidate_alliance->side != owner_alliance->side;
                                 }),
                  ids.end());
        std::sort(ids.begin(), ids.end());
    }
    return out;
}

std::vector<WorldBatchVisualBindingCompatibilityScene>
WorldBatchRuntime::collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
    const std::vector<WorldEntityRef> &refs, int downsample,
    const std::vector<std::vector<uint64_t>> &candidate_ids_batch) const {
    std::vector<WorldBatchVisualBindingCompatibilityScene> out(refs.size());
    for (std::size_t idx = 0; idx < refs.size(); ++idx) {
        const auto &ref = refs[idx];
        const std::vector<uint64_t> *candidates =
            idx < candidate_ids_batch.size() ? &candidate_ids_batch[idx] : nullptr;
        if (!world_batch_visual_binding_compatibility::collect_scene_from_candidate_ids(
                checked_world(static_cast<size_t>(ref.world_index)), ref.entity_id, downsample,
                &out[idx], candidates)) {
            throw std::runtime_error(
                "failed to collect visual scene for world batch visual compatibility helper");
        }
    }
    return out;
}

std::vector<WorldBatchVisualBindingCompatibilityScene>
WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(
    const std::vector<WorldEntityRef> &refs, int downsample, bool use_gpu) const {
    const auto visual_candidate_ids = get_visual_candidate_ids_batch(refs, 25000.0, use_gpu);
    return collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        refs, downsample, visual_candidate_ids);
}
