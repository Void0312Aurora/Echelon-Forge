#include "gpu/gpu_exact_world_step_aircraft_tail_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_aircraft_tail_cuda_runtime_types.h"

#include <cuda_runtime_api.h>

#include <chrono>
#include <cmath>
#include <cstdlib>
#include <vector>

namespace {

using Transform = gpu::aircraft_tail_cuda::Transform;
using Velocity = gpu::aircraft_tail_cuda::Velocity;
using AngularVelocity = gpu::aircraft_tail_cuda::AngularVelocity;
using ForceAccumulator = gpu::aircraft_tail_cuda::ForceAccumulator;
using Mass = gpu::aircraft_tail_cuda::Mass;
using Inertia = gpu::aircraft_tail_cuda::Inertia;
using AeroState = gpu::aircraft_tail_cuda::AeroState;
using Propulsion = gpu::aircraft_tail_cuda::Propulsion;
using FuelSystem = gpu::aircraft_tail_cuda::FuelSystem;
using MassProperties = gpu::aircraft_tail_cuda::MassProperties;
using InstrumentState = gpu::aircraft_tail_cuda::InstrumentState;
using EGI = gpu::aircraft_tail_cuda::EGI;
using PilotAction = gpu::aircraft_tail_cuda::PilotAction;
using MovementCommand = gpu::aircraft_tail_cuda::MovementCommand;
using ActionCommand = gpu::aircraft_tail_cuda::ActionCommand;
using MissionCommand = gpu::aircraft_tail_cuda::MissionCommand;
using LandingGear = gpu::aircraft_tail_cuda::LandingGear;
using GearState = gpu::aircraft_tail_cuda::GearState;
using Ammo = gpu::aircraft_tail_cuda::Ammo;
using RwrSummary = gpu::aircraft_tail_cuda::RwrSummary;
using EnvironmentSample = gpu::aircraft_tail_cuda::EnvironmentSample;
using AircraftTailState = gpu::aircraft_tail_cuda::ExactWorldStepAircraftTailCudaState;

constexpr double kPi = 3.14159265358979323846;
constexpr double kRefLat = 36.24;
constexpr double kRefLon = -115.05;
constexpr double kMetersPerDegLat = 111132.954;
constexpr double kMetersPerDegLon = 90000.0;
constexpr double kBaseWindSpeedMps = 10.0;
constexpr double kBaseWindDirFromDeg = 270.0;
constexpr double kWindShearMpsPerKm = 4.0;
constexpr double kEnvironmentScalarCanonicalQuantum = 0x1p-76;

struct RotationalParams {
    double max_rate_cross_rad_s;
    double max_torque_nm;
    double max_ang_accel_rad_s2;
    double max_rate_rad_s;
    double min_abs_cos_theta;
    double pitch_limit_deg;
};

template <typename T>
void free_device_ptr(T*& ptr) {
    if (ptr != nullptr) {
        cudaFree(ptr);
        ptr = nullptr;
    }
}

template <typename T>
__host__ __device__ T clamp_value(T value, T lo, T hi) {
    return value < lo ? lo : (value > hi ? hi : value);
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

__device__ __forceinline__ double deg_to_rad(double deg) { return deg * kPi / 180.0; }
__device__ __forceinline__ double rad_to_deg(double rad) { return rad * 180.0 / kPi; }
__device__ __forceinline__ double frame_delta_s(double time_step_s) { return static_cast<double>(static_cast<float>(time_step_s)); }

__device__ __forceinline__ double clamp_finite(double value, double lo, double hi) {
    if (!isfinite(value)) {
        return 0.0;
    }
    return clamp_value(value, lo, hi);
}

__device__ __forceinline__ double wrap_360(double deg) {
    deg = fmod(deg, 360.0);
    if (deg < 0.0) {
        deg += 360.0;
    }
    return deg;
}

__device__ __forceinline__ double inst_normalize_heading_deg(double heading_deg) {
    if (!isfinite(heading_deg)) {
        return 0.0;
    }
    return wrap_360(heading_deg);
}

__device__ __forceinline__ bool inst_is_runway_like_surface_code(std::uint8_t surface_code) {
    return surface_code == 0u || surface_code == 1u;
}

__device__ __forceinline__ double mass_total_kg(const Mass& mass) {
    return mass.empty_mass_kg + mass.fuel_mass_kg + mass.stores_mass_kg;
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
    if (mission.command_code == 4 && env_sample != nullptr) {
        if (inst_is_runway_like_surface_code(env_sample->terrain_surface_code) && isfinite(env_sample->runway_heading_deg)) {
            return inst_normalize_heading_deg(env_sample->runway_heading_deg);
        }
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

__device__ __forceinline__ void compute_standard_atmosphere(
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

__device__ void refresh_environment_sample_from_transform(AircraftTailState& state) {
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

struct LocalVec3 {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

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

__device__ void run_rotational_integrate_stage(AircraftTailState& state, const RotationalParams& prm) {
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

    const double Ixx = inertia.ixx;
    const double Iyy = inertia.iyy;
    const double Izz = inertia.izz;

    double p = clamp_finite(ang_vel.p, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);
    double q = clamp_finite(ang_vel.q, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);
    double r = clamp_finite(ang_vel.r, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);

    const double L = clamp_finite(forces.torque_roll, -prm.max_torque_nm, prm.max_torque_nm);
    const double M = clamp_finite(forces.torque_pitch, -prm.max_torque_nm, prm.max_torque_nm);
    const double N = clamp_finite(forces.torque_yaw, -prm.max_torque_nm, prm.max_torque_nm);

    const double p_dot = (L - (Izz - Iyy) * q * r) / Ixx;
    const double q_dot = (M - (Ixx - Izz) * p * r) / Iyy;
    const double r_dot = (N - (Iyy - Ixx) * p * q) / Izz;

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

__device__ void run_leapfrog_integrate_stage(AircraftTailState& state) {
    if (!(state.has_force_accumulator && state.has_mass)) {
        return;
    }

    auto& transform = state.transform;
    auto& velocity = state.velocity;
    const auto& forces = state.force_accumulator;
    const auto& mass = state.mass;

    double dt = frame_delta_s(state.time_step_s);
    if (dt <= 0.0) {
        dt = 0.05;
    }

    double m = mass_total_kg(mass);
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

__device__ void run_navigation_system_stage(AircraftTailState& state) {
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

__device__ void run_update_instruments_stage(AircraftTailState& state) {
    if (!(state.has_instrument_state && state.has_aero_state && state.has_force_accumulator && state.has_mass &&
          state.has_propulsion && state.has_angular_velocity)) {
        return;
    }

    auto& inst = state.instrument_state;
    const auto& transform = state.transform;
    const auto& velocity = state.velocity;
    const auto& aero = state.aero_state;
    const auto& forces = state.force_accumulator;
    const auto& mass = state.mass;
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

    double total_mass = mass_total_kg(mass);
    if (total_mass < 1.0) {
        total_mass = 1.0;
    }
    const LocalVec3 f_contact{forces.fx, forces.fy, forces.fz + (total_mass * 9.80665)};
    const LocalVec3 f_body = project_forces_to_body(f_contact, transform);
    inst.g_load_normal = f_body.z / (total_mass * 9.80665);
    inst.g_load_axial = f_body.x / (total_mass * 9.80665);

    const double tsfc = propulsion.afterburner_active ? 0.25 : 0.1;
    inst.fuel_flow_kg_h = fabs(propulsion.current_thrust_n) * tsfc;
    if (propulsion.afterburner_active) {
        inst.engine_rpm_pct = 100.0 + (propulsion.current_thrust_n / (propulsion.ab_thrust_n + 1e-6)) * 10.0;
    } else {
        inst.engine_rpm_pct = (propulsion.current_thrust_n / (propulsion.mil_thrust_n + 1e-6)) * 100.0;
    }
    inst.engine_temp_c = 600.0 + inst.engine_rpm_pct * 3.0;

    if (state.has_fuel_system) {
        inst.fuel_internal_kg = state.fuel_system.internal_fuel_kg;
        inst.fuel_external_kg = state.fuel_system.external_fuel_kg;
    } else {
        inst.fuel_internal_kg = mass.fuel_mass_kg;
        inst.fuel_external_kg = 0.0;
    }

    if (state.has_landing_gear) {
        inst.gear_pos = static_cast<float>(clamp_value(state.landing_gear.extension_state, 0.0, 1.0));
    } else {
        inst.gear_pos = 0.0f;
    }

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
    compute_standard_atmosphere(transform.z, &temperature_k, &air_density, &speed_of_sound);
    (void)air_density;
    (void)speed_of_sound;
    inst.oat_c = temperature_k - 273.15;
    if (env_sample != nullptr) {
        const double wx = env_sample->wind_vx_mps;
        const double wy = env_sample->wind_vy_mps;
        inst.wind_speed_mps = sqrt(wx * wx + wy * wy);
        double wind_to_deg = atan2(wx, wy) * 180.0 / kPi;
        double wind_from_deg = wind_to_deg + 180.0;
        while (wind_from_deg < 0.0) {
            wind_from_deg += 360.0;
        }
        while (wind_from_deg >= 360.0) {
            wind_from_deg -= 360.0;
        }
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

__device__ void run_fuel_consumption_stage(AircraftTailState& state) {
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

__device__ void run_mass_update_stage(AircraftTailState& state) {
    if (!(state.has_fuel_system && state.has_mass && state.has_mass_properties)) {
        return;
    }

    auto& mass_properties = state.mass_properties;
    auto& rigid_mass = state.mass;
    const auto& fuel = state.fuel_system;

    const double fuel_kg = fmax(0.0, fuel.internal_fuel_kg) + fmax(0.0, fuel.external_fuel_kg);
    rigid_mass.fuel_mass_kg = fuel_kg;
    mass_properties.current_total_mass_kg = mass_properties.empty_mass_kg + fuel_kg;
}

__global__ void exact_world_step_aircraft_tail_cuda_kernel(
    AircraftTailState* states,
    std::size_t count,
    RotationalParams params,
    int stop_stage_code
) {
    const std::size_t idx = static_cast<std::size_t>(blockIdx.x) * static_cast<std::size_t>(blockDim.x) +
        static_cast<std::size_t>(threadIdx.x);
    if (idx >= count || states == nullptr) {
        return;
    }

    auto& state = states[idx];
    run_rotational_integrate_stage(state, params);
    if (stop_stage_code == 0) {
        return;
    }
    run_leapfrog_integrate_stage(state);
    refresh_environment_sample_from_transform(state);
    if (stop_stage_code == 1) {
        return;
    }
    run_navigation_system_stage(state);
    if (stop_stage_code == 2) {
        return;
    }
    run_update_instruments_stage(state);
    if (stop_stage_code == 3) {
        return;
    }
    run_fuel_consumption_stage(state);
    if (stop_stage_code == 4) {
        return;
    }
    run_mass_update_stage(state);
}

}  // namespace

namespace gpu::detail {

bool step_exact_world_step_aircraft_tail_cuda_inplace(
    std::vector<aircraft_tail_cuda::ExactWorldStepAircraftTailCudaState>& states,
    ExactWorldStepAircraftTailCudaStats* stats,
    int stop_stage_code
) {
    if (stats != nullptr) {
        stats->state_count = states.size();
        stats->used_cuda = false;
        stats->host_to_device_ms = 0.0;
        stats->kernel_ms = 0.0;
        stats->device_to_host_ms = 0.0;
        stats->cpu_fallback_ms = 0.0;
    }
    if (states.empty()) {
        return true;
    }

    AircraftTailState* device_states = nullptr;
    const auto h2d_start = std::chrono::steady_clock::now();
    if (cudaMalloc(&device_states, states.size() * sizeof(AircraftTailState)) != cudaSuccess) {
        free_device_ptr(device_states);
        return false;
    }
    if (cudaMemcpy(
            device_states,
            states.data(),
            states.size() * sizeof(AircraftTailState),
            cudaMemcpyHostToDevice
        ) != cudaSuccess) {
        free_device_ptr(device_states);
        return false;
    }
    const auto h2d_end = std::chrono::steady_clock::now();

    const RotationalParams params = rotational_params_host();
    const auto kernel_start = std::chrono::steady_clock::now();
    const int block_size = 128;
    const int grid_size = static_cast<int>((states.size() + static_cast<std::size_t>(block_size) - 1u) /
                                           static_cast<std::size_t>(block_size));
    exact_world_step_aircraft_tail_cuda_kernel<<<grid_size, block_size>>>(
        device_states,
        states.size(),
        params,
        stop_stage_code
    );
    if (cudaGetLastError() != cudaSuccess || cudaDeviceSynchronize() != cudaSuccess) {
        free_device_ptr(device_states);
        return false;
    }
    const auto kernel_end = std::chrono::steady_clock::now();

    const auto d2h_start = std::chrono::steady_clock::now();
    if (cudaMemcpy(
            states.data(),
            device_states,
            states.size() * sizeof(AircraftTailState),
            cudaMemcpyDeviceToHost
        ) != cudaSuccess) {
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
