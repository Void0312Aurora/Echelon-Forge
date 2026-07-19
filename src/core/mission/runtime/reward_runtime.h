#pragma once

struct WaypointRewardInputs {
#define EF_WAYPOINT_INPUT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/waypoint_reward_inputs.inc"
};

struct WaypointRewardProducts {
#define EF_WAYPOINT_PRODUCT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/waypoint_reward_products.inc"
};

struct ApproachRewardInputs {
#define EF_APPROACH_INPUT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/approach_reward_inputs.inc"
};

struct ApproachRewardProducts {
#define EF_APPROACH_PRODUCT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/approach_reward_products.inc"
};

struct FlightShapingRuntimeInputs {
    double truth_altitude_m = 0.0;
    double truth_speed_mps = 0.0;
    double prev_altitude_m = 0.0;
    double prev_ias_mps = 0.0;
    double curr_ias_mps = 0.0;
    double curr_alt_baro_m = 0.0;
    double curr_alt_agl_m = 0.0;
    double curr_gear_fraction = 0.0;
    double curr_roll_deg = 0.0;
    double curr_pitch_deg = 0.0;
    double curr_beta_deg = 0.0;
    double curr_yaw_rate_deg_s = 0.0;
    double curr_g_load = 1.0;
    int step_count = 0;

    double target_altitude_m = 0.0;
    double target_speed_mps = 0.0;
    double heading_error_deg = 0.0;
    double ground_track_error_deg = 0.0;
    double waypoint_turn_relief_activation = 0.0;

    bool preliftoff = false;
    bool on_runway_task = false;
    bool airborne = false;
    bool has_runway_cross_m = false;
    double runway_cross_m = 0.0;
    double runway_width_m = 0.0;
    bool ils_valid = false;
    double ils_loc_dev = 0.0;

    bool liftoff_awarded = false;
    bool gear_bonus_awarded = false;

    // Config-static shaping fields shared with StepEvaluationBatchConfig.
    // The single source of truth for names/types/defaults is the X-macro list
    // in detail/flight_shaping_shared_fields.inc.
#define EF_FLIGHT_SHAPING_FIELD(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/flight_shaping_shared_fields.inc"
};

struct FlightShapingRuntimeProducts {
    bool valid = false;
    double altitude_progress = 0.0;
    double low_alt_descent_penalty = 0.0;
    double speed_progress = 0.0;
    double speed_regress = 0.0;
    double stationary_penalty = 0.0;
    double liftoff_bonus = 0.0;
    bool next_liftoff_awarded = false;
    double rotation_reward = 0.0;
    double rotation_overpitch_penalty = 0.0;
    double gear_up_bonus = 0.0;
    bool next_gear_bonus_awarded = false;
    double roll_stability = 0.0;
    double heading_error_penalty = 0.0;
    double heading_hold_bonus = 0.0;
    double altitude_error_penalty = 0.0;
    double altitude_hold_bonus = 0.0;
    double speed_error_penalty = 0.0;
    double speed_hold_bonus = 0.0;
    double roll_abs_penalty = 0.0;
    double pitch_abs_penalty = 0.0;
    double yaw_rate_abs_penalty = 0.0;
    double beta_abs_penalty = 0.0;
    double g_deviation_penalty = 0.0;
    double speed_reward = 0.0;
    double runway_centerline_m_penalty = 0.0;
    double runway_centerline_penalty = 0.0;
    double runway_centerline_barrier = 0.0;
    double departure_centerline_m_penalty = 0.0;
    double departure_centerline_reward = 0.0;
    double departure_track_error_penalty = 0.0;
    double departure_track_reward = 0.0;
    double alignment_reward = 0.0;
};

WaypointRewardProducts compute_waypoint_reward_terms(const WaypointRewardInputs& inputs);
ApproachRewardProducts compute_approach_reward_terms(const ApproachRewardInputs& inputs);
FlightShapingRuntimeProducts compute_flight_shaping_terms(const FlightShapingRuntimeInputs& inputs);
