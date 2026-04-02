#include "core/engine/world_batch_runtime.h"

#include "components/systems/data_link.h"
#include "components/systems/ew.h"
#include "components/systems/logistics.h"
#include "components/systems/sensor.h"
#include "components/combat/weapon.h"
#include "components/visual/visual_sensor.h"
#include "core/interfaces/environment_model.h"
#include "gpu/gpu_exact_world_step_contract.h"
#include "gpu/gpu_exact_world_step_command_lane_runtime.h"
#include "gpu/gpu_exact_world_step_first_scope_chain_cuda_runtime.h"
#include "gpu/gpu_interaction_broadphase_runtime.h"

#include <algorithm>
#include <atomic>
#include <chrono>
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
void parallel_for_index(size_t task_count, size_t requested_threads, Fn&& fn) {
    if (task_count == 0) {
        return;
    }
    const size_t thread_count = std::min(
        task_count,
        requested_threads == 0 ? hardware_thread_count() : std::max<size_t>(1, requested_threads)
    );
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
    for (auto& worker : workers) {
        worker.join();
    }
    if (first_exception != nullptr) {
        std::rethrow_exception(first_exception);
    }
}

template <typename Item>
std::vector<std::vector<size_t>> group_item_indices_by_world(size_t world_count, const std::vector<Item>& items) {
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

double normalize_heading_deg(double heading_deg) {
    double out = std::fmod(heading_deg, 360.0);
    if (out < 0.0) {
        out += 360.0;
    }
    return out;
}

constexpr double kPi = 3.14159265358979323846;
constexpr double kEnvironmentScalarCanonicalQuantum = 0x1p-76;

double canonicalize_environment_scalar(double value) {
    if (!std::isfinite(value) || kEnvironmentScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (std::abs(value) <= (kEnvironmentScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / kEnvironmentScalarCanonicalQuantum) *
        kEnvironmentScalarCanonicalQuantum;
    return std::abs(rounded) <= (kEnvironmentScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

double nav_heading_deg_from_velocity(double vx_mps, double vy_mps, double fallback_heading_deg) {
    const double horiz_speed_mps = std::hypot(vx_mps, vy_mps);
    if (horiz_speed_mps <= 1e-6) {
        return normalize_heading_deg(fallback_heading_deg);
    }
    const double heading_rad = std::atan2(vx_mps, vy_mps);
    return normalize_heading_deg(heading_rad * 180.0 / kPi);
}

double default_bounding_radius_m(UnitType type) {
    switch (type) {
        case UnitType::Aircraft:
            return 10.0;
        case UnitType::Ship:
            return 50.0;
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
    if (const auto* sig = entity.get<VisualSignature>()) {
        if (std::isfinite(sig->bounding_radius) && sig->bounding_radius > 0.0) {
            return sig->bounding_radius;
        }
    }
    return default_bounding_radius_m(fallback_type);
}

double exact_world_step_command_lane_frame_delta_s(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

bool nearly_equal_command_lane_scalar(double lhs, double rhs, double tol = 1.0e-9) {
    return std::abs(lhs - rhs) <= tol;
}

bool exact_world_step_command_lane_is_quiescent(
    const gpu::ExactWorldStepStateV1& state
) {
    if (state.has_pending_movement_command && state.pending_movement_command.active) {
        return false;
    }
    if (state.has_pending_action_command && state.pending_action_command.active) {
        return false;
    }
    if (state.has_pending_mission_command && state.pending_mission_command.active) {
        return false;
    }
    if (state.has_action_command && state.action_command.active) {
        return false;
    }

    const bool movement_active = state.has_movement_command && state.movement_command.active;
    const bool lagged_present = state.has_lagged_command;
    const bool lagged_active = lagged_present && state.lagged_command.active;

    if (!movement_active) {
        return !lagged_active;
    }
    if (!state.has_command_lag || !lagged_present) {
        return true;
    }
    if (!lagged_active) {
        return false;
    }
    return nearly_equal_command_lane_scalar(
               state.lagged_command.target_heading,
               state.movement_command.target_heading
           ) &&
        nearly_equal_command_lane_scalar(
            state.lagged_command.target_speed,
            state.movement_command.target_speed
        ) &&
        nearly_equal_command_lane_scalar(
            state.lagged_command.target_altitude,
            state.movement_command.target_altitude
        );
}

gpu::InteractionBroadphaseConfig make_interaction_broadphase_config(
    std::size_t max_entities_per_world,
    double range_hint_m
) {
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

std::vector<std::vector<uint64_t>> decode_broadphase_candidate_ids(
    const std::vector<std::uint32_t>& words,
    const std::vector<gpu::InteractionQueryPacked>& queries,
    const std::vector<std::vector<uint64_t>>& ids_by_world,
    int entities_per_world
) {
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
        const auto& ids = ids_by_world[static_cast<std::size_t>(world_index)];
        auto& dst = out[query_index];
        const auto* src = words.data() + query_index * words_per_query;
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

std::vector<std::vector<uint64_t>> run_interaction_broadphase_candidate_ids(
    const std::vector<gpu::InteractionEntityPacked>& entities,
    const std::vector<gpu::InteractionQueryPacked>& queries,
    const std::vector<std::vector<uint64_t>>& ids_by_world,
    const gpu::InteractionBroadphaseConfig& config,
    bool use_gpu
) {
    auto words = use_gpu
        ? gpu::build_interaction_broadphase_experiment_batch(entities, queries, config)
        : gpu::build_interaction_broadphase_reference_cpu_batch(entities, queries, config);
    return decode_broadphase_candidate_ids(words, queries, ids_by_world, config.entities_per_world);
}

std::size_t find_cached_exact_state_index(
    const std::vector<WorldEntityRef>& refs,
    std::uint64_t world_index,
    std::uint64_t entity_id
) {
    for (std::size_t i = 0; i < refs.size(); ++i) {
        if (refs[i].world_index == world_index && refs[i].entity_id == entity_id) {
            return i;
        }
    }
    throw std::invalid_argument("cached exact-state session does not contain the requested world/entity pair");
}

std::vector<std::size_t> collect_unique_world_indices(
    std::size_t world_count,
    const std::vector<WorldEntityRef>& refs
) {
    std::vector<std::size_t> world_indices;
    if (world_count == 0 || refs.empty()) {
        return world_indices;
    }

    std::vector<bool> seen(world_count, false);
    world_indices.reserve(refs.size());
    for (const auto& ref : refs) {
        const auto world_index = static_cast<std::size_t>(ref.world_index);
        if (world_index >= world_count || seen[world_index]) {
            continue;
        }
        seen[world_index] = true;
        world_indices.push_back(world_index);
    }
    return world_indices;
}

gpu::WorldBatchStepState extract_packed_flight_state(const SimulationKernel& world, uint64_t entity_id) {
    const auto entity = world.get_world().entity(entity_id);
    if (!entity.is_valid()) {
        throw std::invalid_argument("cannot extract packed flight state for invalid entity");
    }

    const auto* transform = entity.get<Transform>();
    const auto* velocity = entity.get<Velocity>();
    if (transform == nullptr || velocity == nullptr) {
        throw std::invalid_argument("packed flight state extraction requires Transform and Velocity");
    }

    gpu::WorldBatchStepState state{};
    state.x_m = transform->x;
    state.y_m = transform->y;
    state.z_m = transform->z;
    state.vx_mps = velocity->vx;
    state.vy_mps = velocity->vy;
    state.vz_mps = velocity->vz;
    state.time_step_s = world.get_time_step();

    const auto* env_ref = world.get_world().get<EnvironmentModelRef>();
    if (env_ref != nullptr && env_ref->model != nullptr) {
        const auto atmo = env_ref->model->get_atmosphere_at(transform->x, transform->y, transform->z);
        state.wind_vx_mps = atmo.wind_velocity.x;
        state.wind_vy_mps = atmo.wind_velocity.y;
    }

    double cmd_heading_deg = transform->heading;
    double cmd_speed_mps = std::hypot(velocity->vx, velocity->vy);
    double cmd_altitude_m = transform->z;

    if (const auto* mission = entity.get<MissionCommand>(); mission != nullptr && mission->active) {
        if (std::isfinite(mission->cmd_heading_deg)) {
            cmd_heading_deg = mission->cmd_heading_deg;
        }
        if (std::isfinite(mission->cmd_speed_mps) && mission->cmd_speed_mps >= 0.0) {
            cmd_speed_mps = mission->cmd_speed_mps;
        }
        if (std::isfinite(mission->cmd_altitude_m)) {
            cmd_altitude_m = mission->cmd_altitude_m;
        }
    } else if (const auto* movement = entity.get<MovementCommand>(); movement != nullptr && movement->active) {
        if (std::isfinite(movement->target_heading)) {
            cmd_heading_deg = movement->target_heading;
        }
        if (std::isfinite(movement->target_speed) && movement->target_speed >= 0.0) {
            cmd_speed_mps = movement->target_speed;
        }
        if (std::isfinite(movement->target_altitude)) {
            cmd_altitude_m = movement->target_altitude;
        }
    }

    const double cmd_heading_rad = Math::to_radians(normalize_heading_deg(cmd_heading_deg));
    state.cmd_vx_mps = std::sin(cmd_heading_rad) * cmd_speed_mps;
    state.cmd_vy_mps = std::cos(cmd_heading_rad) * cmd_speed_mps;
    const double altitude_error_m = cmd_altitude_m - transform->z;
    state.cmd_vz_mps = std::clamp(altitude_error_m / 10.0, -25.0, 25.0);

    if (const auto* action_cfg = entity.get<ActionSpaceConfig>()) {
        if (std::isfinite(action_cfg->max_accel_mps2) && action_cfg->max_accel_mps2 > 0.0) {
            state.max_delta_vxy_mps_per_step = action_cfg->max_accel_mps2 * state.time_step_s;
        }
        if (std::isfinite(action_cfg->max_climb_rate_mps) && action_cfg->max_climb_rate_mps > 0.0) {
            state.max_delta_vz_mps_per_step = action_cfg->max_climb_rate_mps * state.time_step_s;
        }
    }

    if (const auto* fuel = entity.get<FuelSystem>()) {
        state.fuel_kg = std::max(0.0, fuel->internal_fuel_kg + fuel->external_fuel_kg);
        if (std::isfinite(fuel->mil_power_flow_rate) && fuel->mil_power_flow_rate > 0.0) {
            state.fuel_idle_burn_kgps = fuel->mil_power_flow_rate * 0.35;
            const double speed_metric = std::max(50.0, std::abs(state.vx_mps) + std::abs(state.vy_mps) + std::abs(state.vz_mps));
            state.fuel_burn_per_speed_kgps_per_mps = fuel->mil_power_flow_rate / speed_metric;
        }
    } else if (const auto* inst = entity.get<InstrumentState>()) {
        state.fuel_kg = std::max(0.0, inst->fuel_internal_kg + inst->fuel_external_kg);
        if (std::isfinite(inst->fuel_flow_kg_h) && inst->fuel_flow_kg_h > 0.0) {
            const double flow_kgps = inst->fuel_flow_kg_h / 3600.0;
            state.fuel_idle_burn_kgps = flow_kgps * 0.35;
            const double speed_metric = std::max(50.0, std::abs(state.vx_mps) + std::abs(state.vy_mps) + std::abs(state.vz_mps));
            state.fuel_burn_per_speed_kgps_per_mps = flow_kgps / speed_metric;
        }
    }

    const ecs_world_info_t* info = ecs_get_world_info(world.get_world().c_ptr());
    state.mission_time_s = info ? static_cast<double>(info->world_time_total) : 0.0;
    return state;
}

void apply_packed_flight_state(SimulationKernel& world, uint64_t entity_id, const gpu::WorldBatchStepState& state) {
    auto entity = world.get_world().entity(entity_id);
    if (!entity.is_valid()) {
        throw std::invalid_argument("cannot apply packed flight state to invalid entity");
    }

    auto* transform = entity.get_mut<Transform>();
    auto* velocity = entity.get_mut<Velocity>();
    if (transform == nullptr || velocity == nullptr) {
        throw std::invalid_argument("packed flight state apply requires Transform and Velocity");
    }

    transform->x = state.x_m;
    transform->y = state.y_m;
    transform->z = state.z_m;
    velocity->vx = state.vx_mps;
    velocity->vy = state.vy_mps;
    velocity->vz = state.vz_mps;

    transform->heading = nav_heading_deg_from_velocity(state.vx_mps, state.vy_mps, transform->heading);
    const double horiz_speed_mps = std::hypot(state.vx_mps, state.vy_mps);
    if (horiz_speed_mps > 1e-6 || std::abs(state.vz_mps) > 1e-6) {
        transform->pitch = std::atan2(state.vz_mps, std::max(1e-6, horiz_speed_mps)) * 180.0 / kPi;
    }

    if (auto* fuel = entity.get_mut<FuelSystem>()) {
        const double previous_total = std::max(0.0, fuel->internal_fuel_kg + fuel->external_fuel_kg);
        if (previous_total > 1e-9) {
            const double internal_ratio = fuel->internal_fuel_kg / previous_total;
            fuel->internal_fuel_kg = std::clamp(state.fuel_kg * internal_ratio, 0.0, fuel->max_internal_fuel_kg);
            fuel->external_fuel_kg = std::clamp(
                std::max(0.0, state.fuel_kg - fuel->internal_fuel_kg),
                0.0,
                fuel->max_external_fuel_kg
            );
        } else {
            fuel->internal_fuel_kg = std::clamp(state.fuel_kg, 0.0, fuel->max_internal_fuel_kg);
            fuel->external_fuel_kg = 0.0;
        }
    }

    if (auto* inst = entity.get_mut<InstrumentState>()) {
        const auto* env_ref = world.get_world().get<EnvironmentModelRef>();
        const double terrain_elevation_m =
            (env_ref != nullptr && env_ref->model != nullptr)
            ? env_ref->model->get_terrain_elevation(state.x_m, state.y_m)
            : 0.0;
        inst->alt_baro_m = state.z_m;
        inst->alt_radar_m = std::max(0.0, state.z_m - terrain_elevation_m);
        inst->ias_mps = std::sqrt(state.vx_mps * state.vx_mps + state.vy_mps * state.vy_mps + state.vz_mps * state.vz_mps);
        inst->vvi_mps = state.vz_mps;
        inst->heading_deg = transform->heading;
        inst->pitch_deg = transform->pitch;
        inst->roll_deg = transform->roll;
        inst->fuel_internal_kg = std::max(0.0, entity.get<FuelSystem>() ? entity.get<FuelSystem>()->internal_fuel_kg : inst->fuel_internal_kg);
        inst->fuel_external_kg = std::max(0.0, entity.get<FuelSystem>() ? entity.get<FuelSystem>()->external_fuel_kg : inst->fuel_external_kg);
        inst->vn_mps = state.vy_mps;
        inst->ve_mps = state.vx_mps;
        inst->vd_mps = -state.vz_mps;
        inst->ground_speed_mps = std::hypot(state.vx_mps + state.wind_vx_mps, state.vy_mps + state.wind_vy_mps);
        inst->ground_track_deg = nav_heading_deg_from_velocity(
            state.vx_mps + state.wind_vx_mps,
            state.vy_mps + state.wind_vy_mps,
            inst->heading_deg
        );
        inst->wind_speed_mps = std::hypot(state.wind_vx_mps, state.wind_vy_mps);
        inst->wind_dir_deg = normalize_heading_deg(
            nav_heading_deg_from_velocity(-state.wind_vx_mps, -state.wind_vy_mps, inst->wind_dir_deg)
        );
        inst->cmd_heading_deg = nav_heading_deg_from_velocity(state.cmd_vx_mps, state.cmd_vy_mps, inst->cmd_heading_deg);
        inst->cmd_speed_mps = std::hypot(state.cmd_vx_mps, state.cmd_vy_mps);
        inst->cmd_alt_m = state.z_m + state.cmd_vz_mps * 10.0;
    }

    if (auto* ground = entity.get_mut<GroundState>()) {
        const auto* env_ref = world.get_world().get<EnvironmentModelRef>();
        const double terrain_elevation_m =
            (env_ref != nullptr && env_ref->model != nullptr)
            ? env_ref->model->get_terrain_elevation(state.x_m, state.y_m)
            : 0.0;
        ground->terrain_elevation = terrain_elevation_m;
        ground->on_ground = state.z_m <= terrain_elevation_m + 0.25;
    }
}

gpu::ExactWorldStepStateV1 extract_exact_world_step_state_v1(const SimulationKernel& world, uint64_t entity_id) {
    const auto entity = world.get_world().entity(entity_id);
    if (!entity.is_valid()) {
        throw std::invalid_argument("cannot extract exact world step state for invalid entity");
    }

    const auto* transform = entity.get<Transform>();
    const auto* velocity = entity.get<Velocity>();
    if (transform == nullptr || velocity == nullptr) {
        throw std::invalid_argument("exact world step extraction requires Transform and Velocity");
    }

    gpu::ExactWorldStepStateV1 state{};
    state.entity_id = entity_id;
    state.time_step_s = world.get_time_step();
    state.transform = *transform;
    state.velocity = *velocity;

    if (const auto* component = entity.get<AngularVelocity>()) {
        state.angular_velocity = *component;
        state.has_angular_velocity = true;
    }
    if (const auto* component = entity.get<ForceAccumulator>()) {
        state.force_accumulator = *component;
        state.has_force_accumulator = true;
    }
    if (const auto* component = entity.get<AeroState>()) {
        state.aero_state = *component;
        state.has_aero_state = true;
    }
    if (const auto* component = entity.get<ControlLawState>()) {
        state.control_law_state = *component;
        state.has_control_law_state = true;
    }
    if (const auto* component = entity.get<PilotAction>()) {
        state.pilot_action = *component;
        state.has_pilot_action = true;
    }
    if (const auto* component = entity.get<MissionCommand>()) {
        state.mission_command = *component;
        state.has_mission_command = true;
    }
    if (const auto* component = entity.get<MovementCommand>()) {
        state.movement_command = *component;
        state.has_movement_command = true;
    }
    if (const auto* component = entity.get<ActionCommand>()) {
        state.action_command = *component;
        state.has_action_command = true;
    }
    if (const auto* component = entity.get<ActionSpaceConfig>()) {
        state.action_space_config = *component;
        state.has_action_space_config = true;
    }
    if (const auto* component = entity.get<CommandLag>()) {
        state.command_lag = *component;
        state.has_command_lag = true;
    }
    if (const auto* component = entity.get<LaggedCommand>()) {
        state.lagged_command = *component;
        state.has_lagged_command = true;
    }
    if (const auto* component = entity.get<CommandLink>()) {
        state.command_link = *component;
        state.has_command_link = true;
    }
    if (const auto* component = entity.get<PendingMovementCommand>()) {
        state.pending_movement_command = *component;
        state.has_pending_movement_command = true;
    }
    if (const auto* component = entity.get<PendingActionCommand>()) {
        state.pending_action_command = *component;
        state.has_pending_action_command = true;
    }
    if (const auto* component = entity.get<PendingMissionCommand>()) {
        state.pending_mission_command = *component;
        state.has_pending_mission_command = true;
    }
    if (const auto* component = entity.get<FlightModel>()) {
        state.flight_model = *component;
        state.has_flight_model = true;
    }
    if (const auto* component = entity.get<Inertia>()) {
        state.inertia = *component;
        state.has_inertia = true;
    }
    if (const auto* component = entity.get<LandingGear>()) {
        state.landing_gear = *component;
        state.has_landing_gear = true;
    }
    if (const auto* component = entity.get<GearState>()) {
        state.gear_state = *component;
        state.has_gear_state = true;
    }
    if (const auto* component = entity.get<FuelSystem>()) {
        state.fuel_system = *component;
        state.has_fuel_system = true;
    }
    if (const auto* component = entity.get<Mass>()) {
        state.mass = *component;
        state.has_mass = true;
    }
    if (const auto* component = entity.get<Propulsion>()) {
        state.propulsion = *component;
        state.has_propulsion = true;
    }
    if (const auto* component = entity.get<MassProperties>()) {
        state.mass_properties = *component;
        state.has_mass_properties = true;
    }
    if (const auto* component = entity.get<GroundState>()) {
        state.ground_state = *component;
        state.has_ground_state = true;
    }
    if (const auto* component = entity.get<Health>()) {
        state.health = *component;
        state.has_health = true;
    }
    if (const auto* component = entity.get<Ammo>()) {
        state.ammo = *component;
        state.has_ammo = true;
    }
    if (const auto* component = entity.get<Missile>()) {
        state.missile = *component;
        state.has_missile = true;
    }
    if (const auto* component = entity.get<RWR>()) {
        state.rwr_summary.detected_count = static_cast<std::uint32_t>(component->detected_radar_ids.size());
        state.rwr_summary.locking_count = static_cast<std::uint32_t>(component->locking_radar_ids.size());
        state.rwr_summary.is_missile_launch = component->is_missile_launch;
        state.has_rwr_summary = true;
    }
    if (const auto* component = entity.get<ContactList>()) {
        const std::size_t count = std::min(
            component->contacts.size(),
            gpu::kExactWorldStepContactSummaryCapacity
        );
        state.contact_list_summary.count = static_cast<std::uint32_t>(count);
        state.contact_list_summary.truncated = component->contacts.size() > count;
        for (std::size_t i = 0; i < count; ++i) {
            state.contact_list_summary.contacts[i] = component->contacts[i];
        }
        state.has_contact_list_summary = true;
    }
    if (const auto* component = entity.get<InstrumentState>()) {
        state.instrument_state = *component;
        state.has_instrument_state = true;
    }
    if (const auto* component = entity.get<EGI>()) {
        state.egi = *component;
        state.has_egi = true;
    }

    const auto* env_ref = world.get_world().get<EnvironmentModelRef>();
    if (env_ref != nullptr && env_ref->model != nullptr) {
        const auto atmo = env_ref->model->get_atmosphere_at(transform->x, transform->y, transform->z);
        const auto terrain = env_ref->model->get_terrain_at(transform->x, transform->y);
        state.environment_sample.terrain_elevation_m = canonicalize_environment_scalar(terrain.elevation);
        state.environment_sample.wind_vx_mps = atmo.wind_velocity.x;
        state.environment_sample.wind_vy_mps = atmo.wind_velocity.y;
        state.environment_sample.terrain_surface_code = static_cast<std::uint8_t>(terrain.type);
        state.environment_sample.runway_heading_deg = terrain.runway_heading;
        state.has_environment_sample = true;
    }

    const ecs_world_info_t* info = ecs_get_world_info(world.get_world().c_ptr());
    state.world_time_s = info ? static_cast<double>(info->world_time_total) : 0.0;
    return state;
}

template <typename Component>
void sync_optional_component(
    flecs::entity entity,
    bool has_component,
    const Component& value
) {
    if (has_component) {
        entity.set<Component>(value);
        return;
    }
    if (entity.has<Component>()) {
        entity.remove<Component>();
    }
}

void apply_exact_world_step_state_v1(SimulationKernel& world, uint64_t entity_id, const gpu::ExactWorldStepStateV1& state) {
    auto entity = world.get_world().entity(entity_id);
    if (!entity.is_valid()) {
        throw std::invalid_argument("cannot apply exact world step state to invalid entity");
    }
    if (!entity.has<Transform>() || !entity.has<Velocity>()) {
        throw std::invalid_argument("exact world step apply requires Transform and Velocity");
    }

    world.set_time_step(state.time_step_s);
    world.restore_exact_replay_world_time(state.world_time_s);
    *entity.get_mut<Transform>() = state.transform;
    *entity.get_mut<Velocity>() = state.velocity;

    sync_optional_component(entity, state.has_angular_velocity, state.angular_velocity);
    sync_optional_component(entity, state.has_force_accumulator, state.force_accumulator);
    sync_optional_component(entity, state.has_aero_state, state.aero_state);
    sync_optional_component(entity, state.has_control_law_state, state.control_law_state);
    sync_optional_component(entity, state.has_pilot_action, state.pilot_action);
    sync_optional_component(entity, state.has_mission_command, state.mission_command);
    sync_optional_component(entity, state.has_movement_command, state.movement_command);
    sync_optional_component(entity, state.has_action_command, state.action_command);
    sync_optional_component(entity, state.has_action_space_config, state.action_space_config);
    sync_optional_component(entity, state.has_command_lag, state.command_lag);
    sync_optional_component(entity, state.has_lagged_command, state.lagged_command);
    sync_optional_component(entity, state.has_command_link, state.command_link);
    sync_optional_component(entity, state.has_pending_movement_command, state.pending_movement_command);
    sync_optional_component(entity, state.has_pending_action_command, state.pending_action_command);
    sync_optional_component(entity, state.has_pending_mission_command, state.pending_mission_command);
    sync_optional_component(entity, state.has_flight_model, state.flight_model);
    sync_optional_component(entity, state.has_inertia, state.inertia);
    sync_optional_component(entity, state.has_landing_gear, state.landing_gear);
    sync_optional_component(entity, state.has_gear_state, state.gear_state);
    sync_optional_component(entity, state.has_fuel_system, state.fuel_system);
    sync_optional_component(entity, state.has_mass, state.mass);
    sync_optional_component(entity, state.has_propulsion, state.propulsion);
    sync_optional_component(entity, state.has_mass_properties, state.mass_properties);
    sync_optional_component(entity, state.has_ground_state, state.ground_state);
    sync_optional_component(entity, state.has_health, state.health);
    sync_optional_component(entity, state.has_ammo, state.ammo);
    sync_optional_component(entity, state.has_missile, state.missile);
    if (state.has_rwr_summary) {
        RWR rwr{};
        rwr.detected_radar_ids.assign(state.rwr_summary.detected_count, 0ull);
        rwr.locking_radar_ids.assign(state.rwr_summary.locking_count, 0ull);
        rwr.is_missile_launch = state.rwr_summary.is_missile_launch;
        entity.set<RWR>(rwr);
    } else if (entity.has<RWR>()) {
        entity.remove<RWR>();
    }
    if (state.has_contact_list_summary) {
        ContactList contacts{};
        contacts.contacts.reserve(state.contact_list_summary.count);
        for (std::size_t i = 0; i < state.contact_list_summary.count; ++i) {
            contacts.contacts.push_back(state.contact_list_summary.contacts[i]);
        }
        entity.set<ContactList>(contacts);
    } else if (entity.has<ContactList>()) {
        entity.remove<ContactList>();
    }
    sync_optional_component(entity, state.has_instrument_state, state.instrument_state);
    sync_optional_component(entity, state.has_egi, state.egi);
}

}  // namespace

WorldBatchRuntime::WorldBatchRuntime(size_t world_count) {
    resize(world_count);
}

void WorldBatchRuntime::resize(size_t world_count) {
    clear_exact_world_step_backend_session();
    worlds_.clear();
    worlds_.reserve(world_count);
    for (size_t i = 0; i < world_count; ++i) {
        worlds_.push_back(std::make_unique<SimulationKernel>());
    }
}

SimulationKernel& WorldBatchRuntime::checked_world(size_t index) {
    if (index >= worlds_.size()) {
        throw std::out_of_range("world index out of range");
    }
    return *worlds_[index];
}

const SimulationKernel& WorldBatchRuntime::checked_world(size_t index) const {
    if (index >= worlds_.size()) {
        throw std::out_of_range("world index out of range");
    }
    return *worlds_[index];
}

SimulationKernel& WorldBatchRuntime::world(size_t index) {
    sync_exact_world_step_backend_world_if_needed(index);
    return checked_world(index);
}

const SimulationKernel& WorldBatchRuntime::world(size_t index) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_world_if_needed(index);
    return checked_world(index);
}

size_t WorldBatchRuntime::resolve_worker_threads(size_t task_count) const noexcept {
    if (task_count == 0) {
        return 1;
    }
    const size_t configured = worker_threads_ == 0 ? hardware_thread_count() : std::max<size_t>(1, worker_threads_);
    return std::min(task_count, configured);
}

size_t WorldBatchRuntime::effective_worker_threads() const noexcept {
    return resolve_worker_threads(worlds_.size());
}

bool WorldBatchRuntime::exact_world_step_backend_uses_first_scope_chain_cached_session() const noexcept {
    return exact_step_backend_ == WorldBatchExactStepBackend::ExactFirstScopeChainCachedCpu ||
        exact_step_backend_ == WorldBatchExactStepBackend::ExactFirstScopeChainCachedGpu;
}

bool WorldBatchRuntime::exact_world_step_backend_ready() const noexcept {
    if (!exact_world_step_backend_uses_first_scope_chain_cached_session()) {
        return false;
    }
    return !first_scope_chain_cached_refs_.empty() &&
        first_scope_chain_cached_refs_.size() == first_scope_chain_cached_states_.size() &&
        first_scope_chain_cached_world_dirty_.size() == worlds_.size();
}

bool WorldBatchRuntime::exact_world_step_backend_covers_world(size_t world_index) const noexcept {
    if (world_index >= worlds_.size()) {
        return false;
    }
    for (const auto& ref : first_scope_chain_cached_refs_) {
        if (static_cast<std::size_t>(ref.world_index) == world_index) {
            return true;
        }
    }
    return false;
}

bool WorldBatchRuntime::exact_world_step_backend_world_dirty(size_t world_index) const noexcept {
    return world_index < first_scope_chain_cached_world_dirty_.size() &&
        first_scope_chain_cached_world_dirty_[world_index];
}

bool WorldBatchRuntime::exact_world_step_first_scope_chain_cached_session_supports_resident_gpu_fast_path() const noexcept {
    if (first_scope_chain_cached_refs_.empty() ||
        first_scope_chain_cached_refs_.size() != first_scope_chain_cached_states_.size()) {
        return false;
    }

    for (const auto& state : first_scope_chain_cached_states_) {
        if (state.has_pending_movement_command && state.pending_movement_command.active) {
            return false;
        }
        if (state.has_pending_action_command && state.pending_action_command.active) {
            return false;
        }
        if (state.has_pending_mission_command && state.pending_mission_command.active) {
            return false;
        }
        if (state.has_action_command && state.action_command.active &&
            (!state.has_movement_command || !state.movement_command.active)) {
            return false;
        }
        if (state.has_command_lag &&
            state.has_lagged_command &&
            state.has_movement_command &&
            state.movement_command.active &&
            !state.lagged_command.active) {
            return false;
        }
    }

    return true;
}

void WorldBatchRuntime::invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path() noexcept {
    first_scope_chain_cached_resident_gpu_uploaded_ = false;
    first_scope_chain_cached_resident_pilot_projection_dirty_ = false;
    first_scope_chain_cached_resident_full_projection_dirty_ = false;
    first_scope_chain_cached_device_state_pending_materialize_ = false;
}

bool WorldBatchRuntime::sync_exact_world_step_first_scope_chain_cached_session_host_from_device() {
    if (!first_scope_chain_cached_device_state_pending_materialize_) {
        return true;
    }
    auto materialized = gpu::download_exact_world_step_first_scope_chain_cuda_states_with_basis(
        first_scope_chain_cached_states_
    );
    if (materialized.size() != first_scope_chain_cached_states_.size()) {
        return false;
    }
    first_scope_chain_cached_states_ = std::move(materialized);
    first_scope_chain_cached_device_state_pending_materialize_ = false;
    return true;
}

void WorldBatchRuntime::mark_exact_world_step_backend_cached_worlds_dirty() noexcept {
    if (first_scope_chain_cached_world_dirty_.size() != worlds_.size()) {
        return;
    }
    for (const auto& ref : first_scope_chain_cached_refs_) {
        const auto world_index = static_cast<std::size_t>(ref.world_index);
        if (world_index < first_scope_chain_cached_world_dirty_.size()) {
            first_scope_chain_cached_world_dirty_[world_index] = true;
        }
    }
}

void WorldBatchRuntime::mark_exact_world_step_backend_worlds_clean(const std::vector<size_t>& world_indices) noexcept {
    if (first_scope_chain_cached_world_dirty_.size() != worlds_.size()) {
        return;
    }
    for (const auto world_index : world_indices) {
        if (world_index < first_scope_chain_cached_world_dirty_.size()) {
            first_scope_chain_cached_world_dirty_[world_index] = false;
        }
    }
}

void WorldBatchRuntime::sync_exact_world_step_backend_world_if_needed(size_t world_index) {
    if (!exact_world_step_backend_ready() ||
        !exact_world_step_backend_covers_world(world_index) ||
        !exact_world_step_backend_world_dirty(world_index)) {
        return;
    }
    if (!sync_exact_world_step_first_scope_chain_cached_session_host_from_device()) {
        throw std::runtime_error("failed to materialize cached exact-step GPU resident state");
    }

    std::vector<WorldEntityRef> local_refs;
    std::vector<gpu::ExactWorldStepStateV1> local_states;
    for (std::size_t state_index = 0; state_index < first_scope_chain_cached_refs_.size(); ++state_index) {
        if (static_cast<std::size_t>(first_scope_chain_cached_refs_[state_index].world_index) != world_index) {
            continue;
        }
        local_refs.push_back(first_scope_chain_cached_refs_[state_index]);
        local_states.push_back(first_scope_chain_cached_states_[state_index]);
    }
    if (local_refs.empty()) {
        return;
    }

    apply_exact_world_step_states_v1_batch(local_refs, local_states);
    mark_exact_world_step_backend_worlds_clean({world_index});
}

void WorldBatchRuntime::sync_exact_world_step_backend_refs_if_needed(const std::vector<WorldEntityRef>& refs) {
    if (!exact_world_step_backend_ready() || refs.empty()) {
        return;
    }

    std::vector<bool> seen(worlds_.size(), false);
    std::vector<std::size_t> world_indices;
    world_indices.reserve(refs.size());
    for (const auto& ref : refs) {
        const auto world_index = static_cast<std::size_t>(ref.world_index);
        if (world_index >= worlds_.size() || seen[world_index]) {
            continue;
        }
        seen[world_index] = true;
        if (exact_world_step_backend_covers_world(world_index) &&
            exact_world_step_backend_world_dirty(world_index)) {
            world_indices.push_back(world_index);
        }
    }
    for (const auto world_index : world_indices) {
        sync_exact_world_step_backend_world_if_needed(world_index);
    }
}

void WorldBatchRuntime::clear_exact_world_step_backend_session() noexcept {
    first_scope_chain_cached_refs_.clear();
    first_scope_chain_cached_states_.clear();
    first_scope_chain_cached_world_dirty_.clear();
    invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path();
    first_scope_chain_cached_session_stats_ = ExactWorldStepFirstScopeChainCachedSessionStats{};
    first_scope_chain_experiment_refs_.clear();
}

void WorldBatchRuntime::reset_batch(const std::vector<uint32_t>& seeds) {
    clear_exact_world_step_backend_session();
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

void WorldBatchRuntime::step_batch() {
    if (exact_world_step_backend_ready()) {
        std::vector<bool> exact_world_covered(worlds_.size(), false);
        for (const auto& ref : first_scope_chain_cached_refs_) {
            const auto world_index = static_cast<std::size_t>(ref.world_index);
            if (world_index < exact_world_covered.size()) {
                exact_world_covered[world_index] = true;
            }
        }
        const bool use_gpu = exact_step_backend_ == WorldBatchExactStepBackend::ExactFirstScopeChainCachedGpu;
        (void)step_exact_world_step_first_scope_chain_cached_session_impl(use_gpu, false, false);

        std::vector<uint64_t> cpu_world_indices;
        cpu_world_indices.reserve(worlds_.size());
        for (std::size_t world_index = 0; world_index < worlds_.size(); ++world_index) {
            if (!exact_world_covered[world_index]) {
                cpu_world_indices.push_back(static_cast<uint64_t>(world_index));
            }
        }
        if (!cpu_world_indices.empty()) {
            parallel_for_index(cpu_world_indices.size(), worker_threads_, [&](size_t i) {
                checked_world(static_cast<std::size_t>(cpu_world_indices[i])).step();
            });
        }
        return;
    }
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        worlds_[i]->step();
    });
}

void WorldBatchRuntime::step_worlds(const std::vector<uint64_t>& world_indices) {
    if (world_indices.empty()) {
        return;
    }
    std::vector<std::size_t> covered_world_indices;
    if (exact_world_step_backend_ready()) {
        std::vector<bool> seen(worlds_.size(), false);
        covered_world_indices.reserve(world_indices.size());
        for (const auto world_index_u64 : world_indices) {
            const auto world_index = static_cast<std::size_t>(world_index_u64);
            sync_exact_world_step_backend_world_if_needed(world_index);
            if (world_index < worlds_.size() &&
                !seen[world_index] &&
                exact_world_step_backend_covers_world(world_index)) {
                seen[world_index] = true;
                covered_world_indices.push_back(world_index);
            }
        }
    }
    parallel_for_index(world_indices.size(), worker_threads_, [&](size_t i) {
        checked_world(static_cast<size_t>(world_indices[i])).step();
    });
    for (const auto world_index : covered_world_indices) {
        std::vector<WorldEntityRef> local_refs;
        std::vector<std::size_t> local_state_indices;
        for (std::size_t state_index = 0; state_index < first_scope_chain_cached_refs_.size(); ++state_index) {
            if (static_cast<std::size_t>(first_scope_chain_cached_refs_[state_index].world_index) != world_index) {
                continue;
            }
            local_refs.push_back(first_scope_chain_cached_refs_[state_index]);
            local_state_indices.push_back(state_index);
        }
        if (local_refs.empty()) {
            continue;
        }
        auto refreshed_states = extract_exact_world_step_states_v1_batch(local_refs);
        for (std::size_t local_index = 0; local_index < local_refs.size(); ++local_index) {
            first_scope_chain_cached_states_[local_state_indices[local_index]] = std::move(refreshed_states[local_index]);
        }
    }
    if (!covered_world_indices.empty()) {
        invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path();
        mark_exact_world_step_backend_worlds_clean(covered_world_indices);
    }
}

bool WorldBatchRuntime::load_database(const std::string& path) {
    std::atomic<bool> ok{true};
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        if (!worlds_[i]->load_database(path)) {
            ok.store(false, std::memory_order_relaxed);
        }
    });
    return ok.load(std::memory_order_relaxed);
}

bool WorldBatchRuntime::load_unit_definitions(const std::string& path, std::string* error) {
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
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        worlds_[i]->set_time_step(dt);
    });
}

void WorldBatchRuntime::set_terrain_types_batch(const std::vector<WorldTerrainAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            world.set_terrain_type(assignments[item_index].terrain_type);
        }
    });
}

