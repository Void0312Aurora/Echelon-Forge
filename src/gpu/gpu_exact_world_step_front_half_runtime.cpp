#include "gpu/gpu_exact_world_step_front_half_runtime.h"

#include <chrono>
#include <stdexcept>
#include <utility>

#include "gpu/gpu_exact_world_step_command_lane_runtime.h"
#include "gpu/gpu_exact_world_step_control_aero_runtime.h"
#include "gpu/gpu_exact_world_step_contract.h"
#include "gpu/gpu_exact_world_step_force_ground_runtime.h"
#include "gpu/gpu_exact_world_step_front_half_runtime_types.h"

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
bool step_exact_world_step_front_half_cuda_inplace(
    std::vector<front_half::ExactWorldStepFrontHalfState>& states,
    ExactWorldStepFrontHalfStats* stats,
    int stop_stage_code
);
#endif

}  // namespace gpu::detail

namespace gpu {

namespace {

ExactWorldStepFrontHalfStats g_last_stats{};

int stop_stage_code(ExactWorldStepFrontHalfStopStage stop_stage) {
    return static_cast<int>(stop_stage);
}

std::vector<front_half::ExactWorldStepFrontHalfState> pack_front_half_states(
    const std::vector<ExactWorldStepStateV1>& states
) {
    std::vector<front_half::ExactWorldStepFrontHalfState> out;
    out.resize(states.size());
    for (std::size_t i = 0; i < states.size(); ++i) {
        const auto& src = states[i];
        auto& dst = out[i];
        dst.time_step_s = src.time_step_s;

        dst.transform = {
            src.transform.x,
            src.transform.y,
            src.transform.z,
            src.transform.heading,
            src.transform.pitch,
            src.transform.roll,
        };
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
        dst.aero_state = {
            src.aero_state.dynamic_pressure,
            src.aero_state.angle_of_attack,
            src.aero_state.sideslip_angle,
            src.aero_state.mach_number,
            src.aero_state.lift_coefficient,
            src.aero_state.drag_coefficient,
        };
        dst.control_law_state = {
            src.control_law_state.stick_roll_filt,
            src.control_law_state.stick_pitch_filt,
            src.control_law_state.stick_yaw_filt,
            src.control_law_state.stick_yaw_cmd,
        };
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
            src.pilot_action.active,
        };
        dst.mission_command = {
            src.mission_command.cmd_heading_deg,
            src.mission_command.cmd_altitude_m,
            src.mission_command.cmd_speed_mps,
            src.mission_command.command_code,
            static_cast<front_half::RecoveryApproachType>(src.mission_command.recovery_approach_type),
            src.mission_command.active,
        };
        dst.movement_command = {
            src.movement_command.throttle_cmd,
            src.movement_command.active,
        };
        dst.landing_gear = {
            src.landing_gear.rolling_friction_coeff,
            src.landing_gear.contact_height_m,
            src.landing_gear.extension_state,
            src.landing_gear.transit_time_s,
        };
        dst.gear_state = {
            src.gear_state.gear_down,
            src.gear_state.stress,
            src.gear_state.collapsed,
            src.gear_state.stress_rate,
            src.gear_state.on_runway,
        };
        dst.mass = {
            src.mass.empty_mass_kg,
            src.mass.fuel_mass_kg,
            src.mass.stores_mass_kg,
        };
        dst.propulsion = {
            src.propulsion.mil_thrust_n,
            src.propulsion.ab_thrust_n,
            src.propulsion.current_thrust_n,
            src.propulsion.afterburner_active,
        };
        dst.mass_properties = {
            src.mass_properties.current_drag_index,
            src.mass_properties.reference_area_m2,
            src.mass_properties.wing_span_m,
            src.mass_properties.chord_m,
        };
        dst.ground_state = {
            src.ground_state.on_ground,
            src.ground_state.terrain_elevation,
        };
        dst.health = {src.health.current_hp};
        dst.environment_sample = {
            src.environment_sample.terrain_elevation_m,
            src.environment_sample.wind_vx_mps,
            src.environment_sample.wind_vy_mps,
            src.environment_sample.terrain_surface_code,
        };

        dst.has_angular_velocity = src.has_angular_velocity;
        dst.has_force_accumulator = src.has_force_accumulator;
        dst.has_aero_state = src.has_aero_state;
        dst.has_control_law_state = src.has_control_law_state;
        dst.has_pilot_action = src.has_pilot_action;
        dst.has_mission_command = src.has_mission_command;
        dst.has_movement_command = src.has_movement_command;
        dst.has_lagged_command = src.has_lagged_command;
        dst.has_flight_model = src.has_flight_model;
        dst.has_landing_gear = src.has_landing_gear;
        dst.has_gear_state = src.has_gear_state;
        dst.has_mass = src.has_mass;
        dst.has_propulsion = src.has_propulsion;
        dst.has_mass_properties = src.has_mass_properties;
        dst.has_ground_state = src.has_ground_state;
        dst.has_health = src.has_health;
        dst.has_environment_sample = src.has_environment_sample;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> unpack_front_half_states(
    const std::vector<front_half::ExactWorldStepFrontHalfState>& states,
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
        dst.aero_state.dynamic_pressure = src.aero_state.dynamic_pressure;
        dst.aero_state.angle_of_attack = src.aero_state.angle_of_attack;
        dst.aero_state.sideslip_angle = src.aero_state.sideslip_angle;
        dst.aero_state.mach_number = src.aero_state.mach_number;
        dst.aero_state.lift_coefficient = src.aero_state.lift_coefficient;
        dst.aero_state.drag_coefficient = src.aero_state.drag_coefficient;
        dst.control_law_state.stick_roll_filt = src.control_law_state.stick_roll_filt;
        dst.control_law_state.stick_pitch_filt = src.control_law_state.stick_pitch_filt;
        dst.control_law_state.stick_yaw_filt = src.control_law_state.stick_yaw_filt;
        dst.control_law_state.stick_yaw_cmd = src.control_law_state.stick_yaw_cmd;
        dst.pilot_action.stick_pitch = src.pilot_action.stick_pitch;
        dst.pilot_action.stick_roll = src.pilot_action.stick_roll;
        dst.pilot_action.rudder = src.pilot_action.rudder;
        dst.pilot_action.throttle = src.pilot_action.throttle;
        dst.pilot_action.gear_handle = src.pilot_action.gear_handle;
        dst.pilot_action.flaps = src.pilot_action.flaps;
        dst.pilot_action.speedbrake = src.pilot_action.speedbrake;
        dst.pilot_action.brake = src.pilot_action.brake;
        dst.pilot_action.brake_left = src.pilot_action.brake_left;
        dst.pilot_action.brake_right = src.pilot_action.brake_right;
        dst.pilot_action.active = src.pilot_action.active;
        dst.mission_command.cmd_heading_deg = src.mission_command.cmd_heading_deg;
        dst.mission_command.cmd_altitude_m = src.mission_command.cmd_altitude_m;
        dst.mission_command.cmd_speed_mps = src.mission_command.cmd_speed_mps;
        dst.mission_command.command_code = src.mission_command.command_code;
        dst.mission_command.recovery_approach_type =
            static_cast<::RecoveryApproachType>(src.mission_command.recovery_approach_type);
        dst.mission_command.active = src.mission_command.active;
        dst.movement_command.throttle_cmd = src.movement_command.throttle_cmd;
        dst.movement_command.active = src.movement_command.active;
        dst.landing_gear.rolling_friction_coeff = src.landing_gear.rolling_friction_coeff;
        dst.landing_gear.contact_height_m = src.landing_gear.contact_height_m;
        dst.landing_gear.extension_state = src.landing_gear.extension_state;
        dst.landing_gear.transit_time_s = src.landing_gear.transit_time_s;
        dst.gear_state.gear_down = src.gear_state.gear_down;
        dst.gear_state.stress = src.gear_state.stress;
        dst.gear_state.collapsed = src.gear_state.collapsed;
        dst.gear_state.stress_rate = src.gear_state.stress_rate;
        dst.gear_state.on_runway = src.gear_state.on_runway;
        dst.mass.empty_mass_kg = src.mass.empty_mass_kg;
        dst.mass.fuel_mass_kg = src.mass.fuel_mass_kg;
        dst.mass.stores_mass_kg = src.mass.stores_mass_kg;
        dst.propulsion.mil_thrust_n = src.propulsion.mil_thrust_n;
        dst.propulsion.ab_thrust_n = src.propulsion.ab_thrust_n;
        dst.propulsion.current_thrust_n = src.propulsion.current_thrust_n;
        dst.propulsion.afterburner_active = src.propulsion.afterburner_active;
        dst.mass_properties.current_drag_index = src.mass_properties.current_drag_index;
        dst.mass_properties.reference_area_m2 = src.mass_properties.reference_area_m2;
        dst.mass_properties.wing_span_m = src.mass_properties.wing_span_m;
        dst.mass_properties.chord_m = src.mass_properties.chord_m;
        dst.ground_state.on_ground = src.ground_state.on_ground;
        dst.ground_state.terrain_elevation = src.ground_state.terrain_elevation;
        dst.health.current_hp = src.health.current_hp;
        dst.environment_sample.terrain_elevation_m = src.environment_sample.terrain_elevation_m;
        dst.environment_sample.wind_vx_mps = src.environment_sample.wind_vx_mps;
        dst.environment_sample.wind_vy_mps = src.environment_sample.wind_vy_mps;
        dst.environment_sample.terrain_surface_code = src.environment_sample.terrain_surface_code;

        dst.has_angular_velocity = src.has_angular_velocity;
        dst.has_force_accumulator = src.has_force_accumulator;
        dst.has_aero_state = src.has_aero_state;
        dst.has_control_law_state = src.has_control_law_state;
        dst.has_pilot_action = src.has_pilot_action;
        dst.has_mission_command = src.has_mission_command;
        dst.has_movement_command = src.has_movement_command;
        dst.has_lagged_command = src.has_lagged_command;
        dst.has_flight_model = src.has_flight_model;
        dst.has_landing_gear = src.has_landing_gear;
        dst.has_gear_state = src.has_gear_state;
        dst.has_mass = src.has_mass;
        dst.has_propulsion = src.has_propulsion;
        dst.has_mass_properties = src.has_mass_properties;
        dst.has_ground_state = src.has_ground_state;
        dst.has_health = src.has_health;
        dst.has_environment_sample = src.has_environment_sample;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> run_front_half_cpu_post_command(
    std::vector<ExactWorldStepStateV1> states,
    ExactWorldStepFrontHalfStats* stats
) {
    const auto cpu_start = std::chrono::steady_clock::now();
    states = step_exact_world_step_control_aero_reference_cpu_batch(states);
    states = step_exact_world_step_force_ground_reference_cpu_batch(states);
    const auto cpu_end = std::chrono::steady_clock::now();
    if (stats != nullptr) {
        stats->cpu_post_command_ms = std::chrono::duration<double, std::milli>(cpu_end - cpu_start).count();
    }
    return states;
}

}  // namespace

std::vector<ExactWorldStepStateV1> step_exact_world_step_front_half_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepFrontHalfStats stats{};
    stats.state_count = initial_states.size();

    auto states = step_exact_world_step_command_lane_reference_cpu_batch(initial_states);
    stats.command_lane_ms = last_exact_world_step_command_lane_stats().total_ms;
    states = run_front_half_cpu_post_command(std::move(states), &stats);

    const auto end = std::chrono::steady_clock::now();
    stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    g_last_stats = stats;
    return states;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_front_half_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepFrontHalfStats stats{};
    stats.state_count = initial_states.size();

    auto states = step_exact_world_step_command_lane_reference_cpu_batch(initial_states);
    stats.command_lane_ms = last_exact_world_step_command_lane_stats().total_ms;

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto front_half_states = pack_front_half_states(states);
    if (detail::step_exact_world_step_front_half_cuda_inplace(
            front_half_states,
            &stats,
            stop_stage_code(ExactWorldStepFrontHalfStopStage::GroundContact)
        )) {
        states = unpack_front_half_states(front_half_states, states);
        const auto end = std::chrono::steady_clock::now();
        stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
        g_last_stats = stats;
        return states;
    }
#endif

    states = run_front_half_cpu_post_command(std::move(states), &stats);
    const auto end = std::chrono::steady_clock::now();
    stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    g_last_stats = stats;
    return states;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_front_half_until_stage_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    ExactWorldStepFrontHalfStopStage stop_stage
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepFrontHalfStats stats{};
    stats.state_count = initial_states.size();

    auto states = step_exact_world_step_command_lane_reference_cpu_batch(initial_states);
    stats.command_lane_ms = last_exact_world_step_command_lane_stats().total_ms;

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto front_half_states = pack_front_half_states(states);
    if (detail::step_exact_world_step_front_half_cuda_inplace(
            front_half_states,
            &stats,
            stop_stage_code(stop_stage)
        )) {
        states = unpack_front_half_states(front_half_states, states);
        const auto end = std::chrono::steady_clock::now();
        stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
        g_last_stats = stats;
        return states;
    }
#endif

    throw std::runtime_error("step_exact_world_step_front_half_until_stage_batch requires CUDA experiments");
}

const ExactWorldStepFrontHalfStats& last_exact_world_step_front_half_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
