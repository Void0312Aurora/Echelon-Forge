#include "gpu/gpu_exact_world_step_aircraft_tail_cuda_runtime.h"

#include <cmath>
#include <chrono>
#include <utility>

#include "gpu/gpu_exact_world_step_aircraft_tail_runtime.h"
#include "gpu/gpu_exact_world_step_aircraft_tail_cuda_runtime_types.h"
#include "gpu/gpu_exact_world_step_contract.h"

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
bool step_exact_world_step_aircraft_tail_cuda_inplace(
    std::vector<aircraft_tail_cuda::ExactWorldStepAircraftTailCudaState>& states,
    ExactWorldStepAircraftTailCudaStats* stats,
    int stop_stage_code
);
#endif

}  // namespace gpu::detail

namespace gpu {

namespace {

ExactWorldStepAircraftTailCudaStats g_last_stats{};

int stop_stage_code(ExactWorldStepAircraftTailStopStage stop_stage) {
    return static_cast<int>(stop_stage);
}

constexpr double kPi = 3.14159265358979323846;
constexpr double kBaseWindSpeedMps = 10.0;
constexpr double kBaseWindDirFromDeg = 270.0;
constexpr double kWindShearMpsPerKm = 4.0;
constexpr double kEnvironmentScalarCanonicalQuantum = 0x1p-76;

double deg_to_rad(double deg) {
    return deg * kPi / 180.0;
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

double default_terrain_elevation_m(double x, double y) {
    constexpr double kPeakX = 25000.0;
    constexpr double kPeakY = 25000.0;
    constexpr double kPeakH = 2000.0;
    constexpr double kSigmaSq = 25000000.0;
    const double d2 = (x - kPeakX) * (x - kPeakX) + (y - kPeakY) * (y - kPeakY);
    return kPeakH * std::exp(-d2 / (2.0 * kSigmaSq));
}

void refresh_environment_sample_from_transform(ExactWorldStepStateV1& state) {
    if (!state.has_environment_sample) {
        return;
    }

    auto& env_sample = state.environment_sample;
    const auto& transform = state.transform;
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
    return {x2, 0.0, -y2 * s_phi + z2 * c_phi};
}

void refresh_instrument_g_loads(ExactWorldStepStateV1& state, const Mass& g_load_mass) {
    if (!(state.has_instrument_state && state.has_force_accumulator && state.has_mass)) {
        return;
    }

    double total_mass = g_load_mass.get_total_kg();
    if (total_mass < 1.0) {
        total_mass = 1.0;
    }
    const LocalVec3 f_contact{
        state.force_accumulator.fx,
        state.force_accumulator.fy,
        state.force_accumulator.fz + (total_mass * 9.80665),
    };
    const LocalVec3 f_body = project_forces_to_body(f_contact, state.transform);
    state.instrument_state.g_load_normal = f_body.z / (total_mass * 9.80665);
    state.instrument_state.g_load_axial = f_body.x / (total_mass * 9.80665);
}

void postprocess_aircraft_tail_cuda_output(
    std::vector<ExactWorldStepStateV1>& states,
    const std::vector<ExactWorldStepStateV1>& basis_states,
    ExactWorldStepAircraftTailStopStage stop_stage
) {
    const int stage_code = stop_stage_code(stop_stage);
    if (stage_code < stop_stage_code(ExactWorldStepAircraftTailStopStage::LeapfrogIntegrate)) {
        return;
    }

    const bool refresh_g_loads =
        stage_code >= stop_stage_code(ExactWorldStepAircraftTailStopStage::UpdateInstruments);
    const bool preserve_pre_mass_update_instruments =
        stage_code >= stop_stage_code(ExactWorldStepAircraftTailStopStage::MassUpdate);
    for (std::size_t i = 0; i < states.size(); ++i) {
        auto& state = states[i];
        refresh_environment_sample_from_transform(state);
        if (refresh_g_loads) {
            const Mass& g_load_mass = preserve_pre_mass_update_instruments ? basis_states[i].mass : state.mass;
            refresh_instrument_g_loads(state, g_load_mass);
        }
    }
}

std::vector<aircraft_tail_cuda::ExactWorldStepAircraftTailCudaState> pack_aircraft_tail_cuda_states(
    const std::vector<ExactWorldStepStateV1>& states
) {
    std::vector<aircraft_tail_cuda::ExactWorldStepAircraftTailCudaState> out;
    out.resize(states.size());
    for (std::size_t i = 0; i < states.size(); ++i) {
        const auto& src = states[i];
        auto& dst = out[i];
        dst.time_step_s = src.time_step_s;

        dst.transform = {src.transform.x, src.transform.y, src.transform.z, src.transform.heading, src.transform.pitch, src.transform.roll};
        dst.velocity = {src.velocity.vx, src.velocity.vy, src.velocity.vz};
        dst.angular_velocity = {src.angular_velocity.p, src.angular_velocity.q, src.angular_velocity.r};
        dst.force_accumulator = {
            src.force_accumulator.fx,
            src.force_accumulator.fy,
            src.force_accumulator.fz,
            src.force_accumulator.torque_roll,
            src.force_accumulator.torque_pitch,
            src.force_accumulator.torque_yaw,
        };
        dst.mass = {src.mass.empty_mass_kg, src.mass.fuel_mass_kg, src.mass.stores_mass_kg};
        dst.inertia = {src.inertia.ixx, src.inertia.iyy, src.inertia.izz};
        dst.aero_state = {
            src.aero_state.dynamic_pressure,
            src.aero_state.angle_of_attack,
            src.aero_state.sideslip_angle,
            src.aero_state.mach_number,
            src.aero_state.lift_coefficient,
            src.aero_state.drag_coefficient,
        };
        dst.propulsion = {
            src.propulsion.mil_thrust_n,
            src.propulsion.ab_thrust_n,
            src.propulsion.current_thrust_n,
            src.propulsion.afterburner_active,
        };
        dst.fuel_system = {
            src.fuel_system.internal_fuel_kg,
            src.fuel_system.external_fuel_kg,
            src.fuel_system.current_flow_rate,
            src.fuel_system.afterburner_active,
            src.fuel_system.mil_power_flow_rate,
            src.fuel_system.ab_flow_rate_multiplier,
        };
        dst.mass_properties = {
            src.mass_properties.empty_mass_kg,
            src.mass_properties.current_total_mass_kg,
            src.mass_properties.current_drag_index,
            src.mass_properties.reference_area_m2,
            src.mass_properties.wing_span_m,
            src.mass_properties.chord_m,
        };
        dst.instrument_state = {
            src.instrument_state.alt_baro_m,
            src.instrument_state.alt_radar_m,
            src.instrument_state.ias_mps,
            src.instrument_state.mach,
            src.instrument_state.vvi_mps,
            src.instrument_state.pitch_deg,
            src.instrument_state.roll_deg,
            src.instrument_state.heading_deg,
            src.instrument_state.aoa_deg,
            src.instrument_state.beta_deg,
            src.instrument_state.g_load_normal,
            src.instrument_state.g_load_axial,
            src.instrument_state.p_deg_s,
            src.instrument_state.q_deg_s,
            src.instrument_state.r_deg_s,
            src.instrument_state.engine_rpm_pct,
            src.instrument_state.engine_temp_c,
            src.instrument_state.fuel_flow_kg_h,
            src.instrument_state.throttle_pos,
            src.instrument_state.fuel_internal_kg,
            src.instrument_state.fuel_external_kg,
            src.instrument_state.gear_pos,
            src.instrument_state.flaps_pos,
            src.instrument_state.speedbrake_pos,
            src.instrument_state.master_arm,
            src.instrument_state.oat_c,
            src.instrument_state.cmd_heading_deg,
            src.instrument_state.cmd_alt_m,
            src.instrument_state.cmd_speed_mps,
            src.instrument_state.rwr_active,
            src.instrument_state.weapon_selected,
            src.instrument_state.missiles_remaining,
            src.instrument_state.lat_deg,
            src.instrument_state.lon_deg,
            src.instrument_state.vn_mps,
            src.instrument_state.ve_mps,
            src.instrument_state.vd_mps,
            src.instrument_state.ground_speed_mps,
            src.instrument_state.ground_track_deg,
            src.instrument_state.wind_speed_mps,
            src.instrument_state.wind_dir_deg,
            src.instrument_state.gps_available,
            src.instrument_state.position_uncertainty_m,
            src.instrument_state.gear_stress,
            src.instrument_state.gear_collapsed,
            src.instrument_state.on_runway,
        };
        dst.egi = {
            src.egi.lat_deg,
            src.egi.lon_deg,
            src.egi.alt_baro_m,
            src.egi.alt_radar_m,
            src.egi.vn_mps,
            src.egi.ve_mps,
            src.egi.vd_mps,
            src.egi.heading_deg,
            src.egi.pitch_deg,
            src.egi.roll_deg,
            src.egi.wind_speed_mps,
            src.egi.wind_dir_deg,
            src.egi.drift_lat_m,
            src.egi.drift_lon_m,
            src.egi.drift_alt_m,
            src.egi.position_uncertainty_m,
            src.egi.time_since_last_gps_fix,
            src.egi.ins_drift_rate_mps,
            src.egi.gps_available,
        };
        dst.pilot_action = {
            src.pilot_action.throttle,
            src.pilot_action.flaps,
            src.pilot_action.speedbrake,
            src.pilot_action.master_arm,
            src.pilot_action.weapon_select_id,
            src.pilot_action.active,
        };
        dst.movement_command = {src.movement_command.throttle_cmd, src.movement_command.active};
        dst.action_command = {src.action_command.accel_cmd, src.action_command.active};
        dst.mission_command = {
            src.mission_command.command_code,
            src.mission_command.cmd_heading_deg,
            src.mission_command.cmd_altitude_m,
            src.mission_command.cmd_speed_mps,
            src.mission_command.active,
        };
        dst.landing_gear = {src.landing_gear.extension_state};
        dst.gear_state = {src.gear_state.stress, src.gear_state.collapsed, src.gear_state.on_runway};
        dst.ammo = {src.ammo.missiles_remaining};
        dst.rwr_summary = {src.rwr_summary.detected_count};
        dst.environment_sample = {
            src.environment_sample.terrain_elevation_m,
            src.environment_sample.wind_vx_mps,
            src.environment_sample.wind_vy_mps,
            src.environment_sample.terrain_surface_code,
            src.environment_sample.runway_heading_deg,
        };

        dst.has_angular_velocity = src.has_angular_velocity;
        dst.has_force_accumulator = src.has_force_accumulator;
        dst.has_mass = src.has_mass;
        dst.has_inertia = src.has_inertia;
        dst.has_aero_state = src.has_aero_state;
        dst.has_propulsion = src.has_propulsion;
        dst.has_fuel_system = src.has_fuel_system;
        dst.has_mass_properties = src.has_mass_properties;
        dst.has_instrument_state = src.has_instrument_state;
        dst.has_egi = src.has_egi;
        dst.has_pilot_action = src.has_pilot_action;
        dst.has_movement_command = src.has_movement_command;
        dst.has_action_command = src.has_action_command;
        dst.has_mission_command = src.has_mission_command;
        dst.has_landing_gear = src.has_landing_gear;
        dst.has_gear_state = src.has_gear_state;
        dst.has_ammo = src.has_ammo;
        dst.has_rwr_summary = src.has_rwr_summary;
        dst.has_environment_sample = src.has_environment_sample;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> unpack_aircraft_tail_cuda_states(
    const std::vector<aircraft_tail_cuda::ExactWorldStepAircraftTailCudaState>& states,
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
    auto out = basis_states;
    for (std::size_t i = 0; i < states.size(); ++i) {
        const auto& src = states[i];
        auto& dst = out[i];
        dst.time_step_s = src.time_step_s;
        dst.transform.x = src.transform.x;
        dst.transform.y = src.transform.y;
        dst.transform.z = src.transform.z;
        dst.transform.heading = src.transform.heading;
        dst.transform.pitch = src.transform.pitch;
        dst.transform.roll = src.transform.roll;
        dst.velocity.vx = src.velocity.vx;
        dst.velocity.vy = src.velocity.vy;
        dst.velocity.vz = src.velocity.vz;
        dst.angular_velocity.p = src.angular_velocity.p;
        dst.angular_velocity.q = src.angular_velocity.q;
        dst.angular_velocity.r = src.angular_velocity.r;
        dst.force_accumulator.fx = src.force_accumulator.fx;
        dst.force_accumulator.fy = src.force_accumulator.fy;
        dst.force_accumulator.fz = src.force_accumulator.fz;
        dst.force_accumulator.torque_roll = src.force_accumulator.torque_roll;
        dst.force_accumulator.torque_pitch = src.force_accumulator.torque_pitch;
        dst.force_accumulator.torque_yaw = src.force_accumulator.torque_yaw;
        dst.mass.empty_mass_kg = src.mass.empty_mass_kg;
        dst.mass.fuel_mass_kg = src.mass.fuel_mass_kg;
        dst.mass.stores_mass_kg = src.mass.stores_mass_kg;
        dst.inertia.ixx = src.inertia.ixx;
        dst.inertia.iyy = src.inertia.iyy;
        dst.inertia.izz = src.inertia.izz;
        dst.aero_state.dynamic_pressure = src.aero_state.dynamic_pressure;
        dst.aero_state.angle_of_attack = src.aero_state.angle_of_attack;
        dst.aero_state.sideslip_angle = src.aero_state.sideslip_angle;
        dst.aero_state.mach_number = src.aero_state.mach_number;
        dst.aero_state.lift_coefficient = src.aero_state.lift_coefficient;
        dst.aero_state.drag_coefficient = src.aero_state.drag_coefficient;
        dst.propulsion.mil_thrust_n = src.propulsion.mil_thrust_n;
        dst.propulsion.ab_thrust_n = src.propulsion.ab_thrust_n;
        dst.propulsion.current_thrust_n = src.propulsion.current_thrust_n;
        dst.propulsion.afterburner_active = src.propulsion.afterburner_active;
        dst.fuel_system.internal_fuel_kg = src.fuel_system.internal_fuel_kg;
        dst.fuel_system.external_fuel_kg = src.fuel_system.external_fuel_kg;
        dst.fuel_system.current_flow_rate = src.fuel_system.current_flow_rate;
        dst.fuel_system.afterburner_active = src.fuel_system.afterburner_active;
        dst.fuel_system.mil_power_flow_rate = src.fuel_system.mil_power_flow_rate;
        dst.fuel_system.ab_flow_rate_multiplier = src.fuel_system.ab_flow_rate_multiplier;
        dst.mass_properties.empty_mass_kg = src.mass_properties.empty_mass_kg;
        dst.mass_properties.current_total_mass_kg = src.mass_properties.current_total_mass_kg;
        dst.mass_properties.current_drag_index = src.mass_properties.current_drag_index;
        dst.mass_properties.reference_area_m2 = src.mass_properties.reference_area_m2;
        dst.mass_properties.wing_span_m = src.mass_properties.wing_span_m;
        dst.mass_properties.chord_m = src.mass_properties.chord_m;
        dst.instrument_state.alt_baro_m = src.instrument_state.alt_baro_m;
        dst.instrument_state.alt_radar_m = src.instrument_state.alt_radar_m;
        dst.instrument_state.ias_mps = src.instrument_state.ias_mps;
        dst.instrument_state.mach = src.instrument_state.mach;
        dst.instrument_state.vvi_mps = src.instrument_state.vvi_mps;
        dst.instrument_state.pitch_deg = src.instrument_state.pitch_deg;
        dst.instrument_state.roll_deg = src.instrument_state.roll_deg;
        dst.instrument_state.heading_deg = src.instrument_state.heading_deg;
        dst.instrument_state.aoa_deg = src.instrument_state.aoa_deg;
        dst.instrument_state.beta_deg = src.instrument_state.beta_deg;
        dst.instrument_state.g_load_normal = src.instrument_state.g_load_normal;
        dst.instrument_state.g_load_axial = src.instrument_state.g_load_axial;
        dst.instrument_state.p_deg_s = src.instrument_state.p_deg_s;
        dst.instrument_state.q_deg_s = src.instrument_state.q_deg_s;
        dst.instrument_state.r_deg_s = src.instrument_state.r_deg_s;
        dst.instrument_state.engine_rpm_pct = src.instrument_state.engine_rpm_pct;
        dst.instrument_state.engine_temp_c = src.instrument_state.engine_temp_c;
        dst.instrument_state.fuel_flow_kg_h = src.instrument_state.fuel_flow_kg_h;
        dst.instrument_state.throttle_pos = src.instrument_state.throttle_pos;
        dst.instrument_state.fuel_internal_kg = src.instrument_state.fuel_internal_kg;
        dst.instrument_state.fuel_external_kg = src.instrument_state.fuel_external_kg;
        dst.instrument_state.gear_pos = src.instrument_state.gear_pos;
        dst.instrument_state.flaps_pos = src.instrument_state.flaps_pos;
        dst.instrument_state.speedbrake_pos = src.instrument_state.speedbrake_pos;
        dst.instrument_state.master_arm = src.instrument_state.master_arm;
        dst.instrument_state.oat_c = src.instrument_state.oat_c;
        dst.instrument_state.cmd_heading_deg = src.instrument_state.cmd_heading_deg;
        dst.instrument_state.cmd_alt_m = src.instrument_state.cmd_alt_m;
        dst.instrument_state.cmd_speed_mps = src.instrument_state.cmd_speed_mps;
        dst.instrument_state.rwr_active = src.instrument_state.rwr_active;
        dst.instrument_state.weapon_selected = src.instrument_state.weapon_selected;
        dst.instrument_state.missiles_remaining = src.instrument_state.missiles_remaining;
        dst.instrument_state.lat_deg = src.instrument_state.lat_deg;
        dst.instrument_state.lon_deg = src.instrument_state.lon_deg;
        dst.instrument_state.vn_mps = src.instrument_state.vn_mps;
        dst.instrument_state.ve_mps = src.instrument_state.ve_mps;
        dst.instrument_state.vd_mps = src.instrument_state.vd_mps;
        dst.instrument_state.ground_speed_mps = src.instrument_state.ground_speed_mps;
        dst.instrument_state.ground_track_deg = src.instrument_state.ground_track_deg;
        dst.instrument_state.wind_speed_mps = src.instrument_state.wind_speed_mps;
        dst.instrument_state.wind_dir_deg = src.instrument_state.wind_dir_deg;
        dst.instrument_state.gps_available = src.instrument_state.gps_available;
        dst.instrument_state.position_uncertainty_m = src.instrument_state.position_uncertainty_m;
        dst.instrument_state.gear_stress = src.instrument_state.gear_stress;
        dst.instrument_state.gear_collapsed = src.instrument_state.gear_collapsed;
        dst.instrument_state.on_runway = src.instrument_state.on_runway;
        dst.egi.lat_deg = src.egi.lat_deg;
        dst.egi.lon_deg = src.egi.lon_deg;
        dst.egi.alt_baro_m = src.egi.alt_baro_m;
        dst.egi.alt_radar_m = src.egi.alt_radar_m;
        dst.egi.vn_mps = src.egi.vn_mps;
        dst.egi.ve_mps = src.egi.ve_mps;
        dst.egi.vd_mps = src.egi.vd_mps;
        dst.egi.heading_deg = src.egi.heading_deg;
        dst.egi.pitch_deg = src.egi.pitch_deg;
        dst.egi.roll_deg = src.egi.roll_deg;
        dst.egi.wind_speed_mps = src.egi.wind_speed_mps;
        dst.egi.wind_dir_deg = src.egi.wind_dir_deg;
        dst.egi.drift_lat_m = src.egi.drift_lat_m;
        dst.egi.drift_lon_m = src.egi.drift_lon_m;
        dst.egi.drift_alt_m = src.egi.drift_alt_m;
        dst.egi.position_uncertainty_m = src.egi.position_uncertainty_m;
        dst.egi.time_since_last_gps_fix = src.egi.time_since_last_gps_fix;
        dst.egi.ins_drift_rate_mps = src.egi.ins_drift_rate_mps;
        dst.egi.gps_available = src.egi.gps_available;
        dst.pilot_action.throttle = src.pilot_action.throttle;
        dst.pilot_action.flaps = src.pilot_action.flaps;
        dst.pilot_action.speedbrake = src.pilot_action.speedbrake;
        dst.pilot_action.master_arm = src.pilot_action.master_arm;
        dst.pilot_action.weapon_select_id = src.pilot_action.weapon_select_id;
        dst.pilot_action.active = src.pilot_action.active;
        dst.movement_command.throttle_cmd = src.movement_command.throttle_cmd;
        dst.movement_command.active = src.movement_command.active;
        dst.action_command.accel_cmd = src.action_command.accel_cmd;
        dst.action_command.active = src.action_command.active;
        dst.mission_command.command_code = src.mission_command.command_code;
        dst.mission_command.cmd_heading_deg = src.mission_command.cmd_heading_deg;
        dst.mission_command.cmd_altitude_m = src.mission_command.cmd_altitude_m;
        dst.mission_command.cmd_speed_mps = src.mission_command.cmd_speed_mps;
        dst.mission_command.active = src.mission_command.active;
        dst.landing_gear.extension_state = src.landing_gear.extension_state;
        dst.gear_state.stress = src.gear_state.stress;
        dst.gear_state.collapsed = src.gear_state.collapsed;
        dst.gear_state.on_runway = src.gear_state.on_runway;
        dst.ammo.missiles_remaining = src.ammo.missiles_remaining;
        dst.rwr_summary.detected_count = src.rwr_summary.detected_count;
        dst.environment_sample.terrain_elevation_m = src.environment_sample.terrain_elevation_m;
        dst.environment_sample.wind_vx_mps = src.environment_sample.wind_vx_mps;
        dst.environment_sample.wind_vy_mps = src.environment_sample.wind_vy_mps;
        dst.environment_sample.terrain_surface_code = src.environment_sample.terrain_surface_code;
        dst.environment_sample.runway_heading_deg = src.environment_sample.runway_heading_deg;

        dst.has_angular_velocity = src.has_angular_velocity;
        dst.has_force_accumulator = src.has_force_accumulator;
        dst.has_mass = src.has_mass;
        dst.has_inertia = src.has_inertia;
        dst.has_aero_state = src.has_aero_state;
        dst.has_propulsion = src.has_propulsion;
        dst.has_fuel_system = src.has_fuel_system;
        dst.has_mass_properties = src.has_mass_properties;
        dst.has_instrument_state = src.has_instrument_state;
        dst.has_egi = src.has_egi;
        dst.has_pilot_action = src.has_pilot_action;
        dst.has_movement_command = src.has_movement_command;
        dst.has_action_command = src.has_action_command;
        dst.has_mission_command = src.has_mission_command;
        dst.has_landing_gear = src.has_landing_gear;
        dst.has_gear_state = src.has_gear_state;
        dst.has_ammo = src.has_ammo;
        dst.has_rwr_summary = src.has_rwr_summary;
        dst.has_environment_sample = src.has_environment_sample;
    }
    return out;
}

}  // namespace

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_tail_cuda_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    auto out = step_exact_world_step_aircraft_tail_reference_cpu_batch(initial_states);
    const auto end = std::chrono::steady_clock::now();

    g_last_stats.state_count = initial_states.size();
    g_last_stats.used_cuda = false;
    g_last_stats.host_to_device_ms = 0.0;
    g_last_stats.kernel_ms = 0.0;
    g_last_stats.device_to_host_ms = 0.0;
    g_last_stats.cpu_fallback_ms = std::chrono::duration<double, std::milli>(end - start).count();
    g_last_stats.total_ms = g_last_stats.cpu_fallback_ms;
    return out;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_tail_cuda_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    return step_exact_world_step_aircraft_tail_cuda_until_stage_batch(
        initial_states,
        ExactWorldStepAircraftTailStopStage::MassUpdate
    );
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_tail_cuda_until_stage_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    ExactWorldStepAircraftTailStopStage stop_stage
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepAircraftTailCudaStats stats{};
    stats.state_count = initial_states.size();

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto cuda_states = pack_aircraft_tail_cuda_states(initial_states);
    if (detail::step_exact_world_step_aircraft_tail_cuda_inplace(
            cuda_states,
            &stats,
            stop_stage_code(stop_stage)
        )) {
        auto out = unpack_aircraft_tail_cuda_states(cuda_states, initial_states);
        postprocess_aircraft_tail_cuda_output(out, initial_states, stop_stage);
        const auto end = std::chrono::steady_clock::now();
        stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
        g_last_stats = stats;
        return out;
    }
#endif

    auto out = step_exact_world_step_aircraft_tail_until_stage_batch(initial_states, stop_stage);
    const auto end = std::chrono::steady_clock::now();
    stats.used_cuda = false;
    stats.host_to_device_ms = 0.0;
    stats.kernel_ms = 0.0;
    stats.device_to_host_ms = 0.0;
    stats.cpu_fallback_ms = std::chrono::duration<double, std::milli>(end - start).count();
    stats.total_ms = stats.cpu_fallback_ms;
    g_last_stats = stats;
    return out;
}

const ExactWorldStepAircraftTailCudaStats& last_exact_world_step_aircraft_tail_cuda_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