void WorldBatchRuntime::set_winds_batch(const std::vector<WorldWindAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_wind(item.speed_mps, item.dir_from_deg, item.shear_mps_per_km);
        }
    });
}

void WorldBatchRuntime::clear_zones_batch(const std::vector<uint64_t>& world_indices) {
    if (world_indices.empty()) {
        parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
            worlds_[i]->clear_zones();
        });
        return;
    }
    parallel_for_index(world_indices.size(), worker_threads_, [&](size_t i) {
        checked_world(static_cast<size_t>(world_indices[i])).clear_zones();
    });
}

void WorldBatchRuntime::add_zones_batch(const std::vector<WorldZoneDefinition>& zones) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), zones);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& zone = zones[item_index];
            world.add_zone(zone.name, zone.x, zone.y, zone.width, zone.length, zone.heading, zone.surface_type);
        }
    });
}

std::vector<uint64_t> WorldBatchRuntime::spawn_units_batch(const std::vector<WorldSpawnRequest>& requests) {
    std::vector<uint64_t> out(requests.size(), 0);
    const auto grouped = group_item_indices_by_world(worlds_.size(), requests);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = requests[item_index];
            const auto entity = world.spawn_unit(
                item.side,
                item.type_name,
                item.x,
                item.y,
                item.z,
                item.heading,
                item.pitch,
                item.roll,
                item.vx,
                item.vy,
                item.vz
            );
            out[item_index] = entity.id();
        }
    });
    return out;
}

