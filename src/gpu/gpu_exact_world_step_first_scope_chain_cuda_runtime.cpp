#include "gpu/gpu_exact_world_step_first_scope_chain_cuda_runtime.h"

#include <chrono>
#include <utility>
#include <vector>

#include "gpu/gpu_exact_world_step_aircraft_chain_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_command_lane_runtime.h"
#include "gpu/gpu_exact_world_step_contract.h"
#include "gpu/gpu_exact_world_step_control_aero_runtime.h"
#include "gpu/gpu_exact_world_step_force_ground_runtime.h"
#include "gpu/gpu_exact_world_step_first_scope_chain_cuda_runtime_types.h"
#include "gpu/gpu_exact_world_step_aircraft_tail_runtime.h"
#include "gpu/gpu_exact_world_step_missile_guidance_runtime.h"

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
bool step_exact_world_step_first_scope_chain_cuda_inplace(
    std::vector<first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState>& states,
    ExactWorldStepFirstScopeChainCudaStats* stats
);
bool upload_exact_world_step_first_scope_chain_cuda_states_cuda(
    const std::vector<first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState>& initial_states
);
bool upload_exact_world_step_first_scope_chain_cuda_states_raw_cuda(
    const std::vector<first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState>& initial_states
);
bool sync_exact_world_step_first_scope_chain_cuda_resident_projection_cuda(
    const std::vector<ExactWorldStepFirstScopeChainCudaResidentProjection>& projections
);
bool sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_cuda(
    const std::vector<ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
);
bool sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_raw_cuda(
    const ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t state_count
);
bool sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_cuda(
    const std::vector<ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
);
bool sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_raw_cuda(
    const ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t state_count
);
ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection*
acquire_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_host_buffer_cuda(
    std::size_t state_count
);
bool replay_exact_world_step_first_scope_chain_cuda_device_sequence_cuda();
bool replay_exact_world_step_first_scope_chain_cuda_resident_current_cuda();
bool replay_exact_world_step_first_scope_chain_cuda_resident_aircraft_only_advance_time_current_cuda();
std::vector<first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState>
download_exact_world_step_first_scope_chain_cuda_states_cuda();
ExactWorldStepFirstScopeChainCudaStats last_exact_world_step_first_scope_chain_cuda_stats_cuda();
const void* last_exact_world_step_first_scope_chain_cuda_output_device_ptr_cuda();
std::size_t last_exact_world_step_first_scope_chain_cuda_output_state_count_cuda();
#endif

}  // namespace gpu::detail

