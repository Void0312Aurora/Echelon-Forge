#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/performance.h"
#include "core/engine/simulation_kernel.h"
#include "components/command/pilot_action.h"

#include <doctest/doctest.h>

namespace {

ForceAccumulator run_force_probe(bool with_primary_control, double empty_mass_kg = 1000.0) {
    SimulationKernel kernel;
    auto world_lease = kernel.acquire_world_lease();
    flecs::world &world = world_lease.world();

    Mass mass{};
    mass.empty_mass_kg = empty_mass_kg;
    Propulsion propulsion{};
    propulsion.current_thrust_n = 0.0;
    FlightModel flight_model{};

    auto entity = world.entity()
                      .set<ForceAccumulator>({})
                      .set<Transform>({})
                      .set<Velocity>({})
                      .set<Mass>(mass)
                      .set<Propulsion>(propulsion)
                      .set<FlightModel>(flight_model);
    if (with_primary_control) {
        PilotAction pilot{};
        pilot.active = true;
        entity.set<PilotAction>(pilot);
    }

    REQUIRE(kernel.run_exact_stage_direct("ComputeForces"));
    const ForceAccumulator *forces = entity.get<ForceAccumulator>();
    REQUIRE(forces != nullptr);
    return *forces;
}

} // namespace

TEST_CASE("ComputeForces applies gravity without primary flight control input") {
    const ForceAccumulator forces = run_force_probe(false);

    CHECK(forces.fx == doctest::Approx(0.0));
    CHECK(forces.fy == doctest::Approx(0.0));
    CHECK(forces.fz == doctest::Approx(-1000.0 * 9.80665));
}

TEST_CASE("ComputeForces preserves commanded gravity parity") {
    const ForceAccumulator no_command = run_force_probe(false);
    const ForceAccumulator neutral_command = run_force_probe(true);

    CHECK(no_command.fz == doctest::Approx(neutral_command.fz));
    CHECK(no_command.fx == doctest::Approx(neutral_command.fx));
    CHECK(no_command.fy == doctest::Approx(neutral_command.fy));
}

TEST_CASE("ComputeForces fails closed for invalid mass without control input") {
    const ForceAccumulator forces = run_force_probe(false, 0.0);

    CHECK(forces.fx == doctest::Approx(0.0));
    CHECK(forces.fy == doctest::Approx(0.0));
    CHECK(forces.fz == doctest::Approx(0.0));
}
