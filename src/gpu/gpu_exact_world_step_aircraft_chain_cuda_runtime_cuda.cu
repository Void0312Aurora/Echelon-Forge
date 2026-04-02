#include "gpu/gpu_exact_world_step_aircraft_chain_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_aircraft_chain_cuda_runtime_types.h"

#include <cuda_runtime_api.h>

#include <chrono>
#include <cmath>
#include <cstdlib>
#include <vector>

namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr double kGravity = 9.80665;
constexpr double kSeaLevelDensity = 1.225;

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

constexpr double kRefLat = 36.24;
constexpr double kRefLon = -115.05;
constexpr double kMetersPerDegLat = 111132.954;
constexpr double kMetersPerDegLon = 90000.0;
constexpr double kForceScalarCanonicalQuantum = 0x1p-32;
constexpr double kDirectionScalarCanonicalQuantum = 1.0e-14;
constexpr double kProjectedForceScalarCanonicalQuantum = 0x1p-32;
constexpr double kBaseWindSpeedMps = 10.0;
constexpr double kBaseWindDirFromDeg = 270.0;
constexpr double kWindShearMpsPerKm = 4.0;
constexpr double kAeroScalarCanonicalQuantum = 1.0e-10;
constexpr double kAeroAngleCanonicalQuantumDeg = 0x1p-40;
constexpr double kEnvironmentScalarCanonicalQuantum = 0x1p-76;

using Transform = gpu::aircraft_chain_cuda::Transform;
using Velocity = gpu::aircraft_chain_cuda::Velocity;
using AngularVelocity = gpu::aircraft_chain_cuda::AngularVelocity;
using ForceAccumulator = gpu::aircraft_chain_cuda::ForceAccumulator;
using AeroState = gpu::aircraft_chain_cuda::AeroState;
using ControlLawState = gpu::aircraft_chain_cuda::ControlLawState;
using PilotAction = gpu::aircraft_chain_cuda::PilotAction;
using MissionCommand = gpu::aircraft_chain_cuda::MissionCommand;
using MovementCommand = gpu::aircraft_chain_cuda::MovementCommand;
using ActionCommand = gpu::aircraft_chain_cuda::ActionCommand;
using LandingGear = gpu::aircraft_chain_cuda::LandingGear;
using GearState = gpu::aircraft_chain_cuda::GearState;
using Mass = gpu::aircraft_chain_cuda::Mass;
using Inertia = gpu::aircraft_chain_cuda::Inertia;
using Propulsion = gpu::aircraft_chain_cuda::Propulsion;
using FuelSystem = gpu::aircraft_chain_cuda::FuelSystem;
using MassProperties = gpu::aircraft_chain_cuda::MassProperties;
using GroundState = gpu::aircraft_chain_cuda::GroundState;
using Health = gpu::aircraft_chain_cuda::Health;
using InstrumentState = gpu::aircraft_chain_cuda::InstrumentState;
using EGI = gpu::aircraft_chain_cuda::EGI;
using Ammo = gpu::aircraft_chain_cuda::Ammo;
using RwrSummary = gpu::aircraft_chain_cuda::RwrSummary;
using EnvironmentSample = gpu::aircraft_chain_cuda::EnvironmentSample;
using RecoveryApproachType = gpu::aircraft_chain_cuda::RecoveryApproachType;
using AircraftChainState = gpu::aircraft_chain_cuda::ExactWorldStepAircraftChainCudaState;

enum class FbwProtectionMode {
    Strict = 0,
    Relaxed = 1,
    Off = 2,
};

struct RotationalParams {
    double max_rate_cross_rad_s;
    double max_torque_nm;
    double max_ang_accel_rad_s2;
    double max_rate_rad_s;
    double min_abs_cos_theta;
    double pitch_limit_deg;
};

template <typename T>
__host__ __device__ T clamp_value(T value, T low, T high) {
    return value < low ? low : (value > high ? high : value);
}

__device__ __forceinline__ double canonicalize_aero_scalar(double value, double quantum) {
    if (!isfinite(value) || quantum <= 0.0) {
        return value;
    }
    if (fabs(value) <= (quantum * 0.5)) {
        return 0.0;
    }
    const double rounded = nearbyint(value / quantum) * quantum;
    return fabs(rounded) <= (quantum * 0.5) ? 0.0 : rounded;
}

__device__ __forceinline__ double canonicalize_aero_angle_deg(double value) {
    return canonicalize_aero_scalar(value, kAeroAngleCanonicalQuantumDeg);
}

