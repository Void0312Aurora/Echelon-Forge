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

void bind_episode_execution_runtime(nb::module_ &m) {
    nb::class_<ExecutionStepRuntimeInputs>(m, "ExecutionStepRuntimeInputs")
        .def(nb::init<>())
        .def_rw("safety", &ExecutionStepRuntimeInputs::safety)
        .def_rw("has_waypoint", &ExecutionStepRuntimeInputs::has_waypoint)
        .def_rw("waypoint", &ExecutionStepRuntimeInputs::waypoint)
        .def_rw("waypoint_episode_success", &ExecutionStepRuntimeInputs::waypoint_episode_success)
        .def_rw("waypoint_episode_success_bonus",
                &ExecutionStepRuntimeInputs::waypoint_episode_success_bonus)
        .def_rw("has_approach", &ExecutionStepRuntimeInputs::has_approach)
        .def_rw("approach", &ExecutionStepRuntimeInputs::approach)
        .def_rw("has_objectives", &ExecutionStepRuntimeInputs::has_objectives)
        .def_rw("objectives", &ExecutionStepRuntimeInputs::objectives)
        .def_rw("objective_inputs", &ExecutionStepRuntimeInputs::objective_inputs)
        .def_rw("objective_shaping", &ExecutionStepRuntimeInputs::objective_shaping)
        .def_rw("truncated", &ExecutionStepRuntimeInputs::truncated);

    nb::class_<ExecutionStepRuntimeProducts>(m, "ExecutionStepRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &ExecutionStepRuntimeProducts::valid)
        .def_ro("safety", &ExecutionStepRuntimeProducts::safety)
        .def_ro("waypoint_evaluated", &ExecutionStepRuntimeProducts::waypoint_evaluated)
        .def_ro("waypoint", &ExecutionStepRuntimeProducts::waypoint)
        .def_ro("waypoint_episode_success", &ExecutionStepRuntimeProducts::waypoint_episode_success)
        .def_ro("waypoint_episode_success_bonus",
                &ExecutionStepRuntimeProducts::waypoint_episode_success_bonus)
        .def_ro("approach_evaluated", &ExecutionStepRuntimeProducts::approach_evaluated)
        .def_ro("approach", &ExecutionStepRuntimeProducts::approach)
        .def_ro("objective_evaluated", &ExecutionStepRuntimeProducts::objective_evaluated)
        .def_ro("matched_objective_index", &ExecutionStepRuntimeProducts::matched_objective_index)
        .def_ro("objective_status_count", &ExecutionStepRuntimeProducts::objective_status_count)
        .def_ro("objective", &ExecutionStepRuntimeProducts::objective)
        .def_ro("compiled_reward_total", &ExecutionStepRuntimeProducts::compiled_reward_total)
        .def_ro("terminated", &ExecutionStepRuntimeProducts::terminated)
        .def_ro("status0", &ExecutionStepRuntimeProducts::status0)
        .def_ro("status1", &ExecutionStepRuntimeProducts::status1)
        .def_ro("status2", &ExecutionStepRuntimeProducts::status2)
        .def_ro("status3", &ExecutionStepRuntimeProducts::status3)
        .def_ro("reason_code", &ExecutionStepRuntimeProducts::reason_code)
        .def_ro("final_reason_code", &ExecutionStepRuntimeProducts::final_reason_code);

    m.def("compute_execution_step_runtime", &compute_execution_step_runtime, nb::arg("inputs"));

    nb::class_<ExecutionFrameRuntimeInputs>(m, "ExecutionFrameRuntimeInputs")
        .def(nb::init<>())
        .def_rw("has_mission_observation", &ExecutionFrameRuntimeInputs::has_mission_observation)
        .def_rw("mission_observation", &ExecutionFrameRuntimeInputs::mission_observation)
        .def_rw("has_step_info", &ExecutionFrameRuntimeInputs::has_step_info)
        .def_rw("step_info", &ExecutionFrameRuntimeInputs::step_info)
        .def_rw("has_execution_step", &ExecutionFrameRuntimeInputs::has_execution_step)
        .def_rw("execution_step", &ExecutionFrameRuntimeInputs::execution_step)
        .def_rw("has_flight_shaping", &ExecutionFrameRuntimeInputs::has_flight_shaping)
        .def_rw("flight_shaping", &ExecutionFrameRuntimeInputs::flight_shaping);

    nb::class_<ExecutionFrameRuntimeProducts>(m, "ExecutionFrameRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &ExecutionFrameRuntimeProducts::valid)
        .def_ro("mission_observation_evaluated",
                &ExecutionFrameRuntimeProducts::mission_observation_evaluated)
        .def_ro("mission_observation", &ExecutionFrameRuntimeProducts::mission_observation)
        .def_ro("step_info_evaluated", &ExecutionFrameRuntimeProducts::step_info_evaluated)
        .def_ro("step_info", &ExecutionFrameRuntimeProducts::step_info)
        .def_ro("execution_step_evaluated",
                &ExecutionFrameRuntimeProducts::execution_step_evaluated)
        .def_ro("execution_step", &ExecutionFrameRuntimeProducts::execution_step)
        .def_ro("flight_shaping_evaluated",
                &ExecutionFrameRuntimeProducts::flight_shaping_evaluated)
        .def_ro("flight_shaping", &ExecutionFrameRuntimeProducts::flight_shaping);

    m.def("compute_execution_frame_runtime", &compute_execution_frame_runtime, nb::arg("inputs"));
    m.def("compute_execution_frame_runtime_batch", &compute_execution_frame_runtime_batch,
          nb::arg("inputs_batch"), nb::call_guard<nb::gil_scoped_release>());

    nb::class_<ExecutionEpisodeRuntimeInputs>(m, "ExecutionEpisodeRuntimeInputs")
        .def(nb::init<>())
        .def_rw("has_mission_observation", &ExecutionEpisodeRuntimeInputs::has_mission_observation)
        .def_rw("mission_observation", &ExecutionEpisodeRuntimeInputs::mission_observation)
        .def_rw("has_step_info", &ExecutionEpisodeRuntimeInputs::has_step_info)
        .def_rw("step_info", &ExecutionEpisodeRuntimeInputs::step_info)
        .def_rw("has_execution_step", &ExecutionEpisodeRuntimeInputs::has_execution_step)
        .def_rw("execution_step", &ExecutionEpisodeRuntimeInputs::execution_step)
        .def_rw("has_flight_shaping", &ExecutionEpisodeRuntimeInputs::has_flight_shaping)
        .def_rw("flight_shaping", &ExecutionEpisodeRuntimeInputs::flight_shaping)
        .def_rw("include_roll_stability", &ExecutionEpisodeRuntimeInputs::include_roll_stability);

    nb::class_<ExecutionEpisodeRuntimeProducts>(m, "ExecutionEpisodeRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &ExecutionEpisodeRuntimeProducts::valid)
        .def_ro("mission_observation_evaluated",
                &ExecutionEpisodeRuntimeProducts::mission_observation_evaluated)
        .def_ro("mission_observation", &ExecutionEpisodeRuntimeProducts::mission_observation)
        .def_ro("step_info_evaluated", &ExecutionEpisodeRuntimeProducts::step_info_evaluated)
        .def_ro("step_info", &ExecutionEpisodeRuntimeProducts::step_info)
        .def_ro("execution_step_evaluated",
                &ExecutionEpisodeRuntimeProducts::execution_step_evaluated)
        .def_ro("execution_step", &ExecutionEpisodeRuntimeProducts::execution_step)
        .def_ro("flight_shaping_evaluated",
                &ExecutionEpisodeRuntimeProducts::flight_shaping_evaluated)
        .def_ro("flight_shaping", &ExecutionEpisodeRuntimeProducts::flight_shaping)
        .def_ro("outcome_evaluated", &ExecutionEpisodeRuntimeProducts::outcome_evaluated)
        .def_ro("compiled_reward_total", &ExecutionEpisodeRuntimeProducts::compiled_reward_total)
        .def_ro("terminated", &ExecutionEpisodeRuntimeProducts::terminated)
        .def_ro("status0", &ExecutionEpisodeRuntimeProducts::status0)
        .def_ro("status1", &ExecutionEpisodeRuntimeProducts::status1)
        .def_ro("status2", &ExecutionEpisodeRuntimeProducts::status2)
        .def_ro("status3", &ExecutionEpisodeRuntimeProducts::status3)
        .def_ro("reason_code", &ExecutionEpisodeRuntimeProducts::reason_code)
        .def_ro("final_reason_code", &ExecutionEpisodeRuntimeProducts::final_reason_code);

    m.def("compute_execution_episode_runtime", &compute_execution_episode_runtime,
          nb::arg("inputs"));
    m.def("compute_execution_episode_runtime_batch", &compute_execution_episode_runtime_batch,
          nb::arg("inputs_batch"), nb::call_guard<nb::gil_scoped_release>());
    m.def("build_episode_reward_breakdown_json", &build_episode_reward_breakdown_json,
          nb::arg("runtime_inputs"), nb::arg("products"), nb::arg("reward_total"),
          nb::arg("waypoint_arrived"), nb::arg("had_post_waypoint_transition_before"),
          nb::arg("phase_transition_bonus"));
}
