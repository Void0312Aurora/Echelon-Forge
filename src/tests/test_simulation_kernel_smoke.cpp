// Smoke tests for SimulationKernel lifecycle and basic operations.
//
// These tests verify the kernel can be constructed, reset, stepped,
// and can spawn / query units without crashing.  They are the minimum
// safety net for the C++ engine and are intended to catch regressions
// early — they do not attempt to validate physics or combat semantics.

#include "core/engine/simulation_kernel.h"
#include "core/engine/simulation_kernel_command_surface.h"
#include "components/command/command_link.h"
#include "components/command/command_link_qos.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/physics/control_surface.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"

#include <doctest/doctest.h>
#include <spdlog/spdlog.h>

#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>
#include <string>

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

namespace {

/// Return true when every element of `v` is finite.
bool all_finite(const std::vector<double> &v) {
    for (double x : v) {
        if (!std::isfinite(x)) return false;
    }
    return true;
}

} // namespace

// ---------------------------------------------------------------------------
// TEST_SUITE: simulation_kernel_smoke
// ---------------------------------------------------------------------------

TEST_SUITE("simulation_kernel_smoke") {

    TEST_CASE("construct_and_destroy") {
        // Verify the kernel can be constructed and destroyed without crashing.
        // The constructor already calls reset(42) and registers all systems.
        {
            SimulationKernel kernel;
            // Default shutdown happens in the destructor — we also call it
            // explicitly to verify it is idempotent.
            kernel.shutdown();
        }
    }

    TEST_CASE("reset_is_deterministic") {
        // Two kernels reset with the same seed should produce identical
        // initial state.
        SimulationKernel a;
        SimulationKernel b;
        a.reset(12345);
        b.reset(12345);

        auto ea = a.spawn_unit(Side::Blue, "Aircraft", 100.0, 200.0, 3000.0, 45.0, 0.0, 0.0, 150.0,
                               0.0, 0.0);
        auto eb = b.spawn_unit(Side::Blue, "Aircraft", 100.0, 200.0, 3000.0, 45.0, 0.0, 0.0, 150.0,
                               0.0, 0.0);

        REQUIRE(ea.is_valid());
        REQUIRE(eb.is_valid());

        // Step both kernels the same number of ticks.
        for (int i = 0; i < 10; ++i) {
            a.step();
            b.step();
        }

        auto pos_a = a.get_unit_position(ea.id());
        auto pos_b = b.get_unit_position(eb.id());

        REQUIRE(pos_a.size() == 3);
        REQUIRE(pos_b.size() == 3);

        // With identical seed & spawn params the two worlds must agree.
        CHECK(pos_a[0] == doctest::Approx(pos_b[0]));
        CHECK(pos_a[1] == doctest::Approx(pos_b[1]));
        CHECK(pos_a[2] == doctest::Approx(pos_b[2]));
    }

    TEST_CASE("reset_with_different_seeds_both_work") {
        // Two kernels with different seeds should both be functional.
        // (Simple forward flight without commands is deterministic — RNG
        // divergence requires explicit stochastic behaviour.)
        SimulationKernel a;
        SimulationKernel b;
        a.reset(111);
        b.reset(999);

        auto ea =
            a.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 200.0, 0.0, 0.0);
        auto eb =
            b.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 200.0, 0.0, 0.0);
        REQUIRE(ea.is_valid());
        REQUIRE(eb.is_valid());

        for (int i = 0; i < 30; ++i) {
            a.step();
            b.step();
        }

        // Both units must still be active after 30 steps.
        CHECK(a.is_unit_active(ea.id()));
        CHECK(b.is_unit_active(eb.id()));

        // Positions should be finite (forward flight moved the aircraft).
        auto pa = a.get_unit_position(ea.id());
        auto pb = b.get_unit_position(eb.id());
        REQUIRE(pa.size() == 3);
        REQUIRE(pb.size() == 3);
        CHECK(std::isfinite(pa[0]));
        CHECK(std::isfinite(pb[0]));
    }

    TEST_CASE("spawn_unit_returns_valid_entity") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 1000.0, 0.0, 0.0, 0.0, 100.0,
                                   0.0, 0.0);
        REQUIRE(e.is_valid());
        CHECK(kernel.is_unit_active(e.id()));
    }

    TEST_CASE("spawn_unit_position_is_correct") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Red, "Aircraft", 1234.0, 5678.0, 9000.0, 90.0, 10.0, -5.0,
                                   200.0, 50.0, 10.0);
        REQUIRE(e.is_valid());

        auto pos = kernel.get_unit_position(e.id());
        REQUIRE(pos.size() == 3);
        CHECK(pos[0] == doctest::Approx(1234.0));
        CHECK(pos[1] == doctest::Approx(5678.0));
        CHECK(pos[2] == doctest::Approx(9000.0));
    }

    TEST_CASE("spawn_unit_velocity_is_correct") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 150.0,
                                   30.0, 5.0);
        REQUIRE(e.is_valid());

        auto vel = kernel.get_unit_velocity(e.id());
        REQUIRE(vel.size() == 3);
        CHECK(vel[0] == doctest::Approx(150.0));
        CHECK(vel[1] == doctest::Approx(30.0));
        CHECK(vel[2] == doctest::Approx(5.0));
    }

    TEST_CASE("step_does_not_crash_over_many_ticks") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 250.0,
                                   0.0, 0.0);
        REQUIRE(e.is_valid());

        // 600 steps = 10 seconds at 60 Hz.
        for (int i = 0; i < 600; ++i) {
            kernel.step();
            REQUIRE(kernel.is_unit_active(e.id()));
        }

        // After stepping, position should have moved from origin.
        auto pos = kernel.get_unit_position(e.id());
        REQUIRE(all_finite(pos));
        // Any component should be non-zero after 600 steps at 250 m/s.
        bool moved = (std::abs(pos[0]) > 1.0 || std::abs(pos[1]) > 1.0);
        CHECK(moved);
    }

    TEST_CASE("spawn_multiple_units") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto b1 = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 200.0,
                                    0.0, 0.0);
        auto b2 = kernel.spawn_unit(Side::Blue, "Aircraft", 1000.0, 0.0, 5000.0, 0.0, 0.0, 0.0,
                                    200.0, 0.0, 0.0);
        auto r1 = kernel.spawn_unit(Side::Red, "Aircraft", 5000.0, 5000.0, 5000.0, 180.0, 0.0, 0.0,
                                    200.0, 0.0, 0.0);
        REQUIRE(b1.is_valid());
        REQUIRE(b2.is_valid());
        REQUIRE(r1.is_valid());

        auto all = kernel.get_all_units();
        CHECK(all.size() >= 3);
    }

    TEST_CASE("shutdown_is_idempotent") {
        SimulationKernel kernel;
        kernel.reset(42);
        kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 1000.0, 0.0, 0.0, 0.0, 100.0, 0.0, 0.0);

        kernel.shutdown();
        // Second shutdown must not crash or throw.
        kernel.shutdown();

        CHECK_THROWS_AS(kernel.reset(7), std::logic_error);
        CHECK_THROWS_AS(kernel.step(), std::logic_error);
        CHECK_THROWS_AS(kernel.set_time_step(0.1), std::logic_error);
        CHECK_THROWS_AS(kernel.load_database("examples/config/database"), std::logic_error);
        CHECK_THROWS_AS(kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 1000.0, 0.0, 0.0, 0.0,
                                          0.0, 0.0, 0.0),
                        std::logic_error);
        CHECK_THROWS_AS(kernel.set_wind(10.0, 270.0, 0.0), std::logic_error);
        CHECK_THROWS_AS(kernel.clear_zones(), std::logic_error);
        CHECK_THROWS_AS(kernel.set_missile_tuning(MissileTuning{}), std::logic_error);
        CHECK_THROWS_AS(kernel.fire_missile(1, 2), std::logic_error);
        CHECK_THROWS_AS(kernel.fire_naval_weapon(1, 2, 0), std::logic_error);
    }

    TEST_CASE("spawn_unit_side_assignment") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto blue = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 1000.0, 0.0, 0.0, 0.0,
                                      100.0, 0.0, 0.0);
        auto red = kernel.spawn_unit(Side::Red, "Aircraft", 0.0, 0.0, 1000.0, 0.0, 0.0, 0.0, 100.0,
                                     0.0, 0.0);
        auto neutral = kernel.spawn_unit(Side::Neutral, "Aircraft", 0.0, 0.0, 1000.0, 0.0, 0.0, 0.0,
                                         100.0, 0.0, 0.0);

        REQUIRE(blue.is_valid());
        REQUIRE(red.is_valid());
        REQUIRE(neutral.is_valid());

        // Three distinct entities must have different ids.
        CHECK(blue.id() != red.id());
        CHECK(blue.id() != neutral.id());
        CHECK(red.id() != neutral.id());

        // All must be reported active.
        CHECK(kernel.is_unit_active(blue.id()));
        CHECK(kernel.is_unit_active(red.id()));
        CHECK(kernel.is_unit_active(neutral.id()));
    }

    TEST_CASE("spawn_ship_unit") {
        SimulationKernel kernel;
        kernel.reset(42);

        // Ships do not have a flight model; they use naval motion systems.
        auto ship =
            kernel.spawn_unit(Side::Blue, "Ship", 0.0, 0.0, 0.0, 45.0, 0.0, 0.0, 10.0, 0.0, 0.0);
        REQUIRE(ship.is_valid());
        CHECK(kernel.is_unit_active(ship.id()));

        // Stepping should not crash even though Ship uses different physics.
        for (int i = 0; i < 10; ++i) {
            kernel.step();
            REQUIRE(kernel.is_unit_active(ship.id()));
        }

        auto pos = kernel.get_unit_position(ship.id());
        REQUIRE(all_finite(pos));
    }

    TEST_CASE("spawn_missile_unit") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto missile = kernel.spawn_unit(Side::Red, "Missile", 0.0, 0.0, 3000.0, 0.0, 0.0, 0.0,
                                         600.0, 0.0, 0.0);
        REQUIRE(missile.is_valid());
        CHECK(kernel.is_unit_active(missile.id()));

        // Missiles may have limited lifetime; step a few ticks and accept
        // either active or destroyed — the contract is "no crash".
        for (int i = 0; i < 5; ++i) {
            kernel.step();
        }
        // Simply reaching here without a crash is the success condition.
        CHECK(true);
    }

    TEST_CASE("fire_missile_requires_inventory_and_records_actual_ammo_delta") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto attacker = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 3000.0, 0.0, 0.0, 0.0,
                                          250.0, 0.0, 0.0);
        auto target = kernel.spawn_unit(Side::Red, "Aircraft", 12000.0, 0.0, 3000.0, 180.0, 0.0,
                                        0.0, -200.0, 0.0, 0.0);
        REQUIRE(attacker.is_valid());
        REQUIRE(target.is_valid());

        auto attacker_entity = kernel.get_world().entity(attacker.id());
        attacker_entity.remove<Ammo>();
        attacker_entity.remove<NavalWeaponSystem>();
        kernel.set_weapon_cooldown(attacker.id(), 0.0, -1.0);

        Detection track{};
        track.target_id = target.id();
        track.range = 12000.0;
        track.bearing = 0.0;
        track.elevation = 0.0;
        track.closing_speed = 450.0;
        track.signal_strength = 1.0;
        track.local_sensor_hit = true;
        kernel.set_contact_list(attacker.id(), {track});

        const auto blocked = kernel.fire_missile(attacker.id(), target.id());
        CHECK_FALSE(blocked.is_valid());
        CHECK(kernel.export_recent_engagement_events().launch_events.empty());

        attacker_entity.set<Ammo>({1, 1});
        const auto launched = kernel.fire_missile(attacker.id(), target.id());
        REQUIRE(launched.is_valid());

        const Ammo *remaining = attacker_entity.get<Ammo>();
        REQUIRE(remaining != nullptr);
        CHECK(remaining->missiles_remaining == 0);

        const auto events = kernel.export_recent_engagement_events();
        REQUIRE(events.launch_events.size() == 1);
        CHECK(events.launch_events.front().accepted);
        CHECK(events.launch_events.front().ammo_delta == -1);
        CHECK(events.launch_events.front().spawned_munition.entity_id == launched.id());
    }

    TEST_CASE("spawn_submarine_unit") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto sub = kernel.spawn_unit(Side::Blue, "Submarine", 0.0, 0.0, -50.0, 0.0, 0.0, 0.0, 5.0,
                                     0.0, 0.0);
        REQUIRE(sub.is_valid());
        CHECK(kernel.is_unit_active(sub.id()));

        for (int i = 0; i < 10; ++i) {
            kernel.step();
            REQUIRE(kernel.is_unit_active(sub.id()));
        }
    }

    TEST_CASE("get_unit_health_for_newly_spawned_unit") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 150.0,
                                   0.0, 0.0);
        REQUIRE(e.is_valid());

        auto health = kernel.get_unit_health(e.id());
        REQUIRE(health.size() == 2);
        CHECK(health[0] == doctest::Approx(100.0)); // current
        CHECK(health[1] == doctest::Approx(100.0)); // max
    }

    TEST_CASE("get_unit_fuel_is_finite") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 150.0,
                                   0.0, 0.0);
        REQUIRE(e.is_valid());

        auto fuel = kernel.get_unit_fuel(e.id());
        REQUIRE(fuel.size() == 4);
        CHECK(all_finite(fuel));
    }

    TEST_CASE("missing_unit_definition_file_fails_closed") {
        SimulationKernel kernel;
        kernel.reset(42);

        std::string error;
        CHECK_FALSE(
            kernel.load_unit_definitions("__ef_test_missing_unit_definitions__.json", &error));
        CHECK_FALSE(error.empty());
    }

    TEST_CASE("set_command_link_clamps_values_and_adds_pending_transports") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 150.0,
                                   0.0, 0.0);
        REQUIRE(e.is_valid());

        kernel.set_command_link(e.id(), -5.0, 2.0);

        auto entity = kernel.get_world().entity(e.id());
        const CommandLink *link = entity.get<CommandLink>();
        REQUIRE(link != nullptr);
        CHECK(link->latency_s == doctest::Approx(0.0));
        CHECK(link->drop_prob == doctest::Approx(1.0));
        CHECK(entity.get<PendingMovementCommand>() != nullptr);
        CHECK(entity.get<PendingActionCommand>() != nullptr);
        CHECK(entity.get<PendingMissionCommand>() != nullptr);
        CHECK(entity.get<MissionCommandPendingQueue>() != nullptr);
    }

    TEST_CASE("command_surface_sets_and_reads_maintained_tasking_components") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 150.0,
                                   0.0, 0.0);
        REQUIRE(e.is_valid());

        SimulationKernelCommandSurface commands(kernel);
        commands.set_command_link(e.id(), 0.0, 0.0);

        MissionCommand mission{};
        mission.command_code = 4;
        mission.cmd_heading_deg = 90.0;
        mission.cmd_altitude_m = 1500.0;
        mission.cmd_speed_mps = 180.0;
        commands.set_mission_command(e.id(), mission);

        TaskOrder order{};
        order.task_id = 77;
        order.element_id = 12;
        commands.set_task_order(e.id(), order);

        LeaderIntent intent{};
        intent.command_code = 9;
        intent.formation_id = 3;
        commands.set_leader_intent(e.id(), intent);

        PilotReport report{};
        report.sender_id = e.id();
        report.status_value = 2.0;
        commands.set_pilot_report(e.id(), report);

        const SimulationKernelCommandReadSurface reader(kernel);
        const MissionCommand got_mission = reader.get_mission_command(e.id());
        CHECK(got_mission.active);
        CHECK(got_mission.command_code == 4);
        CHECK(got_mission.cmd_heading_deg == doctest::Approx(90.0));
        CHECK(got_mission.cmd_altitude_m == doctest::Approx(1500.0));
        CHECK(got_mission.cmd_speed_mps == doctest::Approx(180.0));

        const TaskOrder got_order = reader.get_task_order(e.id());
        CHECK(got_order.active);
        CHECK(got_order.task_id == 77);
        CHECK(got_order.element_id == 12);

        const LeaderIntent got_intent = reader.get_leader_intent(e.id());
        CHECK(got_intent.active);
        CHECK(got_intent.command_code == 9);
        CHECK(got_intent.formation_id == 3);

        const PilotReport got_report = reader.get_pilot_report(e.id());
        CHECK(got_report.active);
        CHECK(got_report.sender_id == e.id());
        CHECK(got_report.status_value == doctest::Approx(2.0));
    }

    TEST_CASE("is_unit_active_returns_false_for_unknown_id") {
        SimulationKernel kernel;
        kernel.reset(42);

        // An entity id that was never spawned.
        CHECK_FALSE(kernel.is_unit_active(99999999));
    }

    TEST_CASE("get_unit_position_for_unknown_id_returns_finite") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto pos = kernel.get_unit_position(99999999);
        // Implementation returns a zero-filled vector for unknown entities.
        REQUIRE(pos.size() == 3);
        CHECK(pos[0] == doctest::Approx(0.0));
        CHECK(pos[1] == doctest::Approx(0.0));
        CHECK(pos[2] == doctest::Approx(0.0));
    }

    TEST_CASE("empty_kernel_step_does_not_crash") {
        // Stepping an empty world (no units) must not crash.
        SimulationKernel kernel;
        kernel.reset(42);

        for (int i = 0; i < 100; ++i) {
            kernel.step();
        }
    }

    TEST_CASE("environment_config_does_not_crash") {
        SimulationKernel kernel;
        kernel.reset(42);

        kernel.set_wind(10.0, 270.0, 2.0);
        kernel.set_terrain_type("flat");
        kernel.set_maritime_state(3.0, 180.0, 8.0);

        auto ms = kernel.get_maritime_state();
        // Just check the call returned without exception — values depend on model.
        (void)ms;

        kernel.clear_maritime_state();
        kernel.add_zone("test_zone", 0.0, 0.0, 1000.0, 1000.0, 0.0, 0);
        kernel.clear_zones();
    }

    TEST_CASE("step_time_default_is_60hz") {
        SimulationKernel kernel;
        CHECK(kernel.get_time_step() == doctest::Approx(1.0 / 60.0));
    }

    TEST_CASE("step_time_is_settable") {
        SimulationKernel kernel;
        kernel.set_time_step(0.1);
        CHECK(kernel.get_time_step() == doctest::Approx(0.1));
        kernel.set_time_step(1.0 / 120.0);
        CHECK(kernel.get_time_step() == doctest::Approx(1.0 / 120.0));
    }

    TEST_CASE("step_time_rejects_non_positive_and_non_finite_values") {
        SimulationKernel kernel;
        const double original = kernel.get_time_step();

        CHECK_THROWS_AS(kernel.set_time_step(0.0), std::invalid_argument);
        CHECK_THROWS_AS(kernel.set_time_step(-0.1), std::invalid_argument);
        CHECK_THROWS_AS(kernel.set_time_step(std::numeric_limits<double>::infinity()),
                        std::invalid_argument);
        CHECK_THROWS_AS(kernel.set_time_step(-std::numeric_limits<double>::infinity()),
                        std::invalid_argument);
        CHECK_THROWS_AS(kernel.set_time_step(std::numeric_limits<double>::quiet_NaN()),
                        std::invalid_argument);
        CHECK(kernel.get_time_step() == doctest::Approx(original));
    }

    TEST_CASE("exact_stage_inventory_is_non_empty") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto stages = kernel.exact_gpu_migration_stage_inventory();
        CHECK_FALSE(stages.empty());

        auto contracts = kernel.exact_gpu_migration_stage_contract_inventory();
        CHECK_FALSE(contracts.empty());

        const auto stage_index = [&](const std::string &name) {
            const auto it = std::find_if(stages.begin(), stages.end(),
                                         [&](const auto &stage) { return stage.name == name; });
            REQUIRE(it != stages.end());
            CHECK(it->gpu_migration_scope);
            CHECK(it->manual_trace_supported);
            return static_cast<std::size_t>(std::distance(stages.begin(), it));
        };
        CHECK(stage_index("ClearForces") < stage_index("FlightControl"));
        CHECK(stage_index("ComputeAeroState") < stage_index("ComputePropulsion"));
        CHECK(stage_index("ComputePropulsion") < stage_index("ComputeForces"));
        CHECK(stage_index("ComputeForces") < stage_index("AdvanceControlSurfaces"));
        CHECK(stage_index("AdvanceControlSurfaces") < stage_index("ComputeAerodynamics"));

        const auto has_contract = [&](const std::string &name) {
            return std::any_of(contracts.begin(), contracts.end(),
                               [&](const auto &contract) { return contract.name == name; });
        };
        CHECK(has_contract("ComputePropulsion"));
        CHECK(has_contract("AdvanceControlSurfaces"));
    }

    TEST_CASE("exact_stage_trace_does_not_crash") {
        SimulationKernel kernel;
        kernel.reset(42);

        kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 200.0, 0.0, 0.0);

        kernel.begin_exact_stage_trace_frame();

        auto stages = kernel.exact_gpu_migration_stage_inventory();
        REQUIRE_FALSE(stages.empty());

        // Run each stage by name — this exercises the traceable pipeline.
        for (const auto &stage : stages) {
            if (stage.manual_trace_supported) {
                bool ok = kernel.run_exact_stage_trace_stage(stage.name);
                CHECK(ok);
            }
        }

        kernel.end_exact_stage_trace_frame();
    }

    TEST_CASE("exact_stage_trace_executes_propulsion_actuator_and_force_effects") {
        SimulationKernel kernel;
        REQUIRE(kernel.load_database("examples/config/database"));
        kernel.reset(42);

        auto entity = kernel.spawn_unit(Side::Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 90.0, 0.0,
                                        0.0, 0.0, 200.0, 0.0);
        REQUIRE(entity.is_valid());

        PilotAction action{};
        action.active = true;
        action.stick_pitch = 0.35;
        action.stick_roll = 0.55;
        action.throttle = 1.0;
        action.gear_handle = 1.0;
        kernel.set_pilot_action(entity.id(), action);

        const Propulsion *propulsion_before = entity.get<Propulsion>();
        const ControlSurfaceState *surfaces_before = entity.get<ControlSurfaceState>();
        REQUIRE(propulsion_before != nullptr);
        const double throttle_state_before = propulsion_before->throttle_state;
        const double aileron_pos_before =
            surfaces_before != nullptr ? surfaces_before->aileron_pos : 0.0;
        const double elevator_pos_before =
            surfaces_before != nullptr ? surfaces_before->elevator_pos : 0.0;

        kernel.step_exact_stage_traceable_pipeline();

        const Propulsion *propulsion_after = entity.get<Propulsion>();
        const ControlSurfaceState *surfaces_after = entity.get<ControlSurfaceState>();
        const ForceAccumulator *forces_after = entity.get<ForceAccumulator>();
        REQUIRE(propulsion_after != nullptr);
        REQUIRE(surfaces_after != nullptr);
        REQUIRE(forces_after != nullptr);
        CHECK(propulsion_after->throttle_state > throttle_state_before);
        CHECK(propulsion_after->current_thrust_n > 0.0);
        CHECK(std::abs(surfaces_after->aileron_pos) > std::abs(aileron_pos_before));
        CHECK(std::abs(surfaces_after->elevator_pos) > std::abs(elevator_pos_before));
        CHECK(std::abs(forces_after->fx) + std::abs(forces_after->fy) + std::abs(forces_after->fz) >
              0.0);
    }

    TEST_CASE("get_agent_observation_for_active_unit") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 200.0,
                                   0.0, 0.0);
        REQUIRE(e.is_valid());

        // Step once so instruments are populated.
        kernel.step();

        auto obs = kernel.get_agent_observation(e.id());
        // total_reward starts at 0 — structural smoke check.
        CHECK(std::isfinite(obs.total_reward));
    }

    TEST_CASE("get_instrument_state_for_active_unit") {
        SimulationKernel kernel;
        kernel.reset(42);

        auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 200.0,
                                   0.0, 0.0);
        REQUIRE(e.is_valid());

        kernel.step();

        auto inst = kernel.get_instrument_state(e.id());
        // After one step, altitude should match spawn z (5000 m).
        CHECK(inst.alt_baro_m == doctest::Approx(5000.0));
    }

} // TEST_SUITE simulation_kernel_smoke
