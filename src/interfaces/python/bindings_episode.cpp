#include "interfaces/python/binding_utils.h"

#include "core/geometry/spatial_query_runtime.h"
#include "core/mission/episode/episode_reward_breakdown.h"
#include "core/mission/episode/execution_episode_batch_prepare.h"
#include "core/mission/episode/execution_episode_controller.h"
#include "core/mission/runtime/execution_episode_runtime.h"
#include "core/mission/episode/execution_episode_state.h"
#include "core/mission/runtime/execution_frame_runtime.h"
#include "core/mission/runtime/execution_observation_runtime.h"
#include "core/mission/runtime/execution_step_runtime.h"
#include "core/mission/runtime/mission_runtime.h"
#include "core/mission/runtime/objective_runtime.h"
#include "core/mission/runtime/reward_runtime.h"
#include "core/mission/runtime/termination_runtime.h"

void bind_episode(nb::module_ &m) {
    nb::class_<SpatialRunwayDefinition>(m, "SpatialRunwayDefinition")
        .def(nb::init<>())
        .def_rw("runway_id", &SpatialRunwayDefinition::runway_id)
        .def_rw("name", &SpatialRunwayDefinition::name)
        .def_rw("center_x_m", &SpatialRunwayDefinition::center_x_m)
        .def_rw("center_y_m", &SpatialRunwayDefinition::center_y_m)
        .def_rw("threshold_x_m", &SpatialRunwayDefinition::threshold_x_m)
        .def_rw("threshold_y_m", &SpatialRunwayDefinition::threshold_y_m)
        .def_rw("heading_deg", &SpatialRunwayDefinition::heading_deg)
        .def_rw("length_m", &SpatialRunwayDefinition::length_m)
        .def_rw("width_m", &SpatialRunwayDefinition::width_m)
        .def_rw("elevation_m", &SpatialRunwayDefinition::elevation_m)
        .def_rw("glide_slope_deg", &SpatialRunwayDefinition::glide_slope_deg)
        .def_rw("localizer_max_deg", &SpatialRunwayDefinition::localizer_max_deg)
        .def_rw("glideslope_max_deg", &SpatialRunwayDefinition::glideslope_max_deg)
        .def_rw("range_m", &SpatialRunwayDefinition::range_m);

    nb::class_<SpatialRouteWaypoint>(m, "SpatialRouteWaypoint")
        .def(nb::init<>())
        .def_rw("x_m", &SpatialRouteWaypoint::x_m)
        .def_rw("y_m", &SpatialRouteWaypoint::y_m)
        .def_rw("z_m", &SpatialRouteWaypoint::z_m)
        .def_rw("radius_m", &SpatialRouteWaypoint::radius_m)
        .def_rw("altitude_m", &SpatialRouteWaypoint::altitude_m)
        .def_rw("speed_mps", &SpatialRouteWaypoint::speed_mps)
        .def_rw("waypoint_mode", &SpatialRouteWaypoint::waypoint_mode);

    nb::class_<SpatialRunwayFrameResult>(m, "SpatialRunwayFrameResult")
        .def(nb::init<>())
        .def_rw("valid", &SpatialRunwayFrameResult::valid)
        .def_rw("runway_id", &SpatialRunwayFrameResult::runway_id)
        .def_rw("along_m", &SpatialRunwayFrameResult::along_m)
        .def_rw("cross_m", &SpatialRunwayFrameResult::cross_m)
        .def_rw("length_m", &SpatialRunwayFrameResult::length_m)
        .def_rw("width_m", &SpatialRunwayFrameResult::width_m)
        .def_rw("heading_deg", &SpatialRunwayFrameResult::heading_deg);

    nb::class_<SpatialILSResult>(m, "SpatialILSResult")
        .def(nb::init<>())
        .def_ro("valid", &SpatialILSResult::valid)
        .def_ro("runway_id", &SpatialILSResult::runway_id)
        .def_ro("loc_dev", &SpatialILSResult::loc_dev)
        .def_ro("gs_dev", &SpatialILSResult::gs_dev)
        .def_ro("dme_m", &SpatialILSResult::dme_m)
        .def_ro("approach_dist_m", &SpatialILSResult::approach_dist_m)
        .def_ro("heading_deg", &SpatialILSResult::heading_deg);

    nb::class_<SpatialRouteQueryOptions>(m, "SpatialRouteQueryOptions")
        .def(nb::init<>())
        .def_rw("waypoint_index", &SpatialRouteQueryOptions::waypoint_index)
        .def_rw("own_x_m", &SpatialRouteQueryOptions::own_x_m)
        .def_rw("own_y_m", &SpatialRouteQueryOptions::own_y_m)
        .def_rw("own_speed_mps", &SpatialRouteQueryOptions::own_speed_mps)
        .def_rw("base_lookahead_m", &SpatialRouteQueryOptions::base_lookahead_m)
        .def_rw("lnav_max_intercept_deg", &SpatialRouteQueryOptions::lnav_max_intercept_deg)
        .def_rw("lnav_capture_max_intercept_deg",
                &SpatialRouteQueryOptions::lnav_capture_max_intercept_deg)
        .def_rw("lnav_capture_xtrack_m", &SpatialRouteQueryOptions::lnav_capture_xtrack_m)
        .def_rw("lnav_capture_course_error_deg",
                &SpatialRouteQueryOptions::lnav_capture_course_error_deg)
        .def_rw("lnav_direct_to_final_fix", &SpatialRouteQueryOptions::lnav_direct_to_final_fix)
        .def_rw("lnav_flyover_capture_window_m",
                &SpatialRouteQueryOptions::lnav_flyover_capture_window_m)
        .def_rw("lnav_bank_limit_deg", &SpatialRouteQueryOptions::lnav_bank_limit_deg)
        .def_rw("lnav_sequence_gate_scale", &SpatialRouteQueryOptions::lnav_sequence_gate_scale)
        .def_rw("lnav_sequence_gate_min_m", &SpatialRouteQueryOptions::lnav_sequence_gate_min_m)
        .def_rw("lnav_sequence_gate_max_m", &SpatialRouteQueryOptions::lnav_sequence_gate_max_m);

    nb::class_<SpatialRouteQueryResult>(m, "SpatialRouteQueryResult")
        .def(nb::init<>())
        .def_ro("valid", &SpatialRouteQueryResult::valid)
        .def_ro("idx", &SpatialRouteQueryResult::idx)
        .def_ro("count", &SpatialRouteQueryResult::count)
        .def_ro("waypoint_mode", &SpatialRouteQueryResult::waypoint_mode)
        .def_ro("sx_m", &SpatialRouteQueryResult::sx_m)
        .def_ro("sy_m", &SpatialRouteQueryResult::sy_m)
        .def_ro("ex_m", &SpatialRouteQueryResult::ex_m)
        .def_ro("ey_m", &SpatialRouteQueryResult::ey_m)
        .def_ro("lx_m", &SpatialRouteQueryResult::lx_m)
        .def_ro("ly_m", &SpatialRouteQueryResult::ly_m)
        .def_ro("leg_len_m", &SpatialRouteQueryResult::leg_len_m)
        .def_ro("dist_m", &SpatialRouteQueryResult::dist_m)
        .def_ro("direct_to_track_deg", &SpatialRouteQueryResult::direct_to_track_deg)
        .def_ro("desired_track_deg", &SpatialRouteQueryResult::desired_track_deg)
        .def_ro("reward_desired_track_deg", &SpatialRouteQueryResult::reward_desired_track_deg)
        .def_ro("xtk_m", &SpatialRouteQueryResult::xtk_m)
        .def_ro("reward_xtk_m", &SpatialRouteQueryResult::reward_xtk_m)
        .def_ro("along_m", &SpatialRouteQueryResult::along_m)
        .def_ro("dtg_m", &SpatialRouteQueryResult::dtg_m)
        .def_ro("reward_dtg_m", &SpatialRouteQueryResult::reward_dtg_m)
        .def_ro("waypoint_radius_m", &SpatialRouteQueryResult::waypoint_radius_m)
        .def_ro("cmd_track_deg", &SpatialRouteQueryResult::cmd_track_deg)
        .def_ro("lookahead_m", &SpatialRouteQueryResult::lookahead_m)
        .def_ro("next_turn_deg", &SpatialRouteQueryResult::next_turn_deg)
        .def_ro("next_turn_abs_deg", &SpatialRouteQueryResult::next_turn_abs_deg)
        .def_ro("prev_turn_abs_deg", &SpatialRouteQueryResult::prev_turn_abs_deg)
        .def_ro("lead_turn_m", &SpatialRouteQueryResult::lead_turn_m)
        .def_ro("sequence_gate_m", &SpatialRouteQueryResult::sequence_gate_m)
        .def_ro("distance_to_turn_m", &SpatialRouteQueryResult::distance_to_turn_m)
        .def_ro("dist_to_next_turn_start_m", &SpatialRouteQueryResult::dist_to_next_turn_start_m)
        .def_ro("distance_from_prev_turn_m", &SpatialRouteQueryResult::distance_from_prev_turn_m)
        .def_ro("use_direct_to", &SpatialRouteQueryResult::use_direct_to)
        .def_ro("direct_to_fix_guidance", &SpatialRouteQueryResult::direct_to_fix_guidance)
        .def_ro("final_leg", &SpatialRouteQueryResult::final_leg)
        .def_ro("passed_fix", &SpatialRouteQueryResult::passed_fix);

    nb::class_<CompiledScenarioGeometry>(m, "CompiledScenarioGeometry")
        .def(nb::init<>())
        .def("clear", &CompiledScenarioGeometry::clear)
        .def("clear_runways", &CompiledScenarioGeometry::clear_runways)
        .def("add_runway", &CompiledScenarioGeometry::add_runway, nb::arg("runway"))
        .def("clear_route", &CompiledScenarioGeometry::clear_route)
        .def("set_route_leg_origin", &CompiledScenarioGeometry::set_route_leg_origin,
             nb::arg("x_m"), nb::arg("y_m"))
        .def("add_route_waypoint", &CompiledScenarioGeometry::add_route_waypoint,
             nb::arg("waypoint"))
        .def("runway_count", &CompiledScenarioGeometry::runway_count)
        .def("route_waypoint_count", &CompiledScenarioGeometry::route_waypoint_count)
        .def("query_runway_local_frame", &CompiledScenarioGeometry::query_runway_local_frame,
             nb::arg("x_m"), nb::arg("y_m"))
        .def("query_ils", &CompiledScenarioGeometry::query_ils, nb::arg("x_m"), nb::arg("y_m"),
             nb::arg("alt_m"), nb::arg("threshold_crossing_height_m") = 0.0)
        .def("query_route_guidance", &CompiledScenarioGeometry::query_route_guidance,
             nb::arg("options"));

    nb::class_<MissionNavInputs> nav_inputs_class(m, "MissionNavInputs");
    nav_inputs_class.def(nb::init<>());
#define EF_NAV_INPUT(type, name, default_value)                                                    \
    nav_inputs_class.def_rw(#name, &MissionNavInputs::name);
#include "core/mission/runtime/detail/mission_nav_inputs.inc"

    nb::class_<MissionNavProducts> nav_products_class(m, "MissionNavProducts");
    nav_products_class.def(nb::init<>());
#define EF_NAV_PRODUCT(type, name, default_value)                                                  \
    nav_products_class.def_ro(#name, &MissionNavProducts::name);
#include "core/mission/runtime/detail/mission_nav_products.inc"

    nb::class_<MissionObservationInputs>(m, "MissionObservationInputs")
        .def(nb::init<>())
        .def_rw("mode_code", &MissionObservationInputs::mode_code)
        .def_rw("command_code", &MissionObservationInputs::command_code)
        .def_rw("target_heading_deg", &MissionObservationInputs::target_heading_deg)
        .def_rw("target_altitude_m", &MissionObservationInputs::target_altitude_m)
        .def_rw("target_speed_mps", &MissionObservationInputs::target_speed_mps)
        .def_rw("takeoff_procedure_code", &MissionObservationInputs::takeoff_procedure_code)
        .def_rw("takeoff_clearance_code", &MissionObservationInputs::takeoff_clearance_code)
        .def_rw("takeoff_interval_s", &MissionObservationInputs::takeoff_interval_s)
        .def_rw("runway_slot_code", &MissionObservationInputs::runway_slot_code)
        .def_rw("form_offset_x", &MissionObservationInputs::form_offset_x)
        .def_rw("form_offset_y", &MissionObservationInputs::form_offset_y)
        .def_rw("form_offset_z", &MissionObservationInputs::form_offset_z)
        .def_rw("self_role_code", &MissionObservationInputs::self_role_code)
        .def_rw("self_formation_role_code", &MissionObservationInputs::self_formation_role_code)
        .def_rw("relative_slot_code", &MissionObservationInputs::relative_slot_code)
        .def_rw("reference_relative_slot_code",
                &MissionObservationInputs::reference_relative_slot_code)
        .def_rw("has_route_guidance", &MissionObservationInputs::has_route_guidance)
        .def_rw("route_guidance", &MissionObservationInputs::route_guidance)
        .def_rw("nav_inputs", &MissionObservationInputs::nav_inputs);

    nb::class_<MissionObservationProducts>(m, "MissionObservationProducts")
        .def(nb::init<>())
        .def_ro("valid", &MissionObservationProducts::valid)
        .def_ro("mode_code", &MissionObservationProducts::mode_code)
        .def_ro("nav_valid", &MissionObservationProducts::nav_valid)
        .def_ro("nav", &MissionObservationProducts::nav)
        .def_ro("values", &MissionObservationProducts::values);

    nb::class_<StepInfoInputs>(m, "StepInfoInputs")
        .def(nb::init<>())
        .def_rw("on_runway", &StepInfoInputs::on_runway)
        .def_rw("gear_collapsed", &StepInfoInputs::gear_collapsed)
        .def_rw("gear_stress", &StepInfoInputs::gear_stress)
        .def_rw("alt_agl_m", &StepInfoInputs::alt_agl_m)
        .def_rw("on_ground_alt_threshold_m", &StepInfoInputs::on_ground_alt_threshold_m)
        .def_rw("airborne_alt_threshold_m", &StepInfoInputs::airborne_alt_threshold_m)
        .def_rw("has_runway_frame", &StepInfoInputs::has_runway_frame)
        .def_rw("runway_frame", &StepInfoInputs::runway_frame)
        .def_rw("runway_width_margin_m", &StepInfoInputs::runway_width_margin_m)
        .def_rw("runway_length_margin_m", &StepInfoInputs::runway_length_margin_m);

    nb::class_<StepInfoProducts> step_info_products_class(m, "StepInfoProducts");
    step_info_products_class.def(nb::init<>());
#define EF_STEP_INFO_PRODUCT(type, name, default_value)                                            \
    step_info_products_class.def_ro(#name, &StepInfoProducts::name);
#include "core/mission/runtime/detail/step_info_products.inc"

    m.def("resolve_ground_track_deg", &resolve_ground_track_deg, nb::arg("fallback_heading_deg"),
          nb::arg("inst_ground_track_deg"));
    m.def("compute_ground_track_error_deg", &compute_ground_track_error_deg,
          nb::arg("target_heading_deg"), nb::arg("fallback_heading_deg"),
          nb::arg("inst_ground_track_deg"));
    m.def("compute_command_tracking_error_deg", &compute_command_tracking_error_deg,
          nb::arg("target_heading_deg"), nb::arg("truth_heading_deg"), nb::arg("command_code"),
          nb::arg("inst_ground_track_deg"));
    m.def("compute_waypoint_mission_nav", &compute_waypoint_mission_nav, nb::arg("route_result"),
          nb::arg("inputs"));
    m.def("compute_mission_observation", &compute_mission_observation, nb::arg("inputs"));
    m.def("compute_step_info_runtime", &compute_step_info_runtime, nb::arg("inputs"));

    nb::class_<WaypointRewardInputs> wp_inputs_class(m, "WaypointRewardInputs");
    wp_inputs_class.def(nb::init<>());
#define EF_WAYPOINT_INPUT(type, name, default_value)                                               \
    wp_inputs_class.def_rw(#name, &WaypointRewardInputs::name);
#include "core/mission/runtime/detail/waypoint_reward_inputs.inc"

    nb::class_<WaypointRewardProducts> wp_products_class(m, "WaypointRewardProducts");
    wp_products_class.def(nb::init<>());
#define EF_WAYPOINT_PRODUCT(type, name, default_value)                                             \
    wp_products_class.def_ro(#name, &WaypointRewardProducts::name);
#include "core/mission/runtime/detail/waypoint_reward_products.inc"

    nb::class_<ApproachRewardInputs> approach_inputs_class(m, "ApproachRewardInputs");
    approach_inputs_class.def(nb::init<>());
#define EF_APPROACH_INPUT(type, name, default_value)                                               \
    approach_inputs_class.def_rw(#name, &ApproachRewardInputs::name);
#include "core/mission/runtime/detail/approach_reward_inputs.inc"

    nb::class_<ApproachRewardProducts> approach_products_class(m, "ApproachRewardProducts");
    approach_products_class.def(nb::init<>());
#define EF_APPROACH_PRODUCT(type, name, default_value)                                             \
    approach_products_class.def_ro(#name, &ApproachRewardProducts::name);
#include "core/mission/runtime/detail/approach_reward_products.inc"

    m.def("compute_waypoint_reward_terms", &compute_waypoint_reward_terms, nb::arg("inputs"));
    m.def("compute_approach_reward_terms", &compute_approach_reward_terms, nb::arg("inputs"));

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

    nb::enum_<ConditionalObjectiveProperty>(m, "ConditionalObjectiveProperty")
        .value("Unknown", ConditionalObjectiveProperty::Unknown)
        .value("Altitude", ConditionalObjectiveProperty::Altitude)
        .value("AltitudeAGL", ConditionalObjectiveProperty::AltitudeAGL)
        .value("Speed", ConditionalObjectiveProperty::Speed)
        .value("GroundSpeed", ConditionalObjectiveProperty::GroundSpeed)
        .value("Gear", ConditionalObjectiveProperty::Gear)
        .value("HeadingErrorDeg", ConditionalObjectiveProperty::HeadingErrorDeg)
        .value("CommandCode", ConditionalObjectiveProperty::CommandCode)
        .value("GroundTrackErrorDeg", ConditionalObjectiveProperty::GroundTrackErrorDeg)
        .value("RunwayCrossAbsM", ConditionalObjectiveProperty::RunwayCrossAbsM)
        .value("RunwayFromThresholdM", ConditionalObjectiveProperty::RunwayFromThresholdM)
        .value("OnRunwayGeom", ConditionalObjectiveProperty::OnRunwayGeom)
        .value("OnRunway", ConditionalObjectiveProperty::OnRunway)
        .value("OnGround", ConditionalObjectiveProperty::OnGround)
        .value("SinkRateAbsMps", ConditionalObjectiveProperty::SinkRateAbsMps)
        .value("IlsLocalizerAbs", ConditionalObjectiveProperty::IlsLocalizerAbs)
        .value("IlsGlideslopeAbs", ConditionalObjectiveProperty::IlsGlideslopeAbs)
        .value("DmeM", ConditionalObjectiveProperty::DmeM)
        .value("Heading", ConditionalObjectiveProperty::Heading)
        .value("X", ConditionalObjectiveProperty::X)
        .value("Y", ConditionalObjectiveProperty::Y)
        .value("SelfActive", ConditionalObjectiveProperty::SelfActive)
        .value("TargetActive", ConditionalObjectiveProperty::TargetActive)
        .value("SelfHealth", ConditionalObjectiveProperty::SelfHealth)
        .value("TargetHealth", ConditionalObjectiveProperty::TargetHealth)
        .value("MissilesRemaining", ConditionalObjectiveProperty::MissilesRemaining)
        .value("TargetRangeM", ConditionalObjectiveProperty::TargetRangeM)
        .export_values();

    nb::enum_<ConditionalObjectiveOp>(m, "ConditionalObjectiveOp")
        .value("GreaterEqual", ConditionalObjectiveOp::GreaterEqual)
        .value("GreaterThan", ConditionalObjectiveOp::GreaterThan)
        .value("LessEqual", ConditionalObjectiveOp::LessEqual)
        .value("LessThan", ConditionalObjectiveOp::LessThan)
        .export_values();

    nb::enum_<ConditionalObjectiveTargetKind>(m, "ConditionalObjectiveTargetKind")
        .value("Literal", ConditionalObjectiveTargetKind::Literal)
        .value("CommandAltitude", ConditionalObjectiveTargetKind::CommandAltitude)
        .value("CommandSpeed", ConditionalObjectiveTargetKind::CommandSpeed)
        .value("CommandHeading", ConditionalObjectiveTargetKind::CommandHeading)
        .export_values();

    nb::class_<ConditionalObjectiveCondition>(m, "ConditionalObjectiveCondition")
        .def(nb::init<>())
        .def_rw("property_code", &ConditionalObjectiveCondition::property_code)
        .def_rw("op_code", &ConditionalObjectiveCondition::op_code)
        .def_rw("target_kind", &ConditionalObjectiveCondition::target_kind)
        .def_rw("target_value", &ConditionalObjectiveCondition::target_value)
        .def_rw("target_scale", &ConditionalObjectiveCondition::target_scale);

    nb::class_<ConditionalObjectiveSpec>(m, "ConditionalObjectiveSpec")
        .def(nb::init<>())
        .def_rw("conditions", &ConditionalObjectiveSpec::conditions)
        .def_rw("reward_bonus", &ConditionalObjectiveSpec::reward_bonus);

    nb::class_<ConditionalObjectiveInputs> obj_inputs_class(m, "ConditionalObjectiveInputs");
    obj_inputs_class.def(nb::init<>());
#define EF_OBJECTIVE_INPUT(type, name, default_value)                                              \
    obj_inputs_class.def_rw(#name, &ConditionalObjectiveInputs::name);
#include "core/mission/runtime/detail/objective_inputs.inc"

    nb::class_<ObjectiveShapingConfig> obj_shaping_class(m, "ObjectiveShapingConfig");
    obj_shaping_class.def(nb::init<>());
#define EF_OBJECTIVE_SHAPING(type, name, default_value)                                            \
    obj_shaping_class.def_rw(#name, &ObjectiveShapingConfig::name);
#include "core/mission/runtime/detail/objective_shaping.inc"

    nb::class_<ConditionalObjectiveProducts> obj_products_class(m, "ConditionalObjectiveProducts");
    obj_products_class.def(nb::init<>());
#define EF_OBJECTIVE_PRODUCT(type, name, default_value)                                            \
    obj_products_class.def_ro(#name, &ConditionalObjectiveProducts::name);
#include "core/mission/runtime/detail/objective_products.inc"

    m.def("evaluate_conditional_objective", &evaluate_conditional_objective, nb::arg("spec"),
          nb::arg("inputs"), nb::arg("shaping"));

    nb::enum_<TerminationReasonCode>(m, "TerminationReasonCode")
        .value("Running", TerminationReasonCode::Running)
        .value("NanGuard", TerminationReasonCode::NanGuard)
        .value("CrashHealth", TerminationReasonCode::CrashHealth)
        .value("FailfastDeepStall", TerminationReasonCode::FailfastDeepStall)
        .value("FailfastInvertedLowAlt", TerminationReasonCode::FailfastInvertedLowAlt)
        .value("FailfastExtremePitch", TerminationReasonCode::FailfastExtremePitch)
        .value("GearCollapse", TerminationReasonCode::GearCollapse)
        .value("OffRunwayTerminate", TerminationReasonCode::OffRunwayTerminate)
        .value("SuccessWaypoint", TerminationReasonCode::SuccessWaypoint)
        .value("SuccessObjective", TerminationReasonCode::SuccessObjective)
        .value("Success", TerminationReasonCode::Success)
        .value("FailureUnknown", TerminationReasonCode::FailureUnknown)
        .value("TerminatedUnknown", TerminationReasonCode::TerminatedUnknown)
        .value("Timeout", TerminationReasonCode::Timeout)
        .export_values();

    nb::class_<SafetyRuntimeInputs> safety_inputs_class(m, "SafetyRuntimeInputs");
    safety_inputs_class.def(nb::init<>());
#define EF_SAFETY_INPUT(type, name, default_value)                                                 \
    safety_inputs_class.def_rw(#name, &SafetyRuntimeInputs::name);
#include "core/mission/runtime/detail/safety_runtime_inputs.inc"

    nb::class_<SafetyRuntimeProducts> safety_products_class(m, "SafetyRuntimeProducts");
    safety_products_class.def(nb::init<>());
#define EF_SAFETY_PRODUCT(type, name, default_value)                                               \
    safety_products_class.def_ro(#name, &SafetyRuntimeProducts::name);
#include "core/mission/runtime/detail/safety_runtime_products.inc"

    m.def("compute_safety_runtime", &compute_safety_runtime, nb::arg("inputs"));
    m.def("finalize_termination_reason", &finalize_termination_reason, nb::arg("current_reason"),
          nb::arg("terminated"), nb::arg("truncated"), nb::arg("status_flag"));
    m.def("termination_reason_name", &termination_reason_name, nb::arg("reason"));

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

    nb::class_<ExecutionEpisodeControllerStepResult>(m, "ExecutionEpisodeControllerStepResult")
        .def(nb::init<>())
        .def_rw("valid", &ExecutionEpisodeControllerStepResult::valid)
        .def_rw("controller_state", &ExecutionEpisodeControllerStepResult::controller_state)
        .def_rw("reward_total", &ExecutionEpisodeControllerStepResult::reward_total)
        .def_rw("terminated", &ExecutionEpisodeControllerStepResult::terminated)
        .def_rw("truncated", &ExecutionEpisodeControllerStepResult::truncated)
        .def_rw("status0", &ExecutionEpisodeControllerStepResult::status0)
        .def_rw("status1", &ExecutionEpisodeControllerStepResult::status1)
        .def_rw("status2", &ExecutionEpisodeControllerStepResult::status2)
        .def_rw("status3", &ExecutionEpisodeControllerStepResult::status3)
        .def_rw("step_info_valid", &ExecutionEpisodeControllerStepResult::step_info_valid)
        .def_rw("step_info", &ExecutionEpisodeControllerStepResult::step_info)
        .def_rw("structural_state_changed",
                &ExecutionEpisodeControllerStepResult::structural_state_changed);

    nb::class_<ExecutionEpisodeController>(m, "ExecutionEpisodeController")
        .def(nb::init<>())
        .def("clear_state", &ExecutionEpisodeController::clear_state)
        .def("has_state", &ExecutionEpisodeController::has_state)
        .def("import_state", &ExecutionEpisodeController::import_state, nb::arg("state"))
        .def("export_state", &ExecutionEpisodeController::export_state)
        .def("prepare_runtime_inputs", &ExecutionEpisodeController::prepare_runtime_inputs,
             nb::arg("config"), nb::arg("env_state"))
        .def("evaluate", &ExecutionEpisodeController::evaluate, nb::arg("config"),
             nb::arg("env_state"))
        .def("step", &ExecutionEpisodeController::step, nb::arg("config"), nb::arg("env_state"))
        .def("step_result", &ExecutionEpisodeController::step_result, nb::arg("config"),
             nb::arg("env_state"));

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
