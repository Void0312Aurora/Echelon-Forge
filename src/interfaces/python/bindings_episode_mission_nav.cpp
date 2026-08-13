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

void bind_episode_mission_nav(nb::module_ &m) {
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
}
