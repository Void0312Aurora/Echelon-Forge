#include <doctest/doctest.h>

#include "components/physics/physics_input_policy.h"
#include "components/physics/forces.h"
#include "components/physics/performance.h"
#include "core/mission/runtime/termination_runtime.h"
#include "systems/domains/air/actuator_system.h"
#include "systems/domains/air/propulsion_system.h"

#include <limits>

namespace {

constexpr double kNaN = std::numeric_limits<double>::quiet_NaN();
constexpr double kPositiveInfinity = std::numeric_limits<double>::infinity();

} // namespace

TEST_SUITE("timestep_contract") {

    TEST_CASE("shared integrator fallback accepts only finite positive dt") {
        for (const double invalid : {0.0, -0.1, kNaN, kPositiveInfinity, -kPositiveInfinity}) {
            CHECK(physics_runtime::resolve_integrator_dt(invalid) ==
                  doctest::Approx(physics_runtime::kIntegratorFallbackDtS));
        }
        CHECK(physics_runtime::resolve_integrator_dt(0.125) == doctest::Approx(0.125));
    }

    TEST_CASE("air actuator and propulsion helpers use the shared fallback") {
        const double expected_actuator = flight_dynamics::actuator_first_order_step(
            0.0, 1.0, physics_runtime::kIntegratorFallbackDtS, 1.0);
        const double expected_propulsion = flight_dynamics::first_order_step(
            0.0, 1.0, physics_runtime::kIntegratorFallbackDtS, 1.0);
        for (const double invalid : {0.0, -0.1, kNaN, kPositiveInfinity}) {
            CHECK(flight_dynamics::actuator_first_order_step(0.0, 1.0, invalid, 1.0) ==
                  doctest::Approx(expected_actuator));
            CHECK(flight_dynamics::first_order_step(0.0, 1.0, invalid, 1.0) ==
                  doctest::Approx(expected_propulsion));
        }
        CHECK(flight_dynamics::actuator_first_order_step(0.0, 1.0, 0.2, 1.0) !=
              doctest::Approx(expected_actuator));
        CHECK(flight_dynamics::first_order_step(0.0, 1.0, 0.2, 1.0) !=
              doctest::Approx(expected_propulsion));
    }

    TEST_CASE("entity damage and naval motion retain a finite one-sixtieth fallback") {
        for (const double invalid : {0.0, -0.1, kNaN, kPositiveInfinity, -kPositiveInfinity}) {
            CHECK(physics_runtime::resolve_entity_dt(invalid) ==
                  doctest::Approx(physics_runtime::kEntityFallbackDtS));
        }
        CHECK(physics_runtime::resolve_entity_dt(0.2) == doctest::Approx(0.2));
    }

    TEST_CASE("mission termination converts invalid dt to the documented 50 ms grace cadence") {
        SafetyRuntimeInputs inputs{};
        inputs.runway_surface_phase = true;
        inputs.on_runway_task = false;
        inputs.off_runway_terminate_speed = 10.0;
        inputs.speed_mps = 20.0;
        inputs.off_runway_terminate_grace_s = 0.10;
        inputs.off_runway_steps = 3;
        inputs.off_runway_terminate_penalty = -7.0;

        for (const double invalid : {0.0, -0.1, kNaN, kPositiveInfinity, -kPositiveInfinity}) {
            inputs.time_step_s = invalid;
            const SafetyRuntimeProducts out = compute_safety_runtime(inputs);
            CHECK(out.terminated);
            CHECK(out.reason_code == TerminationReasonCode::OffRunwayTerminate);
            CHECK(out.off_runway_terminate_penalty == doctest::Approx(-7.0));
        }

        inputs.time_step_s = 0.025;
        const SafetyRuntimeProducts positive = compute_safety_runtime(inputs);
        CHECK_FALSE(positive.terminated);
        CHECK(positive.reason_code == TerminationReasonCode::Running);
    }

} // TEST_SUITE("timestep_contract")
