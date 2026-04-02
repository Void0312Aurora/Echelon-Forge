#include "gpu/gpu_exact_world_step_aircraft_tail_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <stdexcept>

namespace gpu {

namespace {

ExactWorldStepAircraftTailStats g_last_stats{};

int stop_stage_code(ExactWorldStepAircraftTailStopStage stop_stage) {
    return static_cast<int>(stop_stage);
}

constexpr double kPi = 3.14159265358979323846;
constexpr double kRefLat = 36.24;
constexpr double kRefLon = -115.05;
constexpr double kMetersPerDegLat = 111132.954;
constexpr double kMetersPerDegLon = 90000.0;
constexpr double kBaseWindSpeedMps = 10.0;
constexpr double kBaseWindDirFromDeg = 270.0;
constexpr double kWindShearMpsPerKm = 4.0;
constexpr double kEnvironmentScalarCanonicalQuantum = 0x1p-76;

double deg_to_rad(double deg) { return deg * kPi / 180.0; }
double rad_to_deg(double rad) { return rad * 180.0 / kPi; }

double clamp_finite(double value, double lo, double hi) {
    if (!std::isfinite(value)) {
        return 0.0;
    }
    return std::clamp(value, lo, hi);
}

double frame_delta_s(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

double wrap_360(double deg) {
    deg = std::fmod(deg, 360.0);
    if (deg < 0.0) {
        deg += 360.0;
    }
    return deg;
}

double inst_normalize_heading_deg(double heading_deg) {
    if (!std::isfinite(heading_deg)) {
        return 0.0;
    }
    return wrap_360(heading_deg);
}

bool inst_is_runway_like_surface_code(std::uint8_t surface_code) {
    return surface_code == 0u || surface_code == 1u;
}

double inst_ground_track_deg_from_velocity(const Velocity& velocity, double fallback_heading_deg) {
    const double horiz_speed = std::hypot(velocity.vx, velocity.vy);
    if (horiz_speed <= 1.0) {
        return inst_normalize_heading_deg(fallback_heading_deg);
    }
    return inst_normalize_heading_deg(std::atan2(velocity.vx, velocity.vy) * 180.0 / kPi);
}

double inst_canonicalize_ground_track_deg(double value) {
    constexpr double kGroundTrackCanonicalQuantumDeg = 0x1p-32;
    if (!std::isfinite(value)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / kGroundTrackCanonicalQuantumDeg) *
        kGroundTrackCanonicalQuantumDeg;
    return std::abs(rounded) <= (kGroundTrackCanonicalQuantumDeg * 0.5) ? 0.0 : rounded;
}

double inst_mission_heading_bug(
    const MissionCommand& mission,
    const Transform& transform,
    const Velocity& velocity,
    const ExactWorldStepEnvironmentSampleV1* env_sample
) {
    const double fallback_heading_deg = inst_ground_track_deg_from_velocity(velocity, transform.heading);
    if (mission.command_code == 4 && env_sample != nullptr) {
        if (inst_is_runway_like_surface_code(env_sample->terrain_surface_code)
            && std::isfinite(env_sample->runway_heading_deg)) {
            return inst_normalize_heading_deg(env_sample->runway_heading_deg);
        }
    }
    if (std::isfinite(mission.cmd_heading_deg)) {
        return inst_normalize_heading_deg(mission.cmd_heading_deg);
    }
    return fallback_heading_deg;
}

double inst_mission_alt_bug(const MissionCommand& mission, double fallback_alt_m) {
    return std::isfinite(mission.cmd_altitude_m) ? mission.cmd_altitude_m : fallback_alt_m;
}

double inst_mission_speed_bug(const MissionCommand& mission, double fallback_speed_mps) {
    return std::isfinite(mission.cmd_speed_mps) ? mission.cmd_speed_mps : fallback_speed_mps;
}

struct RotationalParams {
    double max_rate_cross_rad_s;
    double max_torque_nm;
    double max_ang_accel_rad_s2;
    double max_rate_rad_s;
    double min_abs_cos_theta;
    double pitch_limit_deg;
};

double env_double(const char* key, double fallback) {
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
}

const RotationalParams& rotational_params() {
    static const RotationalParams params = []() {
        RotationalParams value{};
        value.max_rate_cross_rad_s = std::max(1.0, env_double("CMO_ROT_MAX_RATE_CROSS_RAD_S", 50.0));
        value.max_torque_nm = std::max(1.0e4, env_double("CMO_ROT_MAX_TORQUE_NM", 5.0e6));
        value.max_ang_accel_rad_s2 = std::max(10.0, env_double("CMO_ROT_MAX_ANG_ACCEL_RAD_S2", 1.0e4));
        value.max_rate_rad_s = std::max(0.1, env_double("CMO_ROT_MAX_RATE_RAD_S", 6.0));
        const double min_pitch_deg = std::clamp(
            env_double("CMO_ROT_SINGULARITY_MIN_PITCH_DEG", 85.0),
            70.0,
            89.9
        );
        value.min_abs_cos_theta = std::cos(deg_to_rad(min_pitch_deg));
        value.pitch_limit_deg = std::clamp(
            env_double("CMO_ROT_PITCH_LIMIT_DEG", 89.0),
            70.0,
            89.9
        );
        return value;
    }();
    return params;
}

void compute_standard_atmosphere(
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
    *out_temperature_k = temperature;
    *out_air_density = pressure / (kR * temperature);
    *out_speed_of_sound = std::sqrt(1.4 * kR * temperature);
}

double default_terrain_elevation_m(double x, double y) {
    constexpr double kPeakX = 25000.0;
    constexpr double kPeakY = 25000.0;
    constexpr double kPeakH = 2000.0;
    constexpr double kSigmaSq = 25000000.0;
    const double d2 = (x - kPeakX) * (x - kPeakX) + (y - kPeakY) * (y - kPeakY);
    return kPeakH * std::exp(-d2 / (2.0 * kSigmaSq));
}

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

void refresh_environment_sample_from_transform(ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    if (soa.has_environment_sample[i] == 0) {
        return;
    }

    auto& env_sample = soa.environment_sample[i];
    const auto& transform = soa.transform[i];
    env_sample.terrain_elevation_m = canonicalize_environment_scalar(
        default_terrain_elevation_m(transform.x, transform.y)
    );

    double dir_to_deg = std::fmod(kBaseWindDirFromDeg + 180.0, 360.0);
    if (dir_to_deg < 0.0) {
        dir_to_deg += 360.0;
    }
    const double dir_to_rad = deg_to_rad(dir_to_deg);
    const double ux = std::sin(dir_to_rad);
    const double uy = std::cos(dir_to_rad);
    const double alt_km = std::max(0.0, transform.z) / 1000.0;
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

LocalVec3 project_forces_to_body(const LocalVec3& f_world, const Transform& transform) {
    const double psi = deg_to_rad(90.0 - transform.heading);
    const double theta = deg_to_rad(transform.pitch);
    const double c_psi = std::cos(psi);
    const double s_psi = std::sin(psi);
    const double c_theta = std::cos(theta);
    const double s_theta = std::sin(theta);

    const double x1 = f_world.x * c_psi + f_world.y * s_psi;
    const double y1 = -f_world.x * s_psi + f_world.y * c_psi;
    const double z1 = f_world.z;

    const double x2 = x1 * c_theta + z1 * s_theta;
    const double y2 = y1;
    const double z2 = -x1 * s_theta + z1 * c_theta;

    const double phi = deg_to_rad(transform.roll);
    const double c_phi = std::cos(phi);
    const double s_phi = std::sin(phi);

    return {
        x2,
        0.0,
        -y2 * s_phi + z2 * c_phi,
    };
}

bool has_query_inputs_for_rotational_integrate(const ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    return soa.has_angular_velocity[i] != 0
        && soa.has_inertia[i] != 0
        && soa.has_force_accumulator[i] != 0;
}

bool has_query_inputs_for_leapfrog_integrate(const ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    return soa.has_force_accumulator[i] != 0
        && soa.has_mass[i] != 0;
}

bool has_query_inputs_for_navigation_system(const ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    return soa.has_egi[i] != 0;
}

bool has_query_inputs_for_update_instruments(const ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    return soa.has_instrument_state[i] != 0
        && soa.has_aero_state[i] != 0
        && soa.has_force_accumulator[i] != 0
        && soa.has_mass[i] != 0
        && soa.has_propulsion[i] != 0
        && soa.has_angular_velocity[i] != 0;
}

bool has_query_inputs_for_fuel_consumption(const ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    return soa.has_fuel_system[i] != 0;
}

bool has_query_inputs_for_mass_update(const ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    return soa.has_fuel_system[i] != 0
        && soa.has_mass[i] != 0
        && soa.has_mass_properties[i] != 0;
}

void run_rotational_integrate_stage(ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_rotational_integrate(soa, i)) {
        return;
    }

    auto& transform = soa.transform[i];
    auto& ang_vel = soa.angular_velocity[i];
    const auto& inertia = soa.inertia[i];
    const auto& forces = soa.force_accumulator[i];

    double dt = frame_delta_s(soa.time_step_s[i]);
    if (dt <= 0.0) {
        dt = 0.05;
    }

    const RotationalParams& prm = rotational_params();
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
    const double c_phi = std::cos(phi);
    const double s_phi = std::sin(phi);
    double c_theta = std::cos(theta);
    const double s_theta = std::sin(theta);

    if (std::abs(c_theta) < prm.min_abs_cos_theta) {
        c_theta = std::copysign(prm.min_abs_cos_theta, c_theta);
    }
    const double t_theta = s_theta / c_theta;
    const double sec_theta = 1.0 / c_theta;

    const double d_phi = p + (q * s_phi + r * c_phi) * t_theta;
    const double d_theta = q * c_phi - r * s_phi;
    const double d_psi = (q * s_phi + r * c_phi) * sec_theta;

    transform.roll += rad_to_deg(d_phi) * dt;
    transform.pitch += rad_to_deg(d_theta) * dt;
    transform.heading -= rad_to_deg(d_psi) * dt;

    transform.roll = std::fmod(transform.roll + 180.0, 360.0);
    if (transform.roll < 0.0) {
        transform.roll += 360.0;
    }
    transform.roll -= 180.0;
    transform.pitch = std::clamp(transform.pitch, -prm.pitch_limit_deg, prm.pitch_limit_deg);
    transform.heading = wrap_360(transform.heading);
}

void run_leapfrog_integrate_stage(ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_leapfrog_integrate(soa, i)) {
        return;
    }

    auto& transform = soa.transform[i];
    auto& velocity = soa.velocity[i];
    const auto& forces = soa.force_accumulator[i];
    const auto& mass = soa.mass[i];

    double dt = frame_delta_s(soa.time_step_s[i]);
    if (dt <= 0.0) {
        dt = 0.05;
    }

    double m = mass.get_total_kg();
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

void run_navigation_system_stage(ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_navigation_system(soa, i)) {
        return;
    }

    auto& egi = soa.egi[i];
    const auto& trans = soa.transform[i];
    const auto& vel = soa.velocity[i];

    const double dt = frame_delta_s(soa.time_step_s[i]);

    egi.drift_lat_m = 0.0;
    egi.drift_lon_m = 0.0;
    egi.drift_alt_m = 0.0;

    if (egi.gps_available) {
        egi.time_since_last_gps_fix = 0.0;
        egi.position_uncertainty_m = std::min(egi.position_uncertainty_m, 5.0);
    } else {
        egi.time_since_last_gps_fix += dt;
        egi.position_uncertainty_m = std::max(egi.position_uncertainty_m, 50.0);
    }

    egi.lat_deg = kRefLat + (trans.y / kMetersPerDegLat);
    egi.lon_deg = kRefLon + (trans.x / kMetersPerDegLon);
    egi.vn_mps = vel.vy;
    egi.ve_mps = vel.vx;
    egi.vd_mps = -vel.vz;
    egi.alt_baro_m = trans.z;
    egi.alt_radar_m = std::max(0.0, trans.z);
    egi.heading_deg = wrap_360(trans.heading);
    egi.pitch_deg = trans.pitch;
    egi.roll_deg = trans.roll;
}

void run_update_instruments_stage(ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_update_instruments(soa, i)) {
        return;
    }

