#pragma once

#include <cstdint>
#include <vector>

#include "core/mission/execution_episode_runtime.h"
#include "core/mission/execution_episode_state.h"

// Batch preparation inputs for step evaluation
// This struct contains all the data needed to prepare ExecutionEpisodeRuntimeInputs
// for a batch of environments in C++, avoiding Python loop overhead

struct StepEvaluationBatchConfig {
    // Scenario-static configuration (same for all envs)
    // Flight shaping weights
    double altitude_progress_weight = 0.0;
    double speed_progress_weight = 0.0;
    double speed_progress_negative_weight = 0.0;
    double stationary_penalty = 0.0;
    int stationary_grace_steps = 20;
    double stationary_speed_threshold_mps = 5.0;
    double stationary_alt_threshold_m = 5.0;
    double liftoff_bonus = 0.0;
    double liftoff_speed_threshold_mps = 80.0;
    double liftoff_alt_threshold_m = 5.0;
    double rotation_reward_weight = 0.0;
    double rotation_speed_threshold_mps = 80.0;
    double rotation_alt_threshold_m = 5.0;
    double rotation_pitch_cap_deg = 15.0;
    double rotation_overpitch_penalty_weight = 0.0;
    double gear_up_bonus = 0.0;
    double gear_up_bonus_min_alt_agl_m = 50.0;
    double roll_stability_weight = 0.0;
    double heading_error_weight = 0.0;
    double heading_hold_deadband_deg = 0.0;
    double heading_hold_bonus = 0.0;
    double waypoint_turn_heading_relief_max = 0.0;
    double altitude_error_weight = 0.0;
    double altitude_error_min_alt_m = 0.0;
    double altitude_error_target_m = 0.0;
    double altitude_error_deadband_m = 0.0;
    double altitude_error_norm_m = 100.0;
    double altitude_error_power = 1.0;
    double altitude_error_clip = 0.0;
    double altitude_hold_bonus = 0.0;
    double speed_error_weight = 0.0;
    double speed_error_min_ias_mps = 0.0;
    double speed_error_target_mps = 0.0;
    double speed_error_deadband_mps = 0.0;
    double speed_error_norm_mps = 30.0;
    double speed_error_power = 1.0;
    double speed_error_clip = 0.0;
    double speed_hold_bonus = 0.0;
    double roll_abs_weight = 0.0;
    double roll_abs_deadband_deg = 0.0;
    double roll_abs_norm_deg = 30.0;
    double roll_abs_power = 1.0;
    double pitch_abs_weight = 0.0;
    double pitch_abs_deadband_deg = 0.0;
    double pitch_abs_norm_deg = 20.0;
    double pitch_abs_power = 1.0;
    double yaw_rate_abs_weight = 0.0;
    double yaw_rate_abs_deadband_deg_s = 0.0;
    double yaw_rate_abs_norm_deg_s = 10.0;
    double yaw_rate_abs_power = 1.0;
    double beta_abs_weight = 0.0;
    double beta_abs_deadband_deg = 0.0;
    double beta_abs_norm_deg = 10.0;
    double beta_abs_power = 1.0;
    double g_deviation_weight = 0.0;
    double g_deviation_deadband = 0.0;
    double g_deviation_norm = 0.5;
    double g_deviation_power = 1.0;
    double g_deviation_min_alt_agl_m = 5.0;
    double speed_reward_weight = 0.0;
    double runway_centerline_penalty_min_ias_mps = 0.0;
    double runway_centerline_penalty_max_ias_mps = 0.0;
    double runway_centerline_m_penalty_weight = 0.0;
    double runway_centerline_m_deadband_m = 0.0;
    double runway_centerline_m_norm_m = 5.0;
    double runway_centerline_m_power = 2.0;
    double runway_centerline_m_clip = 0.0;
    double runway_centerline_penalty_weight = 0.0;
    double runway_centerline_safe_frac = 0.0;
    double runway_centerline_penalty_power = 2.0;
    double runway_centerline_barrier_weight = 0.0;
    double runway_centerline_barrier_clip_frac = 0.995;
    double departure_centerline_max_alt_agl_m = 0.0;
    double departure_centerline_m_penalty_weight = 0.0;
    double departure_centerline_m_deadband_m = 0.0;
    double departure_centerline_m_norm_m = 20.0;
    double departure_centerline_m_power = 2.0;
    double departure_centerline_m_clip = 0.0;
    double departure_centerline_reward_weight = 0.0;
    double departure_centerline_reward_band_m = 1.0;
    double departure_track_error_weight = 0.0;
    double departure_track_error_deadband_deg = 0.0;
    double departure_track_error_norm_deg = 10.0;
    double departure_track_error_power = 2.0;
    double departure_track_error_clip = 0.0;
    double departure_track_reward_weight = 0.0;
    double departure_track_reward_band_deg = 10.0;
    double alignment_reward_weight = 0.0;
    double mission_alignment_min_alt_m = 120.0;

