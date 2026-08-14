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

void bind_episode_geometry(nb::module_ &m) {
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
        .def("add_runway", &CompiledScenarioGeometry::add_runway, nb::arg("runway"))
        .def("set_route_leg_origin", &CompiledScenarioGeometry::set_route_leg_origin,
             nb::arg("x_m"), nb::arg("y_m"))
        .def("add_route_waypoint", &CompiledScenarioGeometry::add_route_waypoint,
             nb::arg("waypoint"))
        .def("query_runway_local_frame", &CompiledScenarioGeometry::query_runway_local_frame,
             nb::arg("x_m"), nb::arg("y_m"))
        .def("query_ils", &CompiledScenarioGeometry::query_ils, nb::arg("x_m"), nb::arg("y_m"),
             nb::arg("alt_m"), nb::arg("threshold_crossing_height_m") = 0.0)
        .def("query_route_guidance", &CompiledScenarioGeometry::query_route_guidance,
             nb::arg("options"));
}
