#include "interfaces/python/bindings_core_detail.h"

#include <stdexcept>
#include <string>
#include <tuple>

#include <spdlog/spdlog.h>

#include "components/basic/common.h"
#include "components/physics/instruments.h"
#include "components/systems/navigation.h"
#include "components/systems/sensor.h"
#include "components/visual/visual_sensor.h"
#include "core/interfaces/observation.h"
#include "core/interfaces/unit_data.h"

namespace {
const char *default_unit_name_for(UnitType type) {
    switch (type) {
    case UnitType::Aircraft:
        return "Aircraft";
    case UnitType::Ship:
        return "Ship";
    case UnitType::Submarine:
        return "Submarine";
    case UnitType::Ground:
        return "Ground_Platoon_MVP";
    case UnitType::Missile:
        return "Missile";
    case UnitType::Facility:
        return "Facility";
    case UnitType::C2Node:
        return "AWACS";
    default:
        throw std::invalid_argument(
            "Unsupported UnitType for spawn_unit (use type_name string instead)");
    }
}
} // namespace

void bind_simulation_kernel_maintained_surface(nb::class_<SimulationKernel> &kernel) {
    kernel
        .def("get_instrument_state", &SimulationKernel::get_instrument_state,
             "Get the instrument state for a unit", nb::arg("entity_id"))
        .def("get_egi_state", &SimulationKernel::get_egi_state, "Get the EGI state for a unit",
             nb::arg("entity_id"))
        .def("reset", &SimulationKernel::reset, "Reset the simulation", nb::arg("seed") = 42)
        .def("load_database", &SimulationKernel::load_database, nb::arg("path"),
             "Load unit definitions from JSON directory")
        .def("step", &SimulationKernel::step, "Advance simulation by one fixed tick")
        .def("get_time_step", &SimulationKernel::get_time_step,
             "Get the fixed time step in seconds")
        .def("set_time_step", &SimulationKernel::set_time_step,
             "Set the fixed time step in seconds")
        .def("shutdown", &SimulationKernel::shutdown, "Release simulation kernel resources")
        .def(
            "load_unit_definitions",
            [](SimulationKernel &self, const std::string &path) {
                std::string error;
                bool ok = self.load_unit_definitions(path, &error);
                if (!ok) {
                    spdlog::warn("Failed to load unit definitions: {}", error);
                }
                return ok;
            },
            "Load unit definitions from JSON", nb::arg("path"))
        .def("clear_zones", &SimulationKernel::clear_zones, "Clear all environment zones")
        .def("add_zone", &SimulationKernel::add_zone, "Add a new environment zone", nb::arg("name"),
             nb::arg("x"), nb::arg("y"), nb::arg("width"), nb::arg("height"), nb::arg("heading"),
             nb::arg("surface_type"))
        .def("set_wind", &SimulationKernel::set_wind,
             "Set global wind (speed m/s, dir_from_deg NAV, shear m/s per km)",
             nb::arg("speed_mps"), nb::arg("dir_from_deg"), nb::arg("shear_mps_per_km") = 0.0)
        .def("set_sun_direction", &SimulationKernel::set_sun_direction,
             "Set the sun direction driving optical glare (azimuth deg NAV, elevation deg above "
             "horizon)",
             nb::arg("azimuth_deg"), nb::arg("elevation_deg"))
        .def(
            "get_sun_direction",
            [](SimulationKernel &self) {
                const auto sun = self.get_sun_direction();
                return std::make_tuple(sun.x, sun.y, sun.z);
            },
            "Get the unit vector toward the sun as (east, north, up)")
        .def("set_maritime_state", &SimulationKernel::set_maritime_state,
             "Set global maritime state (sea state, wave heading deg NAV, wave period s)",
             nb::arg("sea_state"), nb::arg("wave_heading_deg") = 0.0,
             nb::arg("wave_period_s") = 8.0)
        .def("clear_maritime_state", &SimulationKernel::clear_maritime_state,
             "Clear global maritime override so platform defaults can apply again")
        .def(
            "get_maritime_state",
            [](SimulationKernel &self) {
                const auto state = self.get_maritime_state();
                return std::make_tuple(state.sea_state, state.wave_heading_deg,
                                       state.wave_period_s);
            },
            "Get global maritime state as (sea_state, wave_heading_deg, wave_period_s)")
        .def("set_terrain_type", &SimulationKernel::set_terrain_type,
             "Set terrain profile ('flat' or explicit compatibility profiles: 'legacy', 'hill', "
             "'gaussian_hill', 'mountain')",
             nb::arg("terrain_type"))
        .def(
            "spawn_unit",
            [](SimulationKernel &self, Side side, const std::string &type, double x, double y,
               double z, double heading, double pitch, double roll, double vx, double vy,
               double vz) {
                auto e = self.spawn_unit(side, type, x, y, z, heading, pitch, roll, vx, vy, vz);
                return e.id();
            },
            "Spawn a unit by name with orientation and return its Entity ID", nb::arg("side"),
            nb::arg("type_name"), nb::arg("x"), nb::arg("y"), nb::arg("z"),
            nb::arg("heading") = 0.0, nb::arg("pitch") = 0.0, nb::arg("roll") = 0.0,
            nb::arg("vx") = 0.0, nb::arg("vy") = 0.0, nb::arg("vz") = 0.0)
        .def(
            "spawn_unit",
            [](SimulationKernel &self, Side side, UnitType type, double x, double y, double z,
               double heading, double pitch, double roll, double vx, double vy, double vz) {
                auto e = self.spawn_unit(side, default_unit_name_for(type), x, y, z, heading, pitch,
                                         roll, vx, vy, vz);
                return e.id();
            },
            "Spawn a default unit for the given UnitType with orientation and return its Entity ID",
            nb::arg("side"), nb::arg("type"), nb::arg("x"), nb::arg("y"), nb::arg("z"),
            nb::arg("heading") = 0.0, nb::arg("pitch") = 0.0, nb::arg("roll") = 0.0,
            nb::arg("vx") = 0.0, nb::arg("vy") = 0.0, nb::arg("vz") = 0.0)
        .def("set_command", &SimulationKernel::set_unit_command, "Set movement command for a unit",
             nb::arg("entity_id"), nb::arg("heading_deg"), nb::arg("speed_mps"),
             nb::arg("altitude_m"))
        .def("set_stick_command", &SimulationKernel::set_unit_stick_command, "Set stick inputs",
             nb::arg("entity_id"), nb::arg("stick_roll"), nb::arg("stick_pitch"),
             nb::arg("throttle"), nb::arg("gear_down") = true)
        .def("set_action", &SimulationKernel::set_unit_action, "Set normalized action for a unit",
             nb::arg("entity_id"), nb::arg("turn_rate_cmd"), nb::arg("accel_cmd"),
             nb::arg("climb_rate_cmd"), nb::arg("fire_cmd"), nb::arg("release_chaff") = false,
             nb::arg("release_flare") = false, nb::arg("jettison_tanks") = false)
        .def("set_action_space_config", &SimulationKernel::set_action_space_config,
             "Override action mapping scales for a unit", nb::arg("entity_id"),
             nb::arg("max_turn_rate_deg_s"), nb::arg("max_accel_mps2"),
             nb::arg("max_climb_rate_mps"), nb::arg("min_speed_mps"), nb::arg("max_speed_mps"),
             nb::arg("min_alt_m"), nb::arg("max_alt_m"))
        .def("set_pilot_action", &SimulationKernel::set_pilot_action,
             "Set raw pilot inputs (stick, throttle, etc) for Digital Pilot", nb::arg("entity_id"),
             nb::arg("action"))
        .def("set_mission_command", &SimulationKernel::set_mission_command,
             "Set high-level mission intent for Digital Pilot", nb::arg("entity_id"),
             nb::arg("command"))
        .def("set_task_order", &SimulationKernel::set_task_order,
             "Set the C2 task order for the entity", nb::arg("entity_id"), nb::arg("task_order"))
        .def("set_leader_intent", &SimulationKernel::set_leader_intent,
             "Set the leader-layer intent for the entity", nb::arg("entity_id"),
             nb::arg("leader_intent"))
        .def("set_pilot_report", &SimulationKernel::set_pilot_report,
             "Store the latest pilot report for the entity", nb::arg("entity_id"),
             nb::arg("pilot_report"))
        .def("set_command_lag", &SimulationKernel::set_command_lag,
             "Override command lag time constants for a unit", nb::arg("entity_id"),
             nb::arg("heading_tau_s"), nb::arg("speed_tau_s"), nb::arg("altitude_tau_s"))
        .def("set_command_link", &SimulationKernel::set_command_link,
             "Set command link latency/drop probability", nb::arg("entity_id"),
             nb::arg("latency_s"), nb::arg("drop_prob"))
        .def("set_unit_ammo", &SimulationKernel::set_unit_ammo, "Override unit ammo counts",
             nb::arg("entity_id"), nb::arg("missiles_remaining"), nb::arg("max_missiles"))
        .def("set_weapon_cooldown", &SimulationKernel::set_weapon_cooldown,
             "Override unit weapon cooldown state", nb::arg("entity_id"), nb::arg("cooldown_s"),
             nb::arg("last_fire_time"))
        .def(
            "fire_missile",
            [](SimulationKernel &self, uint64_t attacker_id, uint64_t target_id) {
                auto e = self.fire_missile(attacker_id, target_id);
                return e.id();
            },
            "Fire a missile from attacker to target", nb::arg("attacker_id"), nb::arg("target_id"))
        .def("fire_naval_weapon", &SimulationKernel::fire_naval_weapon,
             "Fire a naval weapon mount type at target", nb::arg("attacker_id"),
             nb::arg("target_id"), nb::arg("weapon_type_code"))
        .def("export_recent_engagement_events", &SimulationKernel::export_recent_engagement_events,
             "Export recently captured engagement events")
        .def(
            "get_unit_position",
            [](SimulationKernel &self, uint64_t entity_id) {
                auto p = self.get_unit_position(entity_id);
                return std::make_tuple(p[0], p[1], p[2]);
            },
            "Get unit position (x,y,z)")
        .def(
            "get_unit_velocity",
            [](SimulationKernel &self, uint64_t entity_id) {
                auto v = self.get_unit_velocity(entity_id);
                return std::make_tuple(v[0], v[1], v[2]);
            },
            "Get unit velocity (vx,vy,vz)")
        .def("get_unit_heading", &SimulationKernel::get_unit_heading,
             "Get unit heading in degrees (NAV: 0=North, CW)", nb::arg("entity_id"))
        .def("get_unit_type", &SimulationKernel::get_unit_type, "Get unit type enum value",
             nb::arg("entity_id"))
        .def("is_unit_active", &SimulationKernel::is_unit_active, "Check if unit exists",
             nb::arg("entity_id"))
        .def("get_all_units", &SimulationKernel::get_all_units, "Get all units state")
        .def("get_detections", &SimulationKernel::get_detections, "Get unit sensor contacts")
        .def("get_unit_health", &SimulationKernel::get_unit_health,
             "Get unit health [current, max]")
        .def("get_unit_damage_state", &SimulationKernel::get_unit_damage_state,
             "Get unit damage state [mission, mobility, sensor, survivability]")
        .def("get_unit_fuel", &SimulationKernel::get_unit_fuel, nb::arg("entity_id"),
             "Returns [internal, max_internal, external, max_external]")
        .def("get_task_order", &SimulationKernel::get_task_order, "Get the latest task order",
             nb::arg("entity_id"))
        .def("get_leader_intent", &SimulationKernel::get_leader_intent,
             "Get the latest leader intent", nb::arg("entity_id"))
        .def("get_mission_command", &SimulationKernel::get_mission_command,
             "Get the active mission command", nb::arg("entity_id"))
        .def("get_pilot_report", &SimulationKernel::get_pilot_report, "Get the latest pilot report",
             nb::arg("entity_id"))
        .def("get_agent_observation", &SimulationKernel::get_agent_observation,
             "Get complete agent observation")
        .def(
            "get_visual_observation",
            [](SimulationKernel &self, uint64_t entity_id) {
                size_t shape[3] = {
                    static_cast<size_t>(arb::ARB_HEIGHT),
                    static_cast<size_t>(arb::ARB_WIDTH),
                    static_cast<size_t>(arb::ARB_CHANNELS),
                };
                return visual_tensor_to_numpy<nb::shape<static_cast<size_t>(arb::ARB_HEIGHT),
                                                        static_cast<size_t>(arb::ARB_WIDTH),
                                                        static_cast<size_t>(arb::ARB_CHANNELS)>>(
                    self.get_visual_observation(entity_id), 3, shape);
            },
            "Get ARB visual observation [H, W, C] tensor", nb::arg("entity_id"))
        .def(
            "get_visual_observation_downsampled",
            [](SimulationKernel &self, uint64_t entity_id, int factor) {
                const int downsample = factor > 1 ? factor : 1;
                auto downsampled = self.get_visual_observation_downsampled(entity_id, downsample);
                size_t shape[3] = {
                    static_cast<size_t>(arb::ARB_HEIGHT / downsample),
                    static_cast<size_t>(arb::ARB_WIDTH / downsample),
                    static_cast<size_t>(arb::ARB_CHANNELS),
                };
                return visual_tensor_to_numpy<
                    nb::shape<nb::any, nb::any, static_cast<size_t>(arb::ARB_CHANNELS)>>(
                    std::move(downsampled), 3, shape);
            },
            "Get ARB visual observation [H/f, W/f, C] tensor", nb::arg("entity_id"),
            nb::arg("factor"))
        .def("get_unit_messages", &SimulationKernel::get_unit_messages, "Get inbox")
        .def("send_message_command", &SimulationKernel::send_message_command, nb::arg("entity_id"),
             nb::arg("recipient_id"), nb::arg("msg_type"), nb::arg("msg_arg"));
}
