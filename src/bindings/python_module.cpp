#include <nanobind/nanobind.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/vector.h>
#include "core/simulation_kernel.h"
#include <spdlog/spdlog.h>

namespace nb = nanobind;

NB_MODULE(cmo_py, m) {
    // Bind Side Enum
    nb::enum_<Side>(m, "Side")
        .value("Blue", Side::Blue)
        .value("Red", Side::Red)
        .value("Neutral", Side::Neutral)
        .value("Unknown", Side::Unknown);

    // Bind UnitType Enum
    nb::enum_<UnitType>(m, "UnitType")
        .value("Aircraft", UnitType::Aircraft)
        .value("Ship", UnitType::Ship)
        .value("Missile", UnitType::Missile)
        .value("Facility", UnitType::Facility);

    // Bind SimulationKernel
    nb::class_<SimulationKernel>(m, "SimulationKernel")
        .def(nb::init<>())
        .def("reset", &SimulationKernel::reset, "Reset the simulation", nb::arg("seed") = 42)
        .def("step", &SimulationKernel::step, "Advance simulation by one fixed tick")
        .def("get_time_step", &SimulationKernel::get_time_step, "Get the fixed time step in seconds")
        .def("spawn_unit", [](SimulationKernel& self, Side side, UnitType type, 
                              double x, double y, double z, 
                              double vx, double vy, double vz) {
            // We return the Entity ID as an integer for MVP
            auto e = self.spawn_unit(side, type, x, y, z, vx, vy, vz);
            return e.id();
        }, "Spawn a unit and return its Entity ID", 
           nb::arg("side"), nb::arg("type"), 
           nb::arg("x"), nb::arg("y"), nb::arg("z"), 
           nb::arg("vx")=0, nb::arg("vy")=0, nb::arg("vz")=0)

        // Action Interface
        .def("set_command", &SimulationKernel::set_unit_command, "Set movement command for a unit",
             nb::arg("entity_id"), nb::arg("heading_deg"), nb::arg("speed_mps"))
             
        .def("fire_missile", [](SimulationKernel& self, uint64_t attacker_id, uint64_t target_id) {
             auto e = self.fire_missile(attacker_id, target_id);
             return e.id(); // Return ID just like spawn_unit
        }, "Fire a missile from attacker to target", nb::arg("attacker_id"), nb::arg("target_id"))
        
        // Helper to get unit position (state observation)
        .def("get_unit_position", [](SimulationKernel& self, uint64_t entity_id) {
             auto p = self.get_unit_position(entity_id);
             return std::make_tuple(p[0], p[1], p[2]);
        }, "Get unit position (x,y,z)")
        
        // Helper to get unit heading (degrees)
        .def("get_unit_heading", [](SimulationKernel& self, uint64_t entity_id) {
             auto world = self.get_world();
             auto e = world.entity(entity_id);
             if(!e.is_valid()) return 0.0;
             const Velocity* v = e.get<Velocity>();
             if(!v) return 0.0;
             double rad = std::atan2(v->vy, v->vx);
             double deg = rad * 180.0 / M_PI;
             if(deg < 0) deg += 360.0;
             return deg;
        }, "Get unit heading in degrees")
        
        // Helper to get unit type
        .def("get_unit_type", [](SimulationKernel& self, uint64_t entity_id) {
             auto world = self.get_world();
             auto e = world.entity(entity_id);
             if(!e.is_valid()) return 0;
             const KeyEntity* k = e.get<KeyEntity>();
             return k ? (int)k->type : 0;
        }, "Get unit type enum value")
        
        // Helper to check if unit is active/alive
        .def("is_unit_active", [](SimulationKernel& self, uint64_t entity_id) {
             auto world = self.get_world();
             return world.entity(entity_id).is_valid();
        }, "Check if unit exists");
}
