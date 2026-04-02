#include "gpu/gpu_exact_world_step_force_ground_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <stdexcept>

namespace gpu {

namespace {

ExactWorldStepForceGroundStats g_last_stats{};

constexpr double kPi = 3.14159265358979323846;
constexpr double kGravity = 9.80665;
constexpr double kSeaLevelDensity = 1.225;
constexpr double kForceScalarCanonicalQuantum = 0x1p-32;
constexpr double kDirectionScalarCanonicalQuantum = 1.0e-14;
constexpr double kProjectedForceScalarCanonicalQuantum = 0x1p-32;

constexpr double kGroundSpring = 2000000.0;
constexpr double kGroundDamper = 350000.0;
constexpr double kMuBraking = 0.8;
constexpr double kNwsMinSpeedMps = 2.0;
constexpr double kNwsFadeStartMps = 30.0;
constexpr double kNwsFadeEndMps = 55.0;
constexpr double kNwsDeadzone = 0.02;
constexpr double kNwsMaxSteerDeg = 25.0;
constexpr double kNwsHighSpeedFrac = 0.15;
constexpr double kNwsInputScaler = 1.0;
constexpr double kWheelContactNoseX = 4.0;
constexpr double kWheelContactMainX = -2.0;
constexpr double kWheelFnNoseFrac = 0.20;
constexpr double kWheelFnMainFrac = 0.80;
constexpr double kTireCorneringStiffnessPerFn = 18.0;
constexpr double kTireAlphaMaxDeg = 20.0;
constexpr double kTireVrefRollMps = 1.0;
constexpr double kTireVrefBrakeMps = 0.5;

double to_degrees(double radians) {
    return radians * 180.0 / kPi;
}

double to_radians(double degrees) {
    return degrees * kPi / 180.0;
}

double frame_delta_s(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

double canonicalize_force_scalar(double value) {
    if (!std::isfinite(value) || kForceScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (std::abs(value) <= (kForceScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / kForceScalarCanonicalQuantum) *
        kForceScalarCanonicalQuantum;
    return std::abs(rounded) <= (kForceScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

double canonicalize_direction_scalar(double value) {
    if (!std::isfinite(value) || kDirectionScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (std::abs(value) <= (kDirectionScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / kDirectionScalarCanonicalQuantum) *
        kDirectionScalarCanonicalQuantum;
    return std::abs(rounded) <= (kDirectionScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

double canonicalize_projected_force_scalar(double value) {
    if (!std::isfinite(value) || kProjectedForceScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (std::abs(value) <= (kProjectedForceScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / kProjectedForceScalarCanonicalQuantum) *
        kProjectedForceScalarCanonicalQuantum;
    return std::abs(rounded) <= (kProjectedForceScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

struct LocalVec3 {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

LocalVec3 vec_cross(const LocalVec3& a, const LocalVec3& b) {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    };
}

double vec_length(const LocalVec3& v) {
    return std::sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
}

LocalVec3 vec_norm(const LocalVec3& v) {
    const double len = vec_length(v);
    if (len <= 1.0e-9) {
        return {};
    }
    return {v.x / len, v.y / len, v.z / len};
}

double smoothstep01(double x) {
    x = std::clamp(x, 0.0, 1.0);
    return x * x * (3.0 - 2.0 * x);
}

LocalVec3 get_body_right(double heading_deg, double pitch_deg, double roll_deg) {
    const double psi = to_radians(90.0 - heading_deg);
    const double theta = to_radians(pitch_deg);
    const double phi = to_radians(roll_deg);

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

void compute_standard_atmosphere(double altitude_m, double* out_rho, double* out_speed_of_sound) {
    constexpr double kG = 9.80665;
    constexpr double kR = 287.0;
    constexpr double kL = 0.0065;
    constexpr double kT0 = 288.15;
    constexpr double kP0 = 101325.0;
    const double h = std::max(0.0, altitude_m);
    double temperature = 0.0;
    double pressure = 0.0;
    if (h < 11000.0) {
        temperature = kT0 - kL * h;
        pressure = kP0 * std::pow(1.0 - kL * h / kT0, kG / (kR * kL));
    } else {
        constexpr double kT11 = 216.65;
        constexpr double kP11 = 22632.1;
        temperature = kT11;
        pressure = kP11 * std::exp(-kG * (h - 11000.0) / (kR * kT11));
    }
    *out_rho = pressure / (kR * temperature);
    *out_speed_of_sound = std::sqrt(1.4 * kR * temperature);
}

bool has_query_inputs_for_compute_forces(const ExactWorldStepForceGroundSoA& soa, std::size_t i) {
    return soa.has_force_accumulator[i] != 0
        && soa.has_mass[i] != 0
        && soa.has_propulsion[i] != 0
        && soa.has_flight_model[i] != 0
        && soa.has_movement_command[i] != 0;
}

bool has_query_inputs_for_compute_aerodynamics(const ExactWorldStepForceGroundSoA& soa, std::size_t i) {
    return soa.has_force_accumulator[i] != 0
        && soa.has_aero_state[i] != 0
        && soa.has_mass_properties[i] != 0;
}

bool has_query_inputs_for_ground_contact(const ExactWorldStepForceGroundSoA& soa, std::size_t i) {
    return soa.has_force_accumulator[i] != 0
        && soa.has_mass[i] != 0
        && soa.has_ground_state[i] != 0;
}

void run_compute_forces_stage(ExactWorldStepForceGroundSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_compute_forces(soa, i)) {
        return;
    }

    const PilotAction* pilot = soa.has_pilot_action[i] != 0 ? &soa.pilot_action[i] : nullptr;
    const bool has_pilot = pilot != nullptr && pilot->active;
    const bool has_legacy = soa.movement_command[i].active;
    if (!has_pilot && !has_legacy) {
        return;
    }

    double m = soa.mass[i].get_total_kg();
    if (m < 1.0) {
        m = 15000.0;
    }

    const double vx = soa.velocity[i].vx;
    const double vy = soa.velocity[i].vy;
    const double vz = soa.velocity[i].vz;
    const double speed_sq = vx * vx + vy * vy + vz * vz;
    const double speed = std::sqrt(speed_sq);

    soa.force_accumulator[i].add_force(0.0, 0.0, -m * kGravity);

    const double yaw_rad = to_radians(90.0 - soa.transform[i].heading);
    const double pitch_rad = to_radians(soa.transform[i].pitch);
    const double nose_x = canonicalize_direction_scalar(std::cos(yaw_rad) * std::cos(pitch_rad));
    const double nose_y = canonicalize_direction_scalar(std::sin(yaw_rad) * std::cos(pitch_rad));
    const double nose_z = canonicalize_direction_scalar(std::sin(pitch_rad));

    double throttle_input = 0.0;
    if (has_pilot) {
        throttle_input = pilot->throttle;
    } else if (soa.movement_command[i].active) {
        throttle_input = soa.movement_command[i].throttle_cmd;
    }
    throttle_input = std::clamp(throttle_input, 0.0, 1.0);

    double thrust_magnitude = 0.0;
    bool afterburner_active = false;
    if (throttle_input > 0.9) {
        thrust_magnitude = soa.propulsion[i].ab_thrust_n;
        afterburner_active = true;
    } else {
        thrust_magnitude = soa.propulsion[i].mil_thrust_n * throttle_input;
    }

    double rho = kSeaLevelDensity;
    double speed_of_sound = 340.29;
    if (soa.has_environment_sample[i] != 0) {
        compute_standard_atmosphere(soa.transform[i].z, &rho, &speed_of_sound);
    }
    double sigma = rho / kSeaLevelDensity;
    sigma = std::max(0.01, sigma);
    double mach = 0.0;
    if (speed_of_sound > 1.0) {
        mach = speed / speed_of_sound;
    }
    const double ram_factor = 1.0 + 0.3 * mach;
    thrust_magnitude *= sigma * ram_factor;
    thrust_magnitude = canonicalize_force_scalar(thrust_magnitude);

    soa.propulsion[i].current_thrust_n = thrust_magnitude;
    soa.propulsion[i].afterburner_active = afterburner_active;

    const double thrust_fx = canonicalize_projected_force_scalar(thrust_magnitude * nose_x);
    const double thrust_fy = canonicalize_projected_force_scalar(thrust_magnitude * nose_y);
    const double thrust_fz = canonicalize_projected_force_scalar(thrust_magnitude * nose_z);
    soa.force_accumulator[i].add_force(
        thrust_fx,
        thrust_fy,
        thrust_fz
    );
}

void run_compute_aerodynamics_stage(ExactWorldStepForceGroundSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_compute_aerodynamics(soa, i)) {
        return;
    }

    auto& forces = soa.force_accumulator[i];
    auto& aero = soa.aero_state[i];
    const auto& props = soa.mass_properties[i];
    const auto& velocity = soa.velocity[i];
    const auto& transform = soa.transform[i];

    const double q = aero.dynamic_pressure;
    if (q < 0.1) {
        return;
    }

    const double alpha = aero.angle_of_attack;
    double S = props.reference_area_m2;
    if (S < 1.0) {
        S = 30.0;
    }

    constexpr double kClAlphaPerDeg = 0.1;
    constexpr double kCl0 = 0.0;
    double Cl = kCl0 + kClAlphaPerDeg * alpha;

    const PilotAction* pilot = soa.has_pilot_action[i] != 0 ? &soa.pilot_action[i] : nullptr;
    double flaps_deflection = 0.0;
    double speedbrake_pos = 0.0;
    if (pilot != nullptr && pilot->active) {
        flaps_deflection = std::clamp(static_cast<double>(pilot->flaps), 0.0, 1.0);
        speedbrake_pos = std::clamp(static_cast<double>(pilot->speedbrake), 0.0, 1.0);
    }
    Cl += flaps_deflection * 0.35;

    const double alpha_abs = std::abs(alpha);
    const double alpha_sign = alpha >= 0.0 ? 1.0 : -1.0;
    const double alpha_stall_deg = 15.0 + 6.0 * flaps_deflection;
    const double alpha_peak_deg = alpha_stall_deg + 8.0;
    const double alpha_deep_deg = alpha_peak_deg + 18.0;
    const double cl_peak_mag = 1.25 + 0.45 * flaps_deflection;
    const double cl_deep_mag = 0.22 + 0.10 * flaps_deflection;

    if (alpha_abs > alpha_stall_deg) {
        if (alpha_abs <= alpha_peak_deg) {
            const double t = smoothstep01(
                (alpha_abs - alpha_stall_deg) / std::max(1.0e-6, alpha_peak_deg - alpha_stall_deg)
            );
            const double cl_target = alpha_sign * cl_peak_mag;
            Cl = (1.0 - t) * Cl + t * cl_target;
        } else if (alpha_abs <= alpha_deep_deg) {
            const double t = smoothstep01(
                (alpha_abs - alpha_peak_deg) / std::max(1.0e-6, alpha_deep_deg - alpha_peak_deg)
            );
            const double cl_target = alpha_sign * cl_deep_mag;
            const double cl_peak = alpha_sign * cl_peak_mag;
            Cl = (1.0 - t) * cl_peak + t * cl_target;
        } else {
            Cl = alpha_sign * cl_deep_mag;
        }
    }

    double Cd0 = 0.02;
    Cd0 += props.current_drag_index * 0.001;
    if (soa.has_landing_gear[i] != 0) {
        Cd0 += soa.landing_gear[i].extension_state * 0.04;
    }
    Cd0 += speedbrake_pos * 0.08;
    Cd0 += flaps_deflection * 0.02;
    const double k = 0.1;

    double ge = 0.0;
    if (soa.has_environment_sample[i] != 0) {
        const double alt_agl = std::max(0.0, transform.z - soa.environment_sample[i].terrain_elevation_m);
        const double b_ref = std::max(1.0, props.wing_span_m);
        const double ge_fade_h = 0.5 * b_ref;
        if (ge_fade_h > 1.0e-6 && alt_agl < ge_fade_h) {
            ge = 1.0 - (alt_agl / ge_fade_h);
            ge = std::clamp(ge, 0.0, 1.0);
        }
    }
    Cl *= (1.0 + 0.08 * ge);
    const double k_eff = k * (1.0 - 0.70 * ge);

    double stall_drag = 0.0;
    if (alpha_abs > alpha_stall_deg) {
        const double s1 = smoothstep01(
            (alpha_abs - alpha_stall_deg) / std::max(1.0e-6, alpha_peak_deg - alpha_stall_deg)
        );
        const double s2 = smoothstep01(
            (alpha_abs - alpha_peak_deg) / std::max(1.0e-6, alpha_deep_deg - alpha_peak_deg)
        );
        stall_drag = 0.25 * s1 + 0.55 * s2;
    }

    const double Cd = Cd0 + k_eff * Cl * Cl + stall_drag;
    aero.lift_coefficient = Cl;
    aero.drag_coefficient = Cd;

    const double lift_mag = q * S * Cl;
    const double drag_mag = q * S * Cd;

    LocalVec3 v_vec{velocity.vx, velocity.vy, velocity.vz};
    if (soa.has_environment_sample[i] != 0) {
        v_vec.x -= soa.environment_sample[i].wind_vx_mps;
        v_vec.y -= soa.environment_sample[i].wind_vy_mps;
    }
    const LocalVec3 v_hat = vec_norm(v_vec);
    const LocalVec3 drag_dir{-v_hat.x, -v_hat.y, -v_hat.z};
    const LocalVec3 body_right = get_body_right(transform.heading, transform.pitch, transform.roll);
    const LocalVec3 lift_dir = vec_norm(vec_cross(v_vec, body_right));

    forces.add_force(
        drag_mag * drag_dir.x + lift_mag * lift_dir.x,
        drag_mag * drag_dir.y + lift_mag * lift_dir.y,
        drag_mag * drag_dir.z + lift_mag * lift_dir.z
    );

    double b = props.wing_span_m;
    if (b < 1.0) {
        b = 10.0;
    }
    double c_bar = props.chord_m;
    if (c_bar < 0.1) {
        c_bar = 3.0;
    }

    const double V = std::max(
        10.0,
        std::sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy + velocity.vz * velocity.vz)
    );

    double p = 0.0;
    double q_rate = 0.0;
    double r = 0.0;
    if (soa.has_angular_velocity[i] != 0) {
        p = soa.angular_velocity[i].p;
        q_rate = soa.angular_velocity[i].q;
        r = soa.angular_velocity[i].r;
    }

    const double p_hat = p * b / (2.0 * V);
    const double q_hat = q_rate * c_bar / (2.0 * V);
    const double r_hat = r * b / (2.0 * V);

    const double stall_rel = smoothstep01(
        (alpha_abs - alpha_stall_deg) / std::max(1.0e-6, alpha_deep_deg - alpha_stall_deg)
    );
    const double damp_scale = std::clamp(1.0 - 0.7 * stall_rel, 0.25, 1.0);

    const double Cm_alpha = -0.8;
    const double Cm_q = -12.0 * damp_scale;
    const double Cm = Cm_alpha * to_radians(alpha) + Cm_q * q_hat;

    const double beta = aero.sideslip_angle;
    const double Cl_beta = -0.1;
    const double Cl_p = -0.45 * damp_scale;
    const double Cl_r = 0.1;
    const double Cl_mom = Cl_beta * to_radians(beta) + Cl_p * p_hat + Cl_r * r_hat;

    const double Cn_beta = 0.15;
    const double Cn_r = -0.25 * damp_scale;
    const double Cn_mom = Cn_beta * to_radians(beta) + Cn_r * r_hat;

    const double pitch_torque = q * S * c_bar * Cm;
    const double roll_torque = q * S * b * Cl_mom;
    const double yaw_torque = q * S * b * Cn_mom;
    forces.add_torque(roll_torque, pitch_torque, yaw_torque);
}

void run_ground_contact_stage(ExactWorldStepForceGroundSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_ground_contact(soa, i)) {
        return;
    }

    auto& forces = soa.force_accumulator[i];
    const auto& transform = soa.transform[i];
    auto& velocity = soa.velocity[i];
    const auto& mass = soa.mass[i];
    auto& ground = soa.ground_state[i];

    double m = mass.get_total_kg();
    if (m < 1.0) {
        m = 15000.0;
    }
    const double dt = std::max(1.0e-3, frame_delta_s(soa.time_step_s[i]));

    const double terrain_z = soa.has_environment_sample[i] != 0
        ? soa.environment_sample[i].terrain_elevation_m
        : ground.terrain_elevation;
    ground.terrain_elevation = terrain_z;

    double gear_height = 2.0;
    if (soa.has_landing_gear[i] != 0) {
        const double ext = std::clamp(soa.landing_gear[i].extension_state, 0.0, 1.0);
        gear_height = std::max(0.4, soa.landing_gear[i].contact_height_m) * ext;
    }

    const double penetration = gear_height - (transform.z - terrain_z);
    const bool is_touching = penetration > 0.0;
    ground.on_ground = is_touching;
    if (!is_touching) {
        return;
    }

    const double Fn = std::max(0.0, kGroundSpring * penetration - kGroundDamper * velocity.vz);
    forces.add_force(0.0, 0.0, Fn);

    if (soa.has_angular_velocity[i] != 0) {
        const double q_rate = soa.angular_velocity[i].q;
        const double pitch_deg = transform.pitch;
        const double p_rate = soa.angular_velocity[i].p;
        const double roll_deg = transform.roll;
        const double kp_pitch = 2000000.0;
        const double kd_pitch = 200000.0;
        constexpr double kGroundPitchFreeDeg = 10.0;

        if (pitch_deg > kGroundPitchFreeDeg) {
            const double err_deg = pitch_deg - kGroundPitchFreeDeg;
            const double restoring_torque = -kp_pitch * to_radians(err_deg);
            const double damping_torque = -kd_pitch * q_rate;
            forces.add_torque(0.0, restoring_torque + damping_torque, 0.0);
        } else if (std::abs(q_rate) > 0.01) {
            forces.add_torque(0.0, -kd_pitch * q_rate, 0.0);
        }

        const double kp_roll = 2000000.0;
        const double kd_roll = 200000.0;
        const double abs_roll = std::abs(roll_deg);
        if (abs_roll > 2.0) {
            const double restoring = -kp_roll * to_radians(roll_deg);
            const double damping = -kd_roll * p_rate;
            forces.add_torque(restoring + damping, 0.0, 0.0);
        } else if (std::abs(p_rate) > 0.01) {
            forces.add_torque(-kd_roll * p_rate, 0.0, 0.0);
        }
    }

    const double vx = velocity.vx;
    const double vy = velocity.vy;
    const double v_h_sq = vx * vx + vy * vy;
    const PilotAction* pilot = soa.has_pilot_action[i] != 0 ? &soa.pilot_action[i] : nullptr;
    const MovementCommand* cmd = soa.has_movement_command[i] != 0 ? &soa.movement_command[i] : nullptr;
    bool throttle_idle = false;
    double brake_amount = 0.0;
    if (pilot != nullptr && pilot->active) {
        throttle_idle = pilot->throttle < 0.01;
        brake_amount = std::clamp(pilot->brake, 0.0, 1.0);
        if (pilot->brake_left || pilot->brake_right) {
            brake_amount = std::max(brake_amount, 1.0);
        }
    } else if (cmd != nullptr && cmd->active) {
        throttle_idle = cmd->throttle_cmd < 0.01;
        if (throttle_idle) {
            brake_amount = 1.0;
        }
    }

    if (v_h_sq <= 0.001) {
        if (throttle_idle && std::abs(vx) < 0.25 && std::abs(vy) < 0.25) {
            velocity.vx = 0.0;
            velocity.vy = 0.0;
        }
        return;
    }

    const double v_h = std::sqrt(v_h_sq);
    const std::uint8_t surface_code = soa.has_environment_sample[i] != 0
        ? soa.environment_sample[i].terrain_surface_code
        : 3u;

    double gear_mu_roll = 0.02;
    if (soa.has_landing_gear[i] != 0) {
        gear_mu_roll = std::max(0.0, soa.landing_gear[i].rolling_friction_coeff);
    }
    double mu_rolling = gear_mu_roll;
    bool is_offroad = false;
    switch (surface_code) {
        case 0u: mu_rolling = std::max(0.01, gear_mu_roll); break;
        case 1u: mu_rolling = std::max(0.0125, gear_mu_roll * 1.25); break;
        case 2u: mu_rolling = std::max(0.05, gear_mu_roll * 2.5); is_offroad = true; break;
        case 3u: mu_rolling = std::max(0.15, gear_mu_roll * 7.5); is_offroad = true; break;
        case 4u: mu_rolling = std::max(0.80, gear_mu_roll * 20.0); is_offroad = true; break;
        case 5u: mu_rolling = std::max(1.0, gear_mu_roll * 25.0); is_offroad = true; break;
        default: mu_rolling = std::max(0.10, gear_mu_roll * 5.0); is_offroad = true; break;
    }

    if (soa.has_gear_state[i] != 0) {
        auto& gear = soa.gear_state[i];
        gear.on_runway = !is_offroad;
        gear.stress_rate = 0.0;
        if (gear.gear_down && !gear.collapsed && is_offroad && v_h > 40.0) {
            double severity = 1.0;
            if (surface_code == 2u) {
                severity = 0.3;
            } else if (surface_code == 3u) {
                severity = 1.0;
            } else if (surface_code == 4u) {
                severity = 2.0;
            } else if (surface_code == 5u) {
                severity = 5.0;
            }
            gear.stress_rate = severity * (v_h - 40.0) / 60.0;
            gear.stress += gear.stress_rate * dt;
            mu_rolling *= (1.0 + 4.0 * gear.stress);
            if (gear.stress >= 1.0) {
                gear.collapsed = true;
                if (soa.has_health[i] != 0) {
                    soa.health[i].current_hp = 0.0;
                }
            }
        }
    } else if (is_offroad && v_h > 40.0) {
        mu_rolling *= 5.0;
    }

    double nws_steer_rad = 0.0;
    if (pilot != nullptr && pilot->active) {
        double yaw_cmd = pilot->rudder;
        if (soa.has_control_law_state[i] != 0) {
            yaw_cmd = -soa.control_law_state[i].stick_yaw_filt;
        }
        double steer = std::clamp(yaw_cmd, -1.0, 1.0) * kNwsInputScaler;
        if (std::abs(steer) < kNwsDeadzone) {
            steer = 0.0;
        }
        if (std::abs(steer) > 1.0e-6) {
            bool gear_extended = true;
            if (soa.has_landing_gear[i] != 0) {
                gear_extended = soa.landing_gear[i].extension_state >= 0.5;
            }
            if (gear_extended) {
                const double speed_factor = std::clamp(v_h / kNwsMinSpeedMps, 0.0, 1.0);
                double fade = 1.0;
                if (v_h >= kNwsFadeStartMps) {
                    double t = (v_h - kNwsFadeStartMps) / (kNwsFadeEndMps - kNwsFadeStartMps);
                    t = std::clamp(t, 0.0, 1.0);
                    fade = (1.0 - t) * (1.0 - kNwsHighSpeedFrac) + kNwsHighSpeedFrac;
                }
                const double gain = speed_factor * fade;
                if (gain > 0.0) {
                    nws_steer_rad = -steer * to_radians(kNwsMaxSteerDeg) * gain;
                }
            }
        }
    }

    if (throttle_idle && v_h < 10.0) {
        brake_amount = std::max(brake_amount, 1.0);
    }

    double mu_roll = mu_rolling;
    const double mu_brake = std::clamp(brake_amount, 0.0, 1.0) * kMuBraking;

    double mu_lat = mu_rolling;
    switch (surface_code) {
        case 0u: mu_lat = 0.80; break;
        case 1u: mu_lat = 0.75; break;
        case 2u: mu_lat = 0.60; break;
        case 3u: mu_lat = 0.50; break;
        case 4u: mu_lat = 0.20; break;
        case 5u: mu_lat = 1.00; break;
        default: mu_lat = 0.40; break;
    }
    mu_lat = std::max(mu_lat, mu_roll);

    const double hdg_rad = to_radians(transform.heading);
    const double fwd_x = std::sin(hdg_rad);
    const double fwd_y = std::cos(hdg_rad);
    const double left_x = -std::cos(hdg_rad);
    const double left_y = std::sin(hdg_rad);
    const double v_long = vx * fwd_x + vy * fwd_y;
    const double v_lat_comp = vx * left_x + vy * left_y;

    auto smooth_coulomb = [](double v, double mu_in, double Fn_in, double v_ref) {
        if (Fn_in <= 0.0 || mu_in <= 0.0) {
            return 0.0;
        }
        v_ref = std::max(v_ref, 1.0e-3);
        const double s = std::tanh(v / v_ref);
        return -mu_in * Fn_in * s;
    };

    const double alpha_max = to_radians(kTireAlphaMaxDeg);
    const double Fn_nose = Fn * kWheelFnNoseFrac;
    const double Fn_main = Fn * kWheelFnMainFrac;

    double r = 0.0;
    if (soa.has_angular_velocity[i] != 0) {
        r = soa.angular_velocity[i].r;
    }

    auto apply_wheel = [&](double x_body_m, double Fn_w, double steer_rad, double mu_brake_w, double& f_long_sum, double& f_lat_sum, double& tau_yaw_sum) {
        if (Fn_w <= 0.0) {
            return;
        }

        const double v_long_w = v_long;
        const double v_lat_w = v_lat_comp + r * x_body_m;
        const double c = std::cos(steer_rad);
        const double s = std::sin(steer_rad);
        const double v_long_wf = v_long_w * c + v_lat_w * s;
        const double v_lat_wf = -v_long_w * s + v_lat_w * c;

        const double fx_roll = smooth_coulomb(v_long_wf, mu_roll, Fn_w, kTireVrefRollMps);
        double fx_brake = 0.0;
        if (mu_brake_w > 1.0e-6) {
            fx_brake = smooth_coulomb(v_long_wf, mu_brake_w, Fn_w, kTireVrefBrakeMps);
        }

        double alpha = std::atan2(v_lat_wf, std::abs(v_long_wf) + 1.0e-3);
        alpha = std::clamp(alpha, -alpha_max, alpha_max);
        const double C_alpha = kTireCorneringStiffnessPerFn * Fn_w;
        double fy = -C_alpha * alpha;
        const double fy_max = mu_lat * Fn_w;
        if (fy_max > 0.0) {
            fy = std::clamp(fy, -fy_max, fy_max);
        } else {
            fy = 0.0;
        }

        if (mu_brake_w > 1.0e-6 && fy_max > 1.0e-6) {
            const double fx_max = mu_brake_w * Fn_w;
            const double ux = fx_brake / std::max(fx_max, 1.0e-6);
            const double uy = fy / std::max(fy_max, 1.0e-6);
            const double u = std::sqrt(ux * ux + uy * uy);
            if (u > 1.0) {
                fx_brake /= u;
                fy /= u;
            }
        }

        const double fx_wf = fx_roll + fx_brake;
        const double fy_wf = fy;
        const double fx_b = fx_wf * c - fy_wf * s;
        const double fy_b = fx_wf * s + fy_wf * c;

        f_long_sum += fx_b;
        f_lat_sum += fy_b;
        tau_yaw_sum += x_body_m * fy_b;
    };

    double f_long_sum = 0.0;
    double f_lat_sum = 0.0;
    double tau_yaw = 0.0;
    apply_wheel(kWheelContactNoseX, Fn_nose, nws_steer_rad, 0.0, f_long_sum, f_lat_sum, tau_yaw);
    apply_wheel(kWheelContactMainX, Fn_main, 0.0, mu_brake, f_long_sum, f_lat_sum, tau_yaw);

    const double fx = f_long_sum * fwd_x + f_lat_sum * left_x;
    const double fy = f_long_sum * fwd_y + f_lat_sum * left_y;
    forces.add_force(fx, fy, 0.0);
    forces.add_torque(0.0, 0.0, tau_yaw);

    if (throttle_idle && brake_amount > 0.2 && v_h < 3.0) {
        const double hold_force_max = std::max(0.0, 1.20 * Fn);
        const double hold_force_need = (m * v_h) / dt;
        const double hold_force = std::min(hold_force_need, hold_force_max);
        if (hold_force > 0.0 && v_h > 1.0e-6) {
            const double inv_v = 1.0 / v_h;
            forces.add_force(-vx * inv_v * hold_force, -vy * inv_v * hold_force, 0.0);
        }
        if (v_h < 0.25) {
            velocity.vx = 0.0;
            velocity.vy = 0.0;
        }
    }
}

}  // namespace

ExactWorldStepForceGroundSoA pack_exact_world_step_states_v1_force_ground_soa(
    const std::vector<ExactWorldStepStateV1>& states
) {
    ExactWorldStepForceGroundSoA soa{};
    soa.size = states.size();

    soa.time_step_s.resize(soa.size);
    soa.transform.resize(soa.size);
    soa.velocity.resize(soa.size);
    soa.angular_velocity.resize(soa.size);
    soa.force_accumulator.resize(soa.size);
    soa.aero_state.resize(soa.size);
    soa.control_law_state.resize(soa.size);
    soa.pilot_action.resize(soa.size);
    soa.movement_command.resize(soa.size);
    soa.mass.resize(soa.size);
    soa.propulsion.resize(soa.size);
    soa.flight_model.resize(soa.size);
    soa.mass_properties.resize(soa.size);
    soa.landing_gear.resize(soa.size);
    soa.gear_state.resize(soa.size);
    soa.ground_state.resize(soa.size);
    soa.health.resize(soa.size);
    soa.environment_sample.resize(soa.size);

    soa.has_angular_velocity.resize(soa.size);
    soa.has_force_accumulator.resize(soa.size);
    soa.has_aero_state.resize(soa.size);
    soa.has_control_law_state.resize(soa.size);
    soa.has_pilot_action.resize(soa.size);
    soa.has_movement_command.resize(soa.size);
    soa.has_mass.resize(soa.size);
    soa.has_propulsion.resize(soa.size);
    soa.has_flight_model.resize(soa.size);
    soa.has_mass_properties.resize(soa.size);
    soa.has_landing_gear.resize(soa.size);
    soa.has_gear_state.resize(soa.size);
    soa.has_ground_state.resize(soa.size);
    soa.has_health.resize(soa.size);
    soa.has_environment_sample.resize(soa.size);

    for (std::size_t i = 0; i < soa.size; ++i) {
        const auto& state = states[i];
        soa.time_step_s[i] = state.time_step_s;
        soa.transform[i] = state.transform;
        soa.velocity[i] = state.velocity;
        soa.angular_velocity[i] = state.angular_velocity;
        soa.force_accumulator[i] = state.force_accumulator;
        soa.aero_state[i] = state.aero_state;
        soa.control_law_state[i] = state.control_law_state;
        soa.pilot_action[i] = state.pilot_action;
        soa.movement_command[i] = state.movement_command;
        soa.mass[i] = state.mass;
        soa.propulsion[i] = state.propulsion;
        soa.flight_model[i] = state.flight_model;
        soa.mass_properties[i] = state.mass_properties;
        soa.landing_gear[i] = state.landing_gear;
        soa.gear_state[i] = state.gear_state;
        soa.ground_state[i] = state.ground_state;
        soa.health[i] = state.health;
        soa.environment_sample[i] = state.environment_sample;

        soa.has_angular_velocity[i] = state.has_angular_velocity ? 1u : 0u;
        soa.has_force_accumulator[i] = state.has_force_accumulator ? 1u : 0u;
        soa.has_aero_state[i] = state.has_aero_state ? 1u : 0u;
        soa.has_control_law_state[i] = state.has_control_law_state ? 1u : 0u;
        soa.has_pilot_action[i] = state.has_pilot_action ? 1u : 0u;
        soa.has_movement_command[i] = state.has_movement_command ? 1u : 0u;
        soa.has_mass[i] = state.has_mass ? 1u : 0u;
        soa.has_propulsion[i] = state.has_propulsion ? 1u : 0u;
        soa.has_flight_model[i] = state.has_flight_model ? 1u : 0u;
        soa.has_mass_properties[i] = state.has_mass_properties ? 1u : 0u;
        soa.has_landing_gear[i] = state.has_landing_gear ? 1u : 0u;
        soa.has_gear_state[i] = state.has_gear_state ? 1u : 0u;
        soa.has_ground_state[i] = state.has_ground_state ? 1u : 0u;
        soa.has_health[i] = state.has_health ? 1u : 0u;
        soa.has_environment_sample[i] = state.has_environment_sample ? 1u : 0u;
    }

    return soa;
}

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_force_ground_soa(
    const ExactWorldStepForceGroundSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
    if (soa.size != basis_states.size()) {
        throw std::invalid_argument("force-ground SoA size must match basis state count");
    }

    std::vector<ExactWorldStepStateV1> out = basis_states;
    for (std::size_t i = 0; i < soa.size; ++i) {
        auto& state = out[i];
        state.time_step_s = soa.time_step_s[i];
        state.transform = soa.transform[i];
        state.velocity = soa.velocity[i];
        state.angular_velocity = soa.angular_velocity[i];
        state.force_accumulator = soa.force_accumulator[i];
        state.aero_state = soa.aero_state[i];
        state.control_law_state = soa.control_law_state[i];
        state.pilot_action = soa.pilot_action[i];
        state.movement_command = soa.movement_command[i];
        state.mass = soa.mass[i];
        state.propulsion = soa.propulsion[i];
        state.flight_model = soa.flight_model[i];
        state.mass_properties = soa.mass_properties[i];
        state.landing_gear = soa.landing_gear[i];
        state.gear_state = soa.gear_state[i];
        state.ground_state = soa.ground_state[i];
        state.health = soa.health[i];
        state.environment_sample = soa.environment_sample[i];

        state.has_angular_velocity = soa.has_angular_velocity[i] != 0;
        state.has_force_accumulator = soa.has_force_accumulator[i] != 0;
        state.has_aero_state = soa.has_aero_state[i] != 0;
        state.has_control_law_state = soa.has_control_law_state[i] != 0;
        state.has_pilot_action = soa.has_pilot_action[i] != 0;
        state.has_movement_command = soa.has_movement_command[i] != 0;
        state.has_mass = soa.has_mass[i] != 0;
        state.has_propulsion = soa.has_propulsion[i] != 0;
        state.has_flight_model = soa.has_flight_model[i] != 0;
        state.has_mass_properties = soa.has_mass_properties[i] != 0;
        state.has_landing_gear = soa.has_landing_gear[i] != 0;
        state.has_gear_state = soa.has_gear_state[i] != 0;
        state.has_ground_state = soa.has_ground_state[i] != 0;
        state.has_health = soa.has_health[i] != 0;
        state.has_environment_sample = soa.has_environment_sample[i] != 0;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_force_ground_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepForceGroundSoA soa = pack_exact_world_step_states_v1_force_ground_soa(initial_states);
    for (std::size_t i = 0; i < soa.size; ++i) {
        run_compute_forces_stage(soa, i);
        run_compute_aerodynamics_stage(soa, i);
        run_ground_contact_stage(soa, i);
    }
    auto out = unpack_exact_world_step_states_v1_force_ground_soa(soa, initial_states);
    const auto end = std::chrono::steady_clock::now();

    g_last_stats.state_count = initial_states.size();
    g_last_stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    return out;
}

const ExactWorldStepForceGroundStats& last_exact_world_step_force_ground_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
