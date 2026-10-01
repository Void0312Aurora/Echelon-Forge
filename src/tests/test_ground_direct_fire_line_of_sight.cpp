// Ground consumer of the terrain line-of-sight query: the bounded rifle gate
// (docs/systems/environment/work/active/terrain_line_of_sight_v1/README.md).

// The gate rejects a non-visible shot before it consumes ammunition, and keeps
// the existing draw path for visible shots.

#include "core/engine/simulation_kernel.h"

#include "components/basic/common.h"
#include "components/combat/health.h"
#include "components/command/mission_command.h"
#include "components/domains/ground/combat/weapon_ground.h"
#include "components/systems/sensor.h"
#include "tests/terrain_raster_fixture.h"

#include <doctest/doctest.h>

#include <cmath>
#include <cstdint>

namespace {

struct RifleDuel {
    std::uint64_t shooter = 0;
    std::uint64_t target = 0;
};

RifleDuel spawn_rifle_duel(SimulationKernel &kernel, double shooter_x, double target_x, double y) {
    auto shooter = kernel.spawn_unit(Side::Blue, "Ground_Infantry_Soldier_MVP", shooter_x, y, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
    auto target = kernel.spawn_unit(Side::Red, "Ground_Infantry_Soldier_MVP", target_x, y, 0.0, 0.0,
                                    0.0, 0.0, 0.0, 0.0, 0.0);
    REQUIRE(shooter.is_valid());
    REQUIRE(target.is_valid());
    Detection track{};
    track.target_id = target.id();
    track.range = std::abs(target_x - shooter_x);
    shooter.set<ContactList>({{track}});
    return {shooter.id(), target.id()};
}

double rifle_ammunition(SimulationKernel &kernel, std::uint64_t entity_id) {
    return kernel.get_ground_weapon_state(entity_id)[2];
}

void command_stance(SimulationKernel &kernel, std::uint64_t entity_id, GroundStance stance) {
    // Zero-latency link: the stance must be the held command at fire time.
    kernel.set_command_link(entity_id, 0.0, 0.0);
    MissionCommand command = kernel.get_mission_command(entity_id);
    command.stance = stance;
    kernel.set_mission_command(entity_id, command);
}

constexpr int kRifle = static_cast<int>(GroundWeaponType::Rifle);

} // namespace

TEST_SUITE("ground_direct_fire_line_of_sight") {
    TEST_CASE("no measured terrain fails closed without consuming the round") {
        SimulationKernel kernel;
        REQUIRE(kernel.load_database("examples/config/database"));
        const auto duel = spawn_rifle_duel(kernel, 2.0, 18.0, 10.0);
        const double before = rifle_ammunition(kernel, duel.shooter);
        CHECK_FALSE(kernel.fire_ground_weapon(duel.shooter, duel.target, kRifle));
        CHECK(rifle_ammunition(kernel, duel.shooter) == doctest::Approx(before));
    }

    TEST_CASE("a terrain-blocked shot is rejected before release; a visible one fires") {
        const terrain_raster_fixture::ScopedBundle ridge(
            terrain_raster_fixture::east_west_ridge(100.0F, 3.0F));
        SimulationKernel kernel;
        REQUIRE(kernel.load_database("examples/config/database"));
        REQUIRE(kernel.load_arnis_terrain_bundle(ridge.root()));
        const auto blocked = spawn_rifle_duel(kernel, 2.0, 18.0, 10.0);
        const double before = rifle_ammunition(kernel, blocked.shooter);
        const double target_hp = kernel.get_unit_health(blocked.target)[0];
        CHECK_FALSE(kernel.fire_ground_weapon(blocked.shooter, blocked.target, kRifle));
        CHECK(rifle_ammunition(kernel, blocked.shooter) == doctest::Approx(before));
        CHECK(kernel.get_ground_weapon_state(blocked.shooter)[7] == doctest::Approx(0.0));
        CHECK(kernel.get_unit_health(blocked.target)[0] == doctest::Approx(target_hp));

        // Same raster, both soldiers on the same side of the crest: visible.
        const auto visible = spawn_rifle_duel(kernel, 12.0, 18.0, 4.0);
        CHECK(kernel.fire_ground_weapon(visible.shooter, visible.target, kRifle));
        CHECK(rifle_ammunition(kernel, visible.shooter) == doctest::Approx(before - 1.0));
    }

    TEST_CASE("the commanded stance selects the authored sight heights") {
        // A 0.5 m crest: a standing pair sees over it, a prone pair does not.
        const terrain_raster_fixture::ScopedBundle low_ridge(
            terrain_raster_fixture::east_west_ridge(100.0F, 0.5F));
        SimulationKernel kernel;
        REQUIRE(kernel.load_database("examples/config/database"));
        REQUIRE(kernel.load_arnis_terrain_bundle(low_ridge.root()));
        const auto duel = spawn_rifle_duel(kernel, 2.0, 18.0, 10.0);
        command_stance(kernel, duel.shooter, GroundStance::Prone);
        command_stance(kernel, duel.target, GroundStance::Prone);
        const double before = rifle_ammunition(kernel, duel.shooter);
        CHECK_FALSE(kernel.fire_ground_weapon(duel.shooter, duel.target, kRifle));
        CHECK(rifle_ammunition(kernel, duel.shooter) == doctest::Approx(before));

        command_stance(kernel, duel.shooter, GroundStance::Stand);
        command_stance(kernel, duel.target, GroundStance::Stand);
        CHECK(kernel.fire_ground_weapon(duel.shooter, duel.target, kRifle));
        CHECK(rifle_ammunition(kernel, duel.shooter) == doctest::Approx(before - 1.0));
    }
}