__device__ __forceinline__ double canonicalize_force_scalar(double value) {
    if (!isfinite(value) || kForceScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (fabs(value) <= (kForceScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = nearbyint(value / kForceScalarCanonicalQuantum) *
        kForceScalarCanonicalQuantum;
    return fabs(rounded) <= (kForceScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

__device__ __forceinline__ double canonicalize_direction_scalar(double value) {
    if (!isfinite(value) || kDirectionScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (fabs(value) <= (kDirectionScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = nearbyint(value / kDirectionScalarCanonicalQuantum) *
        kDirectionScalarCanonicalQuantum;
    return fabs(rounded) <= (kDirectionScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

__device__ __forceinline__ double canonicalize_projected_force_scalar(double value) {
    if (!isfinite(value) || kProjectedForceScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (fabs(value) <= (kProjectedForceScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = nearbyint(value / kProjectedForceScalarCanonicalQuantum) *
        kProjectedForceScalarCanonicalQuantum;
    return fabs(rounded) <= (kProjectedForceScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

template <typename T>
void free_device_ptr(T*& ptr) {
    if (ptr != nullptr) {
        cudaFree(ptr);
        ptr = nullptr;
    }
}

FbwProtectionMode get_fbw_protection_mode() {
    const char* value = std::getenv("CMO_FBW_PROTECTION_MODE");
    if (value == nullptr) {
        return FbwProtectionMode::Strict;
    }
    const char ch = value[0];
    if (ch == 'o' || ch == 'O' || ch == '0') {
        return FbwProtectionMode::Off;
    }
    if (ch == 'r' || ch == 'R' || ch == '1') {
        return FbwProtectionMode::Relaxed;
    }
    return FbwProtectionMode::Strict;
}

RotationalParams rotational_params_host() {
    auto env_double = [](const char* key, double fallback) {
        const char* value = std::getenv(key);
        if (value == nullptr || *value == '\0') {
            return fallback;
        }
        char* end = nullptr;
        const double out = std::strtod(value, &end);
        if (end == value || !std::isfinite(out)) {
            return fallback;
        }
        return out;
    };

    RotationalParams value{};
    value.max_rate_cross_rad_s = fmax(1.0, env_double("CMO_ROT_MAX_RATE_CROSS_RAD_S", 50.0));
    value.max_torque_nm = fmax(1.0e4, env_double("CMO_ROT_MAX_TORQUE_NM", 5.0e6));
    value.max_ang_accel_rad_s2 = fmax(10.0, env_double("CMO_ROT_MAX_ANG_ACCEL_RAD_S2", 1.0e4));
    value.max_rate_rad_s = fmax(0.1, env_double("CMO_ROT_MAX_RATE_RAD_S", 6.0));
    const double min_pitch_deg = clamp_value(env_double("CMO_ROT_SINGULARITY_MIN_PITCH_DEG", 85.0), 70.0, 89.9);
    value.min_abs_cos_theta = cos(min_pitch_deg * kPi / 180.0);
    value.pitch_limit_deg = clamp_value(env_double("CMO_ROT_PITCH_LIMIT_DEG", 89.0), 70.0, 89.9);
    return value;
}

struct LocalVec3 {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

__device__ __forceinline__ double to_degrees(double radians) { return radians * 180.0 / kPi; }
__device__ __forceinline__ double to_radians(double degrees) { return degrees * kPi / 180.0; }
__device__ __forceinline__ double deg_to_rad(double deg) { return deg * kPi / 180.0; }
__device__ __forceinline__ double rad_to_deg(double rad) { return rad * 180.0 / kPi; }
__device__ __forceinline__ double frame_delta_s(double time_step_s) { return static_cast<double>(static_cast<float>(time_step_s)); }

__device__ __forceinline__ double normalize_angle(double angle_deg) {
    while (angle_deg > 180.0) {
        angle_deg -= 360.0;
    }
    while (angle_deg < -180.0) {
        angle_deg += 360.0;
    }
    return angle_deg;
}

__device__ __forceinline__ double wrap_360(double deg) {
    deg = fmod(deg, 360.0);
    if (deg < 0.0) {
        deg += 360.0;
    }
    return deg;
}

__device__ __forceinline__ double clamp_finite(double value, double lo, double hi) {
    if (!isfinite(value)) {
        return 0.0;
    }
    return clamp_value(value, lo, hi);
}

__device__ __forceinline__ double ground_track_deg_from_velocity(
    const Velocity& velocity,
    double fallback_heading_deg
) {
    const double horiz_speed = hypot(velocity.vx, velocity.vy);
    if (horiz_speed <= 1.0) {
        return fallback_heading_deg;
    }
    double track_deg = fmod(to_degrees(atan2(velocity.vx, velocity.vy)), 360.0);
    if (track_deg < 0.0) {
        track_deg += 360.0;
    }
    return track_deg;
}

__device__ __forceinline__ double landing_bank_limit_deg(const MissionCommand& mission) {
    switch (mission.recovery_approach_type) {
        case RecoveryApproachType::ILS: return 18.0;
        case RecoveryApproachType::Visual: return 24.0;
        case RecoveryApproachType::Overhead: return 30.0;
        case RecoveryApproachType::TACAN: return 20.0;
        case RecoveryApproachType::StraightIn: return 20.0;
        case RecoveryApproachType::None:
        default: return 22.0;
    }
}

__device__ __forceinline__ double landing_heading_reference_deg(const MissionCommand& mission) {
    return mission.cmd_heading_deg;
}

__device__ __forceinline__ double lpf(double prev, double input, double dt_s, double tau_s) {
    if (tau_s <= 0.0) {
        return input;
    }
    const double alpha = dt_s / (tau_s + dt_s);
    return prev + alpha * (input - prev);
}

__device__ __forceinline__ LocalVec3 world_to_body(
    const LocalVec3& v_world,
    double heading_deg,
    double pitch_deg,
    double roll_deg
) {
    const double psi = to_radians(90.0 - heading_deg);
    const double theta = to_radians(pitch_deg);
    const double phi = to_radians(roll_deg);

    const double c_psi = cos(psi);
    const double s_psi = sin(psi);
    const double c_theta = cos(theta);
    const double s_theta = sin(theta);
    const double c_phi = cos(phi);
    const double s_phi = sin(phi);

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

__device__ __forceinline__ LocalVec3 vec_cross(const LocalVec3& a, const LocalVec3& b) {
    return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}

__device__ __forceinline__ double vec_length(const LocalVec3& v) {
    return sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
}

__device__ __forceinline__ LocalVec3 vec_norm(const LocalVec3& v) {
    const double len = vec_length(v);
    if (len <= 1.0e-9) {
        return {};
    }
    return {v.x / len, v.y / len, v.z / len};
}

__device__ __forceinline__ double smoothstep01(double x) {
    x = clamp_value(x, 0.0, 1.0);
    return x * x * (3.0 - 2.0 * x);
}

__device__ __forceinline__ double smooth_coulomb(double v, double mu_in, double Fn_in, double v_ref) {
    if (Fn_in <= 0.0 || mu_in <= 0.0) {
        return 0.0;
    }
    v_ref = fmax(v_ref, 1.0e-3);
    const double s = tanh(v / v_ref);
    return -mu_in * Fn_in * s;
}

__device__ __forceinline__ LocalVec3 get_body_right(double heading_deg, double pitch_deg, double roll_deg) {
    const double psi = to_radians(90.0 - heading_deg);
    const double theta = to_radians(pitch_deg);
    const double phi = to_radians(roll_deg);

    const double c_psi = cos(psi);
    const double s_psi = sin(psi);
    const double c_theta = cos(theta);
    const double s_theta = sin(theta);
    const double c_phi = cos(phi);
    const double s_phi = sin(phi);

    return {
        -s_psi * c_phi + c_psi * s_theta * s_phi,
         c_psi * c_phi + s_psi * s_theta * s_phi,
         c_theta * s_phi,
    };
}

__device__ __forceinline__ void add_force(ForceAccumulator& forces, double x, double y, double z) {
    forces.fx += x;
    forces.fy += y;
    forces.fz += z;
}

__device__ __forceinline__ void add_torque(ForceAccumulator& forces, double roll, double pitch, double yaw) {
    forces.torque_roll += roll;
    forces.torque_pitch += pitch;
    forces.torque_yaw += yaw;
}

__device__ __forceinline__ void clear_forces(ForceAccumulator& forces) {
    forces.fx = 0.0;
    forces.fy = 0.0;
    forces.fz = 0.0;
    forces.torque_roll = 0.0;
    forces.torque_pitch = 0.0;
    forces.torque_yaw = 0.0;
}

__device__ __forceinline__ double mass_total_kg(const Mass& mass) {
    return mass.empty_mass_kg + mass.fuel_mass_kg + mass.stores_mass_kg;
}

__device__ __forceinline__ void compute_standard_atmosphere_front(
    double altitude_m,
    double* out_rho,
    double* out_speed_of_sound
) {
    constexpr double kG = 9.80665;
    constexpr double kR = 287.0;
    constexpr double kL = 0.0065;
    constexpr double kT0 = 288.15;
    constexpr double kP0 = 101325.0;
    const double h = altitude_m < 0.0 ? 0.0 : altitude_m;
    double temperature = 0.0;
    double pressure = 0.0;
    if (h < 11000.0) {
        temperature = kT0 - kL * h;
        pressure = kP0 * pow(1.0 - kL * h / kT0, kG / (kR * kL));
    } else {
        constexpr double kT11 = 216.65;
        constexpr double kP11 = 22632.1;
        temperature = kT11;
        pressure = kP11 * exp(-kG * (h - 11000.0) / (kR * kT11));
    }
    *out_rho = pressure / (kR * temperature);
    *out_speed_of_sound = sqrt(1.4 * kR * temperature);
}

__device__ __forceinline__ void compute_standard_atmosphere_tail(
    double altitude_m,
    double* out_temperature_k,
    double* out_air_density,
    double* out_speed_of_sound
) {
    constexpr double kG = 9.80665;
    constexpr double kR = 287.0;
    constexpr double kL = 0.0065;
    constexpr double kT0 = 288.15;
    constexpr double kP0 = 101325.0;
    const double h = fmax(0.0, altitude_m);
    double temperature = 0.0;
    double pressure = 0.0;
    if (h < 11000.0) {
        temperature = kT0 - kL * h;
        pressure = kP0 * pow(1.0 - kL * h / kT0, kG / (kR * kL));
    } else {
        constexpr double kT11 = 216.65;
        constexpr double kP11 = 22632.1;
        temperature = kT11;
        pressure = kP11 * exp(-kG * (h - 11000.0) / (kR * kT11));
    }
    *out_temperature_k = temperature;
    *out_air_density = pressure / (kR * temperature);
    *out_speed_of_sound = sqrt(1.4 * kR * temperature);
}

__device__ void run_flight_control_stage(AircraftChainState& state, FbwProtectionMode fbw_mode) {
    if (!state.has_lagged_command || !state.has_flight_model) {
        return;
    }

    const PilotAction* pilot = state.has_pilot_action ? &state.pilot_action : nullptr;
    const MissionCommand* mission = state.has_mission_command ? &state.mission_command : nullptr;

    double stick_roll = 0.0;
    double stick_pitch = 0.0;
    double stick_yaw = 0.0;
    bool gear_cmd_down = false;

    const bool has_pilot = pilot != nullptr && pilot->active;
    const bool has_mission = mission != nullptr && mission->active;
    const bool on_ground_hint = state.has_ground_state ? state.ground_state.on_ground : false;

    if (has_pilot) {
        stick_roll = pilot->stick_roll;
        stick_pitch = pilot->stick_pitch;
        stick_yaw = -pilot->rudder;
        gear_cmd_down = pilot->gear_handle >= 0.5f;
    } else if (has_mission) {
        const int command_code = mission->command_code;
        const bool is_route_command = command_code == 3;
        const bool is_landing_command = command_code == 4;

        const double current_heading_deg = state.transform.heading;
        const double current_track_deg = ground_track_deg_from_velocity(state.velocity, current_heading_deg);
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
            reference_heading_deg = landing_heading_reference_deg(*mission);
            bank_limit_deg = landing_bank_limit_deg(*mission);
            if (on_ground_hint) {
                bank_limit_deg = fmin(bank_limit_deg, 8.0);
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
        const double target_bank = clamp_value(heading_err * heading_to_bank_gain, -bank_limit_deg, bank_limit_deg);
        const double bank_err = target_bank - state.transform.roll;
        stick_roll = clamp_value(bank_err * bank_to_stick_gain, -1.0, 1.0);

        const double alt_err = mission->cmd_altitude_m - state.transform.z;
        const double target_pitch = clamp_value(alt_err * altitude_to_pitch_gain, pitch_min_deg, pitch_max_deg);
        const double pitch_err = target_pitch - state.transform.pitch;
        stick_pitch = clamp_value(pitch_err * pitch_to_stick_gain, -1.0, 1.0);

        stick_yaw = 0.0;

        if (!is_landing_command) {
            const double speed = sqrt(
                state.velocity.vx * state.velocity.vx +
                state.velocity.vy * state.velocity.vy +
                state.velocity.vz * state.velocity.vz
            );
            gear_cmd_down = speed < 100.0 || (state.transform.z < 200.0 && mission->cmd_altitude_m < 500.0);
        }
    }

    if (state.has_force_accumulator && state.has_angular_velocity && state.has_aero_state) {
        if (!state.has_control_law_state) {
            state.control_law_state = ControlLawState{};
            state.has_control_law_state = true;
        }

        auto& forces = state.force_accumulator;
        const auto& ang_vel = state.angular_velocity;
        const auto& aero = state.aero_state;
        auto& ctl = state.control_law_state;

        constexpr double kStickTauS = 0.15;
        const double dt_s = frame_delta_s(state.time_step_s);

        ctl.stick_roll_filt = lpf(ctl.stick_roll_filt, stick_roll, dt_s, kStickTauS);
        ctl.stick_pitch_filt = lpf(ctl.stick_pitch_filt, stick_pitch, dt_s, kStickTauS);
        ctl.stick_yaw_filt = lpf(ctl.stick_yaw_filt, stick_yaw, dt_s, kStickTauS);

        const double stick_roll_f = clamp_value(ctl.stick_roll_filt, -1.0, 1.0);
        const double stick_pitch_f = clamp_value(ctl.stick_pitch_filt, -1.0, 1.0);
        const double stick_yaw_f = clamp_value(ctl.stick_yaw_filt, -1.0, 1.0);

        const bool on_ground = state.has_ground_state ? state.ground_state.on_ground : false;
        const double q_bar = fmax(0.0, aero.dynamic_pressure);
        const double q_bar_eff = fmin(q_bar, 9000.0);

        const bool rl_mode = has_pilot;
        const bool fbw_relaxed_for_rl = rl_mode && (fbw_mode == FbwProtectionMode::Relaxed);
        const bool fbw_off_for_rl = rl_mode && (fbw_mode == FbwProtectionMode::Off);

        double stick_yaw_cmd = stick_yaw_f;
        if (on_ground && !fbw_off_for_rl) {
            const double v_h = sqrt(state.velocity.vx * state.velocity.vx + state.velocity.vy * state.velocity.vy);
            constexpr double kYawLimitStartMps = 5.0;
            constexpr double kYawLimitEndMps = 80.0;
            constexpr double kYawMaxLowSpeed = 1.0;
            constexpr double kYawMaxHighSpeed = 0.35;
            constexpr double kYawMaxHighSpeedRelaxed = 0.60;
            double t = 0.0;
            if (v_h > kYawLimitStartMps) {
                t = (v_h - kYawLimitStartMps) / (kYawLimitEndMps - kYawLimitStartMps);
                t = clamp_value(t, 0.0, 1.0);
            }
            const double yaw_high = fbw_relaxed_for_rl ? kYawMaxHighSpeedRelaxed : kYawMaxHighSpeed;
            const double yaw_max = kYawMaxLowSpeed + t * (yaw_high - kYawMaxLowSpeed);
            stick_yaw_cmd = clamp_value(stick_yaw_cmd, -yaw_max, yaw_max);
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
            r_cmd = clamp_value(r_cmd, -kRMaxRadS, kRMaxRadS);
        }

        const double alpha_deg = aero.angle_of_attack;
        const double alpha_abs = fabs(alpha_deg);
        constexpr double kAoASoftDeg = 10.0;
        constexpr double kAoAHardDeg = 18.0;
        if (!fbw_off_for_rl && alpha_abs > kAoASoftDeg) {
            const double t = (alpha_abs - kAoASoftDeg) / (kAoAHardDeg - kAoASoftDeg);
            const double protect_gain = fbw_relaxed_for_rl ? 0.50 : 1.0;
            const double scale = 1.0 - protect_gain * clamp_value(t, 0.0, 1.0);
            q_cmd *= scale;
        }
        if (!fbw_off_for_rl && alpha_abs > kAoAHardDeg) {
            const double q_hard = fbw_relaxed_for_rl ? -0.06 : -0.15;
            q_cmd = fmin(q_cmd, q_hard);
        }

        constexpr double kRollGain = 40.0;
        constexpr double kPitchGain = 60.0;
        constexpr double kYawGain = 20.0;

        const double tau_roll = (p_cmd - ang_vel.p) * (kRollGain * q_bar_eff);
        const double tau_pitch = (q_cmd - ang_vel.q) * (kPitchGain * q_bar_eff);
        const double tau_yaw = (r_cmd - ang_vel.r) * (kYawGain * q_bar_eff);
        add_torque(forces, tau_roll, tau_pitch, tau_yaw);
    }

    if (state.has_landing_gear) {
        if (state.has_ground_state && state.ground_state.on_ground) {
            gear_cmd_down = true;
        }
        auto& gear = state.landing_gear;
        const double rate = 1.0 / (gear.transit_time_s > 0.0 ? gear.transit_time_s : 5.0);
        if (gear_cmd_down) {
            gear.extension_state += rate * frame_delta_s(state.time_step_s);
        } else {
            gear.extension_state -= rate * frame_delta_s(state.time_step_s);
        }
        gear.extension_state = clamp_value(gear.extension_state, 0.0, 1.0);
    }
}

__device__ void run_clear_forces_stage(AircraftChainState& state) {
    if (state.has_force_accumulator) {
        clear_forces(state.force_accumulator);
    }
}

__device__ void run_compute_aero_state_stage(AircraftChainState& state) {
    if (!state.has_aero_state) {
        return;
    }

    double rho = 1.225;
    double speed_of_sound = 340.29;
    LocalVec3 wind{};
    if (state.has_environment_sample) {
        compute_standard_atmosphere_front(state.transform.z, &rho, &speed_of_sound);
        wind.x = state.environment_sample.wind_vx_mps;
        wind.y = state.environment_sample.wind_vy_mps;
    } else {
        const double alt_km = fmax(0.0, state.transform.z) / 1000.0;
        rho = 1.225 * exp(-alt_km / 7.2);
        speed_of_sound = fmax(295.0, 340.29 - (4.0 * alt_km));
    }

    const double vx = state.velocity.vx - wind.x;
    const double vy = state.velocity.vy - wind.y;
    const double vz = state.velocity.vz - wind.z;
    const double v_sq = vx * vx + vy * vy + vz * vz;
    const double v_total = sqrt(v_sq);

    auto& aero = state.aero_state;
    aero.dynamic_pressure = 0.5 * rho * v_sq;
    aero.mach_number = speed_of_sound > 1.0 ? (v_total / speed_of_sound) : 0.0;
    aero.dynamic_pressure = canonicalize_aero_scalar(aero.dynamic_pressure, kAeroScalarCanonicalQuantum);
    aero.mach_number = canonicalize_aero_angle_deg(aero.mach_number);

    const LocalVec3 v_body = world_to_body(LocalVec3{vx, vy, vz}, state.transform.heading, state.transform.pitch, state.transform.roll);

    const double alpha_raw = to_degrees(atan2(-v_body.z, v_body.x));
    double beta_arg = v_body.y / fmax(v_total, 1.0e-6);
    beta_arg = clamp_value(beta_arg, -1.0, 1.0);
    const double beta_raw = to_degrees(asin(beta_arg));

    constexpr double kBlendStartMps = 2.0;
    constexpr double kBlendEndMps = 8.0;
    double blend = 1.0;
    if (v_total <= kBlendStartMps) {
        blend = 0.0;
    } else if (v_total < kBlendEndMps) {
        blend = (v_total - kBlendStartMps) / (kBlendEndMps - kBlendStartMps);
    }
    blend = clamp_value(blend, 0.0, 1.0);

    aero.angle_of_attack = (1.0 - blend) * aero.angle_of_attack + blend * alpha_raw;
    aero.sideslip_angle = (1.0 - blend) * aero.sideslip_angle + blend * beta_raw;
    aero.angle_of_attack = clamp_value(aero.angle_of_attack, -90.0, 90.0);
    aero.sideslip_angle = clamp_value(aero.sideslip_angle, -90.0, 90.0);
    aero.angle_of_attack = canonicalize_aero_angle_deg(aero.angle_of_attack);
    aero.sideslip_angle = canonicalize_aero_angle_deg(aero.sideslip_angle);
}

__device__ void run_compute_forces_stage(AircraftChainState& state) {
    if (!(state.has_force_accumulator && state.has_mass && state.has_propulsion && state.has_flight_model &&
          state.has_movement_command)) {
        return;
    }

    const PilotAction* pilot = state.has_pilot_action ? &state.pilot_action : nullptr;
    const bool has_pilot = pilot != nullptr && pilot->active;
    const bool has_legacy = state.movement_command.active;
    if (!has_pilot && !has_legacy) {
        return;
    }

    double m = mass_total_kg(state.mass);
    if (m < 1.0) {
        m = 15000.0;
    }

    const double vx = state.velocity.vx;
    const double vy = state.velocity.vy;
    const double vz = state.velocity.vz;
    const double speed = sqrt(vx * vx + vy * vy + vz * vz);

    add_force(state.force_accumulator, 0.0, 0.0, -m * kGravity);

    const double yaw_rad = to_radians(90.0 - state.transform.heading);
    const double pitch_rad = to_radians(state.transform.pitch);
    const double nose_x = canonicalize_direction_scalar(cos(yaw_rad) * cos(pitch_rad));
    const double nose_y = canonicalize_direction_scalar(sin(yaw_rad) * cos(pitch_rad));
    const double nose_z = canonicalize_direction_scalar(sin(pitch_rad));

    double throttle_input = 0.0;
    if (has_pilot) {
        throttle_input = pilot->throttle;
    } else if (state.movement_command.active) {
        throttle_input = state.movement_command.throttle_cmd;
    }
    throttle_input = clamp_value(throttle_input, 0.0, 1.0);

    double thrust_magnitude = 0.0;
    bool afterburner_active = false;
    if (throttle_input > 0.9) {
        thrust_magnitude = state.propulsion.ab_thrust_n;
        afterburner_active = true;
    } else {
        thrust_magnitude = state.propulsion.mil_thrust_n * throttle_input;
    }

    double rho = kSeaLevelDensity;
    double speed_of_sound = 340.29;
    if (state.has_environment_sample) {
        compute_standard_atmosphere_front(state.transform.z, &rho, &speed_of_sound);
    }
    double sigma = rho / kSeaLevelDensity;
    sigma = fmax(0.01, sigma);
    double mach = 0.0;
    if (speed_of_sound > 1.0) {
        mach = speed / speed_of_sound;
    }
    thrust_magnitude *= sigma * (1.0 + 0.3 * mach);
    thrust_magnitude = canonicalize_force_scalar(thrust_magnitude);

    state.propulsion.current_thrust_n = thrust_magnitude;
    state.propulsion.afterburner_active = afterburner_active;
    const double thrust_fx = canonicalize_projected_force_scalar(thrust_magnitude * nose_x);
    const double thrust_fy = canonicalize_projected_force_scalar(thrust_magnitude * nose_y);
    const double thrust_fz = canonicalize_projected_force_scalar(thrust_magnitude * nose_z);
    add_force(state.force_accumulator, thrust_fx, thrust_fy, thrust_fz);
}

__device__ void run_compute_aerodynamics_stage(AircraftChainState& state) {
    if (!(state.has_force_accumulator && state.has_aero_state && state.has_mass_properties)) {
        return;
    }

    auto& forces = state.force_accumulator;
    auto& aero = state.aero_state;
    const auto& props = state.mass_properties;
    const auto& velocity = state.velocity;
    const auto& transform = state.transform;

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
    double Cl = kClAlphaPerDeg * alpha;

    const PilotAction* pilot = state.has_pilot_action ? &state.pilot_action : nullptr;
    double flaps_deflection = 0.0;
    double speedbrake_pos = 0.0;
    if (pilot != nullptr && pilot->active) {
        flaps_deflection = clamp_value(static_cast<double>(pilot->flaps), 0.0, 1.0);
        speedbrake_pos = clamp_value(static_cast<double>(pilot->speedbrake), 0.0, 1.0);
    }
    Cl += flaps_deflection * 0.35;

    const double alpha_abs = fabs(alpha);
    const double alpha_sign = alpha >= 0.0 ? 1.0 : -1.0;
    const double alpha_stall_deg = 15.0 + 6.0 * flaps_deflection;
    const double alpha_peak_deg = alpha_stall_deg + 8.0;
    const double alpha_deep_deg = alpha_peak_deg + 18.0;
    const double cl_peak_mag = 1.25 + 0.45 * flaps_deflection;
    const double cl_deep_mag = 0.22 + 0.10 * flaps_deflection;

    if (alpha_abs > alpha_stall_deg) {
        if (alpha_abs <= alpha_peak_deg) {
            const double t = smoothstep01((alpha_abs - alpha_stall_deg) / fmax(1.0e-6, alpha_peak_deg - alpha_stall_deg));
            Cl = (1.0 - t) * Cl + t * (alpha_sign * cl_peak_mag);
        } else if (alpha_abs <= alpha_deep_deg) {
            const double t = smoothstep01((alpha_abs - alpha_peak_deg) / fmax(1.0e-6, alpha_deep_deg - alpha_peak_deg));
            const double cl_peak = alpha_sign * cl_peak_mag;
            Cl = (1.0 - t) * cl_peak + t * (alpha_sign * cl_deep_mag);
        } else {
            Cl = alpha_sign * cl_deep_mag;
        }
    }

    double Cd0 = 0.02;
    Cd0 += props.current_drag_index * 0.001;
    if (state.has_landing_gear) {
        Cd0 += state.landing_gear.extension_state * 0.04;
    }
    Cd0 += speedbrake_pos * 0.08;
    Cd0 += flaps_deflection * 0.02;
    const double k = 0.1;

    double ge = 0.0;
    if (state.has_environment_sample) {
        const double alt_agl = fmax(0.0, transform.z - state.environment_sample.terrain_elevation_m);
        const double b_ref = fmax(1.0, props.wing_span_m);
        const double ge_fade_h = 0.5 * b_ref;
        if (ge_fade_h > 1.0e-6 && alt_agl < ge_fade_h) {
            ge = clamp_value(1.0 - (alt_agl / ge_fade_h), 0.0, 1.0);
        }
    }
    Cl *= (1.0 + 0.08 * ge);
    const double k_eff = k * (1.0 - 0.70 * ge);

    double stall_drag = 0.0;
    if (alpha_abs > alpha_stall_deg) {
        const double s1 = smoothstep01((alpha_abs - alpha_stall_deg) / fmax(1.0e-6, alpha_peak_deg - alpha_stall_deg));
        const double s2 = smoothstep01((alpha_abs - alpha_peak_deg) / fmax(1.0e-6, alpha_deep_deg - alpha_peak_deg));
        stall_drag = 0.25 * s1 + 0.55 * s2;
    }

    const double Cd = Cd0 + k_eff * Cl * Cl + stall_drag;
    aero.lift_coefficient = Cl;
    aero.drag_coefficient = Cd;

    const double lift_mag = q * S * Cl;
    const double drag_mag = q * S * Cd;
    LocalVec3 v_vec{velocity.vx, velocity.vy, velocity.vz};
    if (state.has_environment_sample) {
        v_vec.x -= state.environment_sample.wind_vx_mps;
        v_vec.y -= state.environment_sample.wind_vy_mps;
    }
    const LocalVec3 v_hat = vec_norm(v_vec);
    const LocalVec3 drag_dir{-v_hat.x, -v_hat.y, -v_hat.z};
    const LocalVec3 body_right = get_body_right(transform.heading, transform.pitch, transform.roll);
    const LocalVec3 lift_dir = vec_norm(vec_cross(v_vec, body_right));
    add_force(forces, drag_mag * drag_dir.x + lift_mag * lift_dir.x, drag_mag * drag_dir.y + lift_mag * lift_dir.y, drag_mag * drag_dir.z + lift_mag * lift_dir.z);

    double b = props.wing_span_m < 1.0 ? 10.0 : props.wing_span_m;
    double c_bar = props.chord_m < 0.1 ? 3.0 : props.chord_m;
    const double V = fmax(10.0, sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy + velocity.vz * velocity.vz));

    double p = state.has_angular_velocity ? state.angular_velocity.p : 0.0;
    double q_rate = state.has_angular_velocity ? state.angular_velocity.q : 0.0;
    double r = state.has_angular_velocity ? state.angular_velocity.r : 0.0;

    const double p_hat = p * b / (2.0 * V);
    const double q_hat = q_rate * c_bar / (2.0 * V);
    const double r_hat = r * b / (2.0 * V);
    const double stall_rel = smoothstep01((alpha_abs - alpha_stall_deg) / fmax(1.0e-6, alpha_deep_deg - alpha_stall_deg));
    const double damp_scale = clamp_value(1.0 - 0.7 * stall_rel, 0.25, 1.0);

    const double Cm = -0.8 * to_radians(alpha) + (-12.0 * damp_scale) * q_hat;
    const double beta = aero.sideslip_angle;
    const double Cl_mom = -0.1 * to_radians(beta) + (-0.45 * damp_scale) * p_hat + 0.1 * r_hat;
    const double Cn_mom = 0.15 * to_radians(beta) + (-0.25 * damp_scale) * r_hat;

    add_torque(forces, q * S * b * Cl_mom, q * S * c_bar * Cm, q * S * b * Cn_mom);
}

__device__ void apply_wheel(
    double x_body_m,
    double Fn_w,
    double steer_rad,
    double mu_brake_w,
    double mu_roll,
    double mu_lat,
    double r,
    double v_long,
    double v_lat_comp,
    double* f_long_sum,
    double* f_lat_sum,
    double* tau_yaw_sum
) {
    if (Fn_w <= 0.0) {
        return;
    }

    const double v_long_w = v_long;
    const double v_lat_w = v_lat_comp + r * x_body_m;
    const double c = cos(steer_rad);
    const double s = sin(steer_rad);
    const double v_long_wf = v_long_w * c + v_lat_w * s;
    const double v_lat_wf = -v_long_w * s + v_lat_w * c;

    const double fx_roll = smooth_coulomb(v_long_wf, mu_roll, Fn_w, kTireVrefRollMps);
    double fx_brake = 0.0;
    if (mu_brake_w > 1.0e-6) {
        fx_brake = smooth_coulomb(v_long_wf, mu_brake_w, Fn_w, kTireVrefBrakeMps);
    }

    const double alpha_max = to_radians(kTireAlphaMaxDeg);
    double alpha = atan2(v_lat_wf, fabs(v_long_wf) + 1.0e-3);
    alpha = clamp_value(alpha, -alpha_max, alpha_max);
    const double C_alpha = kTireCorneringStiffnessPerFn * Fn_w;
    double fy = -C_alpha * alpha;
    const double fy_max = mu_lat * Fn_w;
    fy = fy_max > 0.0 ? clamp_value(fy, -fy_max, fy_max) : 0.0;

    if (mu_brake_w > 1.0e-6 && fy_max > 1.0e-6) {
        const double fx_max = mu_brake_w * Fn_w;
        const double ux = fx_brake / fmax(fx_max, 1.0e-6);
        const double uy = fy / fmax(fy_max, 1.0e-6);
        const double u = sqrt(ux * ux + uy * uy);
        if (u > 1.0) {
            fx_brake /= u;
            fy /= u;
        }
    }

    const double fx_wf = fx_roll + fx_brake;
    const double fy_wf = fy;
    const double fx_b = fx_wf * c - fy_wf * s;
    const double fy_b = fx_wf * s + fy_wf * c;

    *f_long_sum += fx_b;
    *f_lat_sum += fy_b;
    *tau_yaw_sum += x_body_m * fy_b;
}

__device__ void run_ground_contact_stage(AircraftChainState& state) {
    if (!(state.has_force_accumulator && state.has_mass && state.has_ground_state)) {
        return;
    }

    auto& forces = state.force_accumulator;
    const auto& transform = state.transform;
    auto& velocity = state.velocity;
    const auto& mass = state.mass;
    auto& ground = state.ground_state;

    double m = mass_total_kg(mass);
    if (m < 1.0) {
        m = 15000.0;
    }
    const double dt = fmax(1.0e-3, frame_delta_s(state.time_step_s));

    const double terrain_z = state.has_environment_sample ? state.environment_sample.terrain_elevation_m : ground.terrain_elevation;
    ground.terrain_elevation = terrain_z;

    double gear_height = 2.0;
    if (state.has_landing_gear) {
        const double ext = clamp_value(state.landing_gear.extension_state, 0.0, 1.0);
        gear_height = fmax(0.4, state.landing_gear.contact_height_m) * ext;
    }

    const double penetration = gear_height - (transform.z - terrain_z);
    const bool is_touching = penetration > 0.0;
    ground.on_ground = is_touching;
    if (!is_touching) {
        return;
    }

    const double Fn = fmax(0.0, kGroundSpring * penetration - kGroundDamper * velocity.vz);
    add_force(forces, 0.0, 0.0, Fn);

    if (state.has_angular_velocity) {
        const double q_rate = state.angular_velocity.q;
        const double p_rate = state.angular_velocity.p;
        const double pitch_deg = transform.pitch;
        const double roll_deg = transform.roll;
        constexpr double kGroundPitchFreeDeg = 10.0;
        const double kp_pitch = 2000000.0;
        const double kd_pitch = 200000.0;

        if (pitch_deg > kGroundPitchFreeDeg) {
            const double err_deg = pitch_deg - kGroundPitchFreeDeg;
            add_torque(forces, 0.0, -kp_pitch * to_radians(err_deg) - kd_pitch * q_rate, 0.0);
        } else if (fabs(q_rate) > 0.01) {
            add_torque(forces, 0.0, -kd_pitch * q_rate, 0.0);
        }

        const double kp_roll = 2000000.0;
        const double kd_roll = 200000.0;
        if (fabs(roll_deg) > 2.0) {
            add_torque(forces, -kp_roll * to_radians(roll_deg) - kd_roll * p_rate, 0.0, 0.0);
        } else if (fabs(p_rate) > 0.01) {
            add_torque(forces, -kd_roll * p_rate, 0.0, 0.0);
        }
    }

    const double vx = velocity.vx;
    const double vy = velocity.vy;
    const double v_h_sq = vx * vx + vy * vy;
    const PilotAction* pilot = state.has_pilot_action ? &state.pilot_action : nullptr;
    const MovementCommand* cmd = state.has_movement_command ? &state.movement_command : nullptr;
    bool throttle_idle = false;
    double brake_amount = 0.0;
    if (pilot != nullptr && pilot->active) {
        throttle_idle = pilot->throttle < 0.01;
        brake_amount = clamp_value(pilot->brake, 0.0, 1.0);
        if (pilot->brake_left || pilot->brake_right) {
            brake_amount = fmax(brake_amount, 1.0);
        }
    } else if (cmd != nullptr && cmd->active) {
        throttle_idle = cmd->throttle_cmd < 0.01;
        if (throttle_idle) {
            brake_amount = 1.0;
        }
    }

    if (v_h_sq <= 0.001) {
        if (throttle_idle && fabs(vx) < 0.25 && fabs(vy) < 0.25) {
            velocity.vx = 0.0;
            velocity.vy = 0.0;
        }
        return;
    }

    const double v_h = sqrt(v_h_sq);
    const std::uint8_t surface_code = state.has_environment_sample ? state.environment_sample.terrain_surface_code : 3u;

    double gear_mu_roll = state.has_landing_gear ? fmax(0.0, state.landing_gear.rolling_friction_coeff) : 0.02;
    double mu_rolling = gear_mu_roll;
    bool is_offroad = false;
    switch (surface_code) {
        case 0u: mu_rolling = fmax(0.01, gear_mu_roll); break;
        case 1u: mu_rolling = fmax(0.0125, gear_mu_roll * 1.25); break;
        case 2u: mu_rolling = fmax(0.05, gear_mu_roll * 2.5); is_offroad = true; break;
        case 3u: mu_rolling = fmax(0.15, gear_mu_roll * 7.5); is_offroad = true; break;
        case 4u: mu_rolling = fmax(0.80, gear_mu_roll * 20.0); is_offroad = true; break;
        case 5u: mu_rolling = fmax(1.0, gear_mu_roll * 25.0); is_offroad = true; break;
        default: mu_rolling = fmax(0.10, gear_mu_roll * 5.0); is_offroad = true; break;
    }

    if (state.has_gear_state) {
        auto& gear = state.gear_state;
        gear.on_runway = !is_offroad;
        gear.stress_rate = 0.0;
        if (gear.gear_down && !gear.collapsed && is_offroad && v_h > 40.0) {
            double severity = 1.0;
            if (surface_code == 2u) {
                severity = 0.3;
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
                if (state.has_health) {
                    state.health.current_hp = 0.0;
                }
            }
        }
    } else if (is_offroad && v_h > 40.0) {
        mu_rolling *= 5.0;
    }

    double nws_steer_rad = 0.0;
    if (pilot != nullptr && pilot->active) {
        double yaw_cmd = pilot->rudder;
        if (state.has_control_law_state) {
            yaw_cmd = -state.control_law_state.stick_yaw_filt;
        }
        double steer = clamp_value(yaw_cmd, -1.0, 1.0) * kNwsInputScaler;
        if (fabs(steer) < kNwsDeadzone) {
            steer = 0.0;
        }
        if (fabs(steer) > 1.0e-6) {
            bool gear_extended = !state.has_landing_gear || state.landing_gear.extension_state >= 0.5;
            if (gear_extended) {
                const double speed_factor = clamp_value(v_h / kNwsMinSpeedMps, 0.0, 1.0);
                double fade = 1.0;
                if (v_h >= kNwsFadeStartMps) {
                    double t = (v_h - kNwsFadeStartMps) / (kNwsFadeEndMps - kNwsFadeStartMps);
                    t = clamp_value(t, 0.0, 1.0);
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
        brake_amount = fmax(brake_amount, 1.0);
    }

    const double mu_roll = mu_rolling;
    const double mu_brake = clamp_value(brake_amount, 0.0, 1.0) * kMuBraking;
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
    mu_lat = fmax(mu_lat, mu_roll);

    const double hdg_rad = to_radians(transform.heading);
    const double fwd_x = sin(hdg_rad);
    const double fwd_y = cos(hdg_rad);
    const double left_x = -cos(hdg_rad);
    const double left_y = sin(hdg_rad);
    const double v_long = vx * fwd_x + vy * fwd_y;
    const double v_lat_comp = vx * left_x + vy * left_y;
    const double Fn_nose = Fn * kWheelFnNoseFrac;
    const double Fn_main = Fn * kWheelFnMainFrac;
    const double r = state.has_angular_velocity ? state.angular_velocity.r : 0.0;

    double f_long_sum = 0.0;
    double f_lat_sum = 0.0;
    double tau_yaw = 0.0;
    apply_wheel(kWheelContactNoseX, Fn_nose, nws_steer_rad, 0.0, mu_roll, mu_lat, r, v_long, v_lat_comp, &f_long_sum, &f_lat_sum, &tau_yaw);
    apply_wheel(kWheelContactMainX, Fn_main, 0.0, mu_brake, mu_roll, mu_lat, r, v_long, v_lat_comp, &f_long_sum, &f_lat_sum, &tau_yaw);

    add_force(forces, f_long_sum * fwd_x + f_lat_sum * left_x, f_long_sum * fwd_y + f_lat_sum * left_y, 0.0);
    add_torque(forces, 0.0, 0.0, tau_yaw);

    if (throttle_idle && brake_amount > 0.2 && v_h < 3.0) {
        const double hold_force_max = fmax(0.0, 1.20 * Fn);
        const double hold_force_need = (m * v_h) / dt;
        const double hold_force = fmin(hold_force_need, hold_force_max);
        if (hold_force > 0.0 && v_h > 1.0e-6) {
            const double inv_v = 1.0 / v_h;
            add_force(forces, -vx * inv_v * hold_force, -vy * inv_v * hold_force, 0.0);
        }
        if (v_h < 0.25) {
            velocity.vx = 0.0;
            velocity.vy = 0.0;
        }
    }
}

__device__ __forceinline__ double inst_normalize_heading_deg(double heading_deg) {
    return isfinite(heading_deg) ? wrap_360(heading_deg) : 0.0;
}

__device__ __forceinline__ bool inst_is_runway_like_surface_code(std::uint8_t surface_code) {
    return surface_code == 0u || surface_code == 1u;
}

__device__ __forceinline__ double inst_ground_track_deg_from_velocity(const Velocity& velocity, double fallback_heading_deg) {
    const double horiz_speed = hypot(velocity.vx, velocity.vy);
    if (horiz_speed <= 1.0) {
        return inst_normalize_heading_deg(fallback_heading_deg);
    }
    return inst_normalize_heading_deg(atan2(velocity.vx, velocity.vy) * 180.0 / kPi);
}

__device__ __forceinline__ double inst_canonicalize_ground_track_deg(double value) {
    constexpr double kGroundTrackCanonicalQuantumDeg = 0x1p-32;
    if (!isfinite(value)) {
        return 0.0;
    }
    const double rounded = nearbyint(value / kGroundTrackCanonicalQuantumDeg) *
        kGroundTrackCanonicalQuantumDeg;
    return fabs(rounded) <= (kGroundTrackCanonicalQuantumDeg * 0.5) ? 0.0 : rounded;
}

__device__ __forceinline__ double inst_mission_heading_bug(
    const MissionCommand& mission,
    const Transform& transform,
    const Velocity& velocity,
    const EnvironmentSample* env_sample
) {
    const double fallback_heading_deg = inst_ground_track_deg_from_velocity(velocity, transform.heading);
    if (mission.command_code == 4 && env_sample != nullptr &&
        inst_is_runway_like_surface_code(env_sample->terrain_surface_code) &&
        isfinite(env_sample->runway_heading_deg)) {
        return inst_normalize_heading_deg(env_sample->runway_heading_deg);
    }
    if (isfinite(mission.cmd_heading_deg)) {
        return inst_normalize_heading_deg(mission.cmd_heading_deg);
    }
    return fallback_heading_deg;
}

__device__ __forceinline__ double inst_mission_alt_bug(const MissionCommand& mission, double fallback_alt_m) {
    return isfinite(mission.cmd_altitude_m) ? mission.cmd_altitude_m : fallback_alt_m;
}

__device__ __forceinline__ double inst_mission_speed_bug(const MissionCommand& mission, double fallback_speed_mps) {
    return isfinite(mission.cmd_speed_mps) ? mission.cmd_speed_mps : fallback_speed_mps;
}

__device__ __forceinline__ double default_terrain_elevation_m(double x, double y) {
    constexpr double kPeakX = 25000.0;
    constexpr double kPeakY = 25000.0;
    constexpr double kPeakH = 2000.0;
    constexpr double kSigmaSq = 25000000.0;
    const double d2 = (x - kPeakX) * (x - kPeakX) + (y - kPeakY) * (y - kPeakY);
    return kPeakH * exp(-d2 / (2.0 * kSigmaSq));
}

__device__ __forceinline__ double canonicalize_environment_scalar(double value) {
    if (!isfinite(value) || kEnvironmentScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (fabs(value) <= (kEnvironmentScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = nearbyint(value / kEnvironmentScalarCanonicalQuantum) *
        kEnvironmentScalarCanonicalQuantum;
    return fabs(rounded) <= (kEnvironmentScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

__device__ void refresh_environment_sample_from_transform(AircraftChainState& state) {
    if (!state.has_environment_sample) {
        return;
    }
    auto& env_sample = state.environment_sample;
    const auto& transform = state.transform;
    env_sample.terrain_elevation_m = canonicalize_environment_scalar(
        default_terrain_elevation_m(transform.x, transform.y)
    );

    double dir_to_deg = fmod(kBaseWindDirFromDeg + 180.0, 360.0);
    if (dir_to_deg < 0.0) {
        dir_to_deg += 360.0;
    }
    const double dir_to_rad = deg_to_rad(dir_to_deg);
    const double ux = sin(dir_to_rad);
    const double uy = cos(dir_to_rad);
    const double alt_km = fmax(0.0, transform.z) / 1000.0;
    double speed_mps = kBaseWindSpeedMps + kWindShearMpsPerKm * alt_km;
    if (speed_mps < 0.0) {
        speed_mps = 0.0;
    }
    env_sample.wind_vx_mps = ux * speed_mps;
    env_sample.wind_vy_mps = uy * speed_mps;
}

__device__ LocalVec3 project_forces_to_body(const LocalVec3& f_world, const Transform& transform) {
    const double psi = deg_to_rad(90.0 - transform.heading);
    const double theta = deg_to_rad(transform.pitch);
    const double c_psi = cos(psi);
    const double s_psi = sin(psi);
    const double c_theta = cos(theta);
    const double s_theta = sin(theta);

    const double x1 = f_world.x * c_psi + f_world.y * s_psi;
    const double y1 = -f_world.x * s_psi + f_world.y * c_psi;
    const double z1 = f_world.z;

    const double x2 = x1 * c_theta + z1 * s_theta;
    const double y2 = y1;
    const double z2 = -x1 * s_theta + z1 * c_theta;

    const double phi = deg_to_rad(transform.roll);
    const double c_phi = cos(phi);
    const double s_phi = sin(phi);
    return {x2, 0.0, -y2 * s_phi + z2 * c_phi};
}

__device__ void run_rotational_integrate_stage(AircraftChainState& state, const RotationalParams& prm) {
    if (!(state.has_angular_velocity && state.has_inertia && state.has_force_accumulator)) {
        return;
    }

    auto& transform = state.transform;
    auto& ang_vel = state.angular_velocity;
    const auto& inertia = state.inertia;
    const auto& forces = state.force_accumulator;

    double dt = frame_delta_s(state.time_step_s);
    if (dt <= 0.0) {
        dt = 0.05;
    }

    double p = clamp_finite(ang_vel.p, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);
    double q = clamp_finite(ang_vel.q, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);
    double r = clamp_finite(ang_vel.r, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);

    const double L = clamp_finite(forces.torque_roll, -prm.max_torque_nm, prm.max_torque_nm);
    const double M = clamp_finite(forces.torque_pitch, -prm.max_torque_nm, prm.max_torque_nm);
    const double N = clamp_finite(forces.torque_yaw, -prm.max_torque_nm, prm.max_torque_nm);

    const double p_dot = (L - (inertia.izz - inertia.iyy) * q * r) / inertia.ixx;
    const double q_dot = (M - (inertia.ixx - inertia.izz) * p * r) / inertia.iyy;
    const double r_dot = (N - (inertia.iyy - inertia.ixx) * p * q) / inertia.izz;

    p += clamp_finite(p_dot, -prm.max_ang_accel_rad_s2, prm.max_ang_accel_rad_s2) * dt;
    q += clamp_finite(q_dot, -prm.max_ang_accel_rad_s2, prm.max_ang_accel_rad_s2) * dt;
    r += clamp_finite(r_dot, -prm.max_ang_accel_rad_s2, prm.max_ang_accel_rad_s2) * dt;

    ang_vel.p = clamp_finite(p, -prm.max_rate_rad_s, prm.max_rate_rad_s);
    ang_vel.q = clamp_finite(q, -prm.max_rate_rad_s, prm.max_rate_rad_s);
    ang_vel.r = clamp_finite(r, -prm.max_rate_rad_s, prm.max_rate_rad_s);

    p = ang_vel.p;
    q = ang_vel.q;
    r = ang_vel.r;

    const double phi = deg_to_rad(transform.roll);
    const double theta = deg_to_rad(transform.pitch);
    const double c_phi = cos(phi);
    const double s_phi = sin(phi);
    double c_theta = cos(theta);
    const double s_theta = sin(theta);

    if (fabs(c_theta) < prm.min_abs_cos_theta) {
        c_theta = copysign(prm.min_abs_cos_theta, c_theta);
    }
    const double t_theta = s_theta / c_theta;
    const double sec_theta = 1.0 / c_theta;

    const double d_phi = p + (q * s_phi + r * c_phi) * t_theta;
    const double d_theta = q * c_phi - r * s_phi;
    const double d_psi = (q * s_phi + r * c_phi) * sec_theta;

    transform.roll += rad_to_deg(d_phi) * dt;
    transform.pitch += rad_to_deg(d_theta) * dt;
    transform.heading -= rad_to_deg(d_psi) * dt;

    transform.roll = fmod(transform.roll + 180.0, 360.0);
    if (transform.roll < 0.0) {
        transform.roll += 360.0;
    }
    transform.roll -= 180.0;
    transform.pitch = clamp_value(transform.pitch, -prm.pitch_limit_deg, prm.pitch_limit_deg);
    transform.heading = wrap_360(transform.heading);
}

__device__ void run_leapfrog_integrate_stage(AircraftChainState& state) {
    if (!(state.has_force_accumulator && state.has_mass)) {
        return;
    }

    auto& transform = state.transform;
    auto& velocity = state.velocity;
    const auto& forces = state.force_accumulator;

    double dt = frame_delta_s(state.time_step_s);
    if (dt <= 0.0) {
        dt = 0.05;
    }

    double m = mass_total_kg(state.mass);
    if (m < 1.0) {
        m = 15000.0;
    }

    const double ax = forces.fx / m;
    const double ay = forces.fy / m;
    const double az = forces.fz / m;

    const double vx_half = velocity.vx + ax * dt * 0.5;
    const double vy_half = velocity.vy + ay * dt * 0.5;
    const double vz_half = velocity.vz + az * dt * 0.5;

    transform.x += vx_half * dt;
    transform.y += vy_half * dt;
    transform.z += vz_half * dt;

    velocity.vx = vx_half + ax * dt * 0.5;
    velocity.vy = vy_half + ay * dt * 0.5;
    velocity.vz = vz_half + az * dt * 0.5;

    if (transform.z < -5.0) {
        transform.z = -5.0;
        if (velocity.vz < 0.0) {
            velocity.vz = 0.0;
        }
    }
}

__device__ void run_navigation_system_stage(AircraftChainState& state) {
    if (!state.has_egi) {
        return;
    }

    auto& egi = state.egi;
    const auto& trans = state.transform;
    const auto& vel = state.velocity;
    const double dt = frame_delta_s(state.time_step_s);

    egi.drift_lat_m = 0.0;
    egi.drift_lon_m = 0.0;
    egi.drift_alt_m = 0.0;

    if (egi.gps_available) {
        egi.time_since_last_gps_fix = 0.0;
        egi.position_uncertainty_m = fmin(egi.position_uncertainty_m, 5.0);
    } else {
        egi.time_since_last_gps_fix += dt;
        egi.position_uncertainty_m = fmax(egi.position_uncertainty_m, 50.0);
    }

    egi.lat_deg = kRefLat + (trans.y / kMetersPerDegLat);
    egi.lon_deg = kRefLon + (trans.x / kMetersPerDegLon);
    egi.vn_mps = vel.vy;
    egi.ve_mps = vel.vx;
    egi.vd_mps = -vel.vz;
    egi.alt_baro_m = trans.z;
    egi.alt_radar_m = fmax(0.0, trans.z);
    egi.heading_deg = wrap_360(trans.heading);
    egi.pitch_deg = trans.pitch;
    egi.roll_deg = trans.roll;
}

__device__ void run_update_instruments_stage(AircraftChainState& state) {
    if (!(state.has_instrument_state && state.has_aero_state && state.has_force_accumulator && state.has_mass &&
          state.has_propulsion && state.has_angular_velocity)) {
        return;
    }

    auto& inst = state.instrument_state;
    const auto& transform = state.transform;
    const auto& velocity = state.velocity;
    const auto& aero = state.aero_state;
    const auto& forces = state.force_accumulator;
    const auto& propulsion = state.propulsion;
    const auto& ang_vel = state.angular_velocity;
    const auto* env_sample = state.has_environment_sample ? &state.environment_sample : nullptr;

    inst.alt_baro_m = transform.z;
    const double terrain_z = env_sample != nullptr ? env_sample->terrain_elevation_m : 0.0;
    inst.alt_radar_m = fmax(0.0, transform.z - terrain_z);
    inst.pitch_deg = transform.pitch;
    inst.roll_deg = transform.roll;
    inst.heading_deg = transform.heading;
    inst.mach = aero.mach_number;
    inst.ias_mps = sqrt(2.0 * aero.dynamic_pressure / 1.225);
    inst.vvi_mps = velocity.vz;
    inst.aoa_deg = aero.angle_of_attack;
    inst.beta_deg = aero.sideslip_angle;
    inst.p_deg_s = rad_to_deg(ang_vel.p);
    inst.q_deg_s = rad_to_deg(ang_vel.q);
    inst.r_deg_s = rad_to_deg(ang_vel.r);

    double total_mass = mass_total_kg(state.mass);
    if (total_mass < 1.0) {
        total_mass = 1.0;
    }
    const LocalVec3 f_contact{forces.fx, forces.fy, forces.fz + (total_mass * kGravity)};
    const LocalVec3 f_body = project_forces_to_body(f_contact, transform);
    inst.g_load_normal = f_body.z / (total_mass * kGravity);
    inst.g_load_axial = f_body.x / (total_mass * kGravity);

    const double tsfc = propulsion.afterburner_active ? 0.25 : 0.1;
    inst.fuel_flow_kg_h = fabs(propulsion.current_thrust_n) * tsfc;
    inst.engine_rpm_pct = propulsion.afterburner_active
        ? 100.0 + (propulsion.current_thrust_n / (propulsion.ab_thrust_n + 1e-6)) * 10.0
        : (propulsion.current_thrust_n / (propulsion.mil_thrust_n + 1e-6)) * 100.0;
    inst.engine_temp_c = 600.0 + inst.engine_rpm_pct * 3.0;

    if (state.has_fuel_system) {
        inst.fuel_internal_kg = state.fuel_system.internal_fuel_kg;
        inst.fuel_external_kg = state.fuel_system.external_fuel_kg;
    } else {
        inst.fuel_internal_kg = state.mass.fuel_mass_kg;
        inst.fuel_external_kg = 0.0;
    }

    inst.gear_pos = state.has_landing_gear ? static_cast<float>(clamp_value(state.landing_gear.extension_state, 0.0, 1.0)) : 0.0f;

    if (state.has_pilot_action && state.pilot_action.active) {
        const auto& pilot = state.pilot_action;
        inst.throttle_pos = clamp_value(pilot.throttle, 0.0, 1.0);
        inst.flaps_pos = clamp_value(pilot.flaps, 0.0f, 1.0f);
        inst.speedbrake_pos = clamp_value(pilot.speedbrake, 0.0f, 1.0f);
        inst.master_arm = pilot.master_arm;
        inst.weapon_selected = pilot.weapon_select_id;
    } else if (state.has_movement_command && state.movement_command.active) {
        inst.throttle_pos = clamp_value(state.movement_command.throttle_cmd, 0.0, 1.0);
        inst.flaps_pos = 0.0f;
        inst.speedbrake_pos = 0.0f;
        inst.master_arm = false;
        inst.weapon_selected = 0;
    } else {
        inst.throttle_pos = 0.0;
        inst.flaps_pos = 0.0f;
        inst.speedbrake_pos = 0.0f;
        inst.master_arm = false;
        inst.weapon_selected = 0;
    }

    double temperature_k = 288.15;
    double air_density = 1.225;
    double speed_of_sound = 340.29;
    compute_standard_atmosphere_tail(transform.z, &temperature_k, &air_density, &speed_of_sound);
    (void)air_density;
    (void)speed_of_sound;
    inst.oat_c = temperature_k - 273.15;
    if (env_sample != nullptr) {
        const double wx = env_sample->wind_vx_mps;
        const double wy = env_sample->wind_vy_mps;
        inst.wind_speed_mps = sqrt(wx * wx + wy * wy);
        double wind_to_deg = atan2(wx, wy) * 180.0 / kPi;
        double wind_from_deg = wrap_360(wind_to_deg + 180.0);
        inst.wind_dir_deg = wind_from_deg;
    } else {
        inst.wind_speed_mps = 0.0;
        inst.wind_dir_deg = 0.0;
    }

    if (state.has_mission_command && state.mission_command.active) {
        inst.cmd_heading_deg = inst_mission_heading_bug(state.mission_command, transform, velocity, env_sample);
        inst.cmd_alt_m = inst_mission_alt_bug(state.mission_command, inst.alt_baro_m);
        inst.cmd_speed_mps = inst_mission_speed_bug(state.mission_command, inst.ias_mps);
    } else {
        inst.cmd_heading_deg = inst.heading_deg;
        inst.cmd_alt_m = inst.alt_baro_m;
        inst.cmd_speed_mps = inst.ias_mps;
    }

    inst.rwr_active = state.has_rwr_summary && state.rwr_summary.detected_count > 0;
    inst.missiles_remaining = state.has_ammo ? state.ammo.missiles_remaining : 0;

    if (state.has_egi) {
        const auto& egi = state.egi;
        inst.lat_deg = egi.lat_deg;
        inst.lon_deg = egi.lon_deg;
        inst.vn_mps = egi.vn_mps;
        inst.ve_mps = egi.ve_mps;
        inst.vd_mps = egi.vd_mps;
        inst.ground_speed_mps = sqrt(egi.vn_mps * egi.vn_mps + egi.ve_mps * egi.ve_mps);
        if (inst.ground_speed_mps > 0.1) {
            inst.ground_track_deg = atan2(egi.ve_mps, egi.vn_mps) * 180.0 / kPi;
            if (inst.ground_track_deg < 0.0) {
                inst.ground_track_deg += 360.0;
            }
            inst.ground_track_deg = inst_canonicalize_ground_track_deg(inst.ground_track_deg);
        } else {
            inst.ground_track_deg = inst.heading_deg;
        }
        inst.gps_available = egi.gps_available;
        inst.position_uncertainty_m = egi.position_uncertainty_m;
    } else {
        inst.lat_deg = 0.0;
        inst.lon_deg = 0.0;
        inst.vn_mps = 0.0;
        inst.ve_mps = 0.0;
        inst.vd_mps = 0.0;
        inst.ground_speed_mps = 0.0;
        inst.ground_track_deg = inst.heading_deg;
        inst.gps_available = false;
        inst.position_uncertainty_m = 1000.0;
    }

    if (state.has_gear_state) {
        inst.gear_stress = state.gear_state.stress;
        inst.gear_collapsed = state.gear_state.collapsed;
        inst.on_runway = state.gear_state.on_runway;
    } else {
        inst.gear_stress = 0.0;
        inst.gear_collapsed = false;
        inst.on_runway = true;
    }
}

__device__ void run_fuel_consumption_stage(AircraftChainState& state) {
    if (!state.has_fuel_system) {
        return;
    }

    auto& fuel = state.fuel_system;
    const double dt = frame_delta_s(state.time_step_s);

    double throttle = 0.0;
    bool throttle_set = false;
    if (state.has_pilot_action && state.pilot_action.active) {
        throttle = clamp_value(state.pilot_action.throttle, 0.0, 1.0);
        throttle_set = true;
    }
    if (!throttle_set && state.has_movement_command && state.movement_command.active) {
        throttle = clamp_value(state.movement_command.throttle_cmd, 0.0, 1.0);
        throttle_set = true;
    }
    if (!throttle_set && state.has_action_command && state.action_command.active) {
        throttle = clamp_value((state.action_command.accel_cmd + 1.0) * 0.5, 0.0, 1.0);
        throttle_set = true;
    }

    constexpr double kAfterburnerThreshold = 0.9;
    if (throttle > kAfterburnerThreshold) {
        fuel.current_flow_rate = fuel.mil_power_flow_rate * fuel.ab_flow_rate_multiplier;
        fuel.afterburner_active = true;
    } else {
        fuel.current_flow_rate = fuel.mil_power_flow_rate * (0.1 + 0.9 * (throttle / kAfterburnerThreshold));
        fuel.afterburner_active = false;
    }

    double fuel_consumed = fuel.current_flow_rate * dt;
    if (fuel.external_fuel_kg > 0.0) {
        if (fuel.external_fuel_kg >= fuel_consumed) {
            fuel.external_fuel_kg -= fuel_consumed;
            fuel_consumed = 0.0;
        } else {
            fuel_consumed -= fuel.external_fuel_kg;
            fuel.external_fuel_kg = 0.0;
        }
    }
    if (fuel_consumed > 0.0) {
        fuel.internal_fuel_kg -= fuel_consumed;
        if (fuel.internal_fuel_kg < 0.0) {
            fuel.internal_fuel_kg = 0.0;
        }
    }
}

__device__ void run_mass_update_stage(AircraftChainState& state) {
    if (!(state.has_fuel_system && state.has_mass && state.has_mass_properties)) {
        return;
    }
    const double fuel_kg = fmax(0.0, state.fuel_system.internal_fuel_kg) + fmax(0.0, state.fuel_system.external_fuel_kg);
    state.mass.fuel_mass_kg = fuel_kg;
    state.mass_properties.current_total_mass_kg = state.mass_properties.empty_mass_kg + fuel_kg;
}

}  // namespace

#ifndef EF_AIRCRAFT_CHAIN_CUDA_DEVICE_ONLY

__global__ void exact_world_step_aircraft_chain_cuda_kernel(
    AircraftChainState* states,
    std::size_t count,
    int fbw_mode_code,
    RotationalParams params
) {
    const std::size_t idx = static_cast<std::size_t>(blockIdx.x) * static_cast<std::size_t>(blockDim.x) +
        static_cast<std::size_t>(threadIdx.x);
    if (idx >= count || states == nullptr) {
        return;
    }

    auto& state = states[idx];
    run_flight_control_stage(state, static_cast<FbwProtectionMode>(fbw_mode_code));
    run_clear_forces_stage(state);
    run_compute_aero_state_stage(state);
    run_compute_forces_stage(state);
    run_compute_aerodynamics_stage(state);
    run_ground_contact_stage(state);
    run_rotational_integrate_stage(state, params);
    run_leapfrog_integrate_stage(state);
    refresh_environment_sample_from_transform(state);
    run_navigation_system_stage(state);
    run_update_instruments_stage(state);
    run_fuel_consumption_stage(state);
    run_mass_update_stage(state);
}

namespace gpu::detail {

bool step_exact_world_step_aircraft_chain_cuda_inplace(
    std::vector<aircraft_chain_cuda::ExactWorldStepAircraftChainCudaState>& states,
    ExactWorldStepAircraftChainCudaStats* stats
) {
    if (stats != nullptr) {
        stats->state_count = states.size();
        stats->used_cuda = false;
        stats->host_to_device_ms = 0.0;
        stats->kernel_ms = 0.0;
        stats->device_to_host_ms = 0.0;
    }
    if (states.empty()) {
        return true;
    }

    AircraftChainState* device_states = nullptr;
    const auto h2d_start = std::chrono::steady_clock::now();
    if (cudaMalloc(&device_states, states.size() * sizeof(AircraftChainState)) != cudaSuccess) {
        free_device_ptr(device_states);
        return false;
    }
    if (cudaMemcpy(device_states, states.data(), states.size() * sizeof(AircraftChainState), cudaMemcpyHostToDevice) != cudaSuccess) {
        free_device_ptr(device_states);
        return false;
    }
    const auto h2d_end = std::chrono::steady_clock::now();

    const int fbw_mode_code = static_cast<int>(get_fbw_protection_mode());
    const RotationalParams params = rotational_params_host();
    const auto kernel_start = std::chrono::steady_clock::now();
    const int block_size = 128;
    const int grid_size = static_cast<int>((states.size() + static_cast<std::size_t>(block_size) - 1u) /
                                           static_cast<std::size_t>(block_size));
    exact_world_step_aircraft_chain_cuda_kernel<<<grid_size, block_size>>>(device_states, states.size(), fbw_mode_code, params);
    if (cudaGetLastError() != cudaSuccess || cudaDeviceSynchronize() != cudaSuccess) {
        free_device_ptr(device_states);
        return false;
    }
    const auto kernel_end = std::chrono::steady_clock::now();

    const auto d2h_start = std::chrono::steady_clock::now();
    if (cudaMemcpy(states.data(), device_states, states.size() * sizeof(AircraftChainState), cudaMemcpyDeviceToHost) != cudaSuccess) {
        free_device_ptr(device_states);
        return false;
    }
    const auto d2h_end = std::chrono::steady_clock::now();
    free_device_ptr(device_states);

    if (stats != nullptr) {
        stats->used_cuda = true;
        stats->host_to_device_ms = std::chrono::duration<double, std::milli>(h2d_end - h2d_start).count();
        stats->kernel_ms = std::chrono::duration<double, std::milli>(kernel_end - kernel_start).count();
        stats->device_to_host_ms = std::chrono::duration<double, std::milli>(d2h_end - d2h_start).count();
    }
    return true;
}

}  // namespace gpu::detail

#endif  // EF_AIRCRAFT_CHAIN_CUDA_DEVICE_ONLY
