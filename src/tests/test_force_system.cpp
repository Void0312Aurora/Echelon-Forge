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

TEST_CASE("clear, compute, and integrate preserve no-command gravity across steps") {
    constexpr double dt = 0.05;
    constexpr double mass_kg = 1000.0;
    constexpr double gravity = 9.80665;
    SimulationKernel kernel;
    kernel.set_time_step(dt);
    auto world_lease = kernel.acquire_world_lease();
    flecs::world &world = world_lease.world();
    const auto entity = world.entity()
                            .set<ForceAccumulator>({123.0, -7.0, 91.0, 0.0, 0.0, 0.0})
                            .set<Transform>({0.0, 0.0, 1000.0, 0.0, 0.0, 0.0})
                            .set<Velocity>({0.0, 0.0, 0.0})
                            .set<Mass>(Mass{mass_kg, 0.0, 0.0})
                            .set<Propulsion>(Propulsion{0.0, 0.0, 0.0, false})
                            .set<FlightModel>(FlightModel{});

    REQUIRE(kernel.run_exact_stage_direct("ClearForces"));
    CHECK(entity.get<ForceAccumulator>()->fz == doctest::Approx(0.0));
    REQUIRE(kernel.run_exact_stage_direct("ComputeForces"));
    CHECK(entity.get<ForceAccumulator>()->fz == doctest::Approx(-mass_kg * gravity));
    REQUIRE(kernel.run_exact_stage_direct("LeapfrogIntegrate"));
    const double first_z = entity.get<Transform>()->z;
    const double first_vz = entity.get<Velocity>()->vz;
    CHECK(first_vz == doctest::Approx(-gravity * dt));
    CHECK(first_z == doctest::Approx(1000.0 - 0.5 * gravity * dt * dt));

    REQUIRE(kernel.run_exact_stage_direct("ClearForces"));
    REQUIRE(kernel.run_exact_stage_direct("ComputeForces"));
    REQUIRE(kernel.run_exact_stage_direct("LeapfrogIntegrate"));
    CHECK(entity.get<Velocity>()->vz - first_vz == doctest::Approx(-gravity * dt));
    CHECK(entity.get<Transform>()->z - first_z ==
          doctest::Approx(first_vz * dt - 0.5 * gravity * dt * dt));
}
