#include "core/engine/world_batch_runtime.h"

#include <doctest/doctest.h>

#include <array>
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <string>
#include <vector>

#include "components/basic/common.h"
#include "components/physics/control_surface.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/performance.h"
#include "runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"
#include "runtime/contracts/cuda_resident_flight_dynamics_fixture_contract.h"

namespace {

bool within_flight_dynamics_kinematics_budget(double actual, double expected) {
    return std::abs(actual - expected) <=
           std::max(1.0e-9, 1.0e-12 * std::max(std::abs(actual), std::abs(expected)));
}

std::vector<WorldSpawnRequest> make_spawns() {
    std::vector<WorldSpawnRequest> spawns;
    for (std::size_t world = 0; world < 2; ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
        spawn.entity_name = "CpuFlightDynamics" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0 + static_cast<double>(world);
        spawn.heading = 90.0;
        spawns.push_back(spawn);
    }
    return spawns;
}

std::vector<WorldPilotActionAssignment> make_actions(const std::vector<std::uint64_t> &entity_ids) {
    std::vector<WorldPilotActionAssignment> actions;
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        WorldPilotActionAssignment action{};
        action.world_index = world;
        action.entity_id = entity_ids[world];
        action.action.active = true;
        action.action.stick_roll =
            runtime::cuda_resident::kCudaResidentFlightDynamicsFirstInputs[world].stick_roll;
        action.action.stick_pitch =
            runtime::cuda_resident::kCudaResidentFlightDynamicsFirstInputs[world].stick_pitch;
        action.action.rudder =
            runtime::cuda_resident::kCudaResidentFlightDynamicsFirstInputs[world].rudder;
        action.action.throttle =
            runtime::cuda_resident::kCudaResidentFlightDynamicsFirstInputs[world].throttle;
        actions.push_back(action);
    }
    return actions;
}

} // namespace

TEST_CASE("CPU reference pins the fixed airborne flight-dynamics window") {
    using namespace runtime::cuda_resident;
    WorldBatchRuntime runtime(2);
    REQUIRE(runtime.load_database("examples/config/database"));
    const std::vector<std::uint32_t> seeds = {101, 202};
    const std::vector<double> time_steps(kCudaResidentFlightDynamicsFixtureTimeSteps.begin(),
                                         kCudaResidentFlightDynamicsFixtureTimeSteps.end());
    const auto ids =
        runtime.apply_world_setup_batch(seeds, {}, {}, {}, make_spawns(), time_steps, {});
    REQUIRE(ids.size() == 2);
    runtime.set_pilot_actions_batch(make_actions(ids));

    constexpr std::array<const char *, 9> stages = {
        "ClearForces",         "FlightControl",       "ComputeAeroState",
        "ComputePropulsion",   "ComputeForces",       "AdvanceControlSurfaces",
        "ComputeAerodynamics", "RotationalIntegrate", "LeapfrogIntegrate",
    };
    for (std::size_t world = 0; world < ids.size(); ++world) {
        auto &kernel = runtime.world_raw_quarantine(world);
        for (const char *stage : stages) {
            REQUIRE(kernel.run_exact_stage_direct(stage));
        }
    }

    for (std::size_t world = 0; world < ids.size(); ++world) {
        const auto entity = runtime.world_raw_quarantine(world).get_world().entity(ids[world]);
        const auto *transform = entity.get<Transform>();
        const auto *velocity = entity.get<Velocity>();
        const auto *angular = entity.get<AngularVelocity>();
        const auto *surfaces = entity.get<ControlSurfaceState>();
        const auto *aero = entity.get<AeroState>();
        const auto *mass = entity.get<Mass>();
        const auto *inertia = entity.get<Inertia>();
        REQUIRE(transform != nullptr);
        REQUIRE(velocity != nullptr);
        REQUIRE(angular != nullptr);
        REQUIRE(surfaces != nullptr);
        REQUIRE(aero != nullptr);
        REQUIRE(mass != nullptr);
        REQUIRE(inertia != nullptr);
        CHECK(mass->get_total_kg() ==
              doctest::Approx(kFlightDynamicsEmptyMassKg + kFlightDynamicsFuelMassKg));
        CHECK(inertia->ixx == doctest::Approx(kFlightDynamicsInertiaRollKgM2));
        CHECK(inertia->iyy == doctest::Approx(kFlightDynamicsInertiaPitchKgM2));
        CHECK(inertia->izz == doctest::Approx(kFlightDynamicsInertiaYawKgM2));
        const std::array<double, 9> kinematics = {
            transform->x, transform->y,       transform->z,     velocity->vx,    velocity->vy,
            velocity->vz, transform->heading, transform->pitch, transform->roll,
        };
        const std::array<double, 11> dynamics = {
            angular->p,
            angular->q,
            angular->r,
            surfaces->elevator_pos,
            surfaces->aileron_pos,
            surfaces->rudder_pos,
            aero->dynamic_pressure,
            aero->angle_of_attack,
            aero->sideslip_angle,
            aero->mach_number,
            aero->drag_coefficient,
        };
        for (std::size_t field = 0; field < kinematics.size(); ++field) {
            CAPTURE(world);
            CAPTURE(field);
            CAPTURE(kinematics[field]);
            CAPTURE(kCudaResidentFlightDynamicsFirstExpected[world].kinematics[field]);
            CHECK(within_flight_dynamics_kinematics_budget(
                kinematics[field],
                kCudaResidentFlightDynamicsFirstExpected[world].kinematics[field]));
        }
        for (std::size_t field = 0; field < dynamics.size(); ++field) {
            CAPTURE(world);
            CAPTURE(field);
            CAPTURE(dynamics[field]);
            CAPTURE(kCudaResidentFlightDynamicsFirstExpected[world].dynamics[field]);
            CHECK(within_flight_dynamics_kinematics_budget(
                dynamics[field], kCudaResidentFlightDynamicsFirstExpected[world].dynamics[field]));
        }
    }
}
