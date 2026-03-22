#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include "components/visual/visual_sensor.h"
#include "core/engine/simulation_kernel.h"
#include "core/engine/world_batch_runtime.h"
#include "core/geometry/spatial_query_runtime.h"
#include "core/mission/execution_episode_runtime.h"
#include "core/mission/execution_frame_runtime.h"
#include "core/mission/execution_observation_runtime.h"
#include "core/mission/execution_step_runtime.h"
#include "core/mission/mission_runtime.h"
#include "core/mission/reward_runtime.h"
#include "core/mission/objective_runtime.h"
#include "core/mission/termination_runtime.h"
#include "components/systems/comm.h"
#include "core/interfaces/unit_data.h"
#include "core/interfaces/observation.h"
#include "components/basic/common.h"
#include "components/physics/action.h" // Added action.h
#include "components/physics/instruments.h" // Added instruments.h
#include "components/systems/sensor.h"
#include "components/systems/navigation.h" // Added navigation.h
#include <spdlog/spdlog.h>
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace nb = nanobind;

namespace {
const char* default_unit_name_for(UnitType type) {
    switch (type) {
        case UnitType::Aircraft:
            return "Aircraft";
        case UnitType::Ship:
            return "Ship";
        case UnitType::Missile:
            return "Missile";
        case UnitType::Facility:
            return "Facility";
        case UnitType::C2Node:
            return "AWACS";
        default:
            throw std::invalid_argument("Unsupported UnitType for spawn_unit (use type_name string instead)");
    }
}

template <typename Shape>
auto visual_tensor_to_numpy(std::vector<float>&& data, size_t ndim, const size_t* shape) {
    auto* output = new std::vector<float>(std::move(data));
    nb::capsule owner(output, [](void* ptr) noexcept {
        delete static_cast<std::vector<float>*>(ptr);
    });
    return nb::ndarray<nb::numpy, const float, Shape>(output->data(), ndim, shape, owner);
}

std::vector<float> downsample_visual_tensor(std::vector<float>&& input, int factor) {
    using namespace arb;

    if (factor <= 1) {
        return std::move(input);
    }
    if (ARB_HEIGHT % factor != 0 || ARB_WIDTH % factor != 0) {
        throw std::invalid_argument("visual downsample factor must divide native ARB dimensions");
    }

    const size_t in_height = static_cast<size_t>(ARB_HEIGHT);
    const size_t in_width = static_cast<size_t>(ARB_WIDTH);
    const size_t channels = static_cast<size_t>(ARB_CHANNELS);
    const size_t out_height = in_height / static_cast<size_t>(factor);
    const size_t out_width = in_width / static_cast<size_t>(factor);
    const size_t area = static_cast<size_t>(factor) * static_cast<size_t>(factor);

    std::vector<float> output(out_height * out_width * channels, 0.0f);
    const float* src = input.data();
    float* dst = output.data();
    const float scale = 1.0f / static_cast<float>(area);

    for (size_t oy = 0; oy < out_height; ++oy) {
        const size_t iy0 = oy * static_cast<size_t>(factor);
        for (size_t ox = 0; ox < out_width; ++ox) {
            const size_t ix0 = ox * static_cast<size_t>(factor);
            const size_t out_base = (oy * out_width + ox) * channels;
            for (int fy = 0; fy < factor; ++fy) {
                const size_t iy = iy0 + static_cast<size_t>(fy);
                for (int fx = 0; fx < factor; ++fx) {
                    const size_t ix = ix0 + static_cast<size_t>(fx);
                    const size_t in_base = (iy * in_width + ix) * channels;
                    for (size_t c = 0; c < channels; ++c) {
                        dst[out_base + c] += src[in_base + c];
                    }
                }
            }
            for (size_t c = 0; c < channels; ++c) {
                dst[out_base + c] *= scale;
            }
        }
    }

    return output;
}
} // namespace