    auto& inst = soa.instrument_state[i];
    const auto& transform = soa.transform[i];
    const auto& velocity = soa.velocity[i];
    const auto& aero = soa.aero_state[i];
    const auto& forces = soa.force_accumulator[i];
    const auto& mass = soa.mass[i];
    const auto& propulsion = soa.propulsion[i];
    const auto& ang_vel = soa.angular_velocity[i];
    const auto* env_sample = soa.has_environment_sample[i] != 0 ? &soa.environment_sample[i] : nullptr;

    inst.alt_baro_m = transform.z;
    const double terrain_z = env_sample != nullptr ? env_sample->terrain_elevation_m : 0.0;
    inst.alt_radar_m = std::max(0.0, transform.z - terrain_z);
    inst.pitch_deg = transform.pitch;
    inst.roll_deg = transform.roll;
    inst.heading_deg = transform.heading;
    inst.mach = aero.mach_number;
    inst.ias_mps = std::sqrt(2.0 * aero.dynamic_pressure / 1.225);
    inst.vvi_mps = velocity.vz;
    inst.aoa_deg = aero.angle_of_attack;
    inst.beta_deg = aero.sideslip_angle;
    inst.p_deg_s = rad_to_deg(ang_vel.p);
    inst.q_deg_s = rad_to_deg(ang_vel.q);
    inst.r_deg_s = rad_to_deg(ang_vel.r);