std::vector<uint64_t> WorldBatchRuntime::apply_world_setup_batch(
    const std::vector<uint32_t>& seeds,
    const std::vector<WorldTerrainAssignment>& terrain_assignments,
    const std::vector<WorldWindAssignment>& wind_assignments,
    const std::vector<WorldZoneDefinition>& zones,
    const std::vector<WorldSpawnRequest>& requests,
    const std::vector<double>& time_steps
) {
    if (!time_steps.empty() && time_steps.size() != 1 && time_steps.size() != worlds_.size()) {
        throw std::invalid_argument("time_steps must have size 0, 1, or world_count");
    }

    std::vector<uint64_t> out(requests.size(), 0);
    const auto terrain_grouped = group_item_indices_by_world(worlds_.size(), terrain_assignments);
    const auto wind_grouped = group_item_indices_by_world(worlds_.size(), wind_assignments);
    const auto zone_grouped = group_item_indices_by_world(worlds_.size(), zones);
    const auto spawn_grouped = group_item_indices_by_world(worlds_.size(), requests);

    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);

        if (!time_steps.empty()) {
            const double dt = time_steps.size() == 1 ? time_steps[0] : time_steps[world_index];
            if (std::isfinite(dt) && dt > 0.0) {
                world.set_time_step(dt);
            }
        }

        for (const size_t item_index : terrain_grouped[world_index]) {
            world.set_terrain_type(terrain_assignments[item_index].terrain_type);
        }
        for (const size_t item_index : wind_grouped[world_index]) {
            const auto& item = wind_assignments[item_index];
            world.set_wind(item.speed_mps, item.dir_from_deg, item.shear_mps_per_km);
        }

        world.clear_zones();
        for (const size_t item_index : zone_grouped[world_index]) {
            const auto& zone = zones[item_index];
            world.add_zone(zone.name, zone.x, zone.y, zone.width, zone.length, zone.heading, zone.surface_type);
        }

        uint32_t seed = static_cast<uint32_t>(42 + world_index);
        if (seeds.size() == worlds_.size()) {
            seed = seeds[world_index];
        } else if (seeds.size() == 1) {
            seed = static_cast<uint32_t>(seeds[0] + static_cast<uint32_t>(world_index));
        }
        world.reset(seed);

        for (const size_t item_index : spawn_grouped[world_index]) {
            const auto& item = requests[item_index];
            const auto entity = world.spawn_unit(
                item.side,
                item.type_name,
                item.x,
                item.y,
                item.z,
                item.heading,
                item.pitch,
                item.roll,
                item.vx,
                item.vy,
                item.vz
            );
            out[item_index] = entity.id();
        }
    });
    return out;
}

