#include "core/mission/episode/execution_episode_batch_prepare.h"
#include "core/mission/runtime/reward_runtime.h"
#include <cmath>
#include <algorithm>

namespace {

inline bool is_finite(double x) {
    return std::isfinite(x);
}

inline bool check_finite_state(const StepEvaluationBatchEnvState& state) {
    return is_finite(state.truth_x) &&
           is_finite(state.truth_y) &&
           is_finite(state.truth_z) &&
           is_finite(state.truth_vx) &&
           is_finite(state.truth_vy) &&
           is_finite(state.truth_vz) &&
           is_finite(state.truth_speed) &&
           is_finite(state.truth_pitch) &&
           is_finite(state.truth_roll) &&
           is_finite(state.truth_heading) &&
           is_finite(state.truth_health);
}

inline double safe_get(const std::vector<double>& vec, size_t idx, double default_val = 0.0) {
    return idx < vec.size() ? vec[idx] : default_val;
}

bool has_rich_runtime_inputs(const StepEvaluationBatchEnvState& state) {
    return state.has_mission_observation ||
        state.has_step_info ||
        state.has_safety ||
        state.has_waypoint ||
        state.has_approach ||
        state.has_objectives ||
        state.has_flight_shaping;
}

ExecutionEpisodeRuntimeInputs build_rich_runtime_inputs(const StepEvaluationBatchEnvState& state) {
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

StepEvaluationBatchEnvState resolve_episode_state_overrides(const StepEvaluationBatchEnvState& state) {
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

int resolve_prior_off_runway_steps(const StepEvaluationBatchEnvState& state) {
    if (state.has_episode_state) {
        return std::max(0, int(state.episode_state.off_runway_steps));
    }
    return 0;
}

FlightShapingRuntimeInputs build_flight_shaping_inputs(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& state,
    double curr_ias,
    double curr_alt_agl,
    double curr_gear,
    double curr_roll,
    double heading_error_deg,
    double ground_track_error_deg,
    bool preliftoff,
    bool on_runway_task,
    bool airborne,
    bool has_runway_cross_m,
    double runway_cross_m,
    double runway_width_m,
    double ils_valid,
    double ils_loc
) {
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

    // Config-static fields (same for all envs)
    inputs.altitude_progress_weight = config.altitude_progress_weight;
    inputs.speed_progress_weight = config.speed_progress_weight;
    inputs.speed_progress_negative_weight = config.speed_progress_negative_weight;
    inputs.stationary_penalty = config.stationary_penalty;
    inputs.stationary_grace_steps = config.stationary_grace_steps;
    inputs.stationary_speed_threshold_mps = config.stationary_speed_threshold_mps;
    inputs.stationary_alt_threshold_m = config.stationary_alt_threshold_m;
    inputs.liftoff_bonus = config.liftoff_bonus;
    inputs.liftoff_speed_threshold_mps = config.liftoff_speed_threshold_mps;
    inputs.liftoff_alt_threshold_m = config.liftoff_alt_threshold_m;
    inputs.rotation_reward_weight = config.rotation_reward_weight;
    inputs.rotation_speed_threshold_mps = config.rotation_speed_threshold_mps;
    inputs.rotation_alt_threshold_m = config.rotation_alt_threshold_m;
    inputs.rotation_pitch_cap_deg = config.rotation_pitch_cap_deg;
    inputs.rotation_overpitch_penalty_weight = config.rotation_overpitch_penalty_weight;
    inputs.gear_up_bonus = config.gear_up_bonus;
    inputs.gear_up_bonus_min_alt_agl_m = config.gear_up_bonus_min_alt_agl_m;
    inputs.roll_stability_weight = config.roll_stability_weight;
    inputs.heading_error_weight = config.heading_error_weight;
    inputs.heading_hold_deadband_deg = config.heading_hold_deadband_deg;
    inputs.heading_hold_bonus = config.heading_hold_bonus;
    inputs.waypoint_turn_heading_relief_max = config.waypoint_turn_heading_relief_max;
    inputs.altitude_error_weight = config.altitude_error_weight;
    inputs.altitude_error_min_alt_m = config.altitude_error_min_alt_m;
    inputs.altitude_error_target_m = config.altitude_error_target_m;
    inputs.altitude_error_deadband_m = config.altitude_error_deadband_m;
    inputs.altitude_error_norm_m = config.altitude_error_norm_m;
    inputs.altitude_error_power = config.altitude_error_power;
    inputs.altitude_error_clip = config.altitude_error_clip;
    inputs.altitude_hold_bonus = config.altitude_hold_bonus;
    inputs.speed_error_weight = config.speed_error_weight;
    inputs.speed_error_min_ias_mps = config.speed_error_min_ias_mps;
    inputs.speed_error_target_mps = config.speed_error_target_mps;
    inputs.speed_error_deadband_mps = config.speed_error_deadband_mps;
    inputs.speed_error_norm_mps = config.speed_error_norm_mps;
    inputs.speed_error_power = config.speed_error_power;
    inputs.speed_error_clip = config.speed_error_clip;
    inputs.speed_hold_bonus = config.speed_hold_bonus;
    inputs.roll_abs_weight = config.roll_abs_weight;
    inputs.roll_abs_deadband_deg = config.roll_abs_deadband_deg;
    inputs.roll_abs_norm_deg = config.roll_abs_norm_deg;
    inputs.roll_abs_power = config.roll_abs_power;
    inputs.pitch_abs_weight = config.pitch_abs_weight;
    inputs.pitch_abs_deadband_deg = config.pitch_abs_deadband_deg;
    inputs.pitch_abs_norm_deg = config.pitch_abs_norm_deg;
    inputs.pitch_abs_power = config.pitch_abs_power;
    inputs.yaw_rate_abs_weight = config.yaw_rate_abs_weight;
    inputs.yaw_rate_abs_deadband_deg_s = config.yaw_rate_abs_deadband_deg_s;
    inputs.yaw_rate_abs_norm_deg_s = config.yaw_rate_abs_norm_deg_s;
    inputs.yaw_rate_abs_power = config.yaw_rate_abs_power;
    inputs.beta_abs_weight = config.beta_abs_weight;
    inputs.beta_abs_deadband_deg = config.beta_abs_deadband_deg;
    inputs.beta_abs_norm_deg = config.beta_abs_norm_deg;
    inputs.beta_abs_power = config.beta_abs_power;
    inputs.g_deviation_weight = config.g_deviation_weight;
    inputs.g_deviation_deadband = config.g_deviation_deadband;
    inputs.g_deviation_norm = config.g_deviation_norm;
    inputs.g_deviation_power = config.g_deviation_power;
    inputs.g_deviation_min_alt_agl_m = config.g_deviation_min_alt_agl_m;
    inputs.speed_reward_weight = config.speed_reward_weight;
    inputs.runway_centerline_penalty_min_ias_mps = config.runway_centerline_penalty_min_ias_mps;
    inputs.runway_centerline_penalty_max_ias_mps = config.runway_centerline_penalty_max_ias_mps;
    inputs.runway_centerline_m_penalty_weight = config.runway_centerline_m_penalty_weight;
    inputs.runway_centerline_m_deadband_m = config.runway_centerline_m_deadband_m;
    inputs.runway_centerline_m_norm_m = config.runway_centerline_m_norm_m;
    inputs.runway_centerline_m_power = config.runway_centerline_m_power;
    inputs.runway_centerline_m_clip = config.runway_centerline_m_clip;
    inputs.runway_centerline_penalty_weight = config.runway_centerline_penalty_weight;
    inputs.runway_centerline_safe_frac = config.runway_centerline_safe_frac;
    inputs.runway_centerline_penalty_power = config.runway_centerline_penalty_power;
    inputs.runway_centerline_barrier_weight = config.runway_centerline_barrier_weight;
    inputs.runway_centerline_barrier_clip_frac = config.runway_centerline_barrier_clip_frac;
    inputs.departure_centerline_max_alt_agl_m = config.departure_centerline_max_alt_agl_m;
    inputs.departure_centerline_m_penalty_weight = config.departure_centerline_m_penalty_weight;
    inputs.departure_centerline_m_deadband_m = config.departure_centerline_m_deadband_m;
    inputs.departure_centerline_m_norm_m = config.departure_centerline_m_norm_m;
    inputs.departure_centerline_m_power = config.departure_centerline_m_power;
    inputs.departure_centerline_m_clip = config.departure_centerline_m_clip;
    inputs.departure_centerline_reward_weight = config.departure_centerline_reward_weight;
    inputs.departure_centerline_reward_band_m = config.departure_centerline_reward_band_m;
    inputs.departure_track_error_weight = config.departure_track_error_weight;
    inputs.departure_track_error_deadband_deg = config.departure_track_error_deadband_deg;
    inputs.departure_track_error_norm_deg = config.departure_track_error_norm_deg;
    inputs.departure_track_error_power = config.departure_track_error_power;
    inputs.departure_track_error_clip = config.departure_track_error_clip;
    inputs.departure_track_reward_weight = config.departure_track_reward_weight;
    inputs.departure_track_reward_band_deg = config.departure_track_reward_band_deg;
    inputs.alignment_reward_weight = config.alignment_reward_weight;
    inputs.mission_alignment_min_alt_m = config.mission_alignment_min_alt_m;

    return inputs;
}

SafetyRuntimeInputs build_safety_inputs(
    const StepEvaluationBatchConfig& config,
    bool finite_state_valid,
    bool airborne,
    bool aoa_valid,
    double curr_aoa,
    double curr_g,
    double curr_alt_agl,
    double curr_roll,
    bool gear_collapsed,
    bool runway_surface_phase,
    bool on_runway_task,
    double gear_stress,
    int off_runway_steps
) {
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

std::vector<ExecutionEpisodeRuntimeInputs> prepare_step_evaluations_batch(
    const StepEvaluationBatchConfig& config,
    const std::vector<StepEvaluationBatchEnvState>& env_states
) {
    std::vector<ExecutionEpisodeRuntimeInputs> results;
    results.reserve(env_states.size());

    for (const auto& state : env_states) {
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
        double curr_ground_speed = safe_get(resolved_state.inst_vec, 29,
            std::hypot(resolved_state.truth_vx, resolved_state.truth_vy));

        // Compute heading errors (simplified - assumes target_heading is in config)
        double heading_error_deg = config.target_heading_deg - resolved_state.truth_heading;
        while (heading_error_deg > 180.0) heading_error_deg -= 360.0;
        while (heading_error_deg < -180.0) heading_error_deg += 360.0;
        double ground_track_error_deg = heading_error_deg; // Simplified

        // ILS values
        double ils_valid = safe_get(resolved_state.ils_vec, 0);
        double ils_loc = safe_get(resolved_state.ils_vec, 1);
        double ils_gs = safe_get(resolved_state.ils_vec, 2);
        double ils_dme = safe_get(resolved_state.ils_vec, 3);

        // Check finite state
        bool finite_state_valid = check_finite_state(resolved_state) &&
            is_finite(curr_ias) && is_finite(curr_alt_agl) &&
            is_finite(curr_aoa) && is_finite(curr_roll) && is_finite(curr_g);

        // Determine flight phase
        bool on_ground = curr_alt_agl <= 1.0; // Simplified threshold
        bool airborne = curr_alt_agl >= 5.0;  // Simplified threshold
        bool preliftoff = !airborne;
        bool on_runway_task = false; // Simplified - would need runway geometry
        bool runway_surface_phase = preliftoff;

        // Build safety inputs
        bool aoa_valid = is_finite(curr_aoa) && std::abs(curr_aoa) < 89.0 && curr_ias > 10.0;
        const int prior_off_runway_steps = resolve_prior_off_runway_steps(resolved_state);
        int off_runway_steps = runway_surface_phase && (!on_runway_task)
            ? (prior_off_runway_steps + 1)
            : 0;
        SafetyRuntimeInputs safety_inputs = build_safety_inputs(
            config, finite_state_valid, airborne, aoa_valid,
            curr_aoa, curr_g, curr_alt_agl, curr_roll,
            false, // gear_collapsed - simplified
            runway_surface_phase, on_runway_task,
            0.0, // gear_stress - simplified
            off_runway_steps
        );

        // Build flight shaping inputs
        FlightShapingRuntimeInputs shaping_inputs = build_flight_shaping_inputs(
            config, resolved_state,
            curr_ias, curr_alt_agl, curr_gear, curr_roll,
            heading_error_deg, ground_track_error_deg,
            preliftoff, on_runway_task, airborne,
            false, 0.0, 0.0, // runway cross - simplified
            ils_valid, ils_loc
        );

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
