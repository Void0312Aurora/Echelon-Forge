#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include "core/engine/simulation_kernel.h"
#include "components/systems/comm.h"
#include "core/interfaces/unit_data.h"
#include "core/interfaces/observation.h"
#include "components/basic/common.h"
#include "components/systems/sensor.h"
#include <spdlog/spdlog.h>

namespace nb = nanobind;

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
        .value("ReportContact", CommMsgType::ReportContact)
        .value("AssignTask", CommMsgType::AssignTask)
        .value("StatusUpdate", CommMsgType::StatusUpdate)
        .value("RequestSupport", CommMsgType::RequestSupport)
        .export_values();

    nb::class_<CommPacket>(m, "CommPacket")
        .def_rw("sender_id", &CommPacket::sender_id)
        .def_rw("target_receiver_id", &CommPacket::target_receiver_id)
        .def_rw("type", &CommPacket::type)
        .def_rw("entity_ref", &CommPacket::entity_ref)
        .def_rw("timestamp", &CommPacket::timestamp);

    // Bind UnitType Enum
    nb::enum_<UnitType>(m, "UnitType")
        .value("Aircraft", UnitType::Aircraft)
        .value("Ship", UnitType::Ship)
        .value("Missile", UnitType::Missile)
        .value("Facility", UnitType::Facility)
        .value("C2Node", UnitType::C2Node);

    // Bind SimulationKernel
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

    nb::class_<SimulationKernel>(m, "SimulationKernel")
        .def(nb::init<>())
        .def("reset", &SimulationKernel::reset, "Reset the simulation", nb::arg("seed") = 42)
        .def("load_database", &SimulationKernel::load_database, nb::arg("path"), "Load unit definitions from JSON directory")
        .def("step", &SimulationKernel::step, "Advance simulation by one fixed tick")
        .def("get_time_step", &SimulationKernel::get_time_step, "Get the fixed time step in seconds")
        .def("load_unit_definitions", [](SimulationKernel& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok) {
                spdlog::warn("Failed to load unit definitions: {}", error);
            }
            return ok;
        }, "Load unit definitions from JSON", nb::arg("path"))
        .def("spawn_unit", [](SimulationKernel& self, Side side, const std::string& type, 
                              double x, double y, double z, 
                              double vx, double vy, double vz) {
            // We return the Entity ID as an integer for MVP
            auto e = self.spawn_unit(side, type, x, y, z, vx, vy, vz);
            return e.id();
        }, "Spawn a unit by name and return its Entity ID", 
           nb::arg("side"), nb::arg("type_name"), 
           nb::arg("x"), nb::arg("y"), nb::arg("z"), 
           nb::arg("vx")=0, nb::arg("vy")=0, nb::arg("vz")=0)

        // Action Interface
        .def("set_command", &SimulationKernel::set_unit_command, "Set movement command for a unit",
             nb::arg("entity_id"), nb::arg("heading_deg"), nb::arg("speed_mps"), nb::arg("altitude_m"))
        .def("set_action", &SimulationKernel::set_unit_action, "Set normalized action for a unit",
             nb::arg("entity_id"),
             nb::arg("turn_rate_cmd"),
             nb::arg("accel_cmd"),
             nb::arg("climb_rate_cmd"),
             nb::arg("fire_cmd"),
             nb::arg("release_chaff") = false,
             nb::arg("release_flare") = false,
             nb::arg("jettison_tanks") = false)
             
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
        .def("get_agent_observation", &SimulationKernel::get_agent_observation, "Get complete agent observation")
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
        .def_ro("time_since_update", &TrackData::time_since_update);

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
        .def_ro("missiles_remaining", &AgentObservation::missiles_remaining)
        .def_ro("can_fire", &AgentObservation::can_fire)
        .def_ro("total_reward", &AgentObservation::total_reward);
}
