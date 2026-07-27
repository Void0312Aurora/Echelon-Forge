#include "core/mission/episode/execution_episode_batch_prepare.h"
#include "core/mission/runtime/reward_runtime.h"
#include <cmath>
#include <algorithm>

namespace {

inline bool is_finite(double x) {
    return std::isfinite(x);
}

inline bool check_finite_state(const StepEvaluationBatchEnvState &state) {
    return is_finite(state.truth_x) && is_finite(state.truth_y) && is_finite(state.truth_z) &&
           is_finite(state.truth_vx) && is_finite(state.truth_vy) && is_finite(state.truth_vz) &&
           is_finite(state.truth_speed) && is_finite(state.truth_pitch) &&
           is_finite(state.truth_roll) && is_finite(state.truth_heading) &&
           is_finite(state.truth_health);
}

inline double safe_get(const std::vector<double> &vec, size_t idx, double default_val = 0.0) {
    return idx < vec.size() ? vec[idx] : default_val;
}

bool has_rich_runtime_inputs(const StepEvaluationBatchEnvState &state) {
    return state.has_mission_observation || state.has_step_info || state.has_safety ||
           state.has_waypoint || state.has_approach || state.has_objectives ||
           state.has_flight_shaping;
}

ExecutionEpisodeRuntimeInputs build_rich_runtime_inputs(const StepEvaluationBatchEnvState &state) {
    ExecutionEpisodeRuntimeInputs runtime_inputs;

    if (state.has_mission_observation) {
        runtime_inputs.has_mission_observation = true;
        runtime_inputs.mission_observation = state.mission_observation;
    }

    if (state.has_step_info) {
        runtime_inputs.has_step_info = true;
        runtime_inputs.step_info = state.step_info;
    }

    ExecutionStepRuntimeInputs exec_inputs;
    bool has_exec_inputs = false;
    if (state.truncated) {
        exec_inputs.truncated = true;
        has_exec_inputs = true;
    }
    if (state.has_safety) {
        exec_inputs.safety = state.safety;
        has_exec_inputs = true;
    } else if (state.has_waypoint || state.has_approach || state.has_objectives) {
        exec_inputs.safety.finite_state_valid = true;
        exec_inputs.safety.health = 100.0;
        has_exec_inputs = true;
    }
    if (state.has_waypoint) {
        exec_inputs.has_waypoint = true;
        exec_inputs.waypoint = state.waypoint;
        exec_inputs.waypoint_episode_success = state.waypoint_episode_success;
        exec_inputs.waypoint_episode_success_bonus = state.waypoint_episode_success_bonus;
        has_exec_inputs = true;
    }
    if (state.has_approach) {
        exec_inputs.has_approach = true;
        exec_inputs.approach = state.approach;
        has_exec_inputs = true;
    }
    if (state.has_objectives) {
        exec_inputs.has_objectives = true;
        exec_inputs.objectives = state.objectives;
        exec_inputs.objective_inputs = state.objective_inputs;
        exec_inputs.objective_shaping = state.objective_shaping;
        has_exec_inputs = true;
    }
    if (has_exec_inputs) {
        runtime_inputs.has_execution_step = true;
        runtime_inputs.execution_step = exec_inputs;
    }

    if (state.has_flight_shaping) {
        runtime_inputs.has_flight_shaping = true;
        runtime_inputs.flight_shaping = state.flight_shaping;
        runtime_inputs.include_roll_stability = state.include_roll_stability;
    }

    return runtime_inputs;
}

StepEvaluationBatchEnvState
resolve_episode_state_overrides(const StepEvaluationBatchEnvState &state) {
    if (!state.has_episode_state) {
        return state;
    }
    StepEvaluationBatchEnvState resolved = state;
    resolved.prev_altitude_m = state.episode_state.prev_altitude_m;
    resolved.prev_ias_mps = state.episode_state.prev_ias_mps;
    resolved.liftoff_awarded = state.episode_state.liftoff_awarded;
    resolved.gear_bonus_awarded = state.episode_state.gear_bonus_awarded;
    return resolved;
}

int resolve_prior_off_runway_steps(const StepEvaluationBatchEnvState &state) {
    if (state.has_episode_state) {
        return std::max(0, int(state.episode_state.off_runway_steps));
    }
    return 0;
}

FlightShapingRuntimeInputs build_flight_shaping_inputs(
    const StepEvaluationBatchConfig &config, const StepEvaluationBatchEnvState &state,
    double curr_ias, double curr_alt_agl, double curr_gear, double curr_roll,
    double heading_error_deg, double ground_track_error_deg, bool preliftoff, bool on_runway_task,
    bool airborne, bool has_runway_cross_m, double runway_cross_m, double runway_width_m,
    double ils_valid, double ils_loc) {
    FlightShapingRuntimeInputs inputs;

    // Dynamic fields
    inputs.truth_altitude_m = state.truth_z;
    inputs.truth_speed_mps = state.truth_speed;
    inputs.prev_altitude_m = state.prev_altitude_m;
    inputs.prev_ias_mps = state.prev_ias_mps;
    inputs.curr_ias_mps = curr_ias;
    inputs.curr_alt_baro_m = safe_get(state.inst_vec, 2);
    inputs.curr_alt_agl_m = curr_alt_agl;
    inputs.curr_gear_fraction = curr_gear;
    inputs.curr_roll_deg = curr_roll;
    inputs.curr_pitch_deg = safe_get(state.inst_vec, 6);
    inputs.curr_beta_deg = safe_get(state.inst_vec, 7);
    inputs.curr_yaw_rate_deg_s = safe_get(state.inst_vec, 9);
    inputs.curr_g_load = safe_get(state.inst_vec, 10, 1.0);
    inputs.step_count = state.steps;

    inputs.target_altitude_m = config.target_altitude_m;
    inputs.target_speed_mps = config.target_speed_mps;
    inputs.heading_error_deg = heading_error_deg;
    inputs.ground_track_error_deg = ground_track_error_deg;
    inputs.waypoint_turn_relief_activation = 0.0; // Simplified for now

    inputs.preliftoff = preliftoff;
    inputs.on_runway_task = on_runway_task;
    inputs.airborne = airborne;
    inputs.has_runway_cross_m = has_runway_cross_m;
    inputs.runway_cross_m = runway_cross_m;
    inputs.runway_width_m = runway_width_m;
    inputs.ils_valid = ils_valid > 0.5;
    inputs.ils_loc_dev = ils_loc;

    inputs.liftoff_awarded = state.liftoff_awarded;
    inputs.gear_bonus_awarded = state.gear_bonus_awarded;

    // Config-static fields (same for all envs), copied via the shared X-macro
    // list so new shaping fields cannot be forgotten here.
#define EF_FLIGHT_SHAPING_FIELD(type, name, default_value) inputs.name = config.name;
#include "core/mission/runtime/detail/flight_shaping_shared_fields.inc"

    return inputs;
}

SafetyRuntimeInputs build_safety_inputs(const StepEvaluationBatchConfig &config,
                                        bool finite_state_valid, bool airborne, bool aoa_valid,
                                        double curr_aoa, double curr_g, double curr_alt_agl,
                                        double curr_roll, bool gear_collapsed,
                                        bool runway_surface_phase, bool on_runway_task,
                                        double gear_stress, int off_runway_steps) {
    SafetyRuntimeInputs inputs;
    inputs.finite_state_valid = finite_state_valid;
    inputs.crash_penalty = config.crash_penalty;

    if (!finite_state_valid) {
        return inputs;
    }

    inputs.airborne = airborne;
    inputs.aoa_valid = aoa_valid;
    inputs.aoa_abs_deg = std::abs(curr_aoa);
    inputs.g_abs = std::abs(curr_g);
    inputs.curr_alt_agl_m = curr_alt_agl;
    inputs.roll_abs_deg = std::abs(curr_roll);
    inputs.gear_collapsed = gear_collapsed;
    inputs.runway_surface_phase = runway_surface_phase;
    inputs.on_runway_task = on_runway_task;
    inputs.gear_stress = gear_stress;
    inputs.off_runway_steps = off_runway_steps;

    // Use the actual field names from SafetyRuntimeInputs
    inputs.stall_penalty_weight = config.aoa_penalty_weight;
    inputs.stall_threshold_deg = config.aoa_penalty_threshold_deg;
    inputs.overload_penalty_weight = config.g_penalty_weight;
    inputs.overload_g_threshold = config.g_penalty_threshold;
    inputs.gear_stress_penalty_weight = config.gear_stress_penalty_weight;
    inputs.off_runway_penalty = config.off_runway_penalty_weight;

    return inputs;
}

} // anonymous namespace