void WorldBatchRuntime::set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_pilot_action(item.entity_id, item.action);
        }
    });
    if (exact_world_step_backend_ready()) {
        std::vector<WorldPilotActionAssignment> cached_assignments;
        cached_assignments.reserve(assignments.size());
        for (const auto& item : assignments) {
            const auto found = std::find_if(
                first_scope_chain_cached_refs_.begin(),
                first_scope_chain_cached_refs_.end(),
                [&](const WorldEntityRef& ref) {
                    return ref.world_index == item.world_index && ref.entity_id == item.entity_id;
                }
            );
            if (found != first_scope_chain_cached_refs_.end()) {
                cached_assignments.push_back(item);
            }
        }
        if (!cached_assignments.empty()) {
            set_pilot_actions_exact_world_step_first_scope_chain_cached_session(cached_assignments);
        }
    }
}

void WorldBatchRuntime::set_mission_commands_batch(const std::vector<WorldMissionCommandAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_mission_command(item.entity_id, item.command);
        }
    });
    if (exact_world_step_backend_ready()) {
        std::vector<WorldMissionCommandAssignment> cached_assignments;
        cached_assignments.reserve(assignments.size());
        for (const auto& item : assignments) {
            const auto found = std::find_if(
                first_scope_chain_cached_refs_.begin(),
                first_scope_chain_cached_refs_.end(),
                [&](const WorldEntityRef& ref) {
                    return ref.world_index == item.world_index && ref.entity_id == item.entity_id;
                }
            );
            if (found != first_scope_chain_cached_refs_.end()) {
                cached_assignments.push_back(item);
            }
        }
        if (!cached_assignments.empty()) {
            set_mission_commands_exact_world_step_first_scope_chain_cached_session(cached_assignments);
        }
    }
}