    // Safety configuration
    double crash_penalty = -1000.0;
    double aoa_penalty_weight = 0.0;
    double aoa_penalty_threshold_deg = 25.0;
    double aoa_penalty_norm_deg = 10.0;
    double aoa_penalty_power = 2.0;
    double g_penalty_weight = 0.0;
    double g_penalty_threshold = 7.0;
    double g_penalty_norm = 2.0;
    double g_penalty_power = 2.0;
    double roll_penalty_weight = 0.0;
    double roll_penalty_threshold_deg = 60.0;
    double roll_penalty_norm_deg = 20.0;
    double roll_penalty_power = 2.0;
    double gear_stress_penalty_weight = 0.0;
    double gear_stress_penalty_threshold = 1.5;
    double gear_stress_penalty_norm = 0.5;
    double gear_stress_penalty_power = 2.0;
    double off_runway_penalty_weight = 0.0;
    int off_runway_grace_steps = 5;

    // Mission parameters
    double target_altitude_m = 0.0;
    double target_speed_mps = 0.0;
    double target_heading_deg = 0.0;
    double time_step_s = 0.05;
};

struct StepEvaluationBatchEnvState {
    // Per-environment dynamic state
    int steps = 0;
    int max_steps = 1000;
    bool truncated = false;

    // Truth state (from observation)
    double truth_x = 0.0;
    double truth_y = 0.0;
    double truth_z = 0.0;
    double truth_vx = 0.0;
    double truth_vy = 0.0;
    double truth_vz = 0.0;
    double truth_speed = 0.0;
    double truth_pitch = 0.0;
    double truth_roll = 0.0;
    double truth_heading = 0.0;
    double truth_health = 100.0;

    // Instrument vector (30+ elements)
    std::vector<double> inst_vec;

    // ILS vector (4 elements: valid, loc, gs, dme)
    std::vector<double> ils_vec;

    // Per-env state flags
    bool liftoff_awarded = false;
    bool gear_bonus_awarded = false;
    double prev_altitude_m = 0.0;
    double prev_ias_mps = 0.0;
    bool defer_landing_post_transition = false;

    // Optional compiled episode-state snapshot. This is not yet required by the
    // batch-prep path, but keeps the state contract available as Phase 2 grows.
    bool has_episode_state = false;
    ExecutionEpisodeState episode_state;

    // Rich prebuilt runtime inputs. When present, batch preparation will build
    // exact ExecutionEpisodeRuntimeInputs from these fields instead of falling
    // back to the older simplified derivation path.
    bool has_mission_observation = false;
    MissionObservationInputs mission_observation;

    bool has_step_info = false;
    StepInfoInputs step_info;

    bool has_safety = false;
    SafetyRuntimeInputs safety;

    bool has_waypoint = false;
    WaypointRewardInputs waypoint;
    bool waypoint_episode_success = false;
    double waypoint_episode_success_bonus = 0.0;

    bool has_approach = false;
    ApproachRewardInputs approach;

    bool has_objectives = false;
    std::vector<ConditionalObjectiveSpec> objectives;
    ConditionalObjectiveInputs objective_inputs;
    ObjectiveShapingConfig objective_shaping;

    bool has_flight_shaping = false;
    FlightShapingRuntimeInputs flight_shaping;
    bool include_roll_stability = false;
};

// Batch prepare step evaluations in C++
// Returns a vector of ExecutionEpisodeRuntimeInputs ready for compute_execution_episode_runtime_batch
std::vector<ExecutionEpisodeRuntimeInputs> prepare_step_evaluations_batch(
    const StepEvaluationBatchConfig& config,
    const std::vector<StepEvaluationBatchEnvState>& env_states
);
