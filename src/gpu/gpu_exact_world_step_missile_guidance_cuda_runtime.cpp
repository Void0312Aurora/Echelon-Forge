#include "gpu/gpu_exact_world_step_missile_guidance_cuda_runtime.h"

#include <chrono>

#include "gpu/gpu_exact_world_step_contract.h"
#include "gpu/gpu_exact_world_step_missile_guidance_cuda_runtime_types.h"
#include "gpu/gpu_exact_world_step_missile_guidance_runtime.h"

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
bool step_exact_world_step_missile_guidance_cuda_inplace(
    std::vector<missile_guidance_cuda::ExactWorldStepMissileGuidanceCudaState>& states,
    ExactWorldStepMissileGuidanceCudaStats* stats
);
#endif

}  // namespace gpu::detail

namespace gpu {

namespace {

ExactWorldStepMissileGuidanceCudaStats g_last_stats{};

std::vector<missile_guidance_cuda::ExactWorldStepMissileGuidanceCudaState> pack_missile_guidance_cuda_states(
    const std::vector<ExactWorldStepStateV1>& states
) {
    std::vector<missile_guidance_cuda::ExactWorldStepMissileGuidanceCudaState> out;
    out.resize(states.size());
    for (std::size_t i = 0; i < states.size(); ++i) {
        const auto& src = states[i];
        auto& dst = out[i];
        dst.entity_id = src.entity_id;
        dst.time_step_s = src.time_step_s;
        dst.world_time_s = src.world_time_s;
        dst.transform = {
            src.transform.x,
            src.transform.y,
            src.transform.z,
            src.transform.heading,
            src.transform.pitch,
            src.transform.roll,
        };
        dst.velocity = {src.velocity.vx, src.velocity.vy, src.velocity.vz};
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

std::vector<ExactWorldStepStateV1> unpack_missile_guidance_cuda_states(
    const std::vector<missile_guidance_cuda::ExactWorldStepMissileGuidanceCudaState>& states,
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
    auto out = basis_states;
    for (std::size_t i = 0; i < states.size(); ++i) {
        const auto& src = states[i];
        auto& dst = out[i];
        dst.entity_id = src.entity_id;
        dst.time_step_s = src.time_step_s;
        dst.world_time_s = src.world_time_s;
        dst.transform.x = src.transform.x;
        dst.transform.y = src.transform.y;
        dst.transform.z = src.transform.z;
        dst.transform.heading = src.transform.heading;
        dst.transform.pitch = src.transform.pitch;
        dst.transform.roll = src.transform.roll;
        dst.velocity.vx = src.velocity.vx;
        dst.velocity.vy = src.velocity.vy;
        dst.velocity.vz = src.velocity.vz;
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

}  // namespace

std::vector<ExactWorldStepStateV1> step_exact_world_step_missile_guidance_cuda_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    auto out = step_exact_world_step_missile_guidance_reference_cpu_batch(initial_states);
    const auto end = std::chrono::steady_clock::now();

    const auto& reference_stats = last_exact_world_step_missile_guidance_stats();
    g_last_stats.state_count = reference_stats.state_count;
    g_last_stats.missile_count = reference_stats.missile_count;
    g_last_stats.used_cuda = false;
    g_last_stats.host_to_device_ms = 0.0;
    g_last_stats.kernel_ms = 0.0;
    g_last_stats.device_to_host_ms = 0.0;
    g_last_stats.cpu_fallback_ms = std::chrono::duration<double, std::milli>(end - start).count();
    g_last_stats.total_ms = g_last_stats.cpu_fallback_ms;
    return out;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_missile_guidance_cuda_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepMissileGuidanceCudaStats stats{};
    stats.state_count = initial_states.size();
    stats.missile_count = static_cast<std::size_t>(std::count_if(
        initial_states.begin(),
        initial_states.end(),
        [](const ExactWorldStepStateV1& state) { return state.has_missile; }
    ));

    if (stats.missile_count == 0) {
        const auto end = std::chrono::steady_clock::now();
        stats.used_cuda = false;
        stats.host_to_device_ms = 0.0;
        stats.kernel_ms = 0.0;
        stats.device_to_host_ms = 0.0;
        stats.cpu_fallback_ms = std::chrono::duration<double, std::milli>(end - start).count();
        stats.total_ms = stats.cpu_fallback_ms;
        g_last_stats = stats;
        return initial_states;
    }

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto cuda_states = pack_missile_guidance_cuda_states(initial_states);
    if (detail::step_exact_world_step_missile_guidance_cuda_inplace(cuda_states, &stats)) {
        auto out = unpack_missile_guidance_cuda_states(cuda_states, initial_states);
        const auto end = std::chrono::steady_clock::now();
        stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
        g_last_stats = stats;
        return out;
    }
#endif

    auto out = step_exact_world_step_missile_guidance_reference_cpu_batch(initial_states);
    const auto end = std::chrono::steady_clock::now();
    const auto& reference_stats = last_exact_world_step_missile_guidance_stats();
    stats.state_count = reference_stats.state_count;
    stats.missile_count = reference_stats.missile_count;
    stats.used_cuda = false;
    stats.host_to_device_ms = 0.0;
    stats.kernel_ms = 0.0;
    stats.device_to_host_ms = 0.0;
    stats.cpu_fallback_ms = std::chrono::duration<double, std::milli>(end - start).count();
    stats.total_ms = stats.cpu_fallback_ms;
    g_last_stats = stats;
    return out;
}

const ExactWorldStepMissileGuidanceCudaStats& last_exact_world_step_missile_guidance_cuda_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