void WorldBatchRuntime::set_task_orders_batch(const std::vector<WorldTaskOrderAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_task_order(item.entity_id, item.order);
        }
    });
}

void WorldBatchRuntime::set_leader_intents_batch(const std::vector<WorldLeaderIntentAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_leader_intent(item.entity_id, item.intent);
        }
    });
}

void WorldBatchRuntime::set_pilot_reports_batch(const std::vector<WorldPilotReportAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_pilot_report(item.entity_id, item.report);
        }
    });
}

std::vector<AgentObservation> WorldBatchRuntime::get_agent_observations_batch(const std::vector<WorldEntityRef>& refs) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<AgentObservation> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_agent_observation(ref.entity_id);
    });
    return out;
}

InstrumentState WorldBatchRuntime::safe_get_instrument_state(const SimulationKernel& world, uint64_t entity_id) {
    auto e = world.get_world().entity(entity_id);
    if (e.is_valid()) {
        const InstrumentState* inst = e.get<InstrumentState>();
        if (inst != nullptr) {
            return *inst;
        }
    }
    return InstrumentState{};
}

std::vector<InstrumentState> WorldBatchRuntime::get_instrument_states_batch(const std::vector<WorldEntityRef>& refs) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<InstrumentState> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = safe_get_instrument_state(checked_world(static_cast<size_t>(ref.world_index)), ref.entity_id);
    });
    return out;
}

