#include "gpu/gpu_exact_world_step_control_aero_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <stdexcept>
#include <string>

namespace gpu {

namespace {

ExactWorldStepControlAeroStats g_last_stats{};

constexpr double kPi = 3.14159265358979323846;
constexpr double kAeroScalarCanonicalQuantum = 1.0e-10;
constexpr double kAeroAngleCanonicalQuantumDeg = 0x1p-40;

double to_degrees(double radians) {
    return radians * 180.0 / kPi;
}

double to_radians(double degrees) {
    return degrees * kPi / 180.0;
}

double normalize_angle(double angle_deg) {
    while (angle_deg > 180.0) {
        angle_deg -= 360.0;
    }
    while (angle_deg < -180.0) {
        angle_deg += 360.0;
    }
    return angle_deg;
}

double canonicalize_aero_scalar(double value, double quantum) {
    if (!std::isfinite(value) || quantum <= 0.0) {
        return value;
    }
    if (std::abs(value) <= (quantum * 0.5)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / quantum) * quantum;
    return std::abs(rounded) <= (quantum * 0.5) ? 0.0 : rounded;
}

double canonicalize_aero_angle_deg(double value) {
    return canonicalize_aero_scalar(value, kAeroAngleCanonicalQuantumDeg);
}

double ground_track_deg_from_velocity(const Velocity& velocity, double fallback_heading_deg) {
    const double horiz_speed = std::hypot(velocity.vx, velocity.vy);
    if (horiz_speed <= 1.0) {
        return fallback_heading_deg;
    }
    double track_deg = std::fmod(to_degrees(std::atan2(velocity.vx, velocity.vy)), 360.0);
    if (track_deg < 0.0) {
        track_deg += 360.0;
    }
    return track_deg;
}

enum class FbwProtectionMode {
    Strict,
    Relaxed,
    Off,
};

FbwProtectionMode get_fbw_protection_mode() {
    static const FbwProtectionMode cached = []() {
        const char* value = std::getenv("CMO_FBW_PROTECTION_MODE");
        if (value == nullptr) {
            return FbwProtectionMode::Strict;
        }
        const std::string mode(value);
        if (mode == "off" || mode == "OFF" || mode == "0") {
            return FbwProtectionMode::Off;
        }
        if (mode == "relaxed" || mode == "RELAXED" || mode == "1") {
            return FbwProtectionMode::Relaxed;
        }
        return FbwProtectionMode::Strict;
    }();
    return cached;
}

bool has_query_inputs_for_flight_control(const ExactWorldStepControlAeroSoA& soa, std::size_t i) {
    return soa.has_lagged_command[i] != 0 && soa.has_flight_model[i] != 0;
}

bool has_query_inputs_for_compute_aero_state(const ExactWorldStepControlAeroSoA& soa, std::size_t i) {
    return soa.has_aero_state[i] != 0;
}

double landing_bank_limit_deg(const MissionCommand& mission) {
    switch (mission.recovery_approach_type) {
        case RecoveryApproachType::ILS:
            return 18.0;
        case RecoveryApproachType::Visual:
            return 24.0;
        case RecoveryApproachType::Overhead:
            return 30.0;
        case RecoveryApproachType::TACAN:
            return 20.0;
        case RecoveryApproachType::StraightIn:
            return 20.0;
        case RecoveryApproachType::None:
        default:
            return 22.0;
    }
}

double landing_heading_reference_deg(
    const MissionCommand& mission
) {
    // The current exact packed contract does not yet carry full terrain-cell metadata.
    // Preserve the live fallback behavior used when runway geometry is unavailable.
    return mission.cmd_heading_deg;
}

double lpf(double prev, double input, double dt_s, double tau_s) {
    if (tau_s <= 0.0) {
        return input;
    }
    const double alpha = dt_s / (tau_s + dt_s);
    return prev + alpha * (input - prev);
}

double frame_delta_s(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

struct LocalVec3 {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

LocalVec3 world_to_body(const LocalVec3& v_world, double heading_deg, double pitch_deg, double roll_deg) {
    const double psi = to_radians(90.0 - heading_deg);
    const double theta = to_radians(pitch_deg);
    const double phi = to_radians(roll_deg);

    const double c_psi = std::cos(psi);
    const double s_psi = std::sin(psi);
    const double c_theta = std::cos(theta);
    const double s_theta = std::sin(theta);
    const double c_phi = std::cos(phi);
    const double s_phi = std::sin(phi);

    const double x1 = v_world.x * c_psi + v_world.y * s_psi;
    const double y1 = -v_world.x * s_psi + v_world.y * c_psi;
    const double z1 = v_world.z;

    const double x2 = x1 * c_theta + z1 * s_theta;
    const double y2 = y1;
    const double z2 = -x1 * s_theta + z1 * c_theta;

    LocalVec3 out{};
    out.x = x2;
    out.y = y2 * c_phi + z2 * s_phi;
    out.z = -y2 * s_phi + z2 * c_phi;
    return out;
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

void run_flight_control_stage(ExactWorldStepControlAeroSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_flight_control(soa, i)) {
        return;
    }

    const PilotAction* pilot = soa.has_pilot_action[i] != 0 ? &soa.pilot_action[i] : nullptr;
    const MissionCommand* mission = soa.has_mission_command[i] != 0 ? &soa.mission_command[i] : nullptr;

    double stick_roll = 0.0;
    double stick_pitch = 0.0;
    double stick_yaw = 0.0;
    bool gear_cmd_down = false;

    const bool has_pilot = pilot != nullptr && pilot->active;
    const bool has_mission = mission != nullptr && mission->active;
    const bool on_ground_hint = soa.has_ground_state[i] != 0 ? soa.ground_state[i].on_ground : false;

    if (has_pilot) {
        stick_roll = pilot->stick_roll;
        stick_pitch = pilot->stick_pitch;
        stick_yaw = -pilot->rudder;
        gear_cmd_down = pilot->gear_handle >= 0.5;
    } else if (has_mission) {
        const int command_code = mission->command_code;
        const bool is_route_command = command_code == 3;
        const bool is_landing_command = command_code == 4;

        const double current_heading_deg = soa.transform[i].heading;
        const double current_track_deg = ground_track_deg_from_velocity(soa.velocity[i], current_heading_deg);
        double reference_heading_deg = mission->cmd_heading_deg;
        double lateral_reference_deg = current_heading_deg;
        double bank_limit_deg = 60.0;
        double heading_to_bank_gain = 2.0;
        double bank_to_stick_gain = 0.05;
        double altitude_to_pitch_gain = 0.1;
        double pitch_min_deg = -15.0;
        double pitch_max_deg = 20.0;
        double pitch_to_stick_gain = 0.1;

        if (is_route_command) {
            lateral_reference_deg = current_track_deg;
            bank_limit_deg = 45.0;
        } else if (is_landing_command) {
            reference_heading_deg = landing_heading_reference_deg(
                *mission
            );
            bank_limit_deg = landing_bank_limit_deg(*mission);
            if (on_ground_hint) {
                bank_limit_deg = std::min(bank_limit_deg, 8.0);
            }
            heading_to_bank_gain = 1.0;
            bank_to_stick_gain = 0.04;
            altitude_to_pitch_gain = 0.05;
            pitch_min_deg = on_ground_hint ? -2.0 : -8.0;
            pitch_max_deg = on_ground_hint ? 5.0 : 12.0;
            pitch_to_stick_gain = 0.08;
            gear_cmd_down = true;
        } else if (command_code == 1) {
            bank_limit_deg = 30.0;
            heading_to_bank_gain = 1.4;
        }

        const double heading_err = normalize_angle(reference_heading_deg - lateral_reference_deg);
        const double target_bank = std::clamp(
            heading_err * heading_to_bank_gain,
            -bank_limit_deg,
            bank_limit_deg
        );
        const double bank_err = target_bank - soa.transform[i].roll;
        stick_roll = std::clamp(bank_err * bank_to_stick_gain, -1.0, 1.0);

        const double alt_err = mission->cmd_altitude_m - soa.transform[i].z;
        const double target_pitch = std::clamp(
            alt_err * altitude_to_pitch_gain,
            pitch_min_deg,
            pitch_max_deg
        );
        const double pitch_err = target_pitch - soa.transform[i].pitch;
        stick_pitch = std::clamp(pitch_err * pitch_to_stick_gain, -1.0, 1.0);

        stick_yaw = 0.0;

        if (!is_landing_command) {
            const double speed = std::sqrt(
                soa.velocity[i].vx * soa.velocity[i].vx +
                soa.velocity[i].vy * soa.velocity[i].vy +
                soa.velocity[i].vz * soa.velocity[i].vz
            );
            if (speed < 100.0 || (soa.transform[i].z < 200.0 && mission->cmd_altitude_m < 500.0)) {
                gear_cmd_down = true;
            } else {
                gear_cmd_down = false;
            }
        }
    }

    if (soa.has_force_accumulator[i] != 0 && soa.has_angular_velocity[i] != 0 && soa.has_aero_state[i] != 0) {
        if (soa.has_control_law_state[i] == 0) {
            soa.control_law_state[i] = ControlLawState{};
            soa.has_control_law_state[i] = 1;
        }

        auto& forces = soa.force_accumulator[i];
        const auto& ang_vel = soa.angular_velocity[i];
        const auto& aero = soa.aero_state[i];
        auto& ctl = soa.control_law_state[i];

        constexpr double kStickTauS = 0.15;
        const double dt_s = frame_delta_s(soa.time_step_s[i]);

        ctl.stick_roll_filt = lpf(ctl.stick_roll_filt, stick_roll, dt_s, kStickTauS);
        ctl.stick_pitch_filt = lpf(ctl.stick_pitch_filt, stick_pitch, dt_s, kStickTauS);
        ctl.stick_yaw_filt = lpf(ctl.stick_yaw_filt, stick_yaw, dt_s, kStickTauS);

        const double stick_roll_f = std::clamp(ctl.stick_roll_filt, -1.0, 1.0);
        const double stick_pitch_f = std::clamp(ctl.stick_pitch_filt, -1.0, 1.0);
        const double stick_yaw_f = std::clamp(ctl.stick_yaw_filt, -1.0, 1.0);

        const bool on_ground = soa.has_ground_state[i] != 0 ? soa.ground_state[i].on_ground : false;
        const double q_bar = std::max(0.0, aero.dynamic_pressure);
        const double q_bar_eff = std::min(q_bar, 9000.0);

        const FbwProtectionMode fbw_mode = get_fbw_protection_mode();
        const bool rl_mode = has_pilot;
        const bool fbw_relaxed_for_rl = rl_mode && (fbw_mode == FbwProtectionMode::Relaxed);
        const bool fbw_off_for_rl = rl_mode && (fbw_mode == FbwProtectionMode::Off);

        double stick_yaw_cmd = stick_yaw_f;
        if (on_ground && !fbw_off_for_rl) {
            const double v_h = std::sqrt(
                soa.velocity[i].vx * soa.velocity[i].vx + soa.velocity[i].vy * soa.velocity[i].vy
            );
            constexpr double kYawLimitStartMps = 5.0;
            constexpr double kYawLimitEndMps = 80.0;
            constexpr double kYawMaxLowSpeed = 1.0;
            constexpr double kYawMaxHighSpeed = 0.35;
            constexpr double kYawMaxHighSpeedRelaxed = 0.60;
            double t = 0.0;
            if (v_h > kYawLimitStartMps) {
                t = (v_h - kYawLimitStartMps) / (kYawLimitEndMps - kYawLimitStartMps);
                t = std::clamp(t, 0.0, 1.0);
            }
            const double yaw_high = fbw_relaxed_for_rl ? kYawMaxHighSpeedRelaxed : kYawMaxHighSpeed;
            const double yaw_max = kYawMaxLowSpeed + t * (yaw_high - kYawMaxLowSpeed);
            stick_yaw_cmd = std::clamp(stick_yaw_cmd, -yaw_max, yaw_max);
        }
        ctl.stick_yaw_cmd = stick_yaw_cmd;

        constexpr double kPMaxRadS = 1.2;
        constexpr double kQMaxRadS = 0.8;
        constexpr double kRMaxRadS = 0.8;

        double p_cmd = stick_roll_f * kPMaxRadS;
        double q_cmd = stick_pitch_f * kQMaxRadS;
        double r_cmd = stick_yaw_cmd * kRMaxRadS;

        if (!on_ground && !fbw_off_for_rl) {
            const double beta_rad = to_radians(aero.sideslip_angle);
            double beta_gain = 1.10;
            double yaw_rate_gain = 0.55;
            if (fbw_relaxed_for_rl) {
                beta_gain *= 0.7;
                yaw_rate_gain *= 0.7;
            }
            r_cmd += (-beta_gain * beta_rad) + (-yaw_rate_gain * ang_vel.r);
            r_cmd = std::clamp(r_cmd, -kRMaxRadS, kRMaxRadS);
        }

        if (on_ground && !fbw_off_for_rl) {
            constexpr double kPitchSoftDeg = 8.0;
            constexpr double kPitchHardDeg = 12.0;
            const double protect_gain = fbw_relaxed_for_rl ? 0.45 : 1.0;
            if (soa.transform[i].pitch > kPitchSoftDeg && q_cmd > 0.0) {
                const double t = (soa.transform[i].pitch - kPitchSoftDeg) / (kPitchHardDeg - kPitchSoftDeg);
                const double scale = 1.0 - protect_gain * std::clamp(t, 0.0, 1.0);
                q_cmd *= scale;
            }
            if (soa.transform[i].pitch > kPitchHardDeg) {
                const double q_hard = fbw_relaxed_for_rl ? -0.08 : -0.2;
                q_cmd = std::min(q_cmd, q_hard);
            }
        }

        if (!on_ground && !fbw_off_for_rl) {
            constexpr double kPitchSoftDeg = 60.0;
            constexpr double kPitchHardDeg = 80.0;
            const double protect_gain = fbw_relaxed_for_rl ? 0.55 : 1.0;
            if (soa.transform[i].pitch > kPitchSoftDeg && q_cmd > 0.0) {
                const double t = (soa.transform[i].pitch - kPitchSoftDeg) / (kPitchHardDeg - kPitchSoftDeg);
                const double scale = 1.0 - protect_gain * std::clamp(t, 0.0, 1.0);
                q_cmd *= scale;
            }
            if (soa.transform[i].pitch > kPitchHardDeg) {
                const double q_hard = fbw_relaxed_for_rl ? -0.10 : -0.2;
                q_cmd = std::min(q_cmd, q_hard);
            }
        }

        const double alpha_deg = aero.angle_of_attack;
        const double alpha_abs = std::abs(alpha_deg);
        constexpr double kAoASoftDeg = 10.0;
        constexpr double kAoAHardDeg = 18.0;
        if (!fbw_off_for_rl && alpha_abs > kAoASoftDeg) {
            const double t = (alpha_abs - kAoASoftDeg) / (kAoAHardDeg - kAoASoftDeg);
            const double protect_gain = fbw_relaxed_for_rl ? 0.50 : 1.0;
            const double scale = 1.0 - protect_gain * std::clamp(t, 0.0, 1.0);
            q_cmd *= scale;
        }
        if (!fbw_off_for_rl && alpha_abs > kAoAHardDeg) {
            const double q_hard = fbw_relaxed_for_rl ? -0.06 : -0.15;
            q_cmd = std::min(q_cmd, q_hard);
        }

        constexpr double kRollGain = 40.0;
        constexpr double kPitchGain = 60.0;
        constexpr double kYawGain = 20.0;

        const double tau_roll = (p_cmd - ang_vel.p) * (kRollGain * q_bar_eff);
        const double tau_pitch = (q_cmd - ang_vel.q) * (kPitchGain * q_bar_eff);
        const double tau_yaw = (r_cmd - ang_vel.r) * (kYawGain * q_bar_eff);

        forces.add_torque(tau_roll, tau_pitch, tau_yaw);
    }

    if (soa.has_landing_gear[i] != 0) {
        if (soa.has_ground_state[i] != 0 && soa.ground_state[i].on_ground) {
            gear_cmd_down = true;
        }
        auto& gear = soa.landing_gear[i];
        const double rate = 1.0 / (gear.transit_time_s > 0.0 ? gear.transit_time_s : 5.0);
        if (gear_cmd_down) {
            gear.extension_state += rate * frame_delta_s(soa.time_step_s[i]);
        } else {
            gear.extension_state -= rate * frame_delta_s(soa.time_step_s[i]);
        }
        gear.extension_state = std::clamp(gear.extension_state, 0.0, 1.0);
    }
}

void run_clear_forces_stage(ExactWorldStepControlAeroSoA& soa, std::size_t i) {
    if (soa.has_force_accumulator[i] != 0) {
        soa.force_accumulator[i].clear();
    }
}

void run_compute_aero_state_stage(ExactWorldStepControlAeroSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_compute_aero_state(soa, i)) {
        return;
    }

    double rho = 1.225;
    double speed_of_sound = 340.29;
    LocalVec3 wind{};
    if (soa.has_environment_sample[i] != 0) {
        compute_standard_atmosphere(soa.transform[i].z, &rho, &speed_of_sound);
        wind.x = soa.environment_sample[i].wind_vx_mps;
        wind.y = soa.environment_sample[i].wind_vy_mps;
    } else {
        const double alt_km = std::max(0.0, soa.transform[i].z) / 1000.0;
        rho = 1.225 * std::exp(-alt_km / 7.2);
        speed_of_sound = std::max(295.0, 340.29 - (4.0 * alt_km));
    }

    const double vx = soa.velocity[i].vx - wind.x;
    const double vy = soa.velocity[i].vy - wind.y;
    const double vz = soa.velocity[i].vz - wind.z;

    const double v_sq = vx * vx + vy * vy + vz * vz;
    const double v_total = std::sqrt(v_sq);

    auto& aero = soa.aero_state[i];
    aero.dynamic_pressure = 0.5 * rho * v_sq;
    aero.mach_number = speed_of_sound > 1.0 ? (v_total / speed_of_sound) : 0.0;
    aero.dynamic_pressure = canonicalize_aero_scalar(aero.dynamic_pressure, kAeroScalarCanonicalQuantum);
    aero.mach_number = canonicalize_aero_angle_deg(aero.mach_number);

    const LocalVec3 v_body = world_to_body(
        LocalVec3{vx, vy, vz},
        soa.transform[i].heading,
        soa.transform[i].pitch,
        soa.transform[i].roll
    );

    const double alpha_raw = to_degrees(std::atan2(-v_body.z, v_body.x));
    double beta_arg = v_body.y / std::max(v_total, 1.0e-6);
    beta_arg = std::clamp(beta_arg, -1.0, 1.0);
    const double beta_raw = to_degrees(std::asin(beta_arg));

    constexpr double kBlendStartMps = 2.0;
    constexpr double kBlendEndMps = 8.0;
    double blend = 1.0;
    if (v_total <= kBlendStartMps) {
        blend = 0.0;
    } else if (v_total < kBlendEndMps) {
        blend = (v_total - kBlendStartMps) / (kBlendEndMps - kBlendStartMps);
    }
    blend = std::clamp(blend, 0.0, 1.0);

    aero.angle_of_attack = (1.0 - blend) * aero.angle_of_attack + blend * alpha_raw;
    aero.sideslip_angle = (1.0 - blend) * aero.sideslip_angle + blend * beta_raw;
    aero.angle_of_attack = std::clamp(aero.angle_of_attack, -90.0, 90.0);
    aero.sideslip_angle = std::clamp(aero.sideslip_angle, -90.0, 90.0);
    aero.angle_of_attack = canonicalize_aero_angle_deg(aero.angle_of_attack);
    aero.sideslip_angle = canonicalize_aero_angle_deg(aero.sideslip_angle);
}

}  // namespace

ExactWorldStepControlAeroSoA pack_exact_world_step_states_v1_control_aero_soa(
    const std::vector<ExactWorldStepStateV1>& states
) {
    ExactWorldStepControlAeroSoA soa{};
    soa.size = states.size();

    soa.time_step_s.resize(soa.size);
    soa.transform.resize(soa.size);
    soa.velocity.resize(soa.size);
    soa.angular_velocity.resize(soa.size);
    soa.force_accumulator.resize(soa.size);
    soa.aero_state.resize(soa.size);
    soa.control_law_state.resize(soa.size);
    soa.pilot_action.resize(soa.size);
    soa.mission_command.resize(soa.size);
    soa.lagged_command.resize(soa.size);
    soa.flight_model.resize(soa.size);
    soa.landing_gear.resize(soa.size);
    soa.ground_state.resize(soa.size);
    soa.environment_sample.resize(soa.size);

    soa.has_angular_velocity.resize(soa.size);
    soa.has_force_accumulator.resize(soa.size);
    soa.has_aero_state.resize(soa.size);
    soa.has_control_law_state.resize(soa.size);
    soa.has_pilot_action.resize(soa.size);
    soa.has_mission_command.resize(soa.size);
    soa.has_lagged_command.resize(soa.size);
    soa.has_flight_model.resize(soa.size);
    soa.has_landing_gear.resize(soa.size);
    soa.has_ground_state.resize(soa.size);
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
        soa.mission_command[i] = state.mission_command;
        soa.lagged_command[i] = state.lagged_command;
        soa.flight_model[i] = state.flight_model;
        soa.landing_gear[i] = state.landing_gear;
        soa.ground_state[i] = state.ground_state;
        soa.environment_sample[i] = state.environment_sample;

        soa.has_angular_velocity[i] = state.has_angular_velocity ? 1u : 0u;
        soa.has_force_accumulator[i] = state.has_force_accumulator ? 1u : 0u;
        soa.has_aero_state[i] = state.has_aero_state ? 1u : 0u;
        soa.has_control_law_state[i] = state.has_control_law_state ? 1u : 0u;
        soa.has_pilot_action[i] = state.has_pilot_action ? 1u : 0u;
        soa.has_mission_command[i] = state.has_mission_command ? 1u : 0u;
        soa.has_lagged_command[i] = state.has_lagged_command ? 1u : 0u;
        soa.has_flight_model[i] = state.has_flight_model ? 1u : 0u;
        soa.has_landing_gear[i] = state.has_landing_gear ? 1u : 0u;
        soa.has_ground_state[i] = state.has_ground_state ? 1u : 0u;
        soa.has_environment_sample[i] = state.has_environment_sample ? 1u : 0u;
    }

