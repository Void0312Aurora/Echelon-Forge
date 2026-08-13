#include "interfaces/python/bindings_episode_detail.h"

#include "core/geometry/spatial_query_runtime.h"
#include "core/mission/episode/episode_reward_breakdown.h"
#include "core/mission/episode/execution_episode_batch_prepare.h"
#include "core/mission/runtime/execution_episode_runtime.h"
#include "core/mission/episode/execution_episode_state.h"
#include "core/mission/runtime/execution_frame_runtime.h"
#include "core/mission/runtime/execution_observation_runtime.h"
#include "core/mission/runtime/execution_step_runtime.h"
#include "core/mission/runtime/mission_runtime.h"
#include "core/mission/runtime/objective_runtime.h"
#include "core/mission/runtime/reward_runtime.h"
#include "core/mission/runtime/termination_runtime.h"

void bind_episode_state_batch(nb::module_ &m) {
    nb::class_<ExecutionEpisodeState>(m, "ExecutionEpisodeState")
        .def(nb::init<>())
        .def_rw("agent_id", &ExecutionEpisodeState::agent_id)
        .def_rw("step_count", &ExecutionEpisodeState::step_count)
        .def_rw("has_mission_command", &ExecutionEpisodeState::has_mission_command)
        .def_rw("mission_command", &ExecutionEpisodeState::mission_command)
        .def_rw("has_mission_command_json", &ExecutionEpisodeState::has_mission_command_json)
        .def_rw("mission_command_json", &ExecutionEpisodeState::mission_command_json)
        .def_rw("route_waypoints", &ExecutionEpisodeState::route_waypoints)
        .def_rw("waypoint_index", &ExecutionEpisodeState::waypoint_index)
        .def_rw("has_waypoint_prev_dist_m", &ExecutionEpisodeState::has_waypoint_prev_dist_m)
        .def_rw("waypoint_prev_dist_m", &ExecutionEpisodeState::waypoint_prev_dist_m)
        .def_rw("waypoint_total_route_length_m",
                &ExecutionEpisodeState::waypoint_total_route_length_m)
        .def_rw("waypoint_leg_origin_x_m", &ExecutionEpisodeState::waypoint_leg_origin_x_m)
        .def_rw("waypoint_leg_origin_y_m", &ExecutionEpisodeState::waypoint_leg_origin_y_m)
        .def_rw("prev_altitude_m", &ExecutionEpisodeState::prev_altitude_m)
        .def_rw("prev_ias_mps", &ExecutionEpisodeState::prev_ias_mps)
        .def_rw("liftoff_awarded", &ExecutionEpisodeState::liftoff_awarded)
        .def_rw("gear_bonus_awarded", &ExecutionEpisodeState::gear_bonus_awarded)
        .def_rw("off_runway_steps", &ExecutionEpisodeState::off_runway_steps)
        .def_rw("has_approach_prev_dme_m", &ExecutionEpisodeState::has_approach_prev_dme_m)
        .def_rw("approach_prev_dme_m", &ExecutionEpisodeState::approach_prev_dme_m)
        .def_rw("has_approach_prev_loc_abs", &ExecutionEpisodeState::has_approach_prev_loc_abs)
        .def_rw("approach_prev_loc_abs", &ExecutionEpisodeState::approach_prev_loc_abs)
        .def_rw("has_approach_prev_gs_abs", &ExecutionEpisodeState::has_approach_prev_gs_abs)
        .def_rw("approach_prev_gs_abs", &ExecutionEpisodeState::approach_prev_gs_abs)
        .def_rw("has_post_waypoint_transition_json",
                &ExecutionEpisodeState::has_post_waypoint_transition_json)
        .def_rw("post_waypoint_transition_json",
                &ExecutionEpisodeState::post_waypoint_transition_json)
        .def_rw("mission_phase_name", &ExecutionEpisodeState::mission_phase_name)
        .def_rw("has_cached_route_ref_id", &ExecutionEpisodeState::has_cached_route_ref_id)
        .def_rw("cached_route_ref_id", &ExecutionEpisodeState::cached_route_ref_id)
        .def_rw("last_termination_reason", &ExecutionEpisodeState::last_termination_reason)
        .def_rw("last_reward_total", &ExecutionEpisodeState::last_reward_total)
        .def_rw("last_reward_breakdown_json", &ExecutionEpisodeState::last_reward_breakdown_json);

    m.def("execution_episode_states_equivalent", &execution_episode_states_equivalent,
          nb::arg("lhs"), nb::arg("rhs"));

    // Batch preparation API
    nb::class_<StepEvaluationBatchConfig>(m, "StepEvaluationBatchConfig")
        .def(nb::init<>())
        .def_rw("altitude_progress_weight", &StepEvaluationBatchConfig::altitude_progress_weight)
        .def_rw("speed_progress_weight", &StepEvaluationBatchConfig::speed_progress_weight)
        .def_rw("speed_progress_negative_weight",
                &StepEvaluationBatchConfig::speed_progress_negative_weight)
        .def_rw("stationary_penalty", &StepEvaluationBatchConfig::stationary_penalty)
        .def_rw("stationary_grace_steps", &StepEvaluationBatchConfig::stationary_grace_steps)
        .def_rw("stationary_speed_threshold_mps",
                &StepEvaluationBatchConfig::stationary_speed_threshold_mps)
        .def_rw("stationary_alt_threshold_m",
                &StepEvaluationBatchConfig::stationary_alt_threshold_m)
        .def_rw("liftoff_bonus", &StepEvaluationBatchConfig::liftoff_bonus)
        .def_rw("liftoff_speed_threshold_mps",
                &StepEvaluationBatchConfig::liftoff_speed_threshold_mps)
        .def_rw("liftoff_alt_threshold_m", &StepEvaluationBatchConfig::liftoff_alt_threshold_m)
        .def_rw("crash_penalty", &StepEvaluationBatchConfig::crash_penalty)
        .def_rw("target_altitude_m", &StepEvaluationBatchConfig::target_altitude_m)
        .def_rw("target_speed_mps", &StepEvaluationBatchConfig::target_speed_mps)
        .def_rw("target_heading_deg", &StepEvaluationBatchConfig::target_heading_deg)
        .def_rw("time_step_s", &StepEvaluationBatchConfig::time_step_s);

    nb::class_<StepEvaluationBatchEnvState>(m, "StepEvaluationBatchEnvState")
        .def(nb::init<>())
        .def_rw("steps", &StepEvaluationBatchEnvState::steps)
        .def_rw("max_steps", &StepEvaluationBatchEnvState::max_steps)
        .def_rw("truncated", &StepEvaluationBatchEnvState::truncated)
        .def_rw("truth_x", &StepEvaluationBatchEnvState::truth_x)
        .def_rw("truth_y", &StepEvaluationBatchEnvState::truth_y)
        .def_rw("truth_z", &StepEvaluationBatchEnvState::truth_z)
        .def_rw("truth_vx", &StepEvaluationBatchEnvState::truth_vx)
        .def_rw("truth_vy", &StepEvaluationBatchEnvState::truth_vy)
        .def_rw("truth_vz", &StepEvaluationBatchEnvState::truth_vz)
        .def_rw("truth_speed", &StepEvaluationBatchEnvState::truth_speed)
        .def_rw("truth_pitch", &StepEvaluationBatchEnvState::truth_pitch)
        .def_rw("truth_roll", &StepEvaluationBatchEnvState::truth_roll)
        .def_rw("truth_heading", &StepEvaluationBatchEnvState::truth_heading)
        .def_rw("truth_health", &StepEvaluationBatchEnvState::truth_health)
        .def_rw("inst_vec", &StepEvaluationBatchEnvState::inst_vec)
        .def_rw("ils_vec", &StepEvaluationBatchEnvState::ils_vec)
        .def_rw("liftoff_awarded", &StepEvaluationBatchEnvState::liftoff_awarded)
        .def_rw("gear_bonus_awarded", &StepEvaluationBatchEnvState::gear_bonus_awarded)
        .def_rw("prev_altitude_m", &StepEvaluationBatchEnvState::prev_altitude_m)
        .def_rw("prev_ias_mps", &StepEvaluationBatchEnvState::prev_ias_mps)
        .def_rw("defer_landing_post_transition",
                &StepEvaluationBatchEnvState::defer_landing_post_transition)
        .def_rw("has_episode_state", &StepEvaluationBatchEnvState::has_episode_state)
        .def_rw("episode_state", &StepEvaluationBatchEnvState::episode_state)
        .def_rw("has_mission_observation", &StepEvaluationBatchEnvState::has_mission_observation)
        .def_rw("mission_observation", &StepEvaluationBatchEnvState::mission_observation)
        .def_rw("has_step_info", &StepEvaluationBatchEnvState::has_step_info)
        .def_rw("step_info", &StepEvaluationBatchEnvState::step_info)
        .def_rw("has_safety", &StepEvaluationBatchEnvState::has_safety)
        .def_rw("safety", &StepEvaluationBatchEnvState::safety)
        .def_rw("has_waypoint", &StepEvaluationBatchEnvState::has_waypoint)
        .def_rw("waypoint", &StepEvaluationBatchEnvState::waypoint)
        .def_rw("waypoint_episode_success", &StepEvaluationBatchEnvState::waypoint_episode_success)
        .def_rw("waypoint_episode_success_bonus",
                &StepEvaluationBatchEnvState::waypoint_episode_success_bonus)
        .def_rw("has_approach", &StepEvaluationBatchEnvState::has_approach)
        .def_rw("approach", &StepEvaluationBatchEnvState::approach)
        .def_rw("has_objectives", &StepEvaluationBatchEnvState::has_objectives)
        .def_rw("objectives", &StepEvaluationBatchEnvState::objectives)
        .def_rw("objective_inputs", &StepEvaluationBatchEnvState::objective_inputs)
        .def_rw("objective_shaping", &StepEvaluationBatchEnvState::objective_shaping)
        .def_rw("has_flight_shaping", &StepEvaluationBatchEnvState::has_flight_shaping)
        .def_rw("flight_shaping", &StepEvaluationBatchEnvState::flight_shaping)
        .def_rw("include_roll_stability", &StepEvaluationBatchEnvState::include_roll_stability);

    m.def("prepare_step_evaluations_batch", &prepare_step_evaluations_batch, nb::arg("config"),
          nb::arg("env_states"), nb::call_guard<nb::gil_scoped_release>());
}