std::vector<MissionCommand> WorldBatchRuntime::get_mission_commands_batch(const std::vector<WorldEntityRef>& refs) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<MissionCommand> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_mission_command(ref.entity_id);
    });
    return out;
}

std::vector<TaskOrder> WorldBatchRuntime::get_task_orders_batch(const std::vector<WorldEntityRef>& refs) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<TaskOrder> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_task_order(ref.entity_id);
    });
    return out;
}

std::vector<LeaderIntent> WorldBatchRuntime::get_leader_intents_batch(const std::vector<WorldEntityRef>& refs) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<LeaderIntent> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_leader_intent(ref.entity_id);
    });
    return out;
}

std::vector<PilotReport> WorldBatchRuntime::get_pilot_reports_batch(const std::vector<WorldEntityRef>& refs) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<PilotReport> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_pilot_report(ref.entity_id);
    });
    return out;
}

std::vector<std::vector<uint64_t>> WorldBatchRuntime::get_sensor_candidate_ids_batch(
    const std::vector<WorldEntityRef>& refs,
    bool use_gpu
) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<std::vector<uint64_t>> ids_by_world(worlds_.size());
    std::vector<gpu::InteractionQueryPacked> queries;
    queries.reserve(refs.size());

    double range_hint_m = 5000.0;
    std::size_t max_entities_per_world = 0;
    for (std::size_t world_index = 0; world_index < worlds_.size(); ++world_index) {
        const auto& world = checked_world(world_index);
        auto query = world.get_world().query<const KeyEntity, const Transform>();
        int local_index = 0;
        query.each([&](flecs::entity entity, const KeyEntity& key, const Transform& transform) {
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

    for (const auto& ref : refs) {
        gpu::InteractionQueryPacked query{};
        query.world_index = static_cast<int>(ref.world_index);
        const auto& world = checked_world(static_cast<size_t>(ref.world_index));
        auto entity = world.get_world().entity(ref.entity_id);
        if (entity.is_valid()) {
            if (const auto* transform = entity.get<Transform>()) {
                query.x = transform->x;
                query.y = transform->y;
                query.z = transform->z;
            }
            if (const auto* sensor = entity.get<Sensor>()) {
                query.range_m = std::max(0.0, sensor->max_range);
                range_hint_m = std::max(range_hint_m, query.range_m);
            }
        }
        queries.push_back(query);
    }

    const auto config = make_interaction_broadphase_config(max_entities_per_world, range_hint_m);
    auto out = run_interaction_broadphase_candidate_ids(entities, queries, ids_by_world, config, use_gpu);
    for (std::size_t idx = 0; idx < refs.size(); ++idx) {
        auto& ids = out[idx];
        ids.erase(std::remove(ids.begin(), ids.end(), refs[idx].entity_id), ids.end());
        std::sort(ids.begin(), ids.end());
    }
    return out;
}

std::vector<std::vector<uint64_t>> WorldBatchRuntime::get_visual_candidate_ids_batch(
    const std::vector<WorldEntityRef>& refs,
    double range_m,
    bool use_gpu
) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<std::vector<uint64_t>> ids_by_world(worlds_.size());
    std::vector<gpu::InteractionQueryPacked> queries;
    queries.reserve(refs.size());

    const double range_hint_m = std::max(1000.0, range_m);
    std::size_t max_entities_per_world = 0;
    for (std::size_t world_index = 0; world_index < worlds_.size(); ++world_index) {
        const auto& world = checked_world(world_index);
        auto query = world.get_world().query<const KeyEntity, const Transform>();
        int local_index = 0;
        query.each([&](flecs::entity entity, const KeyEntity& key, const Transform& transform) {
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

    for (const auto& ref : refs) {
        gpu::InteractionQueryPacked query{};
        query.world_index = static_cast<int>(ref.world_index);
        const auto& world = checked_world(static_cast<size_t>(ref.world_index));
        auto entity = world.get_world().entity(ref.entity_id);
        if (entity.is_valid()) {
            if (const auto* transform = entity.get<Transform>()) {
                query.x = transform->x;
                query.y = transform->y;
                query.z = transform->z;
            }
        }
        query.range_m = std::max(0.0, range_m);
        queries.push_back(query);
    }

    const auto config = make_interaction_broadphase_config(max_entities_per_world, range_hint_m);
    auto out = run_interaction_broadphase_candidate_ids(entities, queries, ids_by_world, config, use_gpu);
    for (std::size_t idx = 0; idx < refs.size(); ++idx) {
        auto& ids = out[idx];
        ids.erase(std::remove(ids.begin(), ids.end(), refs[idx].entity_id), ids.end());
        std::sort(ids.begin(), ids.end());
    }
    return out;
}

std::vector<std::vector<uint64_t>> WorldBatchRuntime::get_comm_candidate_ids_batch(
    const std::vector<WorldEntityRef>& refs,
    bool use_gpu
) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<std::vector<uint64_t>> ids_by_world(worlds_.size());
    std::vector<gpu::InteractionQueryPacked> queries;
    queries.reserve(refs.size());

    double range_hint_m = 10000.0;
    std::size_t max_entities_per_world = 0;
    for (std::size_t world_index = 0; world_index < worlds_.size(); ++world_index) {
        const auto& world = checked_world(world_index);
        auto query = world.get_world().query<const Transform, const DataLink>();
        int local_index = 0;
        query.each([&](flecs::entity entity, const Transform& transform, const DataLink& link) {
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

    for (const auto& ref : refs) {
        gpu::InteractionQueryPacked query{};
        query.world_index = static_cast<int>(ref.world_index);
        const auto& world = checked_world(static_cast<size_t>(ref.world_index));
        auto entity = world.get_world().entity(ref.entity_id);
        if (entity.is_valid()) {
            if (const auto* transform = entity.get<Transform>()) {
                query.x = transform->x;
                query.y = transform->y;
                query.z = transform->z;
            }
            if (const auto* link = entity.get<DataLink>()) {
                query.range_m = std::max(0.0, link->max_range_km * 1000.0);
            }
        }
        queries.push_back(query);
    }

    const auto config = make_interaction_broadphase_config(max_entities_per_world, range_hint_m);
    auto out = run_interaction_broadphase_candidate_ids(entities, queries, ids_by_world, config, use_gpu);
    for (std::size_t idx = 0; idx < refs.size(); ++idx) {
        const auto& world = checked_world(static_cast<size_t>(refs[idx].world_index));
        const auto owner = world.get_world().entity(refs[idx].entity_id);
        const auto* owner_link = owner.is_valid() ? owner.get<DataLink>() : nullptr;
        const auto* owner_alliance = owner.is_valid() ? owner.get<Alliance>() : nullptr;
        auto& ids = out[idx];
        ids.erase(std::remove(ids.begin(), ids.end(), refs[idx].entity_id), ids.end());
        ids.erase(
            std::remove_if(
                ids.begin(),
                ids.end(),
                [&](uint64_t candidate_id) {
                    if (owner_link == nullptr || owner_alliance == nullptr) {
                        return true;
                    }
                    const auto candidate = world.get_world().entity(candidate_id);
                    const auto* candidate_link = candidate.is_valid() ? candidate.get<DataLink>() : nullptr;
                    const auto* candidate_alliance = candidate.is_valid() ? candidate.get<Alliance>() : nullptr;
                    if (candidate_link == nullptr || candidate_alliance == nullptr) {
                        return true;
                    }
                    return (!candidate_link->active) ||
                           candidate_link->network_id != owner_link->network_id ||
                           candidate_alliance->side != owner_alliance->side;
                }
            ),
            ids.end()
        );
        std::sort(ids.begin(), ids.end());
    }
    return out;
}

std::vector<gpu::WorldBatchStepState> WorldBatchRuntime::extract_packed_flight_states_batch(
    const std::vector<WorldEntityRef>& refs
) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<gpu::WorldBatchStepState> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = extract_packed_flight_state(checked_world(static_cast<size_t>(ref.world_index)), ref.entity_id);
    });
    return out;
}

void WorldBatchRuntime::apply_packed_flight_states_batch(
    const std::vector<WorldEntityRef>& refs,
    const std::vector<gpu::WorldBatchStepState>& states
) {
    if (refs.size() != states.size()) {
        throw std::invalid_argument("apply_packed_flight_states_batch requires refs and states to have equal size");
    }
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        apply_packed_flight_state(checked_world(static_cast<size_t>(ref.world_index)), ref.entity_id, states[i]);
    });
}

std::vector<gpu::WorldBatchStepState> WorldBatchRuntime::step_packed_flight_states_experiment_batch(
    const std::vector<WorldEntityRef>& refs,
    int steps,
    bool use_cuda_graph,
    bool write_back
) {
    auto states = extract_packed_flight_states_batch(refs);
    auto out = gpu::step_world_batch_experiment_batch(states, steps, use_cuda_graph);
    if (write_back) {
        apply_packed_flight_states_batch(refs, out);
    }
    return out;
}

std::vector<gpu::ExactWorldStepStateV1> WorldBatchRuntime::extract_exact_world_step_states_v1_batch(
    const std::vector<WorldEntityRef>& refs
) const {
    const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_backend_refs_if_needed(refs);
    std::vector<gpu::ExactWorldStepStateV1> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = extract_exact_world_step_state_v1(checked_world(static_cast<size_t>(ref.world_index)), ref.entity_id);
    });
    return out;
}

