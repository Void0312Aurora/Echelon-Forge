#include "gpu/gpu_exact_world_step_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
bool step_exact_world_step_states_v1_prototype_cuda_inplace(
    ExactWorldStepPrototypeSoA& soa,
    int steps,
    ExactWorldStepPrototypeStats* stats
);
#endif

}  // namespace gpu::detail

namespace gpu {

namespace {

ExactWorldStepPrototypeStats g_last_stats{};

constexpr double kPi = 3.14159265358979323846;
constexpr double kCanonicalQuantum = 1e-8;
constexpr double kRefLat = 36.24;
constexpr double kRefLon = -115.05;
constexpr double kMetersPerDegLat = 111132.954;
constexpr double kMetersPerDegLon = 90000.0;
constexpr double kGravityMps2 = 9.80665;

double wrap_heading_deg(double heading_deg) {
    while (heading_deg < 0.0) {
        heading_deg += 360.0;
    }
    while (heading_deg >= 360.0) {
        heading_deg -= 360.0;
    }
    return heading_deg;
}

double shortest_heading_delta_deg(double target_deg, double current_deg) {
    double delta = target_deg - current_deg;
    while (delta > 180.0) {
        delta -= 360.0;
    }
    while (delta < -180.0) {
        delta += 360.0;
    }
    return delta;
}

double nav_heading_deg_from_velocity(double vx_mps, double vy_mps, double fallback_heading_deg) {
    if (std::hypot(vx_mps, vy_mps) <= 1.0) {
        return wrap_heading_deg(fallback_heading_deg);
    }
    return wrap_heading_deg(std::atan2(vx_mps, vy_mps) * 180.0 / kPi);
}

double lerp_tau(double current, double target, double tau_s, double dt) {
    if (tau_s <= 1e-4 || dt <= 0.0) {
        return target;
    }
    const double alpha = 1.0 - std::exp(-dt / tau_s);
    return current + (target - current) * alpha;
}

double control_lpf(double current, double target, double tau_s, double dt) {
    if (tau_s <= 0.0 || dt <= 0.0) {
        return target;
    }
    const double alpha = dt / (tau_s + dt);
    return current + alpha * (target - current);
}

double clamp_symmetric(double value, double limit) {
    return std::clamp(value, -limit, limit);
}

double canonicalize_scalar(double value) {
    if (!std::isfinite(value) || kCanonicalQuantum <= 0.0) {
        return value;
    }
    if (std::abs(value) <= (kCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / kCanonicalQuantum) * kCanonicalQuantum;
    return std::abs(rounded) <= (kCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

double smoothstep01(double x) {
    x = std::clamp(x, 0.0, 1.0);
    return x * x * (3.0 - 2.0 * x);
}

struct ApproximateVector3 {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

ApproximateVector3 normalize_world_vector(ApproximateVector3 value) {
    const double norm = std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
    if (norm <= 1.0e-9) {
        return {};
    }
    const double inv = 1.0 / norm;
    return {value.x * inv, value.y * inv, value.z * inv};
}

ApproximateVector3 cross_world(const ApproximateVector3& a, const ApproximateVector3& b) {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    };
}

ApproximateVector3 body_right_world(double heading_deg, double pitch_deg, double roll_deg) {
    const double psi = (90.0 - heading_deg) * (kPi / 180.0);
    const double theta = pitch_deg * (kPi / 180.0);
    const double phi = roll_deg * (kPi / 180.0);

    const double c_psi = std::cos(psi);
    const double s_psi = std::sin(psi);
    const double c_theta = std::cos(theta);
    const double s_theta = std::sin(theta);
    const double c_phi = std::cos(phi);
    const double s_phi = std::sin(phi);

    return {
        -s_psi * c_phi + c_psi * s_theta * s_phi,
        c_psi * c_phi + s_psi * s_theta * s_phi,
        c_theta * s_phi,
    };
}

void canonicalize_step_outputs(ExactWorldStepPrototypeSoA& soa, std::size_t i) {
    soa.world_time_s[i] = canonicalize_scalar(soa.world_time_s[i]);
    soa.x_m[i] = canonicalize_scalar(soa.x_m[i]);
    soa.y_m[i] = canonicalize_scalar(soa.y_m[i]);
    soa.z_m[i] = canonicalize_scalar(soa.z_m[i]);
    soa.heading_deg[i] = canonicalize_scalar(wrap_heading_deg(soa.heading_deg[i]));
    soa.pitch_deg[i] = canonicalize_scalar(soa.pitch_deg[i]);
    soa.roll_deg[i] = canonicalize_scalar(soa.roll_deg[i]);
    soa.vx_mps[i] = canonicalize_scalar(soa.vx_mps[i]);
    soa.vy_mps[i] = canonicalize_scalar(soa.vy_mps[i]);
    soa.vz_mps[i] = canonicalize_scalar(soa.vz_mps[i]);
    soa.p_rad_s[i] = canonicalize_scalar(soa.p_rad_s[i]);
    soa.q_rad_s[i] = canonicalize_scalar(soa.q_rad_s[i]);
    soa.r_rad_s[i] = canonicalize_scalar(soa.r_rad_s[i]);
    soa.g_load_normal[i] = canonicalize_scalar(soa.g_load_normal[i]);
    soa.g_load_axial[i] = canonicalize_scalar(soa.g_load_axial[i]);
    soa.lagged_heading_deg[i] = canonicalize_scalar(wrap_heading_deg(soa.lagged_heading_deg[i]));
    soa.lagged_speed_mps[i] = canonicalize_scalar(soa.lagged_speed_mps[i]);
    soa.lagged_altitude_m[i] = canonicalize_scalar(soa.lagged_altitude_m[i]);
    soa.current_drag_index[i] = canonicalize_scalar(soa.current_drag_index[i]);
    soa.gear_extension_state[i] = canonicalize_scalar(soa.gear_extension_state[i]);
    soa.aero_dynamic_pressure_pa[i] = canonicalize_scalar(soa.aero_dynamic_pressure_pa[i]);
    soa.aero_mach_number[i] = canonicalize_scalar(soa.aero_mach_number[i]);
    soa.aero_angle_of_attack_deg[i] = canonicalize_scalar(soa.aero_angle_of_attack_deg[i]);
    soa.aero_sideslip_angle_deg[i] = canonicalize_scalar(soa.aero_sideslip_angle_deg[i]);
    soa.aero_lift_coefficient[i] = canonicalize_scalar(soa.aero_lift_coefficient[i]);
    soa.aero_drag_coefficient[i] = canonicalize_scalar(soa.aero_drag_coefficient[i]);
    soa.force_torque_roll_nm[i] = canonicalize_scalar(soa.force_torque_roll_nm[i]);
    soa.force_torque_pitch_nm[i] = canonicalize_scalar(soa.force_torque_pitch_nm[i]);
    soa.force_torque_yaw_nm[i] = canonicalize_scalar(soa.force_torque_yaw_nm[i]);
    soa.control_stick_roll_filt[i] = canonicalize_scalar(soa.control_stick_roll_filt[i]);
    soa.control_stick_pitch_filt[i] = canonicalize_scalar(soa.control_stick_pitch_filt[i]);
    soa.control_stick_yaw_filt[i] = canonicalize_scalar(soa.control_stick_yaw_filt[i]);
    soa.control_stick_yaw_cmd[i] = canonicalize_scalar(soa.control_stick_yaw_cmd[i]);
    soa.fuel_internal_kg[i] = canonicalize_scalar(soa.fuel_internal_kg[i]);
    soa.fuel_external_kg[i] = canonicalize_scalar(soa.fuel_external_kg[i]);
    soa.fuel_flow_rate_kgps[i] = canonicalize_scalar(soa.fuel_flow_rate_kgps[i]);
    soa.mass_fuel_kg[i] = canonicalize_scalar(soa.mass_fuel_kg[i]);
    soa.total_mass_kg[i] = canonicalize_scalar(soa.total_mass_kg[i]);
}

struct ResolvedTargets {
    double heading_deg = 0.0;
    double speed_mps = 0.0;
    double altitude_m = 0.0;
    bool active = false;
};

struct ApproximateAeroOutputs {
    double dynamic_pressure = 0.0;
    double mach_number = 0.0;
    double angle_of_attack = 0.0;
    double sideslip_angle = 0.0;
};

struct ApproximateAeroCoefficients {
    double lift_coefficient = 0.0;
    double drag_coefficient = 0.0;
};

struct ApproximateBodyVelocity {
    double x_mps = 0.0;
    double y_mps = 0.0;
    double z_mps = 0.0;
};

struct ApproximateInertia {
    double ixx = 10000.0;
    double iyy = 10000.0;
    double izz = 10000.0;
};

double normalize_heading_deg(double heading_deg) {
    return wrap_heading_deg(heading_deg);
}

double mission_heading_bug(
    const MissionCommand& mission,
    double fallback_heading_deg
) {
    if (std::isfinite(mission.cmd_heading_deg)) {
        return normalize_heading_deg(mission.cmd_heading_deg);
    }
    return normalize_heading_deg(fallback_heading_deg);
}

double mission_altitude_bug(
    const MissionCommand& mission,
    double fallback_alt_m
) {
    return std::isfinite(mission.cmd_altitude_m) ? mission.cmd_altitude_m : fallback_alt_m;
}

double mission_speed_bug(
    const MissionCommand& mission,
    double fallback_speed_mps
) {
    return std::isfinite(mission.cmd_speed_mps) ? mission.cmd_speed_mps : fallback_speed_mps;
}

bool commanded_gear_down(const ExactWorldStepStateV1& state) {
    if (state.has_pilot_action && state.pilot_action.active) {
        return state.pilot_action.gear_handle >= 0.5f;
    }
    if (state.has_mission_command && state.mission_command.active) {
        if (state.mission_command.command_code == 4) {
            return true;
        }
        const double speed = std::sqrt(
            state.velocity.vx * state.velocity.vx +
            state.velocity.vy * state.velocity.vy +
            state.velocity.vz * state.velocity.vz
        );
        return speed < 100.0 || (state.transform.z < 200.0 && state.mission_command.cmd_altitude_m < 500.0);
    }
    if (state.has_movement_command && state.movement_command.active) {
        return state.movement_command.gear_handle;
    }
    return state.has_landing_gear ? state.landing_gear.extension_state >= 0.5 : true;
}

ApproximateBodyVelocity world_to_body_velocity(
    double vx_world_mps,
    double vy_world_mps,
    double vz_world_mps,
    double heading_deg,
    double pitch_deg,
    double roll_deg
) {
    const double psi = (90.0 - heading_deg) * (kPi / 180.0);
    const double theta = pitch_deg * (kPi / 180.0);
    const double phi = roll_deg * (kPi / 180.0);

    const double c_psi = std::cos(psi);
    const double s_psi = std::sin(psi);
    const double c_theta = std::cos(theta);
    const double s_theta = std::sin(theta);
    const double c_phi = std::cos(phi);
    const double s_phi = std::sin(phi);

    const double x1 = vx_world_mps * c_psi + vy_world_mps * s_psi;
    const double y1 = -vx_world_mps * s_psi + vy_world_mps * c_psi;
    const double z1 = vz_world_mps;

    const double x2 = x1 * c_theta + z1 * s_theta;
    const double y2 = y1;
    const double z2 = -x1 * s_theta + z1 * c_theta;

    return {
        x2,
        y2 * c_phi + z2 * s_phi,
        -y2 * s_phi + z2 * c_phi,
    };
}

ApproximateAeroOutputs approximate_aero_outputs(const ExactWorldStepStateV1& state) {
    constexpr double kBlendStartMps = 2.0;
    constexpr double kBlendEndMps = 8.0;

    const double wind_vx = state.has_environment_sample ? state.environment_sample.wind_vx_mps : 0.0;
    const double wind_vy = state.has_environment_sample ? state.environment_sample.wind_vy_mps : 0.0;
    const double vx_air = state.velocity.vx - wind_vx;
    const double vy_air = state.velocity.vy - wind_vy;
    const double vz_air = state.velocity.vz;

    const double v_sq = vx_air * vx_air + vy_air * vy_air + vz_air * vz_air;
    const double v_total = std::sqrt(v_sq);
    const double alt_km = std::max(0.0, state.transform.z) / 1000.0;
    const double rho = 1.225 * std::exp(-alt_km / 7.2);
    double speed_of_sound = 340.29 - (4.0 * alt_km);
    if (speed_of_sound < 295.0) {
        speed_of_sound = 295.0;
    }

    const auto v_body = world_to_body_velocity(
        vx_air,
        vy_air,
        vz_air,
        state.transform.heading,
        state.transform.pitch,
        state.transform.roll
    );
    const double alpha_raw = std::atan2(-v_body.z_mps, v_body.x_mps) * (180.0 / kPi);
    double beta_arg = v_body.y_mps / std::max(v_total, 1.0e-6);
    beta_arg = std::clamp(beta_arg, -1.0, 1.0);
    const double beta_raw = std::asin(beta_arg) * (180.0 / kPi);

    double blend = 1.0;
    if (v_total <= kBlendStartMps) {
        blend = 0.0;
    } else if (v_total < kBlendEndMps) {
        blend = (v_total - kBlendStartMps) / (kBlendEndMps - kBlendStartMps);
    }
    blend = std::clamp(blend, 0.0, 1.0);

    const double previous_alpha = state.has_aero_state ? state.aero_state.angle_of_attack : 0.0;
    const double previous_beta = state.has_aero_state ? state.aero_state.sideslip_angle : 0.0;

    ApproximateAeroOutputs out{};
    out.dynamic_pressure = 0.5 * rho * v_sq;
    out.mach_number = speed_of_sound > 1.0 ? (v_total / speed_of_sound) : 0.0;
    out.angle_of_attack = std::clamp((1.0 - blend) * previous_alpha + blend * alpha_raw, -90.0, 90.0);
    out.sideslip_angle = std::clamp((1.0 - blend) * previous_beta + blend * beta_raw, -90.0, 90.0);
    return out;
}

ApproximateAeroOutputs approximate_aero_outputs(const ExactWorldStepPrototypeSoA& soa, std::size_t i) {
    constexpr double kBlendStartMps = 2.0;
    constexpr double kBlendEndMps = 8.0;

    const double vx_air = soa.vx_mps[i] - soa.wind_vx_mps[i];
    const double vy_air = soa.vy_mps[i] - soa.wind_vy_mps[i];
    const double vz_air = soa.vz_mps[i];

    const double v_sq = vx_air * vx_air + vy_air * vy_air + vz_air * vz_air;
    const double v_total = std::sqrt(v_sq);
    const double alt_km = std::max(0.0, soa.z_m[i]) / 1000.0;
    const double rho = 1.225 * std::exp(-alt_km / 7.2);
    double speed_of_sound = 340.29 - (4.0 * alt_km);
    if (speed_of_sound < 295.0) {
        speed_of_sound = 295.0;
    }

    const auto v_body = world_to_body_velocity(
        vx_air,
        vy_air,
        vz_air,
        soa.heading_deg[i],
        soa.pitch_deg[i],
        soa.roll_deg[i]
    );
    const double alpha_raw = std::atan2(-v_body.z_mps, v_body.x_mps) * (180.0 / kPi);
    double beta_arg = v_body.y_mps / std::max(v_total, 1.0e-6);
    beta_arg = std::clamp(beta_arg, -1.0, 1.0);
    const double beta_raw = std::asin(beta_arg) * (180.0 / kPi);

    double blend = 1.0;
    if (v_total <= kBlendStartMps) {
        blend = 0.0;
    } else if (v_total < kBlendEndMps) {
        blend = (v_total - kBlendStartMps) / (kBlendEndMps - kBlendStartMps);
    }
    blend = std::clamp(blend, 0.0, 1.0);

    ApproximateAeroOutputs out{};
    out.dynamic_pressure = 0.5 * rho * v_sq;
    out.mach_number = speed_of_sound > 1.0 ? (v_total / speed_of_sound) : 0.0;
    out.angle_of_attack = std::clamp(
        (1.0 - blend) * soa.aero_angle_of_attack_deg[i] + blend * alpha_raw,
        -90.0,
        90.0
    );
    out.sideslip_angle = std::clamp(
        (1.0 - blend) * soa.aero_sideslip_angle_deg[i] + blend * beta_raw,
        -90.0,
        90.0
    );
    return out;
}

ApproximateAeroCoefficients approximate_aero_coefficients(
    double alpha_deg,
    double current_drag_index,
    double gear_extension_state
) {
    double cl = 0.1 * alpha_deg;
    const double alpha_abs = std::abs(alpha_deg);
    const double alpha_sign = alpha_deg >= 0.0 ? 1.0 : -1.0;
    constexpr double alpha_stall_deg = 15.0;
    constexpr double alpha_peak_deg = 23.0;
    constexpr double alpha_deep_deg = 41.0;
    constexpr double cl_peak_mag = 1.25;
    constexpr double cl_deep_mag = 0.22;

    if (alpha_abs > alpha_stall_deg) {
        if (alpha_abs <= alpha_peak_deg) {
            const double t = smoothstep01((alpha_abs - alpha_stall_deg) / std::max(1e-6, alpha_peak_deg - alpha_stall_deg));
            cl = (1.0 - t) * cl + t * (alpha_sign * cl_peak_mag);
        } else if (alpha_abs <= alpha_deep_deg) {
            const double t = smoothstep01((alpha_abs - alpha_peak_deg) / std::max(1e-6, alpha_deep_deg - alpha_peak_deg));
            cl = (1.0 - t) * (alpha_sign * cl_peak_mag) + t * (alpha_sign * cl_deep_mag);
        } else {
            cl = alpha_sign * cl_deep_mag;
        }
    }

    double cd0 = 0.02;
    cd0 += current_drag_index * 0.001;
    cd0 += std::clamp(gear_extension_state, 0.0, 1.0) * 0.04;
    constexpr double kInducedDrag = 0.1;
    double stall_drag = 0.0;
    if (alpha_abs > alpha_stall_deg) {
        const double s1 = smoothstep01((alpha_abs - alpha_stall_deg) / std::max(1e-6, alpha_peak_deg - alpha_stall_deg));
        const double s2 = smoothstep01((alpha_abs - alpha_peak_deg) / std::max(1e-6, alpha_deep_deg - alpha_peak_deg));
        stall_drag = 0.25 * s1 + 0.55 * s2;
    }

    return {
        cl,
        cd0 + kInducedDrag * cl * cl + stall_drag,
    };
}

ApproximateInertia estimate_inertia(
    double total_mass_kg,
    double wing_span_m,
    double chord_m
) {
    const double mass = std::max(1000.0, total_mass_kg);
    const double span = std::max(4.0, wing_span_m);
    const double chord_extent = std::max(2.0, chord_m * 2.0);
    const double depth_extent = std::max(1.0, chord_m * 0.35);
    return {
        std::max(5000.0, mass * ((depth_extent * depth_extent) + (span * span)) / 12.0),
        std::max(5000.0, mass * ((depth_extent * depth_extent) + (chord_extent * chord_extent)) / 12.0),
        std::max(5000.0, mass * ((span * span) + (chord_extent * chord_extent)) / 12.0),
    };
}

ResolvedTargets resolve_targets(const ExactWorldStepStateV1& state) {
    ResolvedTargets out{};
    out.heading_deg = state.transform.heading;
    out.speed_mps = std::hypot(state.velocity.vx, state.velocity.vy);
    out.altitude_m = state.transform.z;
    if (state.has_mission_command && state.mission_command.active) {
        out.active = true;
        if (std::isfinite(state.mission_command.cmd_heading_deg)) {
            out.heading_deg = state.mission_command.cmd_heading_deg;
        }
        if (std::isfinite(state.mission_command.cmd_speed_mps) && state.mission_command.cmd_speed_mps >= 0.0) {
            out.speed_mps = state.mission_command.cmd_speed_mps;
        }
        if (std::isfinite(state.mission_command.cmd_altitude_m)) {
            out.altitude_m = state.mission_command.cmd_altitude_m;
        }
    } else if (state.has_movement_command && state.movement_command.active) {
        out.active = true;
        if (std::isfinite(state.movement_command.target_heading)) {
            out.heading_deg = state.movement_command.target_heading;
        }
        if (std::isfinite(state.movement_command.target_speed) && state.movement_command.target_speed >= 0.0) {
            out.speed_mps = state.movement_command.target_speed;
        }
        if (std::isfinite(state.movement_command.target_altitude)) {
            out.altitude_m = state.movement_command.target_altitude;
        }
    }
    out.heading_deg = wrap_heading_deg(out.heading_deg);
    out.speed_mps = std::max(0.0, out.speed_mps);
    return out;
}

void prototype_step_once(ExactWorldStepPrototypeSoA& soa, std::size_t i) {
    const double dt = std::max(0.0, soa.time_step_s[i]);
    if (dt <= 0.0) {
        return;
    }

    const double prev_vx = soa.vx_mps[i];
    const double prev_vy = soa.vy_mps[i];
    const double prev_vz = soa.vz_mps[i];
    const double prev_heading = soa.heading_deg[i];
    const double prev_pitch = soa.pitch_deg[i];
    const double prev_roll = soa.roll_deg[i];

    double lagged_heading = soa.lagged_heading_deg[i];
    double lagged_speed = soa.lagged_speed_mps[i];
    double lagged_altitude = soa.lagged_altitude_m[i];

    if (soa.has_command_lag[i] != 0u) {
        const double heading_delta = shortest_heading_delta_deg(soa.target_heading_deg[i], lagged_heading);
        lagged_heading = wrap_heading_deg(
            lagged_heading + lerp_tau(0.0, heading_delta, std::max(1e-4, soa.heading_tau_s[i]), dt)
        );
        lagged_speed = lerp_tau(lagged_speed, soa.target_speed_mps[i], std::max(1e-4, soa.speed_tau_s[i]), dt);
        lagged_altitude = lerp_tau(
            lagged_altitude,
            soa.target_altitude_m[i],
            std::max(1e-4, soa.altitude_tau_s[i]),
            dt
        );
    } else {
        lagged_heading = soa.target_heading_deg[i];
        lagged_speed = soa.target_speed_mps[i];
        lagged_altitude = soa.target_altitude_m[i];
    }

    soa.lagged_heading_deg[i] = wrap_heading_deg(lagged_heading);
    soa.lagged_speed_mps[i] = std::max(0.0, lagged_speed);
    soa.lagged_altitude_m[i] = lagged_altitude;
    soa.lagged_active[i] = 1u;
    soa.output_has_lagged_command[i] = 1u;

    const double guidance_heading_deg = soa.lagged_heading_deg[i];
    const double guidance_altitude_m = soa.lagged_altitude_m[i];

    const double min_speed = std::max(0.0, soa.min_speed_mps[i]);
    const double max_speed = std::max(min_speed, soa.max_speed_mps[i]);
    const double desired_speed = std::clamp(soa.lagged_speed_mps[i], min_speed, max_speed > 0.0 ? max_speed : soa.lagged_speed_mps[i]);
    const double heading_rad = soa.lagged_heading_deg[i] * (kPi / 180.0);
    const double desired_vx = std::sin(heading_rad) * desired_speed;
    const double desired_vy = std::cos(heading_rad) * desired_speed;
    const double max_climb_rate = std::max(1.0, soa.max_climb_rate_mps[i]);
    const double desired_vz = std::clamp((soa.lagged_altitude_m[i] - soa.z_m[i]) / 10.0, -max_climb_rate, max_climb_rate);

    const double dv_limit_xy = std::max(0.1, soa.max_accel_mps2[i] * dt);
    const double dv_limit_z = std::max(0.1, max_climb_rate * dt);

    soa.vx_mps[i] += clamp_symmetric(desired_vx - soa.vx_mps[i], dv_limit_xy);
    soa.vy_mps[i] += clamp_symmetric(desired_vy - soa.vy_mps[i], dv_limit_xy);
    soa.vz_mps[i] += clamp_symmetric(desired_vz - soa.vz_mps[i], dv_limit_z);

    soa.x_m[i] += (soa.vx_mps[i] + soa.wind_vx_mps[i]) * dt;
    soa.y_m[i] += (soa.vy_mps[i] + soa.wind_vy_mps[i]) * dt;
    soa.z_m[i] += soa.vz_mps[i] * dt;
    if (soa.z_m[i] < soa.terrain_elevation_m[i]) {
        soa.z_m[i] = soa.terrain_elevation_m[i];
        if (soa.vz_mps[i] < 0.0) {
            soa.vz_mps[i] = 0.0;
        }
    }

    const bool on_ground = soa.z_m[i] <= soa.terrain_elevation_m[i] + 0.25;
    soa.force_torque_roll_nm[i] = 0.0;
    soa.force_torque_pitch_nm[i] = 0.0;
    soa.force_torque_yaw_nm[i] = 0.0;
    const auto aero = approximate_aero_outputs(soa, i);
    const auto aero_coeff = approximate_aero_coefficients(
        aero.angle_of_attack,
        soa.current_drag_index[i],
        soa.gear_extension_state[i]
    );
    soa.aero_dynamic_pressure_pa[i] = aero.dynamic_pressure;
    soa.aero_mach_number[i] = aero.mach_number;
    soa.aero_angle_of_attack_deg[i] = aero.angle_of_attack;
    soa.aero_sideslip_angle_deg[i] = aero.sideslip_angle;
    soa.aero_lift_coefficient[i] = aero_coeff.lift_coefficient;
    soa.aero_drag_coefficient[i] = aero_coeff.drag_coefficient;

    const double total_mass = std::max(1.0, soa.total_mass_kg[i]);
    soa.force_fx_n[i] = 0.0;
    soa.force_fy_n[i] = 0.0;
    soa.force_fz_n[i] = 0.0;

    const double current_heading_deg = soa.heading_deg[i];
    const double current_track_deg = nav_heading_deg_from_velocity(
        soa.vx_mps[i],
        soa.vy_mps[i],
        current_heading_deg
    );
    double lateral_reference_deg = current_heading_deg;
    double bank_limit_deg = 60.0;
    double heading_to_bank_gain = 2.0;
    double bank_to_stick_gain = 0.05;
    double altitude_to_pitch_gain = 0.1;
    double pitch_min_deg = -15.0;
    double pitch_max_deg = 20.0;
    double pitch_to_stick_gain = 0.1;

    if (soa.control_profile_code[i] == 3) {
        lateral_reference_deg = current_track_deg;
        bank_limit_deg = 45.0;
    } else if (soa.control_profile_code[i] == 4) {
        bank_limit_deg = on_ground ? 8.0 : 22.0;
        heading_to_bank_gain = 1.0;
        bank_to_stick_gain = 0.04;
        altitude_to_pitch_gain = 0.05;
        pitch_min_deg = on_ground ? -2.0 : -8.0;
        pitch_max_deg = on_ground ? 5.0 : 12.0;
        pitch_to_stick_gain = 0.08;
    } else if (soa.control_profile_code[i] == 1) {
        bank_limit_deg = 30.0;
        heading_to_bank_gain = 1.4;
    }

    double stick_roll = 0.0;
    double stick_pitch = 0.0;
    double stick_yaw = 0.0;
    if (soa.control_profile_code[i] != 0 || soa.lagged_active[i] != 0u) {
        const double heading_err = shortest_heading_delta_deg(guidance_heading_deg, lateral_reference_deg);
        const double target_bank = std::clamp(
            heading_err * heading_to_bank_gain,
            -bank_limit_deg,
            bank_limit_deg
        );
        const double bank_err = target_bank - soa.roll_deg[i];
        stick_roll = std::clamp(bank_err * bank_to_stick_gain, -1.0, 1.0);

        const double alt_err = guidance_altitude_m - soa.z_m[i];
        const double target_pitch = std::clamp(
            alt_err * altitude_to_pitch_gain,
            pitch_min_deg,
            pitch_max_deg
        );
        const double pitch_err = target_pitch - soa.pitch_deg[i];
        stick_pitch = std::clamp(pitch_err * pitch_to_stick_gain, -1.0, 1.0);
    }

    constexpr double kPMaxRadS = 1.2;
    constexpr double kQMaxRadS = 0.8;
    constexpr double kRMaxRadS = 0.8;
    constexpr double kRollGain = 40.0;
    constexpr double kPitchGain = 60.0;
    constexpr double kYawGain = 20.0;
    constexpr double kMaxRateCrossRadS = 50.0;
    constexpr double kMaxTorqueNm = 5.0e6;
    constexpr double kMaxAngAccelRadS2 = 1.0e4;
    constexpr double kMaxRateRadS = 6.0;
    constexpr double kMinAbsCosTheta = 0.08715574274765817;  // cos(85 deg)
    constexpr double kPitchLimitDeg = 89.0;

    constexpr double kStickTauS = 0.15;
    soa.control_stick_roll_filt[i] = control_lpf(soa.control_stick_roll_filt[i], stick_roll, kStickTauS, dt);
    soa.control_stick_pitch_filt[i] = control_lpf(soa.control_stick_pitch_filt[i], stick_pitch, kStickTauS, dt);
    soa.control_stick_yaw_filt[i] = control_lpf(soa.control_stick_yaw_filt[i], stick_yaw, kStickTauS, dt);
    soa.has_control_law_state[i] = 1u;

    const double stick_roll_f = std::clamp(soa.control_stick_roll_filt[i], -1.0, 1.0);
    const double stick_pitch_f = std::clamp(soa.control_stick_pitch_filt[i], -1.0, 1.0);
    const double stick_yaw_f = std::clamp(soa.control_stick_yaw_filt[i], -1.0, 1.0);

    double stick_yaw_cmd = stick_yaw_f;
    if (on_ground) {
        constexpr double kYawLimitStartMps = 5.0;
        constexpr double kYawLimitEndMps = 80.0;
        constexpr double kYawMaxLowSpeed = 1.0;
        constexpr double kYawMaxHighSpeed = 0.35;
        const double v_h = std::hypot(soa.vx_mps[i], soa.vy_mps[i]);
        double t = 0.0;
        if (v_h > kYawLimitStartMps) {
            t = (v_h - kYawLimitStartMps) / (kYawLimitEndMps - kYawLimitStartMps);
            t = std::clamp(t, 0.0, 1.0);
        }
        const double yaw_max = kYawMaxLowSpeed + t * (kYawMaxHighSpeed - kYawMaxLowSpeed);
        stick_yaw_cmd = std::clamp(stick_yaw_cmd, -yaw_max, yaw_max);
    }
    soa.control_stick_yaw_cmd[i] = stick_yaw_cmd;

    double p_cmd = stick_roll_f * kPMaxRadS;
    double q_cmd = stick_pitch_f * kQMaxRadS;
    double r_cmd = stick_yaw_cmd * kRMaxRadS;

    if (!on_ground) {
        const double beta_rad = aero.sideslip_angle * (kPi / 180.0);
        r_cmd += (-1.10 * beta_rad) + (-0.55 * soa.r_rad_s[i]);
        r_cmd = std::clamp(r_cmd, -kRMaxRadS, kRMaxRadS);
    }

    if (on_ground) {
        constexpr double kPitchSoftDeg = 8.0;
        constexpr double kPitchHardDeg = 12.0;
        if (soa.pitch_deg[i] > kPitchSoftDeg && q_cmd > 0.0) {
            const double t = (soa.pitch_deg[i] - kPitchSoftDeg) / (kPitchHardDeg - kPitchSoftDeg);
            q_cmd *= 1.0 - std::clamp(t, 0.0, 1.0);
        }
        if (soa.pitch_deg[i] > kPitchHardDeg) {
            q_cmd = std::min(q_cmd, -0.2);
        }
    } else {
        constexpr double kPitchSoftDeg = 60.0;
        constexpr double kPitchHardDeg = 80.0;
        if (soa.pitch_deg[i] > kPitchSoftDeg && q_cmd > 0.0) {
            const double t = (soa.pitch_deg[i] - kPitchSoftDeg) / (kPitchHardDeg - kPitchSoftDeg);
            q_cmd *= 1.0 - std::clamp(t, 0.0, 1.0);
        }
        if (soa.pitch_deg[i] > kPitchHardDeg) {
            q_cmd = std::min(q_cmd, -0.2);
        }
    }

    constexpr double kAoASoftDeg = 10.0;
    constexpr double kAoAHardDeg = 18.0;
    const double alpha_abs = std::abs(aero.angle_of_attack);
    if (alpha_abs > kAoASoftDeg) {
        const double t = (alpha_abs - kAoASoftDeg) / (kAoAHardDeg - kAoASoftDeg);
        q_cmd *= 1.0 - std::clamp(t, 0.0, 1.0);
    }
    if (alpha_abs > kAoAHardDeg) {
        q_cmd = std::min(q_cmd, -0.15);
    }

    const double q_bar_eff = std::min(aero.dynamic_pressure, 9000.0);
    const double control_roll_torque = (p_cmd - soa.p_rad_s[i]) * (kRollGain * q_bar_eff);
    const double control_pitch_torque = (q_cmd - soa.q_rad_s[i]) * (kPitchGain * q_bar_eff);
    const double control_yaw_torque = (r_cmd - soa.r_rad_s[i]) * (kYawGain * q_bar_eff);

    const double ref_area = std::max(1.0, soa.reference_area_m2[i]);
    const double wing_span = std::max(1.0, soa.wing_span_m[i]);
    const double chord = std::max(0.1, soa.chord_m[i]);
    const double speed_total = std::max(
        10.0,
        std::sqrt(
            soa.vx_mps[i] * soa.vx_mps[i] +
            soa.vy_mps[i] * soa.vy_mps[i] +
            soa.vz_mps[i] * soa.vz_mps[i]
        )
    );
    const double p_hat = soa.p_rad_s[i] * wing_span / (2.0 * speed_total);
    const double q_hat = soa.q_rad_s[i] * chord / (2.0 * speed_total);
    const double r_hat = soa.r_rad_s[i] * wing_span / (2.0 * speed_total);
    const double stall_rel = smoothstep01((alpha_abs - 15.0) / (33.0 - 15.0));
    const double damp_scale = std::clamp(1.0 - 0.7 * stall_rel, 0.25, 1.0);
    const double cm = (-0.8 * (aero.angle_of_attack * (kPi / 180.0))) + (-12.0 * damp_scale * q_hat);
    const double cl_mom =
        (-0.1 * (aero.sideslip_angle * (kPi / 180.0))) +
        (-0.45 * damp_scale * p_hat) +
        (0.1 * r_hat);
    const double cn_mom =
        (0.15 * (aero.sideslip_angle * (kPi / 180.0))) +
        (-0.25 * damp_scale * r_hat);
    const double aero_pitch_torque = aero.dynamic_pressure * ref_area * chord * cm;
    const double aero_roll_torque = aero.dynamic_pressure * ref_area * wing_span * cl_mom;
    const double aero_yaw_torque = aero.dynamic_pressure * ref_area * wing_span * cn_mom;

    soa.force_torque_roll_nm[i] = control_roll_torque + aero_roll_torque;
    soa.force_torque_pitch_nm[i] = control_pitch_torque + aero_pitch_torque;
    soa.force_torque_yaw_nm[i] = control_yaw_torque + aero_yaw_torque;

    const auto inertia = estimate_inertia(soa.total_mass_kg[i], wing_span, chord);
    const double p = std::clamp(soa.p_rad_s[i], -kMaxRateCrossRadS, kMaxRateCrossRadS);
    const double q = std::clamp(soa.q_rad_s[i], -kMaxRateCrossRadS, kMaxRateCrossRadS);
    const double r = std::clamp(soa.r_rad_s[i], -kMaxRateCrossRadS, kMaxRateCrossRadS);
    const double roll_torque = std::clamp(soa.force_torque_roll_nm[i], -kMaxTorqueNm, kMaxTorqueNm);
    const double pitch_torque = std::clamp(soa.force_torque_pitch_nm[i], -kMaxTorqueNm, kMaxTorqueNm);
    const double yaw_torque = std::clamp(soa.force_torque_yaw_nm[i], -kMaxTorqueNm, kMaxTorqueNm);
    const double p_dot = (roll_torque - (inertia.izz - inertia.iyy) * q * r) / inertia.ixx;
    const double q_dot = (pitch_torque - (inertia.ixx - inertia.izz) * p * r) / inertia.iyy;
    const double r_dot = (yaw_torque - (inertia.iyy - inertia.ixx) * p * q) / inertia.izz;
    soa.p_rad_s[i] = std::clamp(p + std::clamp(p_dot, -kMaxAngAccelRadS2, kMaxAngAccelRadS2) * dt, -kMaxRateRadS, kMaxRateRadS);
    soa.q_rad_s[i] = std::clamp(q + std::clamp(q_dot, -kMaxAngAccelRadS2, kMaxAngAccelRadS2) * dt, -kMaxRateRadS, kMaxRateRadS);
    soa.r_rad_s[i] = std::clamp(r + std::clamp(r_dot, -kMaxAngAccelRadS2, kMaxAngAccelRadS2) * dt, -kMaxRateRadS, kMaxRateRadS);

    const double phi = soa.roll_deg[i] * (kPi / 180.0);
    const double theta = soa.pitch_deg[i] * (kPi / 180.0);
    const double c_phi = std::cos(phi);
    const double s_phi = std::sin(phi);
    double c_theta = std::cos(theta);
    const double s_theta = std::sin(theta);
    if (std::abs(c_theta) < kMinAbsCosTheta) {
        c_theta = std::copysign(kMinAbsCosTheta, c_theta);
    }
    const double t_theta = s_theta / c_theta;
    const double sec_theta = 1.0 / c_theta;
    const double d_phi = soa.p_rad_s[i] + (soa.q_rad_s[i] * s_phi + soa.r_rad_s[i] * c_phi) * t_theta;
    const double d_theta = soa.q_rad_s[i] * c_phi - soa.r_rad_s[i] * s_phi;
    const double d_psi = (soa.q_rad_s[i] * s_phi + soa.r_rad_s[i] * c_phi) * sec_theta;
    soa.roll_deg[i] += d_phi * dt * (180.0 / kPi);
    soa.pitch_deg[i] += d_theta * dt * (180.0 / kPi);
    soa.heading_deg[i] -= d_psi * dt * (180.0 / kPi);
    soa.roll_deg[i] = std::fmod(soa.roll_deg[i] + 180.0, 360.0);
    if (soa.roll_deg[i] < 0.0) {
        soa.roll_deg[i] += 360.0;
    }
    soa.roll_deg[i] -= 180.0;
    soa.pitch_deg[i] = std::clamp(soa.pitch_deg[i], -kPitchLimitDeg, kPitchLimitDeg);
    soa.heading_deg[i] = wrap_heading_deg(soa.heading_deg[i]);

    const auto sensed_force_body = world_to_body_velocity(
        (soa.vx_mps[i] - prev_vx) / dt,
        (soa.vy_mps[i] - prev_vy) / dt,
        ((soa.vz_mps[i] - prev_vz) / dt) + kGravityMps2,
        soa.heading_deg[i],
        soa.pitch_deg[i],
        soa.roll_deg[i]
    );
    const double inv_weight = 1.0 / kGravityMps2;
    soa.g_load_axial[i] = sensed_force_body.x_mps * inv_weight;
    soa.g_load_normal[i] = sensed_force_body.z_mps * inv_weight;
    soa.world_time_s[i] += dt;

    const double speed_metric = std::abs(soa.vx_mps[i]) + std::abs(soa.vy_mps[i]) + std::abs(soa.vz_mps[i]);
    const double speed_ratio = max_speed > 1e-6 ? std::clamp(desired_speed / max_speed, 0.0, 1.0) : 0.0;
    double burn_rate = soa.fuel_flow_rate_kgps[i];
    if (burn_rate <= 0.0) {
        burn_rate = 0.05 + 0.0006 * speed_metric;
    } else {
        burn_rate *= 0.35 + 0.65 * speed_ratio;
    }
    if (soa.fuel_afterburner_active[i] != 0u) {
        burn_rate *= std::max(1.0, soa.fuel_ab_multiplier[i]);
    }
    const double leak_rate = std::max(0.0, soa.mass_fuel_leak_rate_kgps[i]);
    const double burn_kg = (burn_rate + leak_rate) * dt;
    double remaining_burn = burn_kg;
    const double external_burn = std::min(soa.fuel_external_kg[i], remaining_burn);
    soa.fuel_external_kg[i] -= external_burn;
    remaining_burn -= external_burn;
    const double internal_burn = std::min(soa.fuel_internal_kg[i], remaining_burn);
    soa.fuel_internal_kg[i] -= internal_burn;
    soa.mass_fuel_kg[i] = std::max(0.0, soa.fuel_internal_kg[i] + soa.fuel_external_kg[i]);
    soa.total_mass_kg[i] = soa.mass_empty_kg[i] + soa.mass_stores_kg[i] + soa.mass_fuel_kg[i];
    soa.fuel_flow_rate_kgps[i] = burn_rate;
    canonicalize_step_outputs(soa, i);
}

}  // namespace

ExactWorldStepPrototypeStats last_exact_world_step_prototype_stats() {
    return g_last_stats;
}

ExactWorldStepPrototypeSoA pack_exact_world_step_states_v1_prototype_soa(
    const std::vector<ExactWorldStepStateV1>& states
) {
    ExactWorldStepPrototypeSoA soa{};
    soa.size = states.size();

    auto reserve_all = [&](auto& vec) {
        vec.reserve(states.size());
    };
    reserve_all(soa.time_step_s);
    reserve_all(soa.world_time_s);
    reserve_all(soa.x_m);
    reserve_all(soa.y_m);
    reserve_all(soa.z_m);
    reserve_all(soa.heading_deg);
    reserve_all(soa.pitch_deg);
    reserve_all(soa.roll_deg);
    reserve_all(soa.vx_mps);
    reserve_all(soa.vy_mps);
    reserve_all(soa.vz_mps);
    reserve_all(soa.p_rad_s);
    reserve_all(soa.q_rad_s);
    reserve_all(soa.r_rad_s);
    reserve_all(soa.g_load_normal);
    reserve_all(soa.g_load_axial);
    reserve_all(soa.wind_vx_mps);
    reserve_all(soa.wind_vy_mps);
    reserve_all(soa.terrain_elevation_m);
    reserve_all(soa.target_heading_deg);
    reserve_all(soa.target_speed_mps);
    reserve_all(soa.target_altitude_m);
    reserve_all(soa.heading_tau_s);
    reserve_all(soa.speed_tau_s);
    reserve_all(soa.altitude_tau_s);
    reserve_all(soa.has_command_lag);
    reserve_all(soa.lagged_heading_deg);
    reserve_all(soa.lagged_speed_mps);
    reserve_all(soa.lagged_altitude_m);
    reserve_all(soa.lagged_active);
    reserve_all(soa.output_has_lagged_command);
    reserve_all(soa.max_speed_mps);
    reserve_all(soa.min_speed_mps);
    reserve_all(soa.max_accel_mps2);
    reserve_all(soa.max_climb_rate_mps);
    reserve_all(soa.reference_area_m2);
    reserve_all(soa.wing_span_m);
    reserve_all(soa.chord_m);
    reserve_all(soa.current_drag_index);
    reserve_all(soa.gear_extension_state);
    reserve_all(soa.aero_dynamic_pressure_pa);
    reserve_all(soa.aero_mach_number);
    reserve_all(soa.aero_angle_of_attack_deg);
    reserve_all(soa.aero_sideslip_angle_deg);
    reserve_all(soa.aero_lift_coefficient);
    reserve_all(soa.aero_drag_coefficient);
    reserve_all(soa.force_fx_n);
    reserve_all(soa.force_fy_n);
    reserve_all(soa.force_fz_n);
    reserve_all(soa.force_torque_roll_nm);
    reserve_all(soa.force_torque_pitch_nm);
    reserve_all(soa.force_torque_yaw_nm);
    reserve_all(soa.control_stick_roll_filt);
    reserve_all(soa.control_stick_pitch_filt);
    reserve_all(soa.control_stick_yaw_filt);
    reserve_all(soa.control_stick_yaw_cmd);
    reserve_all(soa.control_profile_code);
    reserve_all(soa.has_angular_velocity);
    reserve_all(soa.has_force_accumulator);
    reserve_all(soa.has_aero_state);
    reserve_all(soa.has_control_law_state);
    reserve_all(soa.fuel_internal_kg);
    reserve_all(soa.fuel_external_kg);
    reserve_all(soa.fuel_flow_rate_kgps);
    reserve_all(soa.fuel_ab_multiplier);
    reserve_all(soa.fuel_afterburner_active);
    reserve_all(soa.has_fuel_system);
    reserve_all(soa.propulsion_current_thrust_n);
    reserve_all(soa.has_propulsion);
    reserve_all(soa.mass_empty_kg);
    reserve_all(soa.mass_stores_kg);
    reserve_all(soa.mass_fuel_kg);
    reserve_all(soa.mass_fuel_leak_rate_kgps);
    reserve_all(soa.has_mass);
    reserve_all(soa.total_mass_kg);
    reserve_all(soa.has_mass_properties);
    reserve_all(soa.has_ground_state);
    reserve_all(soa.has_instrument_state);
    reserve_all(soa.has_egi);

    for (const auto& state : states) {
        const auto resolved = resolve_targets(state);
        const double horiz_speed = std::hypot(state.velocity.vx, state.velocity.vy);

        soa.time_step_s.push_back(state.time_step_s);
        soa.world_time_s.push_back(state.world_time_s);
        soa.x_m.push_back(state.transform.x);
        soa.y_m.push_back(state.transform.y);
        soa.z_m.push_back(state.transform.z);
        soa.heading_deg.push_back(state.transform.heading);
        soa.pitch_deg.push_back(state.transform.pitch);
        soa.roll_deg.push_back(state.transform.roll);
        soa.vx_mps.push_back(state.velocity.vx);
        soa.vy_mps.push_back(state.velocity.vy);
        soa.vz_mps.push_back(state.velocity.vz);
        soa.p_rad_s.push_back(state.has_angular_velocity ? state.angular_velocity.p : 0.0);
        soa.q_rad_s.push_back(state.has_angular_velocity ? state.angular_velocity.q : 0.0);
        soa.r_rad_s.push_back(state.has_angular_velocity ? state.angular_velocity.r : 0.0);
        soa.g_load_normal.push_back(state.has_instrument_state ? state.instrument_state.g_load_normal : 0.0);
        soa.g_load_axial.push_back(state.has_instrument_state ? state.instrument_state.g_load_axial : 0.0);
        soa.wind_vx_mps.push_back(state.has_environment_sample ? state.environment_sample.wind_vx_mps : 0.0);
        soa.wind_vy_mps.push_back(state.has_environment_sample ? state.environment_sample.wind_vy_mps : 0.0);
        soa.terrain_elevation_m.push_back(state.has_environment_sample ? state.environment_sample.terrain_elevation_m : 0.0);

        soa.target_heading_deg.push_back(resolved.heading_deg);
        soa.target_speed_mps.push_back(resolved.speed_mps);
        soa.target_altitude_m.push_back(resolved.altitude_m);

        soa.has_command_lag.push_back(state.has_command_lag ? 1u : 0u);
        soa.heading_tau_s.push_back(state.has_command_lag ? std::max(1e-4, state.command_lag.heading_tau_s) : 0.0);
        soa.speed_tau_s.push_back(state.has_command_lag ? std::max(1e-4, state.command_lag.speed_tau_s) : 0.0);
        soa.altitude_tau_s.push_back(state.has_command_lag ? std::max(1e-4, state.command_lag.altitude_tau_s) : 0.0);

        const bool lag_active = state.has_lagged_command ? state.lagged_command.active : resolved.active;
        soa.lagged_heading_deg.push_back(state.has_lagged_command ? state.lagged_command.target_heading : state.transform.heading);
        soa.lagged_speed_mps.push_back(
            state.has_lagged_command ? state.lagged_command.target_speed : std::hypot(state.velocity.vx, state.velocity.vy)
        );
        soa.lagged_altitude_m.push_back(state.has_lagged_command ? state.lagged_command.target_altitude : state.transform.z);
        soa.lagged_active.push_back(lag_active ? 1u : 0u);
        soa.output_has_lagged_command.push_back((state.has_lagged_command || state.has_command_lag || resolved.active) ? 1u : 0u);

        const double fallback_max_speed = std::max(resolved.speed_mps, horiz_speed) + 50.0;
        soa.max_speed_mps.push_back(state.has_flight_model ? std::max(1.0, state.flight_model.max_speed) : std::max(60.0, fallback_max_speed));
        soa.min_speed_mps.push_back(state.has_flight_model ? std::max(0.0, state.flight_model.min_speed) : 50.0);
        soa.max_accel_mps2.push_back(state.has_flight_model ? std::max(1.0, state.flight_model.max_accel) : 12.0);
        soa.max_climb_rate_mps.push_back(state.has_flight_model ? std::max(1.0, state.flight_model.max_climb_rate) : 25.0);
        soa.reference_area_m2.push_back(state.has_mass_properties ? std::max(1.0, state.mass_properties.reference_area_m2) : 30.0);
        soa.wing_span_m.push_back(state.has_mass_properties ? std::max(1.0, state.mass_properties.wing_span_m) : 10.0);
        soa.chord_m.push_back(state.has_mass_properties ? std::max(0.1, state.mass_properties.chord_m) : 3.0);
        soa.current_drag_index.push_back(state.has_mass_properties ? state.mass_properties.current_drag_index : 0.0);
        soa.gear_extension_state.push_back(state.has_landing_gear ? state.landing_gear.extension_state : 0.0);
        soa.aero_dynamic_pressure_pa.push_back(state.has_aero_state ? state.aero_state.dynamic_pressure : 0.0);
        soa.aero_mach_number.push_back(state.has_aero_state ? state.aero_state.mach_number : 0.0);
        soa.aero_angle_of_attack_deg.push_back(state.has_aero_state ? state.aero_state.angle_of_attack : 0.0);
        soa.aero_sideslip_angle_deg.push_back(state.has_aero_state ? state.aero_state.sideslip_angle : 0.0);
        soa.aero_lift_coefficient.push_back(state.has_aero_state ? state.aero_state.lift_coefficient : 0.0);
        soa.aero_drag_coefficient.push_back(state.has_aero_state ? state.aero_state.drag_coefficient : 0.0);
        soa.force_fx_n.push_back(state.has_force_accumulator ? state.force_accumulator.fx : 0.0);
        soa.force_fy_n.push_back(state.has_force_accumulator ? state.force_accumulator.fy : 0.0);
        soa.force_fz_n.push_back(state.has_force_accumulator ? state.force_accumulator.fz : 0.0);
        soa.force_torque_roll_nm.push_back(state.has_force_accumulator ? state.force_accumulator.torque_roll : 0.0);
        soa.force_torque_pitch_nm.push_back(state.has_force_accumulator ? state.force_accumulator.torque_pitch : 0.0);
        soa.force_torque_yaw_nm.push_back(state.has_force_accumulator ? state.force_accumulator.torque_yaw : 0.0);
        soa.control_stick_roll_filt.push_back(state.has_control_law_state ? state.control_law_state.stick_roll_filt : 0.0);
        soa.control_stick_pitch_filt.push_back(state.has_control_law_state ? state.control_law_state.stick_pitch_filt : 0.0);
        soa.control_stick_yaw_filt.push_back(state.has_control_law_state ? state.control_law_state.stick_yaw_filt : 0.0);
        soa.control_stick_yaw_cmd.push_back(state.has_control_law_state ? state.control_law_state.stick_yaw_cmd : 0.0);
        soa.control_profile_code.push_back(
            state.has_mission_command && state.mission_command.active
                ? static_cast<std::int32_t>(state.mission_command.command_code)
                : (state.has_movement_command && state.movement_command.active ? 2 : 0)
        );
        soa.has_angular_velocity.push_back(state.has_angular_velocity ? 1u : 0u);
        soa.has_force_accumulator.push_back(state.has_force_accumulator ? 1u : 0u);
        soa.has_aero_state.push_back(state.has_aero_state ? 1u : 0u);
        soa.has_control_law_state.push_back(state.has_control_law_state ? 1u : 0u);

        const double fuel_internal = state.has_fuel_system
            ? std::max(0.0, state.fuel_system.internal_fuel_kg)
            : (state.has_instrument_state ? std::max(0.0, state.instrument_state.fuel_internal_kg) : 0.0);
        const double fuel_external = state.has_fuel_system
            ? std::max(0.0, state.fuel_system.external_fuel_kg)
            : (state.has_instrument_state ? std::max(0.0, state.instrument_state.fuel_external_kg) : 0.0);
        const double flow_rate = state.has_fuel_system
            ? std::max(
                0.0,
                state.fuel_system.current_flow_rate > 0.0
                    ? state.fuel_system.current_flow_rate
                    : state.fuel_system.mil_power_flow_rate
            )
            : (state.has_instrument_state ? std::max(0.0, state.instrument_state.fuel_flow_kg_h / 3600.0) : 0.0);
        soa.fuel_internal_kg.push_back(fuel_internal);
        soa.fuel_external_kg.push_back(fuel_external);
        soa.fuel_flow_rate_kgps.push_back(flow_rate);
        soa.fuel_ab_multiplier.push_back(state.has_fuel_system ? std::max(1.0, state.fuel_system.ab_flow_rate_multiplier) : 3.0);
        soa.fuel_afterburner_active.push_back(
            state.has_fuel_system && state.fuel_system.afterburner_active ? 1u :
            (state.has_propulsion && state.propulsion.afterburner_active ? 1u : 0u)
        );
        soa.has_fuel_system.push_back(state.has_fuel_system ? 1u : 0u);
        soa.propulsion_current_thrust_n.push_back(
            state.has_propulsion ? std::max(0.0, state.propulsion.current_thrust_n) : 0.0
        );
        soa.has_propulsion.push_back(state.has_propulsion ? 1u : 0u);

        const double mass_fuel = state.has_mass ? std::max(0.0, state.mass.fuel_mass_kg) : (fuel_internal + fuel_external);
        soa.mass_empty_kg.push_back(state.has_mass ? state.mass.empty_mass_kg : 0.0);
        soa.mass_stores_kg.push_back(state.has_mass ? state.mass.stores_mass_kg : 0.0);
        soa.mass_fuel_kg.push_back(mass_fuel);
        soa.mass_fuel_leak_rate_kgps.push_back(state.has_mass ? std::max(0.0, state.mass.fuel_leak_rate_kg_s) : 0.0);
        soa.has_mass.push_back(state.has_mass ? 1u : 0u);

        soa.total_mass_kg.push_back(
            state.has_mass_properties
                ? state.mass_properties.current_total_mass_kg
                : (soa.mass_empty_kg.back() + soa.mass_stores_kg.back() + mass_fuel)
        );
        soa.has_mass_properties.push_back(state.has_mass_properties ? 1u : 0u);
        soa.has_ground_state.push_back(state.has_ground_state ? 1u : 0u);
        soa.has_instrument_state.push_back(state.has_instrument_state ? 1u : 0u);
        soa.has_egi.push_back(state.has_egi ? 1u : 0u);
    }

    return soa;
}

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_prototype_soa(
    const ExactWorldStepPrototypeSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
    std::vector<ExactWorldStepStateV1> out = basis_states;
    const std::size_t count = std::min(soa.size, out.size());
    for (std::size_t i = 0; i < count; ++i) {
        auto& state = out[i];
        state.time_step_s = soa.time_step_s[i];
        state.world_time_s = soa.world_time_s[i];

        state.transform.x = soa.x_m[i];
        state.transform.y = soa.y_m[i];
        state.transform.z = soa.z_m[i];
        state.transform.heading = wrap_heading_deg(soa.heading_deg[i]);
        state.transform.pitch = soa.pitch_deg[i];
        state.transform.roll = soa.roll_deg[i];

        state.velocity.vx = soa.vx_mps[i];
        state.velocity.vy = soa.vy_mps[i];
        state.velocity.vz = soa.vz_mps[i];

        if (state.has_angular_velocity || soa.has_angular_velocity[i] != 0u) {
            state.has_angular_velocity = true;
            state.angular_velocity.p = soa.p_rad_s[i];
            state.angular_velocity.q = soa.q_rad_s[i];
            state.angular_velocity.r = soa.r_rad_s[i];
        }

        if (state.has_force_accumulator || soa.has_force_accumulator[i] != 0u) {
            state.has_force_accumulator = true;
            state.force_accumulator.fx = soa.force_fx_n[i];
            state.force_accumulator.fy = soa.force_fy_n[i];
            state.force_accumulator.fz = soa.force_fz_n[i];
            state.force_accumulator.torque_roll = soa.force_torque_roll_nm[i];
            state.force_accumulator.torque_pitch = soa.force_torque_pitch_nm[i];
            state.force_accumulator.torque_yaw = soa.force_torque_yaw_nm[i];
        }

        if (state.has_environment_sample) {
            state.environment_sample.terrain_elevation_m = soa.terrain_elevation_m[i];
            state.environment_sample.wind_vx_mps = soa.wind_vx_mps[i];
            state.environment_sample.wind_vy_mps = soa.wind_vy_mps[i];
        }
        const double dt = std::max(1.0e-6, soa.time_step_s[i]);

        state.has_lagged_command = soa.output_has_lagged_command[i] != 0u;
        if (state.has_lagged_command) {
            state.lagged_command.target_heading = wrap_heading_deg(soa.lagged_heading_deg[i]);
            state.lagged_command.target_speed = std::max(0.0, soa.lagged_speed_mps[i]);
            state.lagged_command.target_altitude = soa.lagged_altitude_m[i];
            state.lagged_command.active = soa.lagged_active[i] != 0u;
        }

        if (state.has_fuel_system || soa.has_fuel_system[i] != 0u) {
            state.has_fuel_system = true;
            state.fuel_system.internal_fuel_kg = std::max(0.0, soa.fuel_internal_kg[i]);
            state.fuel_system.external_fuel_kg = std::max(0.0, soa.fuel_external_kg[i]);
            state.fuel_system.current_flow_rate = std::max(0.0, soa.fuel_flow_rate_kgps[i]);
            state.fuel_system.afterburner_active = soa.fuel_afterburner_active[i] != 0u;
        }

        if (state.has_propulsion || soa.has_propulsion[i] != 0u) {
            state.has_propulsion = true;
            state.propulsion.current_thrust_n = std::max(0.0, soa.propulsion_current_thrust_n[i]);
        }

        if (state.has_mass || soa.has_mass[i] != 0u) {
            state.has_mass = true;
            state.mass.empty_mass_kg = soa.mass_empty_kg[i];
            state.mass.stores_mass_kg = soa.mass_stores_kg[i];
            state.mass.fuel_mass_kg = std::max(0.0, soa.mass_fuel_kg[i]);
            state.mass.fuel_leak_rate_kg_s = std::max(0.0, soa.mass_fuel_leak_rate_kgps[i]);
        }

        if (state.has_mass_properties || soa.has_mass_properties[i] != 0u) {
            state.has_mass_properties = true;
            state.mass_properties.current_total_mass_kg = std::max(0.0, soa.total_mass_kg[i]);
        }

        const bool on_ground = soa.z_m[i] <= soa.terrain_elevation_m[i] + 0.25;
        if (state.has_ground_state || soa.has_ground_state[i] != 0u) {
            state.has_ground_state = true;
            state.ground_state.terrain_elevation = soa.terrain_elevation_m[i];
            state.ground_state.on_ground = on_ground;
        }

        if (state.has_landing_gear) {
            const bool gear_down = commanded_gear_down(state);
            const double target_extension = gear_down ? 1.0 : 0.0;
            const double transit_time_s = std::max(1.0e-3, state.landing_gear.transit_time_s);
            const double step_fraction = std::clamp(dt / transit_time_s, 0.0, 1.0);
            state.landing_gear.extension_state +=
                (target_extension - state.landing_gear.extension_state) * step_fraction;
            state.landing_gear.extension_state = std::clamp(state.landing_gear.extension_state, 0.0, 1.0);
        }

        if (state.has_aero_state) {
            state.aero_state.dynamic_pressure = soa.aero_dynamic_pressure_pa[i];
            state.aero_state.mach_number = soa.aero_mach_number[i];
            state.aero_state.angle_of_attack = soa.aero_angle_of_attack_deg[i];
            state.aero_state.sideslip_angle = soa.aero_sideslip_angle_deg[i];
            state.aero_state.lift_coefficient = soa.aero_lift_coefficient[i];
            state.aero_state.drag_coefficient = soa.aero_drag_coefficient[i];
        } else if (soa.has_aero_state[i] != 0u) {
            state.has_aero_state = true;
            state.aero_state.dynamic_pressure = soa.aero_dynamic_pressure_pa[i];
            state.aero_state.mach_number = soa.aero_mach_number[i];
            state.aero_state.angle_of_attack = soa.aero_angle_of_attack_deg[i];
            state.aero_state.sideslip_angle = soa.aero_sideslip_angle_deg[i];
            state.aero_state.lift_coefficient = soa.aero_lift_coefficient[i];
            state.aero_state.drag_coefficient = soa.aero_drag_coefficient[i];
        }

        if (state.has_control_law_state || soa.has_control_law_state[i] != 0u) {
            state.has_control_law_state = true;
            state.control_law_state.stick_roll_filt = soa.control_stick_roll_filt[i];
            state.control_law_state.stick_pitch_filt = soa.control_stick_pitch_filt[i];
            state.control_law_state.stick_yaw_filt = soa.control_stick_yaw_filt[i];
            state.control_law_state.stick_yaw_cmd = soa.control_stick_yaw_cmd[i];
        }

        if (state.has_instrument_state || soa.has_instrument_state[i] != 0u) {
            state.has_instrument_state = true;
            auto& inst = state.instrument_state;
            const ApproximateAeroOutputs aero{
                soa.aero_dynamic_pressure_pa[i],
                soa.aero_mach_number[i],
                soa.aero_angle_of_attack_deg[i],
                soa.aero_sideslip_angle_deg[i],
            };
            const double speed_total = std::sqrt(
                soa.vx_mps[i] * soa.vx_mps[i] +
                soa.vy_mps[i] * soa.vy_mps[i] +
                soa.vz_mps[i] * soa.vz_mps[i]
            );
            inst.alt_baro_m = soa.z_m[i];
            inst.alt_radar_m = std::max(0.0, soa.z_m[i] - soa.terrain_elevation_m[i]);
            inst.ias_mps = std::sqrt(std::max(0.0, (2.0 * aero.dynamic_pressure) / 1.225));
            inst.mach = aero.mach_number;
            inst.vvi_mps = soa.vz_mps[i];
            inst.pitch_deg = soa.pitch_deg[i];
            inst.roll_deg = soa.roll_deg[i];
            inst.heading_deg = wrap_heading_deg(soa.heading_deg[i]);
            inst.aoa_deg = aero.angle_of_attack;
            inst.beta_deg = aero.sideslip_angle;
            inst.p_deg_s = soa.p_rad_s[i] * (180.0 / kPi);
            inst.q_deg_s = soa.q_rad_s[i] * (180.0 / kPi);
            inst.r_deg_s = soa.r_rad_s[i] * (180.0 / kPi);
            inst.g_load_normal = soa.g_load_normal[i];
            inst.g_load_axial = soa.g_load_axial[i];
            inst.fuel_internal_kg = std::max(0.0, soa.fuel_internal_kg[i]);
            inst.fuel_external_kg = std::max(0.0, soa.fuel_external_kg[i]);
            if (state.has_propulsion) {
                const double tsfc = state.propulsion.afterburner_active ? 0.25 : 0.1;
                inst.fuel_flow_kg_h = std::abs(state.propulsion.current_thrust_n) * tsfc;
                if (state.propulsion.afterburner_active) {
                    inst.engine_rpm_pct =
                        100.0 + (state.propulsion.current_thrust_n / (state.propulsion.ab_thrust_n + 1.0e-6)) * 10.0;
                } else {
                    inst.engine_rpm_pct =
                        (state.propulsion.current_thrust_n / (state.propulsion.mil_thrust_n + 1.0e-6)) * 100.0;
                }
                inst.engine_temp_c = 600.0 + inst.engine_rpm_pct * 3.0;
            } else {
                inst.fuel_flow_kg_h = 0.0;
            }
            if (state.has_pilot_action && state.pilot_action.active) {
                inst.throttle_pos = std::clamp(state.pilot_action.throttle, 0.0, 1.0);
                inst.flaps_pos = std::clamp(state.pilot_action.flaps, 0.0f, 1.0f);
                inst.speedbrake_pos = std::clamp(state.pilot_action.speedbrake, 0.0f, 1.0f);
                inst.master_arm = state.pilot_action.master_arm;
            } else if (state.has_movement_command && state.movement_command.active) {
                inst.throttle_pos = std::clamp(state.movement_command.throttle_cmd, 0.0, 1.0);
                inst.flaps_pos = 0.0f;
                inst.speedbrake_pos = 0.0f;
                inst.master_arm = false;
            } else {
                inst.throttle_pos = 0.0;
                inst.flaps_pos = 0.0f;
                inst.speedbrake_pos = 0.0f;
                inst.master_arm = false;
            }
            inst.gear_pos = state.has_landing_gear
                ? static_cast<float>(std::clamp(state.landing_gear.extension_state, 0.0, 1.0))
                : 0.0f;
            inst.oat_c = 15.0 - (soa.z_m[i] / 1000.0) * 6.5;
            if (state.has_mission_command && state.mission_command.active) {
                inst.cmd_heading_deg = mission_heading_bug(state.mission_command, inst.heading_deg);
                inst.cmd_alt_m = mission_altitude_bug(state.mission_command, inst.alt_baro_m);
                inst.cmd_speed_mps = mission_speed_bug(state.mission_command, inst.ias_mps);
            } else {
                inst.cmd_heading_deg = inst.heading_deg;
                inst.cmd_alt_m = inst.alt_baro_m;
                inst.cmd_speed_mps = inst.ias_mps;
            }
            inst.vn_mps = soa.vy_mps[i];
            inst.ve_mps = soa.vx_mps[i];
            inst.vd_mps = -soa.vz_mps[i];
            inst.lat_deg = kRefLat + (soa.y_m[i] / kMetersPerDegLat);
            inst.lon_deg = kRefLon + (soa.x_m[i] / kMetersPerDegLon);
            inst.ground_speed_mps = std::hypot(soa.vx_mps[i] + soa.wind_vx_mps[i], soa.vy_mps[i] + soa.wind_vy_mps[i]);
            inst.ground_track_deg = nav_heading_deg_from_velocity(
                soa.vx_mps[i] + soa.wind_vx_mps[i],
                soa.vy_mps[i] + soa.wind_vy_mps[i],
                inst.heading_deg
            );
            inst.wind_speed_mps = std::hypot(soa.wind_vx_mps[i], soa.wind_vy_mps[i]);
            inst.wind_dir_deg = nav_heading_deg_from_velocity(-soa.wind_vx_mps[i], -soa.wind_vy_mps[i], inst.wind_dir_deg);
            inst.gps_available = state.has_egi ? state.egi.gps_available : false;
            inst.position_uncertainty_m = std::max(0.0, inst.position_uncertainty_m);
            inst.gear_collapsed = inst.gear_collapsed && on_ground;
            inst.on_runway = on_ground;
            (void)speed_total;
        }

        if (state.has_egi || soa.has_egi[i] != 0u) {
            state.has_egi = true;
            auto& egi = state.egi;
            egi.drift_lat_m = 0.0;
            egi.drift_lon_m = 0.0;
            egi.drift_alt_m = 0.0;
            if (egi.gps_available) {
                egi.time_since_last_gps_fix = 0.0;
                egi.position_uncertainty_m = std::min(egi.position_uncertainty_m, 5.0);
            } else {
                egi.time_since_last_gps_fix += soa.time_step_s[i];
                egi.position_uncertainty_m = std::max(egi.position_uncertainty_m, 50.0);
            }
            egi.lat_deg = kRefLat + (soa.y_m[i] / kMetersPerDegLat);
            egi.lon_deg = kRefLon + (soa.x_m[i] / kMetersPerDegLon);
            egi.alt_baro_m = soa.z_m[i];
            egi.alt_radar_m = std::max(0.0, soa.z_m[i]);
            egi.vn_mps = soa.vy_mps[i];
            egi.ve_mps = soa.vx_mps[i];
            egi.vd_mps = -soa.vz_mps[i];
            egi.heading_deg = wrap_heading_deg(soa.heading_deg[i]);
            egi.pitch_deg = soa.pitch_deg[i];
            egi.roll_deg = soa.roll_deg[i];
            egi.wind_speed_mps = std::hypot(soa.wind_vx_mps[i], soa.wind_vy_mps[i]);
            egi.wind_dir_deg = nav_heading_deg_from_velocity(-soa.wind_vx_mps[i], -soa.wind_vy_mps[i], egi.wind_dir_deg);
        }
    }
    return out;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_states_v1_prototype_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    int steps
) {
    const auto t0 = std::chrono::steady_clock::now();
    ExactWorldStepPrototypeSoA soa = pack_exact_world_step_states_v1_prototype_soa(initial_states);
    for (int step_index = 0; step_index < std::max(0, steps); ++step_index) {
        for (std::size_t i = 0; i < soa.size; ++i) {
            prototype_step_once(soa, i);
        }
    }
    auto out = unpack_exact_world_step_states_v1_prototype_soa(soa, initial_states);
    const auto t1 = std::chrono::steady_clock::now();
    g_last_stats = ExactWorldStepPrototypeStats{};
    g_last_stats.total_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return out;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_states_v1_prototype_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    int steps
) {
    ExactWorldStepPrototypeSoA soa = pack_exact_world_step_states_v1_prototype_soa(initial_states);
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    ExactWorldStepPrototypeStats stats{};
    if (detail::step_exact_world_step_states_v1_prototype_cuda_inplace(soa, std::max(0, steps), &stats)) {
        g_last_stats = stats;
        return unpack_exact_world_step_states_v1_prototype_soa(soa, initial_states);
    }
#endif
    return step_exact_world_step_states_v1_prototype_reference_cpu_batch(initial_states, steps);
}

}  // namespace gpu