    return soa;
}

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_control_aero_soa(
    const ExactWorldStepControlAeroSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
    if (soa.size != basis_states.size()) {
        throw std::invalid_argument("control-aero SoA size must match basis state count");
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
        state.mission_command = soa.mission_command[i];
        state.lagged_command = soa.lagged_command[i];
        state.flight_model = soa.flight_model[i];
        state.landing_gear = soa.landing_gear[i];
        state.ground_state = soa.ground_state[i];
        state.environment_sample = soa.environment_sample[i];

        state.has_angular_velocity = soa.has_angular_velocity[i] != 0;
        state.has_force_accumulator = soa.has_force_accumulator[i] != 0;
        state.has_aero_state = soa.has_aero_state[i] != 0;
        state.has_control_law_state = soa.has_control_law_state[i] != 0;
        state.has_pilot_action = soa.has_pilot_action[i] != 0;
        state.has_mission_command = soa.has_mission_command[i] != 0;
        state.has_lagged_command = soa.has_lagged_command[i] != 0;
        state.has_flight_model = soa.has_flight_model[i] != 0;
        state.has_landing_gear = soa.has_landing_gear[i] != 0;
        state.has_ground_state = soa.has_ground_state[i] != 0;
        state.has_environment_sample = soa.has_environment_sample[i] != 0;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_control_aero_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepControlAeroSoA soa = pack_exact_world_step_states_v1_control_aero_soa(initial_states);
    for (std::size_t i = 0; i < soa.size; ++i) {
        run_flight_control_stage(soa, i);
        run_clear_forces_stage(soa, i);
        run_compute_aero_state_stage(soa, i);
    }
    auto out = unpack_exact_world_step_states_v1_control_aero_soa(soa, initial_states);
    const auto end = std::chrono::steady_clock::now();

    g_last_stats.state_count = initial_states.size();
    g_last_stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    return out;
}

const ExactWorldStepControlAeroStats& last_exact_world_step_control_aero_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