std::vector<gpu::ExactWorldStepStateV1> WorldBatchRuntime::step_exact_world_step_first_scope_chain_experiment_batch(
    const std::vector<WorldEntityRef>& refs,
    bool use_gpu,
    bool write_back
) {
    std::vector<gpu::ExactWorldStepStateV1> out(refs.size());
    const auto grouped = group_item_indices_by_world(worlds_.size(), refs);
    for (std::size_t world_index = 0; world_index < grouped.size(); ++world_index) {
        const auto& item_indices = grouped[world_index];
        if (item_indices.empty()) {
            continue;
        }

        std::vector<WorldEntityRef> local_refs;
        local_refs.reserve(item_indices.size());
        for (const std::size_t item_index : item_indices) {
            local_refs.push_back(refs[item_index]);
        }

        auto local_states = extract_exact_world_step_states_v1_batch(local_refs);
        auto stepped = use_gpu
            ? gpu::step_exact_world_step_first_scope_chain_cuda_batch(local_states)
            : gpu::step_exact_world_step_first_scope_chain_cuda_reference_cpu_batch(local_states);
        if (write_back) {
            apply_exact_world_step_states_v1_batch(local_refs, stepped);
        }
        for (std::size_t local_index = 0; local_index < item_indices.size(); ++local_index) {
            out[item_indices[local_index]] = std::move(stepped[local_index]);
        }
    }
    return out;
}

void WorldBatchRuntime::prime_exact_world_step_first_scope_chain_cached_session(
    const std::vector<WorldEntityRef>& refs
) {
    const auto start = std::chrono::steady_clock::now();
    first_scope_chain_cached_refs_ = refs;
    first_scope_chain_cached_states_ = extract_exact_world_step_states_v1_batch(refs);
    first_scope_chain_cached_world_dirty_.assign(worlds_.size(), false);
    invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path();
    const auto end = std::chrono::steady_clock::now();
    first_scope_chain_cached_session_stats_ = ExactWorldStepFirstScopeChainCachedSessionStats{};
    first_scope_chain_cached_session_stats_.state_count = first_scope_chain_cached_states_.size();
    first_scope_chain_cached_session_stats_.prime_extract_ms =
        std::chrono::duration<double, std::milli>(end - start).count();
}

void WorldBatchRuntime::set_pilot_actions_exact_world_step_first_scope_chain_cached_session(
    const std::vector<WorldPilotActionAssignment>& assignments
) {
    const auto start = std::chrono::steady_clock::now();
    for (const auto& item : assignments) {
        const std::size_t index = find_cached_exact_state_index(
            first_scope_chain_cached_refs_,
            item.world_index,
            item.entity_id
        );
        first_scope_chain_cached_states_[index].pilot_action = item.action;
        first_scope_chain_cached_states_[index].has_pilot_action = true;
    }
    first_scope_chain_cached_resident_pilot_projection_dirty_ = true;
    const auto end = std::chrono::steady_clock::now();
    first_scope_chain_cached_session_stats_.state_count = first_scope_chain_cached_states_.size();
    first_scope_chain_cached_session_stats_.pilot_update_ms =
        std::chrono::duration<double, std::milli>(end - start).count();
}

void WorldBatchRuntime::set_mission_commands_exact_world_step_first_scope_chain_cached_session(
    const std::vector<WorldMissionCommandAssignment>& assignments
) {
    const auto start = std::chrono::steady_clock::now();
    for (const auto& item : assignments) {
        const std::size_t index = find_cached_exact_state_index(
            first_scope_chain_cached_refs_,
            item.world_index,
            item.entity_id
        );
        first_scope_chain_cached_states_[index].mission_command = item.command;
        first_scope_chain_cached_states_[index].has_mission_command = true;
    }
    first_scope_chain_cached_resident_full_projection_dirty_ = true;
    const auto end = std::chrono::steady_clock::now();
    first_scope_chain_cached_session_stats_.state_count = first_scope_chain_cached_states_.size();
    first_scope_chain_cached_session_stats_.mission_update_ms =
        std::chrono::duration<double, std::milli>(end - start).count();
}

std::vector<gpu::ExactWorldStepStateV1> WorldBatchRuntime::step_exact_world_step_first_scope_chain_cached_session(
    bool use_gpu,
    bool write_back
) {
    return step_exact_world_step_first_scope_chain_cached_session_impl(use_gpu, write_back, true);
}