std::vector<ExecutionEpisodeRuntimeInputs>
prepare_step_evaluations_batch(const StepEvaluationBatchConfig &config,
                               const std::vector<StepEvaluationBatchEnvState> &env_states) {
    std::vector<ExecutionEpisodeRuntimeInputs> results;
    results.reserve(env_states.size());

    for (const auto &state : env_states) {
        if (has_rich_runtime_inputs(state)) {
            results.push_back(build_rich_runtime_inputs(state));
            continue;
        }

        const StepEvaluationBatchEnvState resolved_state = resolve_episode_state_overrides(state);
        ExecutionEpisodeRuntimeInputs runtime_inputs;

        // Extract instrument values
        double curr_aoa = safe_get(resolved_state.inst_vec, 5);
        double curr_roll = safe_get(resolved_state.inst_vec, 8);
        double curr_g = safe_get(resolved_state.inst_vec, 10, 1.0);
        double curr_gear = safe_get(resolved_state.inst_vec, 18);
        double curr_ias = safe_get(resolved_state.inst_vec, 0);
        double curr_alt_agl = safe_get(resolved_state.inst_vec, 3, resolved_state.truth_z);
        double curr_ground_speed =
            safe_get(resolved_state.inst_vec, 29,
                     std::hypot(resolved_state.truth_vx, resolved_state.truth_vy));

        // Compute heading errors (simplified - assumes target_heading is in config)
        double heading_error_deg = config.target_heading_deg - resolved_state.truth_heading;
        while (heading_error_deg > 180.0)
            heading_error_deg -= 360.0;
        while (heading_error_deg < -180.0)
            heading_error_deg += 360.0;
        double ground_track_error_deg = heading_error_deg; // Simplified

        // ILS values
        double ils_valid = safe_get(resolved_state.ils_vec, 0);
        double ils_loc = safe_get(resolved_state.ils_vec, 1);
        double ils_gs = safe_get(resolved_state.ils_vec, 2);
        double ils_dme = safe_get(resolved_state.ils_vec, 3);

        // Check finite state
        bool finite_state_valid = check_finite_state(resolved_state) && is_finite(curr_ias) &&
                                  is_finite(curr_alt_agl) && is_finite(curr_aoa) &&
                                  is_finite(curr_roll) && is_finite(curr_g);

        // Determine flight phase
        bool on_ground = curr_alt_agl <= 1.0; // Simplified threshold
        bool airborne = curr_alt_agl >= 5.0;  // Simplified threshold
        bool preliftoff = !airborne;
        bool on_runway_task = false; // Simplified - would need runway geometry
        bool runway_surface_phase = preliftoff;

        // Build safety inputs
        bool aoa_valid = is_finite(curr_aoa) && std::abs(curr_aoa) < 89.0 && curr_ias > 10.0;
        const int prior_off_runway_steps = resolve_prior_off_runway_steps(resolved_state);
        int off_runway_steps =
            runway_surface_phase && (!on_runway_task) ? (prior_off_runway_steps + 1) : 0;
        SafetyRuntimeInputs safety_inputs =
            build_safety_inputs(config, finite_state_valid, airborne, aoa_valid, curr_aoa, curr_g,
                                curr_alt_agl, curr_roll,
                                false, // gear_collapsed - simplified
                                runway_surface_phase, on_runway_task,
                                0.0, // gear_stress - simplified
                                off_runway_steps);

        // Build flight shaping inputs
        FlightShapingRuntimeInputs shaping_inputs = build_flight_shaping_inputs(
            config, resolved_state, curr_ias, curr_alt_agl, curr_gear, curr_roll, heading_error_deg,
            ground_track_error_deg, preliftoff, on_runway_task, airborne, false, 0.0,
            0.0, // runway cross - simplified
            ils_valid, ils_loc);

        // Build execution step inputs
        ExecutionStepRuntimeInputs exec_inputs;
        exec_inputs.truncated = resolved_state.truncated;
        exec_inputs.safety = safety_inputs;
        // Approach and waypoint inputs omitted for simplification

        // Build execution episode inputs
        runtime_inputs.has_execution_step = true;
        runtime_inputs.execution_step = exec_inputs;
        runtime_inputs.has_flight_shaping = true;
        runtime_inputs.flight_shaping = shaping_inputs;
        runtime_inputs.include_roll_stability = resolved_state.truth_z < 100.0;

        results.push_back(runtime_inputs);
    }

    return results;
}
