#include "gpu/gpu_exact_world_step_missile_guidance_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <unordered_map>

namespace gpu {

namespace {

ExactWorldStepMissileGuidanceStats g_last_stats{};

constexpr double kPi = 3.14159265358979323846;

double to_radians(double deg) { return deg * kPi / 180.0; }

std::vector<ExactWorldStepStateV1> step_exact_world_step_missile_guidance_reference_cpu_batch_impl(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    std::size_t* out_missile_count
) {
    std::vector<ExactWorldStepStateV1> out = initial_states;
    std::unordered_map<std::uint64_t, std::size_t> state_index_by_entity_id;
    state_index_by_entity_id.reserve(initial_states.size());
    for (std::size_t i = 0; i < initial_states.size(); ++i) {
        state_index_by_entity_id.emplace(initial_states[i].entity_id, i);
    }

    std::size_t missile_count = 0;
    for (std::size_t i = 0; i < out.size(); ++i) {
        auto& state = out[i];
        if (!state.has_missile) {
            continue;
        }
        missile_count += 1;
        auto& missile = state.missile;
        if (!missile.active) {
            continue;
        }
        const double delta_time = static_cast<double>(static_cast<float>(state.time_step_s));

        const double current_time = state.world_time_s;
        if (missile.launch_time <= 0.0) {
            missile.launch_time = current_time;
        }
        if (missile.max_flight_time_s > 0.0
            && (current_time - missile.launch_time) > missile.max_flight_time_s) {
            missile.active = false;
            continue;
        }
        if ((current_time - missile.launch_time) < missile.guidance_delay_s) {
            continue;
        }
        if (missile.guidance_update_period_s > 0.0
            && (current_time - missile.last_guidance_time) < missile.guidance_update_period_s) {
            continue;
        }
        missile.last_guidance_time = current_time;

        if (!state.has_contact_list_summary || state.contact_list_summary.count == 0) {
            continue;
        }

        const Detection* best_det = nullptr;
        double max_sig = -1.0;
        const auto count = std::min<std::size_t>(
            state.contact_list_summary.count,
            kExactWorldStepContactSummaryCapacity
        );
        for (std::size_t det_index = 0; det_index < count; ++det_index) {
            const auto& detection = state.contact_list_summary.contacts[det_index];
            const double dist = detection.range;
            if (missile.seeker_lock_range > 0.0 && dist > missile.seeker_lock_range) {
                continue;
            }
            const double rel_bearing = detection.bearing;
            if (missile.seeker_fov_deg > 0.0
                && std::abs(rel_bearing) > missile.seeker_fov_deg * 0.5) {
                continue;
            }
            if (detection.signal_strength > max_sig) {
                max_sig = detection.signal_strength;
                best_det = &detection;
            }
        }
        if (best_det == nullptr) {
            continue;
        }

        missile.target_id = best_det->target_id;

        const ExactWorldStepStateV1* target_state = nullptr;
        if (const auto it = state_index_by_entity_id.find(missile.target_id);
            it != state_index_by_entity_id.end()) {
            target_state = &initial_states[it->second];
        }

        auto& velocity = state.velocity;
        const auto& transform = state.transform;
        const auto* target_transform = target_state != nullptr ? &target_state->transform : nullptr;
        const auto* target_velocity = target_state != nullptr ? &target_state->velocity : nullptr;

        const double speed = std::sqrt(
            velocity.vx * velocity.vx + velocity.vy * velocity.vy + velocity.vz * velocity.vz
        );
        const double rx = target_transform != nullptr
            ? (target_transform->x - transform.x)
            : (speed * std::cos(to_radians(90.0 - best_det->bearing)) * delta_time);
        const double ry = target_transform != nullptr
            ? (target_transform->y - transform.y)
            : (speed * std::sin(to_radians(90.0 - best_det->bearing)) * delta_time);
        const double rz = target_transform != nullptr ? (target_transform->z - transform.z) : 0.0;

        const double r_sq = rx * rx + ry * ry + rz * rz;
        const double r_mag = std::sqrt(r_sq);
        if (r_mag <= 1.0e-8 || r_sq <= 1.0e-12) {
            continue;
        }

        const double vm_x = velocity.vx;
        const double vm_y = velocity.vy;
        const double vm_z = velocity.vz;
        const double vt_x = target_velocity != nullptr ? target_velocity->vx : 0.0;
        const double vt_y = target_velocity != nullptr ? target_velocity->vy : 0.0;
        const double vt_z = target_velocity != nullptr ? target_velocity->vz : 0.0;

        const double vr_x = vt_x - vm_x;
        const double vr_y = vt_y - vm_y;
        const double vr_z = vt_z - vm_z;

        const double cx = ry * vr_z - rz * vr_y;
        const double cy = rz * vr_x - rx * vr_z;
        const double cz = rx * vr_y - ry * vr_x;

        const double omega_x = cx / r_sq;
        const double omega_y = cy / r_sq;
        const double omega_z = cz / r_sq;

        double v_mag = std::sqrt(vm_x * vm_x + vm_y * vm_y + vm_z * vm_z);
        if (v_mag < 0.1) {
            v_mag = 0.1;
        }
        const double v_dir_x = vm_x / v_mag;
        const double v_dir_y = vm_y / v_mag;
        const double v_dir_z = vm_z / v_mag;

        const double nav_gain = missile.nav_gain > 0.0 ? missile.nav_gain : 3.0;
        double rate_x = nav_gain * omega_x;
        double rate_y = nav_gain * omega_y;
        double rate_z = nav_gain * omega_z;

        double rate_mag = std::sqrt(rate_x * rate_x + rate_y * rate_y + rate_z * rate_z);
        const double max_rate_rad = to_radians(missile.turn_rate);
        if (rate_mag > max_rate_rad && rate_mag > 1.0e-12) {
            const double scale = max_rate_rad / rate_mag;
            rate_x *= scale;
            rate_y *= scale;
            rate_z *= scale;
            rate_mag = max_rate_rad;
        }

        if (rate_mag > 1.0e-8) {
            const double axis_x = rate_x / rate_mag;
            const double axis_y = rate_y / rate_mag;
            const double axis_z = rate_z / rate_mag;
            const double theta = rate_mag * delta_time;
            const double cos_t = std::cos(theta);
            const double sin_t = std::sin(theta);

            const double cross_x = axis_y * vm_z - axis_z * vm_y;
            const double cross_y = axis_z * vm_x - axis_x * vm_z;
            const double cross_z = axis_x * vm_y - axis_y * vm_x;
            const double dot = axis_x * vm_x + axis_y * vm_y + axis_z * vm_z;

            const double v_new_x = vm_x * cos_t + cross_x * sin_t + axis_x * dot * (1.0 - cos_t);
            const double v_new_y = vm_y * cos_t + cross_y * sin_t + axis_y * dot * (1.0 - cos_t);
            const double v_new_z = vm_z * cos_t + cross_z * sin_t + axis_z * dot * (1.0 - cos_t);

            double vn_norm = std::sqrt(v_new_x * v_new_x + v_new_y * v_new_y + v_new_z * v_new_z);
            if (vn_norm < 1.0e-8) {
                vn_norm = 1.0;
            }
            velocity.vx = (v_new_x / vn_norm) * missile.max_speed;
            velocity.vy = (v_new_y / vn_norm) * missile.max_speed;
            velocity.vz = (v_new_z / vn_norm) * missile.max_speed;
        } else {
            velocity.vx = v_dir_x * missile.max_speed;
            velocity.vy = v_dir_y * missile.max_speed;
            velocity.vz = v_dir_z * missile.max_speed;
        }
    }

    if (out_missile_count != nullptr) {
        *out_missile_count = missile_count;
    }
    return out;
}

}  // namespace

std::vector<ExactWorldStepStateV1> step_exact_world_step_missile_guidance_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    std::size_t missile_count = 0;
    auto out = step_exact_world_step_missile_guidance_reference_cpu_batch_impl(initial_states, &missile_count);
    const auto end = std::chrono::steady_clock::now();
    g_last_stats.state_count = initial_states.size();
    g_last_stats.missile_count = missile_count;
    g_last_stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    return out;
}

const ExactWorldStepMissileGuidanceStats& last_exact_world_step_missile_guidance_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