std::vector<gpu::ExactWorldStepStateV1> WorldBatchRuntime::step_exact_world_step_first_scope_chain_cached_session_impl(
    bool use_gpu,
    bool write_back,
    bool materialize_result
) {
    if (first_scope_chain_cached_refs_.empty() || first_scope_chain_cached_states_.empty()) {
        return {};
    }
    const auto start = std::chrono::steady_clock::now();
    double chain_command_lane_ms = 0.0;
    bool used_resident_gpu_fast_path = false;
    if (use_gpu && exact_world_step_first_scope_chain_cached_session_supports_resident_gpu_fast_path()) {
        if (!first_scope_chain_cached_resident_gpu_uploaded_) {
            if (!gpu::upload_exact_world_step_first_scope_chain_cuda_states_raw(first_scope_chain_cached_states_)) {
                invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path();
            } else {
                first_scope_chain_cached_resident_gpu_uploaded_ = true;
                first_scope_chain_cached_resident_pilot_projection_dirty_ = false;
                first_scope_chain_cached_resident_full_projection_dirty_ = false;
            }
        }
        if (first_scope_chain_cached_resident_gpu_uploaded_) {
            bool quiescent_command_lane = true;
            bool no_missile_rows = true;

            for (const auto& state : first_scope_chain_cached_states_) {
                if (!exact_world_step_command_lane_is_quiescent(state)) {
                    quiescent_command_lane = false;
                    break;
                }

                no_missile_rows = no_missile_rows && !state.has_missile;
            }

            if (quiescent_command_lane) {
                bool replay_ok = false;
                if (first_scope_chain_cached_resident_full_projection_dirty_) {
                    auto projected_states = first_scope_chain_cached_states_;
                    for (auto& state : projected_states) {
                        state.world_time_s += exact_world_step_command_lane_frame_delta_s(state.time_step_s);
                    }
                    replay_ok = gpu::sync_exact_world_step_first_scope_chain_cuda_resident_projection(projected_states) &&
                        gpu::replay_exact_world_step_first_scope_chain_cuda_resident_current();
                    if (replay_ok) {
                        first_scope_chain_cached_states_ = std::move(projected_states);
                        first_scope_chain_cached_resident_full_projection_dirty_ = false;
                        first_scope_chain_cached_resident_pilot_projection_dirty_ = false;
                    }
                } else if (no_missile_rows && !first_scope_chain_cached_resident_pilot_projection_dirty_) {
                    replay_ok = gpu::replay_exact_world_step_first_scope_chain_cuda_resident_aircraft_only_advance_time_current();
                    if (replay_ok) {
                        for (auto& state : first_scope_chain_cached_states_) {
                            state.world_time_s += exact_world_step_command_lane_frame_delta_s(state.time_step_s);
                        }
                    }
                } else {
                    auto* projections =
                        gpu::acquire_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_host_buffer(
                            first_scope_chain_cached_states_.size()
                        );
                    if (projections == nullptr) {
                        auto& projection_scratch = first_scope_chain_cached_resident_pilot_time_projection_scratch_;
                        projection_scratch.resize(first_scope_chain_cached_states_.size());
                        projections = projection_scratch.data();
                    }
                    for (std::size_t i = 0; i < first_scope_chain_cached_states_.size(); ++i) {
                        const auto& state = first_scope_chain_cached_states_[i];
                        auto& projection = projections[i];
                        projection.world_time_s =
                            state.world_time_s + exact_world_step_command_lane_frame_delta_s(state.time_step_s);
                        projection.pilot_action = {
                            state.pilot_action.stick_pitch,
                            state.pilot_action.stick_roll,
                            state.pilot_action.rudder,
                            state.pilot_action.throttle,
                            state.pilot_action.gear_handle,
                            state.pilot_action.flaps,
                            state.pilot_action.speedbrake,
                            state.pilot_action.brake,
                            state.pilot_action.brake_left,
                            state.pilot_action.brake_right,
                            state.pilot_action.master_arm,
                            state.pilot_action.weapon_select_id,
                            state.pilot_action.active,
                        };
                        projection.has_pilot_action = state.has_pilot_action;
                    }
                    replay_ok = no_missile_rows
                        ? gpu::sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_raw(
                            projections,
                            first_scope_chain_cached_states_.size()
                        )
                        : (
                            gpu::sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_raw(
                                projections,
                                first_scope_chain_cached_states_.size()
                            ) &&
                            gpu::replay_exact_world_step_first_scope_chain_cuda_resident_current()
                        );
                    if (replay_ok) {
                        for (std::size_t i = 0; i < first_scope_chain_cached_states_.size(); ++i) {
                            first_scope_chain_cached_states_[i].world_time_s = projections[i].world_time_s;
                        }
                        first_scope_chain_cached_resident_pilot_projection_dirty_ = false;
                    }
                }
                if (replay_ok) {
                    chain_command_lane_ms = 0.0;
                    if (materialize_result || write_back) {
                        auto materialized = gpu::download_exact_world_step_first_scope_chain_cuda_states_with_basis(
                            first_scope_chain_cached_states_
                        );
                        if (materialized.size() != first_scope_chain_cached_states_.size()) {
                            throw std::runtime_error("failed to materialize cached exact-step GPU resident step");
                        }
                        first_scope_chain_cached_states_ = std::move(materialized);
                        first_scope_chain_cached_device_state_pending_materialize_ = false;
                    } else {
                        first_scope_chain_cached_device_state_pending_materialize_ = true;
                    }
                    used_resident_gpu_fast_path = true;
                } else {
                    invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path();
                }
            } else {
                std::vector<gpu::ExactWorldStepStateV1> projected_states;
                projected_states =
                    gpu::step_exact_world_step_command_lane_reference_cpu_batch(first_scope_chain_cached_states_);
                chain_command_lane_ms = gpu::last_exact_world_step_command_lane_stats().total_ms;
                if (gpu::sync_exact_world_step_first_scope_chain_cuda_resident_projection(projected_states) &&
                    gpu::replay_exact_world_step_first_scope_chain_cuda_resident_current()) {
                    first_scope_chain_cached_states_ = std::move(projected_states);
                    first_scope_chain_cached_resident_pilot_projection_dirty_ = false;
                    first_scope_chain_cached_resident_full_projection_dirty_ = false;
                    if (materialize_result || write_back) {
                        auto materialized = gpu::download_exact_world_step_first_scope_chain_cuda_states_with_basis(
                            first_scope_chain_cached_states_
                        );
                        if (materialized.size() != first_scope_chain_cached_states_.size()) {
                            throw std::runtime_error("failed to materialize cached exact-step GPU resident step");
                        }
                        first_scope_chain_cached_states_ = std::move(materialized);
                        first_scope_chain_cached_device_state_pending_materialize_ = false;
                    } else {
                        first_scope_chain_cached_device_state_pending_materialize_ = true;
                    }
                    used_resident_gpu_fast_path = true;
                } else {
                    invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path();
                }
            }
        }
    }
    if (!used_resident_gpu_fast_path) {
        if (!sync_exact_world_step_first_scope_chain_cached_session_host_from_device()) {
            throw std::runtime_error("failed to materialize cached exact-step GPU resident state before fallback");
        }
        invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path();
        first_scope_chain_cached_states_ = use_gpu
            ? gpu::step_exact_world_step_first_scope_chain_cuda_batch(first_scope_chain_cached_states_)
            : gpu::step_exact_world_step_first_scope_chain_cuda_reference_cpu_batch(first_scope_chain_cached_states_);
    }
    const auto after_chain = std::chrono::steady_clock::now();
    if (write_back) {
        const auto write_back_start = std::chrono::steady_clock::now();
        apply_exact_world_step_states_v1_batch(first_scope_chain_cached_refs_, first_scope_chain_cached_states_);
        const auto write_back_end = std::chrono::steady_clock::now();
        mark_exact_world_step_backend_worlds_clean(
            collect_unique_world_indices(worlds_.size(), first_scope_chain_cached_refs_)
        );
        first_scope_chain_cached_session_stats_.write_back_ms =
            std::chrono::duration<double, std::milli>(write_back_end - write_back_start).count();
    } else {
        mark_exact_world_step_backend_cached_worlds_dirty();
        first_scope_chain_cached_session_stats_.write_back_ms = 0.0;
    }
    const auto end = std::chrono::steady_clock::now();
    const auto& chain_stats = gpu::last_exact_world_step_first_scope_chain_cuda_stats();
    first_scope_chain_cached_session_stats_.state_count = first_scope_chain_cached_states_.size();
    first_scope_chain_cached_session_stats_.used_gpu = use_gpu;
    first_scope_chain_cached_session_stats_.step_total_ms =
        std::chrono::duration<double, std::milli>(end - start).count();
    first_scope_chain_cached_session_stats_.chain_command_lane_ms =
        used_resident_gpu_fast_path ? chain_command_lane_ms : chain_stats.command_lane_ms;
    first_scope_chain_cached_session_stats_.chain_host_to_device_ms = chain_stats.host_to_device_ms;
    first_scope_chain_cached_session_stats_.chain_front_kernel_ms = chain_stats.front_kernel_ms;
    first_scope_chain_cached_session_stats_.chain_guidance_kernel_ms = chain_stats.guidance_kernel_ms;
    first_scope_chain_cached_session_stats_.chain_tail_kernel_ms = chain_stats.tail_kernel_ms;
    first_scope_chain_cached_session_stats_.chain_kernel_ms = chain_stats.kernel_ms;
    first_scope_chain_cached_session_stats_.chain_device_to_host_ms = chain_stats.device_to_host_ms;
    first_scope_chain_cached_session_stats_.chain_cpu_fallback_ms = chain_stats.cpu_fallback_ms;
    first_scope_chain_cached_session_stats_.chain_total_ms = chain_stats.total_ms;
    // Preserve a direct measurement of the step body even if the chain stats omit runtime glue.
    if (first_scope_chain_cached_session_stats_.step_total_ms <
        std::chrono::duration<double, std::milli>(after_chain - start).count()) {
        first_scope_chain_cached_session_stats_.step_total_ms =
            std::chrono::duration<double, std::milli>(after_chain - start).count();
    }
    return first_scope_chain_cached_states_;
}

const ExactWorldStepFirstScopeChainCachedSessionStats&
WorldBatchRuntime::last_exact_world_step_first_scope_chain_cached_session_stats() const noexcept {
    return first_scope_chain_cached_session_stats_;
}

void WorldBatchRuntime::apply_exact_world_step_first_scope_chain_cached_session_to_world() {
    if (first_scope_chain_cached_refs_.empty() || first_scope_chain_cached_states_.empty()) {
        return;
    }
    if (first_scope_chain_cached_refs_.size() != first_scope_chain_cached_states_.size()) {
        throw std::runtime_error(
            "apply_exact_world_step_first_scope_chain_cached_session_to_world size mismatch"
        );
    }
    if (!sync_exact_world_step_first_scope_chain_cached_session_host_from_device()) {
        throw std::runtime_error("failed to materialize cached exact-step GPU resident state before apply");
    }
    apply_exact_world_step_states_v1_batch(first_scope_chain_cached_refs_, first_scope_chain_cached_states_);
    mark_exact_world_step_backend_worlds_clean(
        collect_unique_world_indices(worlds_.size(), first_scope_chain_cached_refs_)
    );
}

std::vector<gpu::ExactWorldStepStateV1> WorldBatchRuntime::extract_exact_world_step_first_scope_chain_cached_session() const {
    if (!const_cast<WorldBatchRuntime*>(this)->sync_exact_world_step_first_scope_chain_cached_session_host_from_device()) {
        throw std::runtime_error("failed to materialize cached exact-step GPU resident state before extract");
    }
    return first_scope_chain_cached_states_;
}

bool WorldBatchRuntime::upload_exact_world_step_first_scope_chain_experiment_batch(
    const std::vector<WorldEntityRef>& refs
) {
    auto states = extract_exact_world_step_states_v1_batch(refs);
    if (!gpu::upload_exact_world_step_first_scope_chain_cuda_states(states)) {
        first_scope_chain_experiment_refs_.clear();
        return false;
    }
    first_scope_chain_experiment_refs_ = refs;
    return true;
}

bool WorldBatchRuntime::replay_exact_world_step_first_scope_chain_experiment_device_sequence() {
    return gpu::replay_exact_world_step_first_scope_chain_cuda_device_sequence();
}

std::vector<gpu::ExactWorldStepStateV1> WorldBatchRuntime::download_exact_world_step_first_scope_chain_experiment_batch(
    bool write_back
) {
    auto states = gpu::download_exact_world_step_first_scope_chain_cuda_states();
    if (states.size() != first_scope_chain_experiment_refs_.size()) {
        if (states.empty() && first_scope_chain_experiment_refs_.empty()) {
            return states;
        }
        throw std::runtime_error(
            "download_exact_world_step_first_scope_chain_experiment_batch size mismatch with uploaded refs"
        );
    }
    if (write_back && !states.empty()) {
        apply_exact_world_step_states_v1_batch(first_scope_chain_experiment_refs_, states);
    }
    return states;
}

void WorldBatchRuntime::apply_exact_world_step_states_v1_batch(
    const std::vector<WorldEntityRef>& refs,
    const std::vector<gpu::ExactWorldStepStateV1>& states
) {
    if (refs.size() != states.size()) {
        throw std::invalid_argument(
            "apply_exact_world_step_states_v1_batch requires refs and states to have equal size"
        );
    }
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        apply_exact_world_step_state_v1(
            checked_world(static_cast<size_t>(ref.world_index)),
            ref.entity_id,
            states[i]
        );
    });
}
