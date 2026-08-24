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

void bind_episode_flight_shaping(nb::module_ &m) {
    nb::class_<FlightShapingRuntimeInputs> flight_shaping_inputs_class(
        m, "FlightShapingRuntimeInputs");
    flight_shaping_inputs_class.def(nb::init<>())
        .def_rw("truth_altitude_m", &FlightShapingRuntimeInputs::truth_altitude_m)
        .def_rw("truth_speed_mps", &FlightShapingRuntimeInputs::truth_speed_mps)
        .def_rw("prev_altitude_m", &FlightShapingRuntimeInputs::prev_altitude_m)
        .def_rw("prev_ias_mps", &FlightShapingRuntimeInputs::prev_ias_mps)
        .def_rw("curr_ias_mps", &FlightShapingRuntimeInputs::curr_ias_mps)
        .def_rw("curr_alt_baro_m", &FlightShapingRuntimeInputs::curr_alt_baro_m)
        .def_rw("curr_alt_agl_m", &FlightShapingRuntimeInputs::curr_alt_agl_m)
        .def_rw("curr_gear_fraction", &FlightShapingRuntimeInputs::curr_gear_fraction)
        .def_rw("curr_roll_deg", &FlightShapingRuntimeInputs::curr_roll_deg)
        .def_rw("curr_pitch_deg", &FlightShapingRuntimeInputs::curr_pitch_deg)
        .def_rw("curr_beta_deg", &FlightShapingRuntimeInputs::curr_beta_deg)
        .def_rw("curr_yaw_rate_deg_s", &FlightShapingRuntimeInputs::curr_yaw_rate_deg_s)
        .def_rw("curr_g_load", &FlightShapingRuntimeInputs::curr_g_load)
        .def_rw("step_count", &FlightShapingRuntimeInputs::step_count)
        .def_rw("target_altitude_m", &FlightShapingRuntimeInputs::target_altitude_m)
        .def_rw("target_speed_mps", &FlightShapingRuntimeInputs::target_speed_mps)
        .def_rw("heading_error_deg", &FlightShapingRuntimeInputs::heading_error_deg)
        .def_rw("ground_track_error_deg", &FlightShapingRuntimeInputs::ground_track_error_deg)
        .def_rw("waypoint_turn_relief_activation",
                &FlightShapingRuntimeInputs::waypoint_turn_relief_activation)
        .def_rw("preliftoff", &FlightShapingRuntimeInputs::preliftoff)
        .def_rw("on_runway_task", &FlightShapingRuntimeInputs::on_runway_task)
        .def_rw("airborne", &FlightShapingRuntimeInputs::airborne)
        .def_rw("has_runway_cross_m", &FlightShapingRuntimeInputs::has_runway_cross_m)
        .def_rw("runway_cross_m", &FlightShapingRuntimeInputs::runway_cross_m)
        .def_rw("runway_width_m", &FlightShapingRuntimeInputs::runway_width_m)
        .def_rw("ils_valid", &FlightShapingRuntimeInputs::ils_valid)
        .def_rw("ils_loc_dev", &FlightShapingRuntimeInputs::ils_loc_dev)
        .def_rw("liftoff_awarded", &FlightShapingRuntimeInputs::liftoff_awarded)
        .def_rw("gear_bonus_awarded", &FlightShapingRuntimeInputs::gear_bonus_awarded);
    // Config-static shaping fields shared with StepEvaluationBatchConfig,
    // bound from the same X-macro list that declares the struct members so the
    // exposed attribute names cannot drift from the C++ fields.
#define EF_FLIGHT_SHAPING_FIELD(type, name, default_value)                                         \
    flight_shaping_inputs_class.def_rw(#name, &FlightShapingRuntimeInputs::name);
#include "core/mission/runtime/detail/flight_shaping_shared_fields.inc"

    nb::class_<FlightShapingRuntimeProducts>(m, "FlightShapingRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &FlightShapingRuntimeProducts::valid)
        .def_ro("altitude_progress", &FlightShapingRuntimeProducts::altitude_progress)
        .def_ro("low_alt_descent_penalty", &FlightShapingRuntimeProducts::low_alt_descent_penalty)
        .def_ro("speed_progress", &FlightShapingRuntimeProducts::speed_progress)
        .def_ro("speed_regress", &FlightShapingRuntimeProducts::speed_regress)
        .def_ro("stationary_penalty", &FlightShapingRuntimeProducts::stationary_penalty)
        .def_ro("liftoff_bonus", &FlightShapingRuntimeProducts::liftoff_bonus)
        .def_ro("next_liftoff_awarded", &FlightShapingRuntimeProducts::next_liftoff_awarded)
        .def_ro("rotation_reward", &FlightShapingRuntimeProducts::rotation_reward)
        .def_ro("rotation_overpitch_penalty",
                &FlightShapingRuntimeProducts::rotation_overpitch_penalty)
        .def_ro("gear_up_bonus", &FlightShapingRuntimeProducts::gear_up_bonus)
        .def_ro("next_gear_bonus_awarded", &FlightShapingRuntimeProducts::next_gear_bonus_awarded)
        .def_ro("roll_stability", &FlightShapingRuntimeProducts::roll_stability)
        .def_ro("heading_error_penalty", &FlightShapingRuntimeProducts::heading_error_penalty)
        .def_ro("heading_hold_bonus", &FlightShapingRuntimeProducts::heading_hold_bonus)
        .def_ro("altitude_error_penalty", &FlightShapingRuntimeProducts::altitude_error_penalty)
        .def_ro("altitude_hold_bonus", &FlightShapingRuntimeProducts::altitude_hold_bonus)
        .def_ro("speed_error_penalty", &FlightShapingRuntimeProducts::speed_error_penalty)
        .def_ro("speed_hold_bonus", &FlightShapingRuntimeProducts::speed_hold_bonus)
        .def_ro("roll_abs_penalty", &FlightShapingRuntimeProducts::roll_abs_penalty)
        .def_ro("pitch_abs_penalty", &FlightShapingRuntimeProducts::pitch_abs_penalty)
        .def_ro("yaw_rate_abs_penalty", &FlightShapingRuntimeProducts::yaw_rate_abs_penalty)
        .def_ro("beta_abs_penalty", &FlightShapingRuntimeProducts::beta_abs_penalty)
        .def_ro("g_deviation_penalty", &FlightShapingRuntimeProducts::g_deviation_penalty)
        .def_ro("speed_reward", &FlightShapingRuntimeProducts::speed_reward)
        .def_ro("runway_centerline_m_penalty",
                &FlightShapingRuntimeProducts::runway_centerline_m_penalty)
        .def_ro("runway_centerline_penalty",
                &FlightShapingRuntimeProducts::runway_centerline_penalty)
        .def_ro("runway_centerline_barrier",
                &FlightShapingRuntimeProducts::runway_centerline_barrier)
        .def_ro("departure_centerline_m_penalty",
                &FlightShapingRuntimeProducts::departure_centerline_m_penalty)
        .def_ro("departure_centerline_reward",
                &FlightShapingRuntimeProducts::departure_centerline_reward)
        .def_ro("departure_track_error_penalty",
                &FlightShapingRuntimeProducts::departure_track_error_penalty)
        .def_ro("departure_track_reward", &FlightShapingRuntimeProducts::departure_track_reward)
        .def_ro("alignment_reward", &FlightShapingRuntimeProducts::alignment_reward);

    m.def("compute_flight_shaping_terms", &compute_flight_shaping_terms, nb::arg("inputs"));
}