NB_MODULE(ef_py, m) {
    m.def("set_log_level", [](const std::string& level) {
        if (level == "trace") spdlog::set_level(spdlog::level::trace);
        else if (level == "debug") spdlog::set_level(spdlog::level::debug);
        else if (level == "info") spdlog::set_level(spdlog::level::info);
        else if (level == "warn") spdlog::set_level(spdlog::level::warn);
        else if (level == "error") spdlog::set_level(spdlog::level::err);
        else if (level == "critical") spdlog::set_level(spdlog::level::critical);
        else if (level == "off") spdlog::set_level(spdlog::level::off);
    }, "Set global log level (trace/debug/info/warn/error/critical/off)", nb::arg("level"));
    // Bind Side Enum
    nb::enum_<Side>(m, "Side")
        .value("Blue", Side::Blue)
        .value("Red", Side::Red)
        .value("Neutral", Side::Neutral)
        .value("Unknown", Side::Unknown)
        .export_values();

    nb::enum_<CommMsgType>(m, "CommMsgType")
        .value("None", CommMsgType::None)
        .value("REP_WILCO", CommMsgType::REP_WILCO)
        .value("REP_ROGER", CommMsgType::REP_ROGER)
        .value("REP_UNABLE", CommMsgType::REP_UNABLE)
        .value("REP_CANT_DO", CommMsgType::REP_CANT_DO)
        .value("STATUS_FUEL", CommMsgType::STATUS_FUEL)
        .value("STATUS_AMMO", CommMsgType::STATUS_AMMO)
        .value("STATUS_DAMAGE", CommMsgType::STATUS_DAMAGE)
        .value("STATUS_POS", CommMsgType::STATUS_POS)
        .value("REP_TALLY", CommMsgType::REP_TALLY)
        .value("REP_VISUAL", CommMsgType::REP_VISUAL)
        .value("REP_BLIND", CommMsgType::REP_BLIND)
        .value("REP_SPIKE", CommMsgType::REP_SPIKE)
        .value("REP_FAILED_SORT", CommMsgType::REP_FAILED_SORT)
        .value("REP_ENGAGED", CommMsgType::REP_ENGAGED)
        .value("REP_SPLASH", CommMsgType::REP_SPLASH)
        .value("REP_DEFENDING", CommMsgType::REP_DEFENDING)
        .value("REP_ON_STATION", CommMsgType::REP_ON_STATION)
        .value("REP_FENCE_IN", CommMsgType::REP_FENCE_IN)
        .value("REP_FENCE_OUT", CommMsgType::REP_FENCE_OUT)
        .value("REP_RTB", CommMsgType::REP_RTB)
        .value("WARN_FLAMEOUT", CommMsgType::WARN_FLAMEOUT)
        .value("WARN_BINGO", CommMsgType::WARN_BINGO)
        .value("WARN_LAUNCH", CommMsgType::WARN_LAUNCH)
        .value("ACK_WILCO", CommMsgType::ACK_WILCO)
        .value("ACK_ROGER", CommMsgType::ACK_ROGER)
        .value("ACK_UNABLE", CommMsgType::ACK_UNABLE)
        .value("ACK_CANT_DO", CommMsgType::ACK_CANT_DO)
        .value("ReportContact", CommMsgType::ReportContact)
        .value("AssignTask", CommMsgType::AssignTask)
        .value("StatusUpdate", CommMsgType::StatusUpdate)
        .value("RequestSupport", CommMsgType::RequestSupport)
        .export_values();

    nb::enum_<TaskType>(m, "TaskType")
        .value("Idle", TaskType::Idle)
        .value("Scramble", TaskType::Scramble)
        .value("CAP", TaskType::CAP)
        .value("RTB", TaskType::RTB)
        .value("RecoverLand", TaskType::RecoverLand)
        .value("CAPMission", TaskType::CAPMission);

    nb::enum_<StationType>(m, "StationType")
        .value("Orbit", StationType::Orbit)
        .value("Racetrack", StationType::Racetrack)
        .value("RouteCAP", StationType::RouteCAP);

    nb::enum_<LeaderPhase>(m, "LeaderPhase")
        .value("Idle", LeaderPhase::Idle)
        .value("Scramble", LeaderPhase::Scramble)
        .value("Takeoff", LeaderPhase::Takeoff)
        .value("Departure", LeaderPhase::Departure)
        .value("TransitToStation", LeaderPhase::TransitToStation)
        .value("EstablishCAP", LeaderPhase::EstablishCAP)
        .value("OnStation", LeaderPhase::OnStation)
        .value("Reposition", LeaderPhase::Reposition)
        .value("RTB", LeaderPhase::RTB)
        .value("ApproachArmed", LeaderPhase::ApproachArmed)
        .value("LandingFinal", LeaderPhase::LandingFinal)
        .value("Rollout", LeaderPhase::Rollout)
        .value("Abort", LeaderPhase::Abort);

    nb::enum_<RecoveryApproachType>(m, "RecoveryApproachType")
        .value("None", RecoveryApproachType::None)
        .value("StraightIn", RecoveryApproachType::StraightIn)
        .value("ILS", RecoveryApproachType::ILS)
        .value("Visual", RecoveryApproachType::Visual)
        .value("Overhead", RecoveryApproachType::Overhead)
        .value("TACAN", RecoveryApproachType::TACAN);

    nb::class_<CommPacket>(m, "CommPacket")
        .def(nb::init<>())
        .def_rw("sender_id", &CommPacket::sender_id)
        .def_rw("target_receiver_id", &CommPacket::target_receiver_id)
        .def_rw("type", &CommPacket::type)
        .def_rw("entity_ref", &CommPacket::entity_ref)
        .def_rw("location_x", &CommPacket::location_x)
        .def_rw("location_y", &CommPacket::location_y)
        .def_rw("location_z", &CommPacket::location_z)
        .def_rw("value", &CommPacket::value)
        .def_rw("status_code", &CommPacket::status_code)
        .def_rw("timestamp", &CommPacket::timestamp);

    nb::class_<PilotReport>(m, "PilotReport")
        .def(nb::init<>())
        .def_rw("report_type", &PilotReport::report_type)
        .def_rw("sender_id", &PilotReport::sender_id)
        .def_rw("task_id", &PilotReport::task_id)
        .def_rw("phase_id", &PilotReport::phase_id)
        .def_rw("timestamp_s", &PilotReport::timestamp_s)
        .def_rw("status_value", &PilotReport::status_value)
        .def_rw("entity_ref", &PilotReport::entity_ref)
        .def_rw("location_x_m", &PilotReport::location_x_m)
        .def_rw("location_y_m", &PilotReport::location_y_m)
        .def_rw("location_z_m", &PilotReport::location_z_m)
        .def_rw("active", &PilotReport::active);

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
        .def_ro("valid", &SpatialRunwayFrameResult::valid)
        .def_ro("runway_id", &SpatialRunwayFrameResult::runway_id)
        .def_ro("along_m", &SpatialRunwayFrameResult::along_m)
        .def_ro("cross_m", &SpatialRunwayFrameResult::cross_m)
        .def_ro("length_m", &SpatialRunwayFrameResult::length_m)
        .def_ro("width_m", &SpatialRunwayFrameResult::width_m)
        .def_ro("heading_deg", &SpatialRunwayFrameResult::heading_deg);

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
        .def_rw("lnav_capture_max_intercept_deg", &SpatialRouteQueryOptions::lnav_capture_max_intercept_deg)
        .def_rw("lnav_capture_xtrack_m", &SpatialRouteQueryOptions::lnav_capture_xtrack_m)
        .def_rw("lnav_capture_course_error_deg", &SpatialRouteQueryOptions::lnav_capture_course_error_deg)
        .def_rw("lnav_direct_to_final_fix", &SpatialRouteQueryOptions::lnav_direct_to_final_fix)
        .def_rw("lnav_flyover_capture_window_m", &SpatialRouteQueryOptions::lnav_flyover_capture_window_m)
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
        .def("set_route_leg_origin", &CompiledScenarioGeometry::set_route_leg_origin, nb::arg("x_m"), nb::arg("y_m"))
        .def("add_route_waypoint", &CompiledScenarioGeometry::add_route_waypoint, nb::arg("waypoint"))
        .def("runway_count", &CompiledScenarioGeometry::runway_count)
        .def("route_waypoint_count", &CompiledScenarioGeometry::route_waypoint_count)
        .def("query_runway_local_frame", &CompiledScenarioGeometry::query_runway_local_frame, nb::arg("x_m"), nb::arg("y_m"))
        .def("query_ils", &CompiledScenarioGeometry::query_ils, nb::arg("x_m"), nb::arg("y_m"), nb::arg("alt_m"), nb::arg("threshold_crossing_height_m") = 0.0)
        .def("query_route_guidance", &CompiledScenarioGeometry::query_route_guidance, nb::arg("options"));

    nb::class_<MissionNavInputs>(m, "MissionNavInputs")
        .def(nb::init<>())
        .def_rw("own_altitude_m", &MissionNavInputs::own_altitude_m)
        .def_rw("truth_heading_deg", &MissionNavInputs::truth_heading_deg)
        .def_rw("truth_speed_mps", &MissionNavInputs::truth_speed_mps)
        .def_rw("inst_heading_deg", &MissionNavInputs::inst_heading_deg)
        .def_rw("inst_ground_track_deg", &MissionNavInputs::inst_ground_track_deg)
        .def_rw("inst_ias_mps", &MissionNavInputs::inst_ias_mps)
        .def_rw("waypoint_altitude_m", &MissionNavInputs::waypoint_altitude_m)
        .def_rw("cdi_full_scale_m", &MissionNavInputs::cdi_full_scale_m);

    nb::class_<MissionNavProducts>(m, "MissionNavProducts")
        .def(nb::init<>())
        .def_ro("valid", &MissionNavProducts::valid)
        .def_ro("active_wp_idx", &MissionNavProducts::active_wp_idx)
        .def_ro("total_wps", &MissionNavProducts::total_wps)
        .def_ro("selected_steerpoint", &MissionNavProducts::selected_steerpoint)
        .def_ro("steerpoint_mode_code", &MissionNavProducts::steerpoint_mode_code)
        .def_ro("dist_m", &MissionNavProducts::dist_m)
        .def_ro("xtk_m", &MissionNavProducts::xtk_m)
        .def_ro("dtg_m", &MissionNavProducts::dtg_m)
        .def_ro("direct_bearing_deg", &MissionNavProducts::direct_bearing_deg)
        .def_ro("desired_leg_track_deg", &MissionNavProducts::desired_leg_track_deg)
        .def_ro("bearing_rel_deg", &MissionNavProducts::bearing_rel_deg)
        .def_ro("altitude_delta_m", &MissionNavProducts::altitude_delta_m)
        .def_ro("cdi_norm", &MissionNavProducts::cdi_norm)
        .def_ro("track_angle_error_deg", &MissionNavProducts::track_angle_error_deg)
        .def_ro("next_turn_deg", &MissionNavProducts::next_turn_deg)
        .def_ro("distance_to_turn_m", &MissionNavProducts::distance_to_turn_m)
        .def_ro("own_heading_deg", &MissionNavProducts::own_heading_deg)
        .def_ro("ground_track_deg", &MissionNavProducts::ground_track_deg)
        .def_ro("reference_speed_mps", &MissionNavProducts::reference_speed_mps);

    nb::class_<MissionObservationInputs>(m, "MissionObservationInputs")
        .def(nb::init<>())
        .def_rw("mode_code", &MissionObservationInputs::mode_code)
        .def_rw("command_code", &MissionObservationInputs::command_code)
        .def_rw("target_heading_deg", &MissionObservationInputs::target_heading_deg)
        .def_rw("target_altitude_m", &MissionObservationInputs::target_altitude_m)
        .def_rw("target_speed_mps", &MissionObservationInputs::target_speed_mps)
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

    nb::class_<StepInfoProducts>(m, "StepInfoProducts")
        .def(nb::init<>())
        .def_ro("valid", &StepInfoProducts::valid)
        .def_ro("on_runway", &StepInfoProducts::on_runway)
        .def_ro("gear_collapsed", &StepInfoProducts::gear_collapsed)
        .def_ro("gear_stress", &StepInfoProducts::gear_stress)
        .def_ro("on_ground", &StepInfoProducts::on_ground)
        .def_ro("airborne", &StepInfoProducts::airborne)
        .def_ro("preliftoff", &StepInfoProducts::preliftoff)
        .def_ro("has_runway_frame", &StepInfoProducts::has_runway_frame)
        .def_ro("on_runway_geom", &StepInfoProducts::on_runway_geom)
        .def_ro("runway_cross_m", &StepInfoProducts::runway_cross_m)
        .def_ro("runway_along_m", &StepInfoProducts::runway_along_m);

    m.def("resolve_ground_track_deg", &resolve_ground_track_deg, nb::arg("fallback_heading_deg"), nb::arg("inst_ground_track_deg"));
    m.def("compute_ground_track_error_deg", &compute_ground_track_error_deg, nb::arg("target_heading_deg"), nb::arg("fallback_heading_deg"), nb::arg("inst_ground_track_deg"));
    m.def("compute_command_tracking_error_deg", &compute_command_tracking_error_deg, nb::arg("target_heading_deg"), nb::arg("truth_heading_deg"), nb::arg("command_code"), nb::arg("inst_ground_track_deg"));
    m.def("compute_waypoint_mission_nav", &compute_waypoint_mission_nav, nb::arg("route_result"), nb::arg("inputs"));
    m.def("compute_mission_observation", &compute_mission_observation, nb::arg("inputs"));
    m.def("compute_step_info_runtime", &compute_step_info_runtime, nb::arg("inputs"));

    nb::class_<WaypointRewardInputs>(m, "WaypointRewardInputs")
        .def(nb::init<>())
        .def_rw("valid", &WaypointRewardInputs::valid)
        .def_rw("waypoint_index", &WaypointRewardInputs::waypoint_index)
        .def_rw("waypoint_count", &WaypointRewardInputs::waypoint_count)
        .def_rw("is_flyover", &WaypointRewardInputs::is_flyover)
        .def_rw("has_guidance", &WaypointRewardInputs::has_guidance)
        .def_rw("passed_fix", &WaypointRewardInputs::passed_fix)
        .def_rw("dist_m", &WaypointRewardInputs::dist_m)
        .def_rw("xtk_m", &WaypointRewardInputs::xtk_m)
        .def_rw("dtg_m", &WaypointRewardInputs::dtg_m)
        .def_rw("waypoint_radius_m", &WaypointRewardInputs::waypoint_radius_m)
        .def_rw("leg_len_m", &WaypointRewardInputs::leg_len_m)
        .def_rw("lead_turn_m", &WaypointRewardInputs::lead_turn_m)
        .def_rw("sequence_gate_m", &WaypointRewardInputs::sequence_gate_m)
        .def_rw("has_prev_dist", &WaypointRewardInputs::has_prev_dist)
        .def_rw("prev_dist_m", &WaypointRewardInputs::prev_dist_m)
        .def_rw("route_length_m", &WaypointRewardInputs::route_length_m)
        .def_rw("turn_relief_activation", &WaypointRewardInputs::turn_relief_activation)
        .def_rw("progress_weight", &WaypointRewardInputs::progress_weight)
        .def_rw("progress_negative_scale", &WaypointRewardInputs::progress_negative_scale)
        .def_rw("distance_weight", &WaypointRewardInputs::distance_weight)
        .def_rw("distance_clip_m", &WaypointRewardInputs::distance_clip_m)
        .def_rw("distance_scale_by_route", &WaypointRewardInputs::distance_scale_by_route)
        .def_rw("distance_route_ref_m", &WaypointRewardInputs::distance_route_ref_m)
        .def_rw("distance_route_scale_min", &WaypointRewardInputs::distance_route_scale_min)
        .def_rw("distance_route_scale_max", &WaypointRewardInputs::distance_route_scale_max)
        .def_rw("cross_track_weight", &WaypointRewardInputs::cross_track_weight)
        .def_rw("cross_track_deadband_m", &WaypointRewardInputs::cross_track_deadband_m)
        .def_rw("cross_track_norm_m", &WaypointRewardInputs::cross_track_norm_m)
        .def_rw("cross_track_power", &WaypointRewardInputs::cross_track_power)
        .def_rw("cross_track_clip", &WaypointRewardInputs::cross_track_clip)
        .def_rw("turn_relief_max", &WaypointRewardInputs::turn_relief_max)
        .def_rw("proximity_weight", &WaypointRewardInputs::proximity_weight)
        .def_rw("proximity_ref_m", &WaypointRewardInputs::proximity_ref_m)
        .def_rw("proximity_power", &WaypointRewardInputs::proximity_power)
        .def_rw("reached_bonus", &WaypointRewardInputs::reached_bonus);

    nb::class_<WaypointRewardProducts>(m, "WaypointRewardProducts")
        .def(nb::init<>())
        .def_ro("valid", &WaypointRewardProducts::valid)
        .def_ro("waypoint_progress", &WaypointRewardProducts::waypoint_progress)
        .def_ro("waypoint_distance", &WaypointRewardProducts::waypoint_distance)
        .def_ro("waypoint_cross_track", &WaypointRewardProducts::waypoint_cross_track)
        .def_ro("waypoint_proximity", &WaypointRewardProducts::waypoint_proximity)
        .def_ro("waypoint_reached_bonus", &WaypointRewardProducts::waypoint_reached_bonus)
        .def_ro("arrived", &WaypointRewardProducts::arrived)
        .def_ro("next_prev_dist_valid", &WaypointRewardProducts::next_prev_dist_valid)
        .def_ro("next_prev_dist_m", &WaypointRewardProducts::next_prev_dist_m);

    nb::class_<ApproachRewardInputs>(m, "ApproachRewardInputs")
        .def(nb::init<>())
        .def_rw("valid", &ApproachRewardInputs::valid)
        .def_rw("ils_valid", &ApproachRewardInputs::ils_valid)
        .def_rw("ils_loc_dev", &ApproachRewardInputs::ils_loc_dev)
        .def_rw("ils_gs_dev", &ApproachRewardInputs::ils_gs_dev)
        .def_rw("ils_dme_m", &ApproachRewardInputs::ils_dme_m)
        .def_rw("has_prev_loc", &ApproachRewardInputs::has_prev_loc)
        .def_rw("prev_loc_abs", &ApproachRewardInputs::prev_loc_abs)
        .def_rw("has_prev_gs", &ApproachRewardInputs::has_prev_gs)
        .def_rw("prev_gs_abs", &ApproachRewardInputs::prev_gs_abs)
        .def_rw("has_prev_dme", &ApproachRewardInputs::has_prev_dme)
        .def_rw("prev_dme_m", &ApproachRewardInputs::prev_dme_m)
        .def_rw("localizer_weight", &ApproachRewardInputs::localizer_weight)
        .def_rw("localizer_deadband", &ApproachRewardInputs::localizer_deadband)
        .def_rw("localizer_norm", &ApproachRewardInputs::localizer_norm)
        .def_rw("localizer_power", &ApproachRewardInputs::localizer_power)
        .def_rw("localizer_clip", &ApproachRewardInputs::localizer_clip)
        .def_rw("localizer_improve_weight", &ApproachRewardInputs::localizer_improve_weight)
        .def_rw("glideslope_weight", &ApproachRewardInputs::glideslope_weight)
        .def_rw("glideslope_deadband", &ApproachRewardInputs::glideslope_deadband)
        .def_rw("glideslope_norm", &ApproachRewardInputs::glideslope_norm)
        .def_rw("glideslope_power", &ApproachRewardInputs::glideslope_power)
        .def_rw("glideslope_clip", &ApproachRewardInputs::glideslope_clip)
        .def_rw("glideslope_improve_weight", &ApproachRewardInputs::glideslope_improve_weight)
        .def_rw("dme_progress_weight", &ApproachRewardInputs::dme_progress_weight)
        .def_rw("dme_progress_localizer_band", &ApproachRewardInputs::dme_progress_localizer_band)
        .def_rw("dme_progress_glideslope_band", &ApproachRewardInputs::dme_progress_glideslope_band)
        .def_rw("dme_progress_quality_power", &ApproachRewardInputs::dme_progress_quality_power)
        .def_rw("capture_bonus", &ApproachRewardInputs::capture_bonus)
        .def_rw("capture_localizer_band", &ApproachRewardInputs::capture_localizer_band)
        .def_rw("capture_glideslope_band", &ApproachRewardInputs::capture_glideslope_band)
        .def_rw("sink_rate_weight", &ApproachRewardInputs::sink_rate_weight)
        .def_rw("flare_agl_m", &ApproachRewardInputs::flare_agl_m)
        .def_rw("curr_alt_agl_m", &ApproachRewardInputs::curr_alt_agl_m)
        .def_rw("sink_rate_mps", &ApproachRewardInputs::sink_rate_mps)
        .def_rw("sink_rate_deadband_mps", &ApproachRewardInputs::sink_rate_deadband_mps)
        .def_rw("sink_rate_norm_mps", &ApproachRewardInputs::sink_rate_norm_mps)
        .def_rw("sink_rate_power", &ApproachRewardInputs::sink_rate_power)
        .def_rw("sink_rate_clip", &ApproachRewardInputs::sink_rate_clip);

    nb::class_<ApproachRewardProducts>(m, "ApproachRewardProducts")
        .def(nb::init<>())
        .def_ro("valid", &ApproachRewardProducts::valid)
        .def_ro("approach_localizer", &ApproachRewardProducts::approach_localizer)
        .def_ro("approach_localizer_improve", &ApproachRewardProducts::approach_localizer_improve)
        .def_ro("approach_glideslope", &ApproachRewardProducts::approach_glideslope)
        .def_ro("approach_glideslope_improve", &ApproachRewardProducts::approach_glideslope_improve)
        .def_ro("approach_dme_progress", &ApproachRewardProducts::approach_dme_progress)
        .def_ro("approach_capture_bonus", &ApproachRewardProducts::approach_capture_bonus)
        .def_ro("landing_sink_rate_penalty", &ApproachRewardProducts::landing_sink_rate_penalty)
        .def_ro("clear_history", &ApproachRewardProducts::clear_history)
        .def_ro("next_prev_valid", &ApproachRewardProducts::next_prev_valid)
        .def_ro("next_prev_loc_abs", &ApproachRewardProducts::next_prev_loc_abs)
        .def_ro("next_prev_gs_abs", &ApproachRewardProducts::next_prev_gs_abs)
        .def_ro("next_prev_dme_m", &ApproachRewardProducts::next_prev_dme_m);

    m.def("compute_waypoint_reward_terms", &compute_waypoint_reward_terms, nb::arg("inputs"));
    m.def("compute_approach_reward_terms", &compute_approach_reward_terms, nb::arg("inputs"));

    nb::class_<FlightShapingRuntimeInputs>(m, "FlightShapingRuntimeInputs")
        .def(nb::init<>())
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
        .def_rw("waypoint_turn_relief_activation", &FlightShapingRuntimeInputs::waypoint_turn_relief_activation)
        .def_rw("preliftoff", &FlightShapingRuntimeInputs::preliftoff)
        .def_rw("on_runway_task", &FlightShapingRuntimeInputs::on_runway_task)
        .def_rw("airborne", &FlightShapingRuntimeInputs::airborne)
        .def_rw("has_runway_cross_m", &FlightShapingRuntimeInputs::has_runway_cross_m)
        .def_rw("runway_cross_m", &FlightShapingRuntimeInputs::runway_cross_m)
        .def_rw("runway_width_m", &FlightShapingRuntimeInputs::runway_width_m)
        .def_rw("ils_valid", &FlightShapingRuntimeInputs::ils_valid)
        .def_rw("ils_loc_dev", &FlightShapingRuntimeInputs::ils_loc_dev)
        .def_rw("liftoff_awarded", &FlightShapingRuntimeInputs::liftoff_awarded)
        .def_rw("gear_bonus_awarded", &FlightShapingRuntimeInputs::gear_bonus_awarded)
        .def_rw("altitude_progress_weight", &FlightShapingRuntimeInputs::altitude_progress_weight)
        .def_rw("speed_progress_weight", &FlightShapingRuntimeInputs::speed_progress_weight)
        .def_rw("speed_progress_negative_weight", &FlightShapingRuntimeInputs::speed_progress_negative_weight)
        .def_rw("stationary_penalty", &FlightShapingRuntimeInputs::stationary_penalty)
        .def_rw("stationary_grace_steps", &FlightShapingRuntimeInputs::stationary_grace_steps)
        .def_rw("stationary_speed_threshold_mps", &FlightShapingRuntimeInputs::stationary_speed_threshold_mps)
        .def_rw("stationary_alt_threshold_m", &FlightShapingRuntimeInputs::stationary_alt_threshold_m)
        .def_rw("liftoff_bonus", &FlightShapingRuntimeInputs::liftoff_bonus)
        .def_rw("liftoff_speed_threshold_mps", &FlightShapingRuntimeInputs::liftoff_speed_threshold_mps)
        .def_rw("liftoff_alt_threshold_m", &FlightShapingRuntimeInputs::liftoff_alt_threshold_m)
        .def_rw("rotation_reward_weight", &FlightShapingRuntimeInputs::rotation_reward_weight)
        .def_rw("rotation_speed_threshold_mps", &FlightShapingRuntimeInputs::rotation_speed_threshold_mps)
        .def_rw("rotation_alt_threshold_m", &FlightShapingRuntimeInputs::rotation_alt_threshold_m)
        .def_rw("rotation_pitch_cap_deg", &FlightShapingRuntimeInputs::rotation_pitch_cap_deg)
        .def_rw("rotation_overpitch_penalty_weight", &FlightShapingRuntimeInputs::rotation_overpitch_penalty_weight)
        .def_rw("gear_up_bonus", &FlightShapingRuntimeInputs::gear_up_bonus)
        .def_rw("gear_up_bonus_min_alt_agl_m", &FlightShapingRuntimeInputs::gear_up_bonus_min_alt_agl_m)
        .def_rw("roll_stability_weight", &FlightShapingRuntimeInputs::roll_stability_weight)
        .def_rw("heading_error_weight", &FlightShapingRuntimeInputs::heading_error_weight)
        .def_rw("heading_hold_deadband_deg", &FlightShapingRuntimeInputs::heading_hold_deadband_deg)
        .def_rw("heading_hold_bonus", &FlightShapingRuntimeInputs::heading_hold_bonus)
        .def_rw("waypoint_turn_heading_relief_max", &FlightShapingRuntimeInputs::waypoint_turn_heading_relief_max)
        .def_rw("altitude_error_weight", &FlightShapingRuntimeInputs::altitude_error_weight)
        .def_rw("altitude_error_min_alt_m", &FlightShapingRuntimeInputs::altitude_error_min_alt_m)
        .def_rw("altitude_error_target_m", &FlightShapingRuntimeInputs::altitude_error_target_m)
        .def_rw("altitude_error_deadband_m", &FlightShapingRuntimeInputs::altitude_error_deadband_m)
        .def_rw("altitude_error_norm_m", &FlightShapingRuntimeInputs::altitude_error_norm_m)
        .def_rw("altitude_error_power", &FlightShapingRuntimeInputs::altitude_error_power)
        .def_rw("altitude_error_clip", &FlightShapingRuntimeInputs::altitude_error_clip)
        .def_rw("altitude_hold_bonus", &FlightShapingRuntimeInputs::altitude_hold_bonus)
        .def_rw("speed_error_weight", &FlightShapingRuntimeInputs::speed_error_weight)
        .def_rw("speed_error_min_ias_mps", &FlightShapingRuntimeInputs::speed_error_min_ias_mps)
        .def_rw("speed_error_target_mps", &FlightShapingRuntimeInputs::speed_error_target_mps)
        .def_rw("speed_error_deadband_mps", &FlightShapingRuntimeInputs::speed_error_deadband_mps)
        .def_rw("speed_error_norm_mps", &FlightShapingRuntimeInputs::speed_error_norm_mps)
        .def_rw("speed_error_power", &FlightShapingRuntimeInputs::speed_error_power)
        .def_rw("speed_error_clip", &FlightShapingRuntimeInputs::speed_error_clip)
        .def_rw("speed_hold_bonus", &FlightShapingRuntimeInputs::speed_hold_bonus)
        .def_rw("roll_abs_weight", &FlightShapingRuntimeInputs::roll_abs_weight)
        .def_rw("roll_abs_deadband_deg", &FlightShapingRuntimeInputs::roll_abs_deadband_deg)
        .def_rw("roll_abs_norm_deg", &FlightShapingRuntimeInputs::roll_abs_norm_deg)
        .def_rw("roll_abs_power", &FlightShapingRuntimeInputs::roll_abs_power)
        .def_rw("pitch_abs_weight", &FlightShapingRuntimeInputs::pitch_abs_weight)
        .def_rw("pitch_abs_deadband_deg", &FlightShapingRuntimeInputs::pitch_abs_deadband_deg)
        .def_rw("pitch_abs_norm_deg", &FlightShapingRuntimeInputs::pitch_abs_norm_deg)
        .def_rw("pitch_abs_power", &FlightShapingRuntimeInputs::pitch_abs_power)
        .def_rw("yaw_rate_abs_weight", &FlightShapingRuntimeInputs::yaw_rate_abs_weight)
        .def_rw("yaw_rate_abs_deadband_deg_s", &FlightShapingRuntimeInputs::yaw_rate_abs_deadband_deg_s)
        .def_rw("yaw_rate_abs_norm_deg_s", &FlightShapingRuntimeInputs::yaw_rate_abs_norm_deg_s)
        .def_rw("yaw_rate_abs_power", &FlightShapingRuntimeInputs::yaw_rate_abs_power)
        .def_rw("beta_abs_weight", &FlightShapingRuntimeInputs::beta_abs_weight)
        .def_rw("beta_abs_deadband_deg", &FlightShapingRuntimeInputs::beta_abs_deadband_deg)
        .def_rw("beta_abs_norm_deg", &FlightShapingRuntimeInputs::beta_abs_norm_deg)
        .def_rw("beta_abs_power", &FlightShapingRuntimeInputs::beta_abs_power)
        .def_rw("g_deviation_weight", &FlightShapingRuntimeInputs::g_deviation_weight)
        .def_rw("g_deviation_deadband", &FlightShapingRuntimeInputs::g_deviation_deadband)
        .def_rw("g_deviation_norm", &FlightShapingRuntimeInputs::g_deviation_norm)
        .def_rw("g_deviation_power", &FlightShapingRuntimeInputs::g_deviation_power)
        .def_rw("g_deviation_min_alt_agl_m", &FlightShapingRuntimeInputs::g_deviation_min_alt_agl_m)
        .def_rw("speed_reward_weight", &FlightShapingRuntimeInputs::speed_reward_weight)
        .def_rw("runway_centerline_penalty_min_ias_mps", &FlightShapingRuntimeInputs::runway_centerline_penalty_min_ias_mps)
        .def_rw("runway_centerline_penalty_max_ias_mps", &FlightShapingRuntimeInputs::runway_centerline_penalty_max_ias_mps)
        .def_rw("runway_centerline_m_penalty_weight", &FlightShapingRuntimeInputs::runway_centerline_m_penalty_weight)
        .def_rw("runway_centerline_m_deadband_m", &FlightShapingRuntimeInputs::runway_centerline_m_deadband_m)
        .def_rw("runway_centerline_m_norm_m", &FlightShapingRuntimeInputs::runway_centerline_m_norm_m)
        .def_rw("runway_centerline_m_power", &FlightShapingRuntimeInputs::runway_centerline_m_power)
        .def_rw("runway_centerline_m_clip", &FlightShapingRuntimeInputs::runway_centerline_m_clip)
        .def_rw("runway_centerline_penalty_weight", &FlightShapingRuntimeInputs::runway_centerline_penalty_weight)
        .def_rw("runway_centerline_safe_frac", &FlightShapingRuntimeInputs::runway_centerline_safe_frac)
        .def_rw("runway_centerline_penalty_power", &FlightShapingRuntimeInputs::runway_centerline_penalty_power)
        .def_rw("runway_centerline_barrier_weight", &FlightShapingRuntimeInputs::runway_centerline_barrier_weight)
        .def_rw("runway_centerline_barrier_clip_frac", &FlightShapingRuntimeInputs::runway_centerline_barrier_clip_frac)
        .def_rw("departure_centerline_max_alt_agl_m", &FlightShapingRuntimeInputs::departure_centerline_max_alt_agl_m)
        .def_rw("departure_centerline_m_penalty_weight", &FlightShapingRuntimeInputs::departure_centerline_m_penalty_weight)
        .def_rw("departure_centerline_m_deadband_m", &FlightShapingRuntimeInputs::departure_centerline_m_deadband_m)
        .def_rw("departure_centerline_m_norm_m", &FlightShapingRuntimeInputs::departure_centerline_m_norm_m)
        .def_rw("departure_centerline_m_power", &FlightShapingRuntimeInputs::departure_centerline_m_power)
        .def_rw("departure_centerline_m_clip", &FlightShapingRuntimeInputs::departure_centerline_m_clip)
        .def_rw("departure_centerline_reward_weight", &FlightShapingRuntimeInputs::departure_centerline_reward_weight)
        .def_rw("departure_centerline_reward_band_m", &FlightShapingRuntimeInputs::departure_centerline_reward_band_m)
        .def_rw("departure_track_error_weight", &FlightShapingRuntimeInputs::departure_track_error_weight)
        .def_rw("departure_track_error_deadband_deg", &FlightShapingRuntimeInputs::departure_track_error_deadband_deg)
        .def_rw("departure_track_error_norm_deg", &FlightShapingRuntimeInputs::departure_track_error_norm_deg)
        .def_rw("departure_track_error_power", &FlightShapingRuntimeInputs::departure_track_error_power)
        .def_rw("departure_track_error_clip", &FlightShapingRuntimeInputs::departure_track_error_clip)
        .def_rw("departure_track_reward_weight", &FlightShapingRuntimeInputs::departure_track_reward_weight)
        .def_rw("departure_track_reward_band_deg", &FlightShapingRuntimeInputs::departure_track_reward_band_deg)
        .def_rw("alignment_reward_weight", &FlightShapingRuntimeInputs::alignment_reward_weight)
        .def_rw("mission_alignment_min_alt_m", &FlightShapingRuntimeInputs::mission_alignment_min_alt_m);

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
        .def_ro("rotation_overpitch_penalty", &FlightShapingRuntimeProducts::rotation_overpitch_penalty)
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
        .def_ro("runway_centerline_m_penalty", &FlightShapingRuntimeProducts::runway_centerline_m_penalty)
        .def_ro("runway_centerline_penalty", &FlightShapingRuntimeProducts::runway_centerline_penalty)
        .def_ro("runway_centerline_barrier", &FlightShapingRuntimeProducts::runway_centerline_barrier)
        .def_ro("departure_centerline_m_penalty", &FlightShapingRuntimeProducts::departure_centerline_m_penalty)
        .def_ro("departure_centerline_reward", &FlightShapingRuntimeProducts::departure_centerline_reward)
        .def_ro("departure_track_error_penalty", &FlightShapingRuntimeProducts::departure_track_error_penalty)
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

    nb::class_<ConditionalObjectiveInputs>(m, "ConditionalObjectiveInputs")
        .def(nb::init<>())
        .def_rw("altitude_m", &ConditionalObjectiveInputs::altitude_m)
        .def_rw("altitude_agl_m", &ConditionalObjectiveInputs::altitude_agl_m)
        .def_rw("speed_mps", &ConditionalObjectiveInputs::speed_mps)
        .def_rw("ground_speed_mps", &ConditionalObjectiveInputs::ground_speed_mps)
        .def_rw("gear_fraction", &ConditionalObjectiveInputs::gear_fraction)
        .def_rw("heading_error_deg", &ConditionalObjectiveInputs::heading_error_deg)
        .def_rw("command_code", &ConditionalObjectiveInputs::command_code)
        .def_rw("ground_track_error_deg", &ConditionalObjectiveInputs::ground_track_error_deg)
        .def_rw("has_runway_cross_m", &ConditionalObjectiveInputs::has_runway_cross_m)
        .def_rw("runway_cross_m", &ConditionalObjectiveInputs::runway_cross_m)
        .def_rw("has_runway_from_threshold_m", &ConditionalObjectiveInputs::has_runway_from_threshold_m)
        .def_rw("runway_from_threshold_m", &ConditionalObjectiveInputs::runway_from_threshold_m)
        .def_rw("on_runway_geom", &ConditionalObjectiveInputs::on_runway_geom)
        .def_rw("on_runway_task", &ConditionalObjectiveInputs::on_runway_task)
        .def_rw("on_ground", &ConditionalObjectiveInputs::on_ground)
        .def_rw("sink_rate_abs_mps", &ConditionalObjectiveInputs::sink_rate_abs_mps)
        .def_rw("ils_localizer_abs", &ConditionalObjectiveInputs::ils_localizer_abs)
        .def_rw("ils_glideslope_abs", &ConditionalObjectiveInputs::ils_glideslope_abs)
        .def_rw("dme_m", &ConditionalObjectiveInputs::dme_m)
        .def_rw("heading_deg", &ConditionalObjectiveInputs::heading_deg)
        .def_rw("x_m", &ConditionalObjectiveInputs::x_m)
        .def_rw("y_m", &ConditionalObjectiveInputs::y_m)
        .def_rw("target_altitude_m", &ConditionalObjectiveInputs::target_altitude_m)
        .def_rw("target_speed_mps", &ConditionalObjectiveInputs::target_speed_mps)
        .def_rw("target_heading_deg", &ConditionalObjectiveInputs::target_heading_deg);

    nb::class_<ObjectiveShapingConfig>(m, "ObjectiveShapingConfig")
        .def(nb::init<>())
        .def_rw("runway_cross_penalty_weight", &ObjectiveShapingConfig::runway_cross_penalty_weight)
        .def_rw("runway_cross_deadband_m", &ObjectiveShapingConfig::runway_cross_deadband_m)
        .def_rw("runway_cross_norm_m", &ObjectiveShapingConfig::runway_cross_norm_m)
        .def_rw("runway_cross_power", &ObjectiveShapingConfig::runway_cross_power)
        .def_rw("runway_cross_clip", &ObjectiveShapingConfig::runway_cross_clip)
        .def_rw("ground_track_penalty_weight", &ObjectiveShapingConfig::ground_track_penalty_weight)
        .def_rw("ground_track_deadband_deg", &ObjectiveShapingConfig::ground_track_deadband_deg)
        .def_rw("ground_track_norm_deg", &ObjectiveShapingConfig::ground_track_norm_deg)
        .def_rw("ground_track_power", &ObjectiveShapingConfig::ground_track_power)
        .def_rw("ground_track_clip", &ObjectiveShapingConfig::ground_track_clip);

    nb::class_<ConditionalObjectiveProducts>(m, "ConditionalObjectiveProducts")
        .def(nb::init<>())
        .def_ro("valid", &ConditionalObjectiveProducts::valid)
        .def_ro("matched", &ConditionalObjectiveProducts::matched)
        .def_ro("unknown_property", &ConditionalObjectiveProducts::unknown_property)
        .def_ro("status0", &ConditionalObjectiveProducts::status0)
        .def_ro("status1", &ConditionalObjectiveProducts::status1)
        .def_ro("status2", &ConditionalObjectiveProducts::status2)
        .def_ro("status_count", &ConditionalObjectiveProducts::status_count)
        .def_ro("success_runway_cross_penalty", &ConditionalObjectiveProducts::success_runway_cross_penalty)
        .def_ro("success_ground_track_error_penalty", &ConditionalObjectiveProducts::success_ground_track_error_penalty)
        .def_ro("objective_bonus", &ConditionalObjectiveProducts::objective_bonus);

    m.def(
        "evaluate_conditional_objective",
        &evaluate_conditional_objective,
        nb::arg("spec"),
        nb::arg("inputs"),
        nb::arg("shaping")
    );

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

    nb::class_<SafetyRuntimeInputs>(m, "SafetyRuntimeInputs")
        .def(nb::init<>())
        .def_rw("finite_state_valid", &SafetyRuntimeInputs::finite_state_valid)
        .def_rw("crash_penalty", &SafetyRuntimeInputs::crash_penalty)
        .def_rw("survival_reward", &SafetyRuntimeInputs::survival_reward)
        .def_rw("health", &SafetyRuntimeInputs::health)
        .def_rw("airborne", &SafetyRuntimeInputs::airborne)
        .def_rw("aoa_valid", &SafetyRuntimeInputs::aoa_valid)
        .def_rw("aoa_abs_deg", &SafetyRuntimeInputs::aoa_abs_deg)
        .def_rw("stall_threshold_deg", &SafetyRuntimeInputs::stall_threshold_deg)
        .def_rw("stall_penalty_weight", &SafetyRuntimeInputs::stall_penalty_weight)
        .def_rw("stall_penalty_clip", &SafetyRuntimeInputs::stall_penalty_clip)
        .def_rw("g_abs", &SafetyRuntimeInputs::g_abs)
        .def_rw("overload_g_threshold", &SafetyRuntimeInputs::overload_g_threshold)
        .def_rw("overload_penalty_weight", &SafetyRuntimeInputs::overload_penalty_weight)
        .def_rw("overload_penalty_clip", &SafetyRuntimeInputs::overload_penalty_clip)
        .def_rw("curr_alt_agl_m", &SafetyRuntimeInputs::curr_alt_agl_m)
        .def_rw("overload_min_alt_agl_m", &SafetyRuntimeInputs::overload_min_alt_agl_m)
        .def_rw("altitude_m", &SafetyRuntimeInputs::altitude_m)
        .def_rw("roll_abs_deg", &SafetyRuntimeInputs::roll_abs_deg)
        .def_rw("pitch_abs_deg", &SafetyRuntimeInputs::pitch_abs_deg)
        .def_rw("failfast_penalty", &SafetyRuntimeInputs::failfast_penalty)
        .def_rw("gear_collapsed", &SafetyRuntimeInputs::gear_collapsed)
        .def_rw("gear_collapse_penalty", &SafetyRuntimeInputs::gear_collapse_penalty)
        .def_rw("runway_surface_phase", &SafetyRuntimeInputs::runway_surface_phase)
        .def_rw("on_runway_task", &SafetyRuntimeInputs::on_runway_task)
        .def_rw("gear_stress", &SafetyRuntimeInputs::gear_stress)
        .def_rw("gear_stress_penalty_weight", &SafetyRuntimeInputs::gear_stress_penalty_weight)
        .def_rw("off_runway_penalty", &SafetyRuntimeInputs::off_runway_penalty)
        .def_rw("speed_mps", &SafetyRuntimeInputs::speed_mps)
        .def_rw("off_runway_steps", &SafetyRuntimeInputs::off_runway_steps)
        .def_rw("off_runway_terminate_speed", &SafetyRuntimeInputs::off_runway_terminate_speed)
        .def_rw("off_runway_terminate_grace_s", &SafetyRuntimeInputs::off_runway_terminate_grace_s)
        .def_rw("time_step_s", &SafetyRuntimeInputs::time_step_s)
        .def_rw("off_runway_terminate_penalty", &SafetyRuntimeInputs::off_runway_terminate_penalty);

    nb::class_<SafetyRuntimeProducts>(m, "SafetyRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &SafetyRuntimeProducts::valid)
        .def_ro("early_return", &SafetyRuntimeProducts::early_return)
        .def_ro("terminated", &SafetyRuntimeProducts::terminated)
        .def_ro("status_flag", &SafetyRuntimeProducts::status_flag)
        .def_ro("reason_code", &SafetyRuntimeProducts::reason_code)
        .def_ro("survival", &SafetyRuntimeProducts::survival)
        .def_ro("crash_penalty", &SafetyRuntimeProducts::crash_penalty)
        .def_ro("nan_guard_marker", &SafetyRuntimeProducts::nan_guard_marker)
        .def_ro("stall_penalty", &SafetyRuntimeProducts::stall_penalty)
        .def_ro("overload_penalty", &SafetyRuntimeProducts::overload_penalty)
        .def_ro("failfast_penalty", &SafetyRuntimeProducts::failfast_penalty)
        .def_ro("gear_collapse_penalty", &SafetyRuntimeProducts::gear_collapse_penalty)
        .def_ro("off_runway_penalty", &SafetyRuntimeProducts::off_runway_penalty)
        .def_ro("gear_stress_penalty", &SafetyRuntimeProducts::gear_stress_penalty)
        .def_ro("off_runway_terminate_penalty", &SafetyRuntimeProducts::off_runway_terminate_penalty);

    m.def("compute_safety_runtime", &compute_safety_runtime, nb::arg("inputs"));
    m.def(
        "finalize_termination_reason",
        &finalize_termination_reason,
        nb::arg("current_reason"),
        nb::arg("terminated"),
        nb::arg("truncated"),
        nb::arg("status_flag")
    );
    m.def("termination_reason_name", &termination_reason_name, nb::arg("reason"));

    nb::class_<ExecutionStepRuntimeInputs>(m, "ExecutionStepRuntimeInputs")
        .def(nb::init<>())
        .def_rw("safety", &ExecutionStepRuntimeInputs::safety)
        .def_rw("has_waypoint", &ExecutionStepRuntimeInputs::has_waypoint)
        .def_rw("waypoint", &ExecutionStepRuntimeInputs::waypoint)
        .def_rw("waypoint_episode_success", &ExecutionStepRuntimeInputs::waypoint_episode_success)
        .def_rw("waypoint_episode_success_bonus", &ExecutionStepRuntimeInputs::waypoint_episode_success_bonus)
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
        .def_ro("waypoint_episode_success_bonus", &ExecutionStepRuntimeProducts::waypoint_episode_success_bonus)
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
        .def_ro("mission_observation_evaluated", &ExecutionFrameRuntimeProducts::mission_observation_evaluated)
        .def_ro("mission_observation", &ExecutionFrameRuntimeProducts::mission_observation)
        .def_ro("step_info_evaluated", &ExecutionFrameRuntimeProducts::step_info_evaluated)
        .def_ro("step_info", &ExecutionFrameRuntimeProducts::step_info)
        .def_ro("execution_step_evaluated", &ExecutionFrameRuntimeProducts::execution_step_evaluated)
        .def_ro("execution_step", &ExecutionFrameRuntimeProducts::execution_step)
        .def_ro("flight_shaping_evaluated", &ExecutionFrameRuntimeProducts::flight_shaping_evaluated)
        .def_ro("flight_shaping", &ExecutionFrameRuntimeProducts::flight_shaping);

    m.def("compute_execution_frame_runtime", &compute_execution_frame_runtime, nb::arg("inputs"));

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
        .def_ro("mission_observation_evaluated", &ExecutionEpisodeRuntimeProducts::mission_observation_evaluated)
        .def_ro("mission_observation", &ExecutionEpisodeRuntimeProducts::mission_observation)
        .def_ro("step_info_evaluated", &ExecutionEpisodeRuntimeProducts::step_info_evaluated)
        .def_ro("step_info", &ExecutionEpisodeRuntimeProducts::step_info)
        .def_ro("execution_step_evaluated", &ExecutionEpisodeRuntimeProducts::execution_step_evaluated)
        .def_ro("execution_step", &ExecutionEpisodeRuntimeProducts::execution_step)
        .def_ro("flight_shaping_evaluated", &ExecutionEpisodeRuntimeProducts::flight_shaping_evaluated)
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

    m.def("compute_execution_episode_runtime", &compute_execution_episode_runtime, nb::arg("inputs"));
    m.def(
        "compute_execution_observation_runtime_numpy",
        [](const InstrumentState& inst,
           const AgentObservation& truth,
           float ils_valid,
           float ils_loc,
           float ils_gs,
           float ils_dme,
           int max_contacts,
           int max_rwr) {
            ExecutionObservationRuntimeProducts out = compute_execution_observation_runtime(
                inst,
                truth,
                static_cast<double>(ils_valid),
                static_cast<double>(ils_loc),
                static_cast<double>(ils_gs),
                static_cast<double>(ils_dme),
                max_contacts,
                max_rwr
            );
            size_t instrument_shape[1] = {out.instrument_values.size()};
            size_t contact_shape[2] = {static_cast<size_t>(std::max(0, max_contacts)), 5u};
            size_t rwr_shape[2] = {static_cast<size_t>(std::max(0, max_rwr)), 4u};
            return nb::make_tuple(
                visual_tensor_to_numpy<nb::ndim<1>>(std::move(out.instrument_values), 1, instrument_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(out.contact_values), 2, contact_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(out.rwr_values), 2, rwr_shape)
            );
        },
        nb::arg("inst"),
        nb::arg("truth"),
        nb::arg("ils_valid"),
        nb::arg("ils_loc"),
        nb::arg("ils_gs"),
        nb::arg("ils_dme"),
        nb::arg("max_contacts"),
        nb::arg("max_rwr")
    );

    nb::class_<RWREvent>(m, "RWREvent")
        .def_ro("source_id", &RWREvent::source_id)
        .def_ro("bearing", &RWREvent::bearing)
        .def_ro("signal_strength", &RWREvent::signal_strength)
        .def_ro("is_lock", &RWREvent::is_lock)
        .def_ro("is_launch", &RWREvent::is_launch);

    // Bind UnitType Enum
    nb::enum_<UnitType>(m, "UnitType")
        .value("Aircraft", UnitType::Aircraft)
        .value("Ship", UnitType::Ship)
        .value("Missile", UnitType::Missile)
        .value("Facility", UnitType::Facility)
        .value("C2Node", UnitType::C2Node);

    // Bind InstrumentState
    nb::class_<InstrumentState>(m, "InstrumentState")
        .def(nb::init<>())
        .def_rw("alt_baro", &InstrumentState::alt_baro_m)
        .def_rw("alt_radar", &InstrumentState::alt_radar_m)
        .def_rw("ias", &InstrumentState::ias_mps)
        .def_rw("mach", &InstrumentState::mach)
        .def_rw("vvi", &InstrumentState::vvi_mps)
        .def_rw("pitch", &InstrumentState::pitch_deg)
        .def_rw("roll", &InstrumentState::roll_deg)
        .def_rw("heading", &InstrumentState::heading_deg)
        .def_rw("aoa", &InstrumentState::aoa_deg)
        .def_rw("beta", &InstrumentState::beta_deg)
        .def_rw("g_load", &InstrumentState::g_load_normal)
        .def_rw("g_load_axial", &InstrumentState::g_load_axial)
        .def_rw("p", &InstrumentState::p_deg_s)
        .def_rw("q", &InstrumentState::q_deg_s)
        .def_rw("r", &InstrumentState::r_deg_s)
        .def_rw("engine_rpm", &InstrumentState::engine_rpm_pct)
        .def_rw("engine_temp", &InstrumentState::engine_temp_c)
        .def_rw("fuel_flow", &InstrumentState::fuel_flow_kg_h)
        .def_rw("throttle_pos", &InstrumentState::throttle_pos)
        .def_rw("fuel_internal", &InstrumentState::fuel_internal_kg)
        .def_rw("fuel_external", &InstrumentState::fuel_external_kg)
        .def_rw("gear_pos", &InstrumentState::gear_pos)
        .def_rw("flaps_pos", &InstrumentState::flaps_pos)
        .def_rw("speedbrake_pos", &InstrumentState::speedbrake_pos)
        .def_rw("master_arm", &InstrumentState::master_arm)
        .def_rw("oat", &InstrumentState::oat_c)
        .def_rw("cmd_heading", &InstrumentState::cmd_heading_deg)
        .def_rw("cmd_alt", &InstrumentState::cmd_alt_m)
        .def_rw("cmd_speed", &InstrumentState::cmd_speed_mps)
        .def_rw("rwr_active", &InstrumentState::rwr_active)
        .def_rw("missiles_remaining", &InstrumentState::missiles_remaining)
        // EGI / Navigation
        .def_rw("lat", &InstrumentState::lat_deg)
        .def_rw("lon", &InstrumentState::lon_deg)
        .def_rw("vn", &InstrumentState::vn_mps)
        .def_rw("ve", &InstrumentState::ve_mps)
        .def_rw("vd", &InstrumentState::vd_mps)
        .def_rw("ground_speed", &InstrumentState::ground_speed_mps)
        .def_rw("ground_track", &InstrumentState::ground_track_deg)
        .def_rw("wind_speed", &InstrumentState::wind_speed_mps)
        .def_rw("wind_dir", &InstrumentState::wind_dir_deg)
        .def_rw("gps_available", &InstrumentState::gps_available)
        .def_rw("position_uncertainty", &InstrumentState::position_uncertainty_m)
        // Internal physics (for reward, not observation)
        .def_rw("gear_stress", &InstrumentState::gear_stress)
        .def_rw("gear_collapsed", &InstrumentState::gear_collapsed)
        .def_rw("on_runway", &InstrumentState::on_runway);

    // Bind EGI
    nb::class_<EGI>(m, "EGI")
        .def(nb::init<>())
        .def_rw("lat", &EGI::lat_deg)
        .def_rw("lon", &EGI::lon_deg)
        .def_rw("alt_baro", &EGI::alt_baro_m)
        .def_rw("alt_radar", &EGI::alt_radar_m)
        .def_rw("vn", &EGI::vn_mps)
        .def_rw("ve", &EGI::ve_mps)
        .def_rw("vd", &EGI::vd_mps)
        .def_rw("heading", &EGI::heading_deg)
        .def_rw("pitch", &EGI::pitch_deg)
        .def_rw("roll", &EGI::roll_deg)
        .def_rw("wind_speed", &EGI::wind_speed_mps)
        .def_rw("wind_dir", &EGI::wind_dir_deg)
        .def_rw("drift_lat", &EGI::drift_lat_m)
        .def_rw("drift_lon", &EGI::drift_lon_m)
        .def_rw("drift_alt", &EGI::drift_alt_m)
        .def_rw("pos_uncertainty", &EGI::position_uncertainty_m)
        .def_rw("time_since_fix", &EGI::time_since_last_gps_fix)
        .def_rw("gps_avail", &EGI::gps_available);

    // Bind MissileTuning
    nb::class_<MissileTuning>(m, "MissileTuning")
        .def(nb::init<>())
        .def_rw("max_speed", &MissileTuning::max_speed)
        .def_rw("turn_rate", &MissileTuning::turn_rate)
        .def_rw("fuse_distance", &MissileTuning::fuse_distance)
        .def_rw("damage", &MissileTuning::damage)
        .def_rw("seeker_fov_deg", &MissileTuning::seeker_fov_deg)
        .def_rw("seeker_lock_range", &MissileTuning::seeker_lock_range)
        .def_rw("guidance_delay_s", &MissileTuning::guidance_delay_s)
        .def_rw("guidance_update_period_s", &MissileTuning::guidance_update_period_s)
        .def_rw("max_flight_time_s", &MissileTuning::max_flight_time_s)
        .def_rw("nav_gain", &MissileTuning::nav_gain)
        .def_rw("sensor_max_range", &MissileTuning::sensor_max_range)
        .def_rw("sensor_fov_deg", &MissileTuning::sensor_fov_deg)
        .def_rw("sensor_scan_period", &MissileTuning::sensor_scan_period)
        .def_rw("sensor_detection_prob", &MissileTuning::sensor_detection_prob)
        .def_rw("sensor_bearing_noise_std", &MissileTuning::sensor_bearing_noise_std)
        .def_rw("sensor_range_noise_std", &MissileTuning::sensor_range_noise_std)
        .def_rw("sensor_track_memory_s", &MissileTuning::sensor_track_memory_s);

    // Bind PilotAction
    nb::class_<PilotAction>(m, "PilotAction")
        .def(nb::init<>())
        .def_rw("stick_pitch", &PilotAction::stick_pitch)
        .def_rw("stick_roll", &PilotAction::stick_roll)
        .def_rw("rudder", &PilotAction::rudder)
        .def_rw("throttle", &PilotAction::throttle)
        .def_rw("gear_handle", &PilotAction::gear_handle)
        .def_rw("flaps", &PilotAction::flaps)
        .def_rw("speedbrake", &PilotAction::speedbrake)
        .def_rw("brake", &PilotAction::brake)
        .def_rw("brake_left", &PilotAction::brake_left)
        .def_rw("brake_right", &PilotAction::brake_right)
        .def_rw("radar_active", &PilotAction::radar_active)
        .def_rw("radar_scan_az", &PilotAction::radar_scan_az)
        .def_rw("radar_scan_el", &PilotAction::radar_scan_el)
        .def_rw("tms_up", &PilotAction::tms_up)
        .def_rw("master_arm", &PilotAction::master_arm)
        .def_rw("fire_weapon", &PilotAction::fire_weapon)
        .def_rw("fire_gun", &PilotAction::fire_gun)
        .def_rw("weapon_select_id", &PilotAction::weapon_select_id)
        .def_rw("jettison_emergency", &PilotAction::jettison_emergency)
        .def_rw("program_chaff", &PilotAction::program_chaff)
        .def_rw("program_flare", &PilotAction::program_flare)
        .def_rw("active", &PilotAction::active);

    // Bind MissionCommand
    nb::class_<MissionCommand>(m, "MissionCommand")
        .def(nb::init<>())
        .def_rw("cmd_heading_deg", &MissionCommand::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &MissionCommand::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &MissionCommand::cmd_speed_mps)
        .def_rw("command_code", &MissionCommand::command_code)
        .def_rw("route_ref_id", &MissionCommand::route_ref_id)
        .def_rw("recovery_base_id", &MissionCommand::recovery_base_id)
        .def_rw("recovery_runway_id", &MissionCommand::recovery_runway_id)
        .def_rw("recovery_approach_type", &MissionCommand::recovery_approach_type)
        .def_rw("formation_id", &MissionCommand::formation_id)
        .def_rw("form_offset_x", &MissionCommand::form_offset_x)
        .def_rw("form_offset_y", &MissionCommand::form_offset_y)
        .def_rw("form_offset_z", &MissionCommand::form_offset_z)
        .def_rw("assigned_target_id", &MissionCommand::assigned_target_id)
        .def_rw("authorization_to_fire", &MissionCommand::authorization_to_fire)
        .def_rw("active", &MissionCommand::active);

    nb::class_<TaskOrder>(m, "TaskOrder")
        .def(nb::init<>())
        .def_rw("task_id", &TaskOrder::task_id)
        .def_rw("task_type", &TaskOrder::task_type)
        .def_rw("priority", &TaskOrder::priority)
        .def_rw("issuer_id", &TaskOrder::issuer_id)
        .def_rw("assignee_id", &TaskOrder::assignee_id)
        .def_rw("active", &TaskOrder::active)
        .def_rw("issue_time_s", &TaskOrder::issue_time_s)
        .def_rw("anchor_x_m", &TaskOrder::anchor_x_m)
        .def_rw("anchor_y_m", &TaskOrder::anchor_y_m)
        .def_rw("anchor_z_m", &TaskOrder::anchor_z_m)
        .def_rw("station_type", &TaskOrder::station_type)
        .def_rw("station_radius_m", &TaskOrder::station_radius_m)
        .def_rw("station_leg_length_m", &TaskOrder::station_leg_length_m)
        .def_rw("station_heading_deg", &TaskOrder::station_heading_deg)
        .def_rw("altitude_block_min_m", &TaskOrder::altitude_block_min_m)
        .def_rw("altitude_block_max_m", &TaskOrder::altitude_block_max_m)
        .def_rw("target_altitude_m", &TaskOrder::target_altitude_m)
        .def_rw("speed_min_mps", &TaskOrder::speed_min_mps)
        .def_rw("speed_max_mps", &TaskOrder::speed_max_mps)
        .def_rw("target_speed_mps", &TaskOrder::target_speed_mps)
        .def_rw("entry_condition_code", &TaskOrder::entry_condition_code)
        .def_rw("exit_condition_code", &TaskOrder::exit_condition_code)
        .def_rw("on_station_time_s", &TaskOrder::on_station_time_s)
        .def_rw("fuel_bingo_override_kg", &TaskOrder::fuel_bingo_override_kg)
        .def_rw("recovery_base_id", &TaskOrder::recovery_base_id)
        .def_rw("recovery_runway_id", &TaskOrder::recovery_runway_id)
        .def_rw("recovery_approach_type", &TaskOrder::recovery_approach_type);

    nb::class_<LeaderIntent>(m, "LeaderIntent")
        .def(nb::init<>())
        .def_rw("phase_id", &LeaderIntent::phase_id)
        .def_rw("command_code", &LeaderIntent::command_code)
        .def_rw("route_ref_id", &LeaderIntent::route_ref_id)
        .def_rw("recovery_base_id", &LeaderIntent::recovery_base_id)
        .def_rw("recovery_runway_id", &LeaderIntent::recovery_runway_id)
        .def_rw("recovery_approach_type", &LeaderIntent::recovery_approach_type)
        .def_rw("cmd_heading_deg", &LeaderIntent::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &LeaderIntent::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &LeaderIntent::cmd_speed_mps)
        .def_rw("formation_id", &LeaderIntent::formation_id)
        .def_rw("form_offset_x", &LeaderIntent::form_offset_x)
        .def_rw("form_offset_y", &LeaderIntent::form_offset_y)
        .def_rw("form_offset_z", &LeaderIntent::form_offset_z)
        .def_rw("assigned_target_id", &LeaderIntent::assigned_target_id)
        .def_rw("authorization_to_fire", &LeaderIntent::authorization_to_fire)
        .def_rw("approach_armed", &LeaderIntent::approach_armed)
        .def_rw("commit_to_land", &LeaderIntent::commit_to_land)
        .def_rw("abort_flag", &LeaderIntent::abort_flag)
        .def_rw("active", &LeaderIntent::active);

    nb::class_<WorldEntityRef>(m, "WorldEntityRef")
        .def(nb::init<>())
        .def_rw("world_index", &WorldEntityRef::world_index)
        .def_rw("entity_id", &WorldEntityRef::entity_id);

    nb::class_<WorldTerrainAssignment>(m, "WorldTerrainAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTerrainAssignment::world_index)
        .def_rw("terrain_type", &WorldTerrainAssignment::terrain_type);

    nb::class_<WorldWindAssignment>(m, "WorldWindAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldWindAssignment::world_index)
        .def_rw("speed_mps", &WorldWindAssignment::speed_mps)
        .def_rw("dir_from_deg", &WorldWindAssignment::dir_from_deg)
        .def_rw("shear_mps_per_km", &WorldWindAssignment::shear_mps_per_km);

    nb::class_<WorldZoneDefinition>(m, "WorldZoneDefinition")
        .def(nb::init<>())
        .def_rw("world_index", &WorldZoneDefinition::world_index)
        .def_rw("name", &WorldZoneDefinition::name)
        .def_rw("x", &WorldZoneDefinition::x)
        .def_rw("y", &WorldZoneDefinition::y)
        .def_rw("width", &WorldZoneDefinition::width)
        .def_rw("length", &WorldZoneDefinition::length)
        .def_rw("heading", &WorldZoneDefinition::heading)
        .def_rw("surface_type", &WorldZoneDefinition::surface_type);

    nb::class_<WorldSpawnRequest>(m, "WorldSpawnRequest")
        .def(nb::init<>())
        .def_rw("world_index", &WorldSpawnRequest::world_index)
        .def_rw("side", &WorldSpawnRequest::side)
        .def_rw("type_name", &WorldSpawnRequest::type_name)
        .def_rw("entity_name", &WorldSpawnRequest::entity_name)
        .def_rw("is_agent", &WorldSpawnRequest::is_agent)
        .def_rw("x", &WorldSpawnRequest::x)
        .def_rw("y", &WorldSpawnRequest::y)
        .def_rw("z", &WorldSpawnRequest::z)
        .def_rw("heading", &WorldSpawnRequest::heading)
        .def_rw("pitch", &WorldSpawnRequest::pitch)
        .def_rw("roll", &WorldSpawnRequest::roll)
        .def_rw("vx", &WorldSpawnRequest::vx)
        .def_rw("vy", &WorldSpawnRequest::vy)
        .def_rw("vz", &WorldSpawnRequest::vz);

    nb::class_<WorldPilotActionAssignment>(m, "WorldPilotActionAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotActionAssignment::world_index)
        .def_rw("entity_id", &WorldPilotActionAssignment::entity_id)
        .def_rw("action", &WorldPilotActionAssignment::action);

    nb::class_<WorldMissionCommandAssignment>(m, "WorldMissionCommandAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldMissionCommandAssignment::world_index)
        .def_rw("entity_id", &WorldMissionCommandAssignment::entity_id)
        .def_rw("command", &WorldMissionCommandAssignment::command);

    nb::class_<WorldTaskOrderAssignment>(m, "WorldTaskOrderAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTaskOrderAssignment::world_index)
        .def_rw("entity_id", &WorldTaskOrderAssignment::entity_id)
        .def_rw("order", &WorldTaskOrderAssignment::order);

    nb::class_<WorldLeaderIntentAssignment>(m, "WorldLeaderIntentAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldLeaderIntentAssignment::world_index)
        .def_rw("entity_id", &WorldLeaderIntentAssignment::entity_id)
        .def_rw("intent", &WorldLeaderIntentAssignment::intent);

    nb::class_<WorldPilotReportAssignment>(m, "WorldPilotReportAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotReportAssignment::world_index)
        .def_rw("entity_id", &WorldPilotReportAssignment::entity_id)
        .def_rw("report", &WorldPilotReportAssignment::report);

    nb::class_<SimulationKernel>(m, "SimulationKernel")
        .def(nb::init<>())
        .def("get_instrument_state", [](SimulationKernel& self, uint64_t entity_id) {
            auto e = self.get_world().entity(entity_id);
            if (e.is_valid()) {
                const InstrumentState* inst = e.get<InstrumentState>();
                if (inst) return *inst;
            }
            return InstrumentState{};
        }, "Get the instrument state for a unit")
        .def("get_egi_state", [](SimulationKernel& self, uint64_t entity_id) {
            auto e = self.get_world().entity(entity_id);
            if (e.is_valid()) {
                const EGI* egi = e.get<EGI>();
                if (egi) return *egi;
            }
            return EGI{};
        }, "Get the EGI state for a unit")
        .def("reset", &SimulationKernel::reset, "Reset the simulation", nb::arg("seed") = 42)
        .def("load_database", &SimulationKernel::load_database, nb::arg("path"), "Load unit definitions from JSON directory")
        .def("step", &SimulationKernel::step, "Advance simulation by one fixed tick")
        .def("get_time_step", &SimulationKernel::get_time_step, "Get the fixed time step in seconds")
        .def("set_time_step", &SimulationKernel::set_time_step, "Set the fixed time step in seconds")
        .def("load_unit_definitions", [](SimulationKernel& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok) {
                spdlog::warn("Failed to load unit definitions: {}", error);
            }
            return ok;
        }, "Load unit definitions from JSON", nb::arg("path"))
        .def("clear_zones", &SimulationKernel::clear_zones, "Clear all environment zones")
        .def("add_zone", &SimulationKernel::add_zone, 
             "Add a new environment zone",
             nb::arg("name"), nb::arg("x"), nb::arg("y"), nb::arg("width"), nb::arg("height"), nb::arg("heading"), nb::arg("surface_type"))
        .def("set_wind", &SimulationKernel::set_wind,
             "Set global wind (speed m/s, dir_from_deg NAV, shear m/s per km)",
             nb::arg("speed_mps"), nb::arg("dir_from_deg"), nb::arg("shear_mps_per_km") = 0.0)
        .def("set_terrain_type", &SimulationKernel::set_terrain_type,
             "Set terrain profile (e.g. 'flat', 'legacy', 'hill')",
             nb::arg("terrain_type"))
        .def("spawn_unit", [](SimulationKernel& self, Side side, const std::string& type, 
                              double x, double y, double z, 
                              double heading, double pitch, double roll,
                              double vx, double vy, double vz) {
            // We return the Entity ID as an integer for MVP
            auto e = self.spawn_unit(side, type, x, y, z, heading, pitch, roll, vx, vy, vz);
            return e.id();
        }, "Spawn a unit by name with orientation and return its Entity ID", 
           nb::arg("side"), nb::arg("type_name"), 
           nb::arg("x"), nb::arg("y"), nb::arg("z"), 
           nb::arg("heading")=0.0, nb::arg("pitch")=0.0, nb::arg("roll")=0.0,
           nb::arg("vx")=0.0, nb::arg("vy")=0.0, nb::arg("vz")=0.0)
        .def("spawn_unit", [](SimulationKernel& self, Side side, UnitType type,
                              double x, double y, double z,
                              double heading, double pitch, double roll,
                              double vx, double vy, double vz) {
            auto e = self.spawn_unit(side, default_unit_name_for(type), x, y, z, heading, pitch, roll, vx, vy, vz);
            return e.id();
        }, "Spawn a default unit for the given UnitType with orientation and return its Entity ID",
           nb::arg("side"), nb::arg("type"),
           nb::arg("x"), nb::arg("y"), nb::arg("z"),
           nb::arg("heading")=0.0, nb::arg("pitch")=0.0, nb::arg("roll")=0.0,
           nb::arg("vx")=0.0, nb::arg("vy")=0.0, nb::arg("vz")=0.0)

        // Action Interface
        .def("set_command", &SimulationKernel::set_unit_command, "Set movement command for a unit",
             nb::arg("entity_id"), nb::arg("heading_deg"), nb::arg("speed_mps"), nb::arg("altitude_m"))
        .def("set_stick_command", &SimulationKernel::set_unit_stick_command, "Set stick inputs",
             nb::arg("entity_id"), nb::arg("stick_roll"), nb::arg("stick_pitch"), nb::arg("throttle"), nb::arg("gear_down")=true)
        .def("set_action", &SimulationKernel::set_unit_action, "Set normalized action for a unit",
             nb::arg("entity_id"),
             nb::arg("turn_rate_cmd"),
             nb::arg("accel_cmd"),
             nb::arg("climb_rate_cmd"),
             nb::arg("fire_cmd"),
             nb::arg("release_chaff") = false,
             nb::arg("release_flare") = false,
             nb::arg("jettison_tanks") = false)
        .def("set_action_space_config", &SimulationKernel::set_action_space_config, "Override action mapping scales for a unit",
             nb::arg("entity_id"),
             nb::arg("max_turn_rate_deg_s"),
             nb::arg("max_accel_mps2"),
             nb::arg("max_climb_rate_mps"),
             nb::arg("min_speed_mps"),
             nb::arg("max_speed_mps"),
             nb::arg("min_alt_m"),
             nb::arg("max_alt_m"))
        
        // Digital Pilot Bindings
        .def("set_pilot_action", &SimulationKernel::set_pilot_action, 
             "Set raw pilot inputs (stick, throttle, etc) for Digital Pilot",
             nb::arg("entity_id"), nb::arg("action"))
        .def("set_mission_command", &SimulationKernel::set_mission_command,
             "Set high-level mission intent for Digital Pilot",
             nb::arg("entity_id"), nb::arg("command"))
        .def("set_task_order", &SimulationKernel::set_task_order,
             "Set the C2 task order for the entity",
             nb::arg("entity_id"), nb::arg("task_order"))
        .def("set_leader_intent", &SimulationKernel::set_leader_intent,
             "Set the leader-layer intent for the entity",
             nb::arg("entity_id"), nb::arg("leader_intent"))
        .def("set_pilot_report", &SimulationKernel::set_pilot_report,
             "Store the latest pilot report for the entity",
             nb::arg("entity_id"), nb::arg("pilot_report"))

        .def("set_command_lag", &SimulationKernel::set_command_lag, "Override command lag time constants for a unit",
             nb::arg("entity_id"),
             nb::arg("heading_tau_s"),
             nb::arg("speed_tau_s"),
             nb::arg("altitude_tau_s"))
        .def("set_command_link", &SimulationKernel::set_command_link, "Set command link latency/drop probability",
             nb::arg("entity_id"), nb::arg("latency_s"), nb::arg("drop_prob"))
             
        .def("fire_missile", [](SimulationKernel& self, uint64_t attacker_id, uint64_t target_id) {
             auto e = self.fire_missile(attacker_id, target_id);
             return e.id(); // Return ID just like spawn_unit
        }, "Fire a missile from attacker to target", nb::arg("attacker_id"), nb::arg("target_id"))
        
        // Helper to get unit position (state observation)
        .def("get_unit_position", [](SimulationKernel& self, uint64_t entity_id) {
             auto p = self.get_unit_position(entity_id);
             return std::make_tuple(p[0], p[1], p[2]);
        }, "Get unit position (x,y,z)")
        
        // Helper to get unit heading (degrees, NAV convention: 0=North, CW)
        .def("get_unit_heading", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             auto e = world.entity(entity_id);
             if(!e.is_valid()) return 0.0;
             const Transform* t = e.get<Transform>();
             if (t) return t->heading;
             const Velocity* v = e.get<Velocity>();
             if(!v) return 0.0;
             // Math angle: atan2(vy, vx) where 0=East, CCW positive
             double math_rad = std::atan2(v->vy, v->vx);
             double math_deg = math_rad * 180.0 / M_PI;
             // NAV angle: 0=North, CW positive => NAV = 90 - Math
             double nav_deg = 90.0 - math_deg;
             // Normalize to [0, 360)
             while (nav_deg < 0) nav_deg += 360.0;
             while (nav_deg >= 360.0) nav_deg -= 360.0;
             return nav_deg;
        }, "Get unit heading in degrees (NAV: 0=North, CW)")
        
        // Helper to get unit type
        .def("get_unit_type", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             auto e = world.entity(entity_id);
             if(!e.is_valid()) return 0;
             const KeyEntity* k = e.get<KeyEntity>();
             return k ? (int)k->type : 0;
        }, "Get unit type enum value")
        
        // Helper to check if unit is active/alive
        .def("is_unit_active", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             return world.entity(entity_id).is_valid();
        }, "Check if unit exists")
        
        .def("get_all_units", &SimulationKernel::get_all_units, "Get all units state")
        .def("get_detections", &SimulationKernel::get_detections, "Get unit sensor contacts")
        .def("get_unit_health", &SimulationKernel::get_unit_health, "Get unit health [current, max]")
        .def("get_unit_fuel", &SimulationKernel::get_unit_fuel, nb::arg("entity_id"),
             "Returns [internal, max_internal, external, max_external]")
        .def("get_task_order", &SimulationKernel::get_task_order, "Get the latest task order", nb::arg("entity_id"))
        .def("get_leader_intent", &SimulationKernel::get_leader_intent, "Get the latest leader intent", nb::arg("entity_id"))
        .def("get_mission_command", &SimulationKernel::get_mission_command, "Get the active mission command", nb::arg("entity_id"))
        .def("get_pilot_report", &SimulationKernel::get_pilot_report, "Get the latest pilot report", nb::arg("entity_id"))
        .def("get_agent_observation", &SimulationKernel::get_agent_observation, "Get complete agent observation")
        .def("get_visual_observation", [](SimulationKernel& self, uint64_t entity_id) {
             size_t shape[3] = {
                 static_cast<size_t>(arb::ARB_HEIGHT),
                 static_cast<size_t>(arb::ARB_WIDTH),
                 static_cast<size_t>(arb::ARB_CHANNELS),
             };
             return visual_tensor_to_numpy<
                 nb::shape<
                     static_cast<size_t>(arb::ARB_HEIGHT),
                     static_cast<size_t>(arb::ARB_WIDTH),
                     static_cast<size_t>(arb::ARB_CHANNELS)
                 >
             >(self.get_visual_observation(entity_id), 3, shape);
        }, "Get ARB visual observation [H, W, C] tensor", nb::arg("entity_id"))
        .def("get_visual_observation_downsampled", [](SimulationKernel& self, uint64_t entity_id, int factor) {
             const int downsample = factor > 1 ? factor : 1;
             auto downsampled = self.get_visual_observation_downsampled(entity_id, downsample);
             size_t shape[3] = {
                 static_cast<size_t>(arb::ARB_HEIGHT / downsample),
                 static_cast<size_t>(arb::ARB_WIDTH / downsample),
                 static_cast<size_t>(arb::ARB_CHANNELS),
             };
             return visual_tensor_to_numpy<
                 nb::shape<
                     nb::any,
                     nb::any,
                     static_cast<size_t>(arb::ARB_CHANNELS)
                 >
             >(std::move(downsampled), 3, shape);
        }, "Get ARB visual observation [H/f, W/f, C] tensor", nb::arg("entity_id"), nb::arg("factor"))
        .def("get_unit_messages", &SimulationKernel::get_unit_messages, "Get inbox")
        .def("send_message_command", &SimulationKernel::send_message_command, 
             nb::arg("entity_id"), nb::arg("recipient_id"), nb::arg("msg_type"), nb::arg("msg_arg"))
        .def("debug_get_last_scan_time", &SimulationKernel::debug_get_last_scan_time, "Debug: get sensor last_scan_time")
        .def("debug_get_contact_count", &SimulationKernel::debug_get_contact_count, "Debug: get ContactList size")
        .def("set_missile_tuning", &SimulationKernel::set_missile_tuning,
             "Override missile parameters for diagnostics", nb::arg("tuning"));

    nb::class_<WorldBatchRuntime>(m, "WorldBatchRuntime")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def("world_count", &WorldBatchRuntime::world_count)
        .def("resize", &WorldBatchRuntime::resize, nb::arg("world_count"))
        .def("set_worker_threads", &WorldBatchRuntime::set_worker_threads, nb::arg("worker_threads"))
        .def("worker_threads", &WorldBatchRuntime::worker_threads)
        .def("effective_worker_threads", &WorldBatchRuntime::effective_worker_threads)
        .def("world", nb::overload_cast<size_t>(&WorldBatchRuntime::world), nb::rv_policy::reference_internal, nb::arg("index"))
        .def("reset_batch", &WorldBatchRuntime::reset_batch, nb::arg("seeds") = std::vector<uint32_t>{})
        .def("step_batch", &WorldBatchRuntime::step_batch)
        .def("step_worlds", &WorldBatchRuntime::step_worlds, nb::arg("world_indices"))
        .def("load_database", &WorldBatchRuntime::load_database, nb::arg("path"))
        .def("load_unit_definitions", [](WorldBatchRuntime& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok && !error.empty()) {
                spdlog::warn("WorldBatchRuntime failed to load unit definitions: {}", error);
            }
            return ok;
        }, nb::arg("path"))
        .def("set_time_step", &WorldBatchRuntime::set_time_step, nb::arg("dt"))
        .def("set_terrain_types_batch", &WorldBatchRuntime::set_terrain_types_batch, nb::arg("assignments"))
        .def("set_winds_batch", &WorldBatchRuntime::set_winds_batch, nb::arg("assignments"))
        .def("clear_zones_batch", &WorldBatchRuntime::clear_zones_batch, nb::arg("world_indices") = std::vector<uint64_t>{})
        .def("add_zones_batch", &WorldBatchRuntime::add_zones_batch, nb::arg("zones"))
        .def("spawn_units_batch", &WorldBatchRuntime::spawn_units_batch, nb::arg("requests"))
        .def(
            "apply_world_setup_batch",
            &WorldBatchRuntime::apply_world_setup_batch,
            nb::arg("seeds"),
            nb::arg("terrain_assignments"),
            nb::arg("wind_assignments"),
            nb::arg("zones"),
            nb::arg("requests"),
            nb::arg("time_steps") = std::vector<double>{}
        )
        .def("set_pilot_actions_batch", &WorldBatchRuntime::set_pilot_actions_batch, nb::arg("assignments"))
        .def("set_mission_commands_batch", &WorldBatchRuntime::set_mission_commands_batch, nb::arg("assignments"))
        .def("set_task_orders_batch", &WorldBatchRuntime::set_task_orders_batch, nb::arg("assignments"))
        .def("set_leader_intents_batch", &WorldBatchRuntime::set_leader_intents_batch, nb::arg("assignments"))
        .def("set_pilot_reports_batch", &WorldBatchRuntime::set_pilot_reports_batch, nb::arg("assignments"))
        .def("get_agent_observations_batch", &WorldBatchRuntime::get_agent_observations_batch, nb::arg("refs"))
        .def("get_instrument_states_batch", &WorldBatchRuntime::get_instrument_states_batch, nb::arg("refs"))
        .def("get_mission_commands_batch", &WorldBatchRuntime::get_mission_commands_batch, nb::arg("refs"))
        .def("get_task_orders_batch", &WorldBatchRuntime::get_task_orders_batch, nb::arg("refs"))
        .def("get_leader_intents_batch", &WorldBatchRuntime::get_leader_intents_batch, nb::arg("refs"))
        .def("get_pilot_reports_batch", &WorldBatchRuntime::get_pilot_reports_batch, nb::arg("refs"));
    
    nb::class_<UnitData>(m, "UnitData")
        .def_ro("id", &UnitData::id)
        .def_ro("side", &UnitData::side)
        .def_ro("type", &UnitData::type)
        .def_ro("x", &UnitData::x)
        .def_ro("y", &UnitData::y)
        .def_ro("z", &UnitData::z)
        .def_ro("heading", &UnitData::heading);

    nb::class_<Detection>(m, "Detection")
        .def_ro("target_id", &Detection::target_id)
        .def_ro("range", &Detection::range)
        .def_ro("bearing", &Detection::bearing)
        .def_ro("elevation", &Detection::elevation)
        .def_ro("signal_strength", &Detection::signal_strength)
        .def_ro("timestamp", &Detection::timestamp);

    nb::class_<TrackData>(m, "TrackData")
        .def_ro("id", &TrackData::id)
        .def_ro("range", &TrackData::range)
        .def_ro("azimuth", &TrackData::azimuth)
        .def_ro("elevation", &TrackData::elevation)
        .def_ro("closing_speed", &TrackData::closing_speed)
        .def_ro("time_since_update", &TrackData::time_since_update)
        .def_ro("source", &TrackData::source)
        .def_ro("classification", &TrackData::classification);

    nb::class_<AgentObservation>(m, "AgentObservation")
        .def_ro("sim_time", &AgentObservation::sim_time)
        .def_ro("id", &AgentObservation::id)
        .def_ro("x", &AgentObservation::x)
        .def_ro("y", &AgentObservation::y)
        .def_ro("z", &AgentObservation::z)
        .def_ro("vx", &AgentObservation::vx)
        .def_ro("vy", &AgentObservation::vy)
        .def_ro("vz", &AgentObservation::vz)
        .def_ro("heading", &AgentObservation::heading)
        .def_ro("pitch", &AgentObservation::pitch)
        .def_ro("roll", &AgentObservation::roll)
        .def_ro("speed", &AgentObservation::speed)
        .def_ro("health", &AgentObservation::health)
        .def_ro("contacts", &AgentObservation::contacts)
        .def_ro("rwr_warnings", &AgentObservation::rwr_warnings)
        .def_ro("missiles_remaining", &AgentObservation::missiles_remaining)
        .def_ro("can_fire", &AgentObservation::can_fire)
        .def_ro("gear_state", &AgentObservation::gear_state)
        .def_ro("throttle", &AgentObservation::throttle)
        .def_ro("total_reward", &AgentObservation::total_reward);
}