namespace gpu {

namespace {

using first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState;

ExactWorldStepFirstScopeChainCudaStats g_last_stats{};
std::vector<ExactWorldStepStateV1> g_last_uploaded_basis_states{};

void apply_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_to_basis(
    const ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t projection_count
) {
    if (projections == nullptr || g_last_uploaded_basis_states.size() != projection_count) {
        return;
    }
    for (std::size_t i = 0; i < projection_count; ++i) {
        g_last_uploaded_basis_states[i].world_time_s = projections[i].world_time_s;
        g_last_uploaded_basis_states[i].pilot_action.stick_pitch = projections[i].pilot_action.stick_pitch;
        g_last_uploaded_basis_states[i].pilot_action.stick_roll = projections[i].pilot_action.stick_roll;
        g_last_uploaded_basis_states[i].pilot_action.rudder = projections[i].pilot_action.rudder;
        g_last_uploaded_basis_states[i].pilot_action.throttle = projections[i].pilot_action.throttle;
        g_last_uploaded_basis_states[i].pilot_action.gear_handle = projections[i].pilot_action.gear_handle;
        g_last_uploaded_basis_states[i].pilot_action.flaps = projections[i].pilot_action.flaps;
        g_last_uploaded_basis_states[i].pilot_action.speedbrake = projections[i].pilot_action.speedbrake;
        g_last_uploaded_basis_states[i].pilot_action.brake = projections[i].pilot_action.brake;
        g_last_uploaded_basis_states[i].pilot_action.brake_left = projections[i].pilot_action.brake_left;
        g_last_uploaded_basis_states[i].pilot_action.brake_right = projections[i].pilot_action.brake_right;
        g_last_uploaded_basis_states[i].pilot_action.master_arm = projections[i].pilot_action.master_arm;
        g_last_uploaded_basis_states[i].pilot_action.weapon_select_id = projections[i].pilot_action.weapon_select_id;
        g_last_uploaded_basis_states[i].pilot_action.active = projections[i].pilot_action.active;
        g_last_uploaded_basis_states[i].has_pilot_action = projections[i].has_pilot_action;
    }
}

void apply_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_to_basis(
    const std::vector<ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
) {
    apply_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_to_basis(
        projections.data(),
        projections.size()
    );
}

std::vector<ExactWorldStepFirstScopeChainCudaResidentProjection>
pack_exact_world_step_first_scope_chain_cuda_resident_projection(
    const std::vector<ExactWorldStepStateV1>& states
) {
    std::vector<ExactWorldStepFirstScopeChainCudaResidentProjection> out(states.size());
    for (std::size_t i = 0; i < states.size(); ++i) {
        const auto& src = states[i];
        auto& dst = out[i];
        dst.world_time_s = src.world_time_s;
        dst.pilot_action = {
            src.pilot_action.stick_pitch,
            src.pilot_action.stick_roll,
            src.pilot_action.rudder,
            src.pilot_action.throttle,
            src.pilot_action.gear_handle,
            src.pilot_action.flaps,
            src.pilot_action.speedbrake,
            src.pilot_action.brake,
            src.pilot_action.brake_left,
            src.pilot_action.brake_right,
            src.pilot_action.master_arm,
            src.pilot_action.weapon_select_id,
            src.pilot_action.active,
        };
        dst.mission_command = {
            src.mission_command.cmd_heading_deg,
            src.mission_command.cmd_altitude_m,
            src.mission_command.cmd_speed_mps,
            src.mission_command.command_code,
            static_cast<aircraft_chain_cuda::RecoveryApproachType>(src.mission_command.recovery_approach_type),
            src.mission_command.active,
        };
        dst.movement_command = {
            src.movement_command.throttle_cmd,
            src.movement_command.active,
        };
        dst.has_pilot_action = src.has_pilot_action;
        dst.has_mission_command = src.has_mission_command;
        dst.has_movement_command = src.has_movement_command;
    }
    return out;
}

std::vector<ExactWorldStepFirstScopeChainCudaState> pack_exact_world_step_first_scope_chain_cuda_states(
    const std::vector<ExactWorldStepStateV1>& states
) {
    auto aircraft_states = pack_exact_world_step_aircraft_chain_cuda_states(states);
    std::vector<ExactWorldStepFirstScopeChainCudaState> out(states.size());
    for (std::size_t i = 0; i < states.size(); ++i) {
        const auto& src = states[i];
        auto& dst = out[i];
        dst.aircraft = aircraft_states[i];
        dst.entity_id = src.entity_id;
        dst.world_time_s = src.world_time_s;
        dst.missile = {
            src.missile.attacker_id,
            src.missile.target_id,
            src.missile.max_speed,
            src.missile.turn_rate,
            src.missile.fuse_distance,
            src.missile.damage,
            src.missile.seeker_fov_deg,
            src.missile.seeker_lock_range,
            src.missile.guidance_delay_s,
            src.missile.guidance_update_period_s,
            src.missile.last_guidance_time,
            src.missile.launch_time,
            src.missile.max_flight_time_s,
            src.missile.nav_gain,
            src.missile.active,
            src.missile.rng_state,
            src.missile.proximity_min_dist_m,
            src.missile.proximity_last_dist_m,
            src.missile.proximity_engaged,
        };
        dst.contact_list_summary.count = src.contact_list_summary.count;
        dst.contact_list_summary.truncated = src.contact_list_summary.truncated;
        for (std::size_t j = 0; j < missile_guidance_cuda::kContactSummaryCapacity; ++j) {
            const auto& det = src.contact_list_summary.contacts[j];
            dst.contact_list_summary.contacts[j] = {
                det.target_id,
                det.range,
                det.bearing,
                det.elevation,
                det.closing_speed,
                det.signal_strength,
                det.timestamp,
            };
        }
        dst.has_missile = src.has_missile;
        dst.has_contact_list_summary = src.has_contact_list_summary;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_first_scope_chain_cuda_states(
    const std::vector<ExactWorldStepFirstScopeChainCudaState>& states,
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
    std::vector<aircraft_chain_cuda::ExactWorldStepAircraftChainCudaState> aircraft_states;
    aircraft_states.reserve(states.size());
    for (const auto& state : states) {
        aircraft_states.push_back(state.aircraft);
    }
    auto out = unpack_exact_world_step_aircraft_chain_cuda_states(aircraft_states, basis_states);
    for (std::size_t i = 0; i < states.size(); ++i) {
        const auto& src = states[i];
        auto& dst = out[i];
        dst.entity_id = src.entity_id;
        dst.world_time_s = src.world_time_s;
        dst.missile.attacker_id = src.missile.attacker_id;
        dst.missile.target_id = src.missile.target_id;
        dst.missile.max_speed = src.missile.max_speed;
        dst.missile.turn_rate = src.missile.turn_rate;
        dst.missile.fuse_distance = src.missile.fuse_distance;
        dst.missile.damage = src.missile.damage;
        dst.missile.seeker_fov_deg = src.missile.seeker_fov_deg;
        dst.missile.seeker_lock_range = src.missile.seeker_lock_range;
        dst.missile.guidance_delay_s = src.missile.guidance_delay_s;
        dst.missile.guidance_update_period_s = src.missile.guidance_update_period_s;
        dst.missile.last_guidance_time = src.missile.last_guidance_time;
        dst.missile.launch_time = src.missile.launch_time;
        dst.missile.max_flight_time_s = src.missile.max_flight_time_s;
        dst.missile.nav_gain = src.missile.nav_gain;
        dst.missile.active = src.missile.active;
        dst.missile.rng_state = src.missile.rng_state;
        dst.missile.proximity_min_dist_m = src.missile.proximity_min_dist_m;
        dst.missile.proximity_last_dist_m = src.missile.proximity_last_dist_m;
        dst.missile.proximity_engaged = src.missile.proximity_engaged;
        dst.contact_list_summary.count = src.contact_list_summary.count;
        dst.contact_list_summary.truncated = src.contact_list_summary.truncated;
        for (std::size_t j = 0; j < missile_guidance_cuda::kContactSummaryCapacity; ++j) {
            const auto& det = src.contact_list_summary.contacts[j];
            dst.contact_list_summary.contacts[j].target_id = det.target_id;
            dst.contact_list_summary.contacts[j].range = det.range;
            dst.contact_list_summary.contacts[j].bearing = det.bearing;
            dst.contact_list_summary.contacts[j].elevation = det.elevation;
            dst.contact_list_summary.contacts[j].closing_speed = det.closing_speed;
            dst.contact_list_summary.contacts[j].signal_strength = det.signal_strength;
            dst.contact_list_summary.contacts[j].timestamp = det.timestamp;
        }
        dst.has_missile = src.has_missile;
        dst.has_contact_list_summary = src.has_contact_list_summary;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> run_first_scope_chain_cpu_post_command(
    std::vector<ExactWorldStepStateV1> states,
    ExactWorldStepFirstScopeChainCudaStats* stats
) {
    const auto cpu_start = std::chrono::steady_clock::now();
    states = step_exact_world_step_control_aero_reference_cpu_batch(states);
    states = step_exact_world_step_force_ground_reference_cpu_batch(states);
    states = step_exact_world_step_missile_guidance_reference_cpu_batch(states);
    states = step_exact_world_step_aircraft_tail_reference_cpu_batch(states);
    const auto cpu_end = std::chrono::steady_clock::now();
    if (stats != nullptr) {
        stats->missile_count = last_exact_world_step_missile_guidance_stats().missile_count;
        stats->cpu_fallback_ms = std::chrono::duration<double, std::milli>(cpu_end - cpu_start).count();
    }
    return states;
}

}  // namespace

std::vector<ExactWorldStepStateV1> step_exact_world_step_first_scope_chain_cuda_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepFirstScopeChainCudaStats stats{};
    stats.state_count = initial_states.size();

    auto states = step_exact_world_step_command_lane_reference_cpu_batch(initial_states);
    stats.command_lane_ms = last_exact_world_step_command_lane_stats().total_ms;
    states = run_first_scope_chain_cpu_post_command(std::move(states), &stats);

    const auto end = std::chrono::steady_clock::now();
    stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    g_last_stats = stats;
    return states;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_first_scope_chain_cuda_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepFirstScopeChainCudaStats stats{};
    stats.state_count = initial_states.size();

    auto states = step_exact_world_step_command_lane_reference_cpu_batch(initial_states);
    stats.command_lane_ms = last_exact_world_step_command_lane_stats().total_ms;

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto cuda_states = pack_exact_world_step_first_scope_chain_cuda_states(states);
    if (detail::step_exact_world_step_first_scope_chain_cuda_inplace(cuda_states, &stats)) {
        states = unpack_exact_world_step_first_scope_chain_cuda_states(cuda_states, states);
        const auto end = std::chrono::steady_clock::now();
        stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
        g_last_stats = stats;
        return states;
    }
#endif

    states = run_first_scope_chain_cpu_post_command(std::move(states), &stats);
    const auto end = std::chrono::steady_clock::now();
    stats.used_cuda = false;
    stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    g_last_stats = stats;
    return states;
}

bool upload_exact_world_step_first_scope_chain_cuda_states(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    ExactWorldStepFirstScopeChainCudaStats stats{};
    stats.state_count = initial_states.size();
    auto states = step_exact_world_step_command_lane_reference_cpu_batch(initial_states);
    stats.command_lane_ms = last_exact_world_step_command_lane_stats().total_ms;

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto cuda_states = pack_exact_world_step_first_scope_chain_cuda_states(states);
    if (detail::upload_exact_world_step_first_scope_chain_cuda_states_cuda(cuda_states)) {
        g_last_uploaded_basis_states = std::move(states);
        g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
        g_last_stats.command_lane_ms = stats.command_lane_ms;
        return true;
    }
#endif

    g_last_uploaded_basis_states.clear();
    g_last_stats = stats;
    g_last_stats.used_cuda = false;
    return false;
}

bool upload_exact_world_step_first_scope_chain_cuda_states_raw(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    ExactWorldStepFirstScopeChainCudaStats stats{};
    stats.state_count = initial_states.size();

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto cuda_states = pack_exact_world_step_first_scope_chain_cuda_states(initial_states);
    if (detail::upload_exact_world_step_first_scope_chain_cuda_states_raw_cuda(cuda_states)) {
        g_last_uploaded_basis_states = initial_states;
        g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
        g_last_stats.command_lane_ms = 0.0;
        return true;
    }
#endif

    g_last_uploaded_basis_states.clear();
    g_last_stats = stats;
    g_last_stats.used_cuda = false;
    return false;
}

bool sync_exact_world_step_first_scope_chain_cuda_resident_projection(
    const std::vector<ExactWorldStepStateV1>& projected_states
) {
    ExactWorldStepFirstScopeChainCudaStats stats{};
    stats.state_count = projected_states.size();

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto projections = pack_exact_world_step_first_scope_chain_cuda_resident_projection(projected_states);
    if (detail::sync_exact_world_step_first_scope_chain_cuda_resident_projection_cuda(projections)) {
        g_last_uploaded_basis_states = projected_states;
        g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
        return true;
    }
#endif

    g_last_stats = stats;
    g_last_stats.used_cuda = false;
    return false;
}

bool sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection(
    const std::vector<ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
) {
    return sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_raw(
        projections.data(),
        projections.size()
    );
}

bool sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_raw(
    const ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t state_count
) {
    ExactWorldStepFirstScopeChainCudaStats stats{};
    stats.state_count = state_count;

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (detail::sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_raw_cuda(
            projections,
            state_count
        )) {
        apply_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_to_basis(projections, state_count);
        g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
        return true;
    }
#endif

    g_last_stats = stats;
    g_last_stats.used_cuda = false;
    return false;
}

bool sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current(
    const std::vector<ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
) {
    return sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_raw(
        projections.data(),
        projections.size()
    );
}

bool sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_raw(
    const ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t state_count
) {
    ExactWorldStepFirstScopeChainCudaStats stats{};
    stats.state_count = state_count;

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (detail::sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_raw_cuda(
            projections,
            state_count
        )) {
        apply_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_to_basis(projections, state_count);
        g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
        return true;
    }
#endif

    g_last_stats = stats;
    g_last_stats.used_cuda = false;
    return false;
}

ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection*
acquire_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_host_buffer(
    std::size_t state_count
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::acquire_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_host_buffer_cuda(
        state_count
    );
#else
    static_cast<void>(state_count);
    return nullptr;
#endif
}

bool replay_exact_world_step_first_scope_chain_cuda_device_sequence() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    const double command_lane_ms = g_last_stats.command_lane_ms;
    if (detail::replay_exact_world_step_first_scope_chain_cuda_device_sequence_cuda()) {
        g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
        g_last_stats.command_lane_ms = command_lane_ms;
        return true;
    }
#endif
    return false;
}

bool replay_exact_world_step_first_scope_chain_cuda_resident_current() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    const double command_lane_ms = g_last_stats.command_lane_ms;
    if (detail::replay_exact_world_step_first_scope_chain_cuda_resident_current_cuda()) {
        g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
        g_last_stats.command_lane_ms = command_lane_ms;
        return true;
    }
#endif
    return false;
}

bool replay_exact_world_step_first_scope_chain_cuda_resident_aircraft_only_advance_time_current() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    const double command_lane_ms = g_last_stats.command_lane_ms;
    if (detail::replay_exact_world_step_first_scope_chain_cuda_resident_aircraft_only_advance_time_current_cuda()) {
        g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
        g_last_stats.command_lane_ms = command_lane_ms;
        return true;
    }
#endif
    return false;
}

std::vector<ExactWorldStepStateV1> download_exact_world_step_first_scope_chain_cuda_states() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    const double command_lane_ms = g_last_stats.command_lane_ms;
    const auto cuda_states = detail::download_exact_world_step_first_scope_chain_cuda_states_cuda();
    g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
    g_last_stats.command_lane_ms = command_lane_ms;
    if (cuda_states.size() != g_last_uploaded_basis_states.size()) {
        return {};
    }
    return unpack_exact_world_step_first_scope_chain_cuda_states(cuda_states, g_last_uploaded_basis_states);
#else
    return {};
#endif
}

std::vector<ExactWorldStepStateV1> download_exact_world_step_first_scope_chain_cuda_states_with_basis(
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    const double command_lane_ms = g_last_stats.command_lane_ms;
    const auto cuda_states = detail::download_exact_world_step_first_scope_chain_cuda_states_cuda();
    g_last_stats = detail::last_exact_world_step_first_scope_chain_cuda_stats_cuda();
    g_last_stats.command_lane_ms = command_lane_ms;
    if (cuda_states.size() != basis_states.size()) {
        return {};
    }
    g_last_uploaded_basis_states = basis_states;
    return unpack_exact_world_step_first_scope_chain_cuda_states(cuda_states, basis_states);
#else
    return {};
#endif
}

const void* last_exact_world_step_first_scope_chain_cuda_output_device_ptr() noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_exact_world_step_first_scope_chain_cuda_output_device_ptr_cuda();
#else
    return nullptr;
#endif
}

std::size_t last_exact_world_step_first_scope_chain_cuda_output_state_count() noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_exact_world_step_first_scope_chain_cuda_output_state_count_cuda();
#else
    return 0;
#endif
}

const ExactWorldStepFirstScopeChainCudaStats& last_exact_world_step_first_scope_chain_cuda_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
