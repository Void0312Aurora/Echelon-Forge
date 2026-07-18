#pragma once

#include <cstdint>
#include <vector>

#include "core/mission/runtime/execution_episode_runtime.h"
#include "core/mission/episode/execution_episode_state.h"

// Batch preparation inputs for step evaluation
// This struct contains all the data needed to prepare ExecutionEpisodeRuntimeInputs
// for a batch of environments in C++, avoiding Python loop overhead

struct StepEvaluationBatchConfig {
    // Scenario-static configuration (same for all envs)
    // Flight shaping weights, shared field-for-field with
    // FlightShapingRuntimeInputs via the X-macro list in
    // core/mission/runtime/detail/flight_shaping_shared_fields.inc.
#define EF_FLIGHT_SHAPING_FIELD(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/flight_shaping_shared_fields.inc"

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
