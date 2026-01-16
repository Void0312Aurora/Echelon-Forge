#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
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
        
        // Helper to get unit position (state observation)
        .def("get_unit_position", [](SimulationKernel& self, uint64_t entity_id) {
            auto world = self.get_world();
            auto e = world.entity(entity_id);
            if (!e.is_valid()) {
                throw std::runtime_error("Invalid entity ID");
            }
            const Transform* t = e.get<Transform>();
            if (!t) {
                throw std::runtime_error("Entity has no Transform");
            }
            return std::vector<double>{t->x, t->y, t->z};
        });
}