    double total_mass = mass.get_total_kg();
    if (total_mass < 1.0) {
        total_mass = 1.0;
    }
    const LocalVec3 f_contact{
        forces.fx,
        forces.fy,
        forces.fz + (total_mass * 9.80665),
    };
    const LocalVec3 f_body = project_forces_to_body(f_contact, transform);
    inst.g_load_normal = f_body.z / (total_mass * 9.80665);
    inst.g_load_axial = f_body.x / (total_mass * 9.80665);

    const double tsfc = propulsion.afterburner_active ? 0.25 : 0.1;
    inst.fuel_flow_kg_h = std::abs(propulsion.current_thrust_n) * tsfc;
    if (propulsion.afterburner_active) {
        inst.engine_rpm_pct = 100.0 + (propulsion.current_thrust_n / (propulsion.ab_thrust_n + 1e-6)) * 10.0;
    } else {
        inst.engine_rpm_pct = (propulsion.current_thrust_n / (propulsion.mil_thrust_n + 1e-6)) * 100.0;
    }
    inst.engine_temp_c = 600.0 + inst.engine_rpm_pct * 3.0;

    if (soa.has_fuel_system[i] != 0) {
        inst.fuel_internal_kg = soa.fuel_system[i].internal_fuel_kg;
        inst.fuel_external_kg = soa.fuel_system[i].external_fuel_kg;
    } else {
        inst.fuel_internal_kg = mass.fuel_mass_kg;
        inst.fuel_external_kg = 0.0;
    }

