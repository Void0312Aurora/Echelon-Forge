#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include "core/engine/simulation_kernel.h"
#include "components/systems/comm.h"
#include "core/interfaces/unit_data.h"
#include "core/interfaces/observation.h"
#include "components/basic/common.h"
#include "components/physics/action.h" // Added action.h
#include "components/physics/instruments.h" // Added instruments.h
#include "components/systems/sensor.h"
#include "components/systems/navigation.h" // Added navigation.h
#include <spdlog/spdlog.h>
#include <stdexcept>

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
        .def("get_visual_observation", &SimulationKernel::get_visual_observation, 
             "Get ARB visual observation [H*W*C] tensor", nb::arg("entity_id"))
        .def("get_unit_messages", &SimulationKernel::get_unit_messages, "Get inbox")
        .def("send_message_command", &SimulationKernel::send_message_command, 
             nb::arg("entity_id"), nb::arg("recipient_id"), nb::arg("msg_type"), nb::arg("msg_arg"))
        .def("debug_get_last_scan_time", &SimulationKernel::debug_get_last_scan_time, "Debug: get sensor last_scan_time")
        .def("debug_get_contact_count", &SimulationKernel::debug_get_contact_count, "Debug: get ContactList size")
        .def("set_missile_tuning", &SimulationKernel::set_missile_tuning,
             "Override missile parameters for diagnostics", nb::arg("tuning"));
    
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