    if (soa.has_landing_gear[i] != 0) {
        inst.gear_pos = static_cast<float>(std::clamp(soa.landing_gear[i].extension_state, 0.0, 1.0));
    } else {
        inst.gear_pos = 0.0f;
    }

    if (soa.has_pilot_action[i] != 0 && soa.pilot_action[i].active) {
        const auto& pilot = soa.pilot_action[i];
        inst.throttle_pos = std::clamp(pilot.throttle, 0.0, 1.0);
        inst.flaps_pos = std::clamp(pilot.flaps, 0.0f, 1.0f);
        inst.speedbrake_pos = std::clamp(pilot.speedbrake, 0.0f, 1.0f);
        inst.master_arm = pilot.master_arm;
        inst.weapon_selected = pilot.weapon_select_id;
    } else if (soa.has_movement_command[i] != 0 && soa.movement_command[i].active) {
        inst.throttle_pos = std::clamp(soa.movement_command[i].throttle_cmd, 0.0, 1.0);
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
        inst.wind_speed_mps = std::sqrt(wx * wx + wy * wy);
        double wind_to_deg = std::atan2(wx, wy) * 180.0 / kPi;
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

    if (soa.has_mission_command[i] != 0 && soa.mission_command[i].active) {
        inst.cmd_heading_deg = inst_mission_heading_bug(soa.mission_command[i], transform, velocity, env_sample);
        inst.cmd_alt_m = inst_mission_alt_bug(soa.mission_command[i], inst.alt_baro_m);
        inst.cmd_speed_mps = inst_mission_speed_bug(soa.mission_command[i], inst.ias_mps);
    } else {
        inst.cmd_heading_deg = inst.heading_deg;
        inst.cmd_alt_m = inst.alt_baro_m;
        inst.cmd_speed_mps = inst.ias_mps;
    }

    inst.rwr_active = soa.has_rwr_summary[i] != 0 && soa.rwr_summary[i].detected_count > 0;
    inst.missiles_remaining = soa.has_ammo[i] != 0 ? soa.ammo[i].missiles_remaining : 0;

    if (soa.has_egi[i] != 0) {
        const auto& egi = soa.egi[i];
        inst.lat_deg = egi.lat_deg;
        inst.lon_deg = egi.lon_deg;
        inst.vn_mps = egi.vn_mps;
        inst.ve_mps = egi.ve_mps;
        inst.vd_mps = egi.vd_mps;
        inst.ground_speed_mps = std::sqrt(egi.vn_mps * egi.vn_mps + egi.ve_mps * egi.ve_mps);
        if (inst.ground_speed_mps > 0.1) {
            inst.ground_track_deg = std::atan2(egi.ve_mps, egi.vn_mps) * 180.0 / kPi;
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

    if (soa.has_gear_state[i] != 0) {
        inst.gear_stress = soa.gear_state[i].stress;
        inst.gear_collapsed = soa.gear_state[i].collapsed;
        inst.on_runway = soa.gear_state[i].on_runway;
    } else {
        inst.gear_stress = 0.0;
        inst.gear_collapsed = false;
        inst.on_runway = true;
    }
}

void run_fuel_consumption_stage(ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_fuel_consumption(soa, i)) {
        return;
    }

    auto& fuel = soa.fuel_system[i];
    const double dt = frame_delta_s(soa.time_step_s[i]);

    double throttle = 0.0;
    bool throttle_set = false;
    if (soa.has_pilot_action[i] != 0 && soa.pilot_action[i].active) {
        throttle = std::clamp(soa.pilot_action[i].throttle, 0.0, 1.0);
        throttle_set = true;
    }
    if (!throttle_set && soa.has_movement_command[i] != 0 && soa.movement_command[i].active) {
        throttle = std::clamp(soa.movement_command[i].throttle_cmd, 0.0, 1.0);
        throttle_set = true;
    }
    if (!throttle_set && soa.has_action_command[i] != 0 && soa.action_command[i].active) {
        throttle = std::clamp((soa.action_command[i].accel_cmd + 1.0) * 0.5, 0.0, 1.0);
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

void run_mass_update_stage(ExactWorldStepAircraftTailSoA& soa, std::size_t i) {
    if (!has_query_inputs_for_mass_update(soa, i)) {
        return;
    }

    auto& mass_properties = soa.mass_properties[i];
    auto& rigid_mass = soa.mass[i];
    const auto& fuel = soa.fuel_system[i];

    const double fuel_kg =
        std::max(0.0, fuel.internal_fuel_kg) + std::max(0.0, fuel.external_fuel_kg);
    rigid_mass.fuel_mass_kg = fuel_kg;
    mass_properties.current_total_mass_kg = mass_properties.empty_mass_kg + fuel_kg;
}

}  // namespace

ExactWorldStepAircraftTailSoA pack_exact_world_step_states_v1_aircraft_tail_soa(
    const std::vector<ExactWorldStepStateV1>& states
) {
    ExactWorldStepAircraftTailSoA soa{};
    soa.size = states.size();

    soa.time_step_s.resize(soa.size);
    soa.transform.resize(soa.size);
    soa.velocity.resize(soa.size);
    soa.angular_velocity.resize(soa.size);
    soa.force_accumulator.resize(soa.size);
    soa.mass.resize(soa.size);
    soa.inertia.resize(soa.size);
    soa.aero_state.resize(soa.size);
    soa.propulsion.resize(soa.size);
    soa.fuel_system.resize(soa.size);
    soa.mass_properties.resize(soa.size);
    soa.instrument_state.resize(soa.size);
    soa.egi.resize(soa.size);
    soa.pilot_action.resize(soa.size);
    soa.movement_command.resize(soa.size);
    soa.action_command.resize(soa.size);
    soa.mission_command.resize(soa.size);
    soa.landing_gear.resize(soa.size);
    soa.gear_state.resize(soa.size);
    soa.ammo.resize(soa.size);
    soa.rwr_summary.resize(soa.size);
    soa.environment_sample.resize(soa.size);

    soa.has_angular_velocity.resize(soa.size);
    soa.has_force_accumulator.resize(soa.size);
    soa.has_mass.resize(soa.size);
    soa.has_inertia.resize(soa.size);
    soa.has_aero_state.resize(soa.size);
    soa.has_propulsion.resize(soa.size);
    soa.has_fuel_system.resize(soa.size);
    soa.has_mass_properties.resize(soa.size);
    soa.has_instrument_state.resize(soa.size);
    soa.has_egi.resize(soa.size);
    soa.has_pilot_action.resize(soa.size);
    soa.has_movement_command.resize(soa.size);
    soa.has_action_command.resize(soa.size);
    soa.has_mission_command.resize(soa.size);
    soa.has_landing_gear.resize(soa.size);
    soa.has_gear_state.resize(soa.size);
    soa.has_ammo.resize(soa.size);
    soa.has_rwr_summary.resize(soa.size);
    soa.has_environment_sample.resize(soa.size);

    for (std::size_t i = 0; i < soa.size; ++i) {
        const auto& state = states[i];
        soa.time_step_s[i] = state.time_step_s;
        soa.transform[i] = state.transform;
        soa.velocity[i] = state.velocity;
        soa.angular_velocity[i] = state.angular_velocity;
        soa.force_accumulator[i] = state.force_accumulator;
        soa.mass[i] = state.mass;
        soa.inertia[i] = state.inertia;
        soa.aero_state[i] = state.aero_state;
        soa.propulsion[i] = state.propulsion;
        soa.fuel_system[i] = state.fuel_system;
        soa.mass_properties[i] = state.mass_properties;
        soa.instrument_state[i] = state.instrument_state;
        soa.egi[i] = state.egi;
        soa.pilot_action[i] = state.pilot_action;
        soa.movement_command[i] = state.movement_command;
        soa.action_command[i] = state.action_command;
        soa.mission_command[i] = state.mission_command;
        soa.landing_gear[i] = state.landing_gear;
        soa.gear_state[i] = state.gear_state;
        soa.ammo[i] = state.ammo;
        soa.rwr_summary[i] = state.rwr_summary;
        soa.environment_sample[i] = state.environment_sample;

        soa.has_angular_velocity[i] = state.has_angular_velocity ? 1u : 0u;
        soa.has_force_accumulator[i] = state.has_force_accumulator ? 1u : 0u;
        soa.has_mass[i] = state.has_mass ? 1u : 0u;
        soa.has_inertia[i] = state.has_inertia ? 1u : 0u;
        soa.has_aero_state[i] = state.has_aero_state ? 1u : 0u;
        soa.has_propulsion[i] = state.has_propulsion ? 1u : 0u;
        soa.has_fuel_system[i] = state.has_fuel_system ? 1u : 0u;
        soa.has_mass_properties[i] = state.has_mass_properties ? 1u : 0u;
        soa.has_instrument_state[i] = state.has_instrument_state ? 1u : 0u;
        soa.has_egi[i] = state.has_egi ? 1u : 0u;
        soa.has_pilot_action[i] = state.has_pilot_action ? 1u : 0u;
        soa.has_movement_command[i] = state.has_movement_command ? 1u : 0u;
        soa.has_action_command[i] = state.has_action_command ? 1u : 0u;
        soa.has_mission_command[i] = state.has_mission_command ? 1u : 0u;
        soa.has_landing_gear[i] = state.has_landing_gear ? 1u : 0u;
        soa.has_gear_state[i] = state.has_gear_state ? 1u : 0u;
        soa.has_ammo[i] = state.has_ammo ? 1u : 0u;
        soa.has_rwr_summary[i] = state.has_rwr_summary ? 1u : 0u;
        soa.has_environment_sample[i] = state.has_environment_sample ? 1u : 0u;
    }

    return soa;
}

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_aircraft_tail_soa(
    const ExactWorldStepAircraftTailSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
    if (soa.size != basis_states.size()) {
        throw std::invalid_argument("aircraft-tail SoA size must match basis state count");
    }

    std::vector<ExactWorldStepStateV1> out = basis_states;
    for (std::size_t i = 0; i < soa.size; ++i) {
        auto& state = out[i];
        state.time_step_s = soa.time_step_s[i];
        state.transform = soa.transform[i];
        state.velocity = soa.velocity[i];
        state.angular_velocity = soa.angular_velocity[i];
        state.force_accumulator = soa.force_accumulator[i];
        state.mass = soa.mass[i];
        state.inertia = soa.inertia[i];
        state.aero_state = soa.aero_state[i];
        state.propulsion = soa.propulsion[i];
        state.fuel_system = soa.fuel_system[i];
        state.mass_properties = soa.mass_properties[i];
        state.instrument_state = soa.instrument_state[i];
        state.egi = soa.egi[i];
        state.pilot_action = soa.pilot_action[i];
        state.movement_command = soa.movement_command[i];
        state.action_command = soa.action_command[i];
        state.mission_command = soa.mission_command[i];
        state.landing_gear = soa.landing_gear[i];
        state.gear_state = soa.gear_state[i];
        state.ammo = soa.ammo[i];
        state.rwr_summary = soa.rwr_summary[i];
        state.environment_sample = soa.environment_sample[i];

        state.has_angular_velocity = soa.has_angular_velocity[i] != 0;
        state.has_force_accumulator = soa.has_force_accumulator[i] != 0;
        state.has_mass = soa.has_mass[i] != 0;
        state.has_inertia = soa.has_inertia[i] != 0;
        state.has_aero_state = soa.has_aero_state[i] != 0;
        state.has_propulsion = soa.has_propulsion[i] != 0;
        state.has_fuel_system = soa.has_fuel_system[i] != 0;
        state.has_mass_properties = soa.has_mass_properties[i] != 0;
        state.has_instrument_state = soa.has_instrument_state[i] != 0;
        state.has_egi = soa.has_egi[i] != 0;
        state.has_pilot_action = soa.has_pilot_action[i] != 0;
        state.has_movement_command = soa.has_movement_command[i] != 0;
        state.has_action_command = soa.has_action_command[i] != 0;
        state.has_mission_command = soa.has_mission_command[i] != 0;
        state.has_landing_gear = soa.has_landing_gear[i] != 0;
        state.has_gear_state = soa.has_gear_state[i] != 0;
        state.has_ammo = soa.has_ammo[i] != 0;
        state.has_rwr_summary = soa.has_rwr_summary[i] != 0;
        state.has_environment_sample = soa.has_environment_sample[i] != 0;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_tail_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    return step_exact_world_step_aircraft_tail_until_stage_batch(
        initial_states,
        ExactWorldStepAircraftTailStopStage::MassUpdate
    );
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_tail_until_stage_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    ExactWorldStepAircraftTailStopStage stop_stage
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepAircraftTailSoA soa = pack_exact_world_step_states_v1_aircraft_tail_soa(initial_states);
    const int stop_code = stop_stage_code(stop_stage);
    for (std::size_t i = 0; i < soa.size; ++i) {
        run_rotational_integrate_stage(soa, i);
        if (stop_code == stop_stage_code(ExactWorldStepAircraftTailStopStage::RotationalIntegrate)) {
            continue;
        }
        run_leapfrog_integrate_stage(soa, i);
        refresh_environment_sample_from_transform(soa, i);
        if (stop_code == stop_stage_code(ExactWorldStepAircraftTailStopStage::LeapfrogIntegrate)) {
            continue;
        }
        run_navigation_system_stage(soa, i);
        if (stop_code == stop_stage_code(ExactWorldStepAircraftTailStopStage::NavigationSystem)) {
            continue;
        }
        run_update_instruments_stage(soa, i);
        if (stop_code == stop_stage_code(ExactWorldStepAircraftTailStopStage::UpdateInstruments)) {
            continue;
        }
        run_fuel_consumption_stage(soa, i);
        if (stop_code == stop_stage_code(ExactWorldStepAircraftTailStopStage::FuelConsumption)) {
            continue;
        }
        run_mass_update_stage(soa, i);
    }
    auto out = unpack_exact_world_step_states_v1_aircraft_tail_soa(soa, initial_states);
    const auto end = std::chrono::steady_clock::now();

    g_last_stats.state_count = initial_states.size();
    g_last_stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    return out;
}

const ExactWorldStepAircraftTailStats& last_exact_world_step_aircraft_tail_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
