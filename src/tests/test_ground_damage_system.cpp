#include "components/combat/common/damage_common.h"
#include "components/combat/health.h"
#include "components/domains/ground/combat/damage_ground.h"
#include "systems/domains/ground/damage_system_ground.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <cmath>
#include <limits>

namespace {

struct GroundDamageRig {
    flecs::world world;
    flecs::entity entity;

    GroundDamageRig() {
        runtime::systems::register_default_component_contributions(world);
        register_ground_damage_system(world);

        GroundPlatformDamageState ground{};
        ground.mobility_integrity = 0.85;
        ground.track_integrity = 0.90;
        ground.fire_severity = 0.60;
        ground.ignition_source_severity = 0.40;
        ground.fire_suppression_integrity = 0.75;
        ground.structural_integrity = 0.80;
        ground.ongoing_structural_damage = 0.30;
        ground.casualty_fraction = 0.10;
        ground.command_integrity = 0.95;

        PlatformDamageState platform{};
        platform.fire_severity = ground.fire_severity;
        platform.ongoing_hull_breach = ground.ongoing_structural_damage;
        entity = world.entity()
                     .set<Health>({100.0, 100.0})
                     .set<PlatformDamageState>(platform)
                     .set<GroundPlatformDamageState>(ground);
    }

    void step(double dt, int count) {
        for (int i = 0; i < count; ++i) {
            world.progress(static_cast<float>(dt));
        }
    }
};

void check_same_state(const GroundDamageRig &lhs, const GroundDamageRig &rhs) {
    const auto *left_ground = lhs.entity.get<GroundPlatformDamageState>();
    const auto *right_ground = rhs.entity.get<GroundPlatformDamageState>();
    const auto *left_platform = lhs.entity.get<PlatformDamageState>();
    const auto *right_platform = rhs.entity.get<PlatformDamageState>();
    REQUIRE(left_ground != nullptr);
    REQUIRE(right_ground != nullptr);
    REQUIRE(left_platform != nullptr);
    REQUIRE(right_platform != nullptr);

    CHECK(left_ground->fire_severity == doctest::Approx(right_ground->fire_severity).epsilon(5e-4));
    CHECK(left_ground->ignition_source_severity ==
          doctest::Approx(right_ground->ignition_source_severity).epsilon(5e-4));
    CHECK(left_ground->ongoing_structural_damage ==
          doctest::Approx(right_ground->ongoing_structural_damage).epsilon(5e-4));
    CHECK(left_ground->structural_integrity ==
          doctest::Approx(right_ground->structural_integrity).epsilon(5e-4));
    CHECK(left_ground->casualty_fraction ==
          doctest::Approx(right_ground->casualty_fraction).epsilon(5e-4));
    CHECK(left_platform->mission_capability ==
          doctest::Approx(right_platform->mission_capability).epsilon(5e-4));
    CHECK(left_platform->mobility_capability ==
          doctest::Approx(right_platform->mobility_capability).epsilon(5e-4));
    CHECK(left_platform->survivability_margin ==
          doctest::Approx(right_platform->survivability_margin).epsilon(5e-4));
}

} // namespace

TEST_SUITE("ground_damage_system") {

    TEST_CASE("progressive ground damage is expressed per simulated second") {
        GroundDamageRig sixty_hz;
        GroundDamageRig twenty_hz;
        GroundDamageRig ten_hz;

        sixty_hz.step(1.0 / 60.0, 60);
        twenty_hz.step(0.05, 20);
        ten_hz.step(0.1, 10);

        check_same_state(sixty_hz, twenty_hz);
        check_same_state(sixty_hz, ten_hz);
    }

    TEST_CASE("the one-sixtieth baseline preserves the former per-tick response") {
        GroundDamageRig rig;
        rig.step(1.0 / 60.0, 1);

        const auto *ground = rig.entity.get<GroundPlatformDamageState>();
        const auto *platform = rig.entity.get<PlatformDamageState>();
        REQUIRE(ground != nullptr);
        REQUIRE(platform != nullptr);
        CHECK(ground->fire_severity == doctest::Approx(0.5992));
        CHECK(ground->ignition_source_severity == doctest::Approx(0.3995));
        CHECK(ground->ongoing_structural_damage == doctest::Approx(0.2999));
        CHECK(ground->casualty_fraction == doctest::Approx(0.1009));
        CHECK(platform->mission_capability == doctest::Approx(0.99868));
        CHECK(platform->mobility_capability == doctest::Approx(0.99935));
        CHECK(platform->survivability_margin == doctest::Approx(0.99814));
    }

    TEST_CASE("paused or invalid ground damage deltas are a no-op") {
        CHECK(ground_damage_detail::resolve_damage_dt(0.0) == doctest::Approx(0.0));
        CHECK(ground_damage_detail::resolve_damage_dt(-0.1) == doctest::Approx(0.0));
        CHECK(ground_damage_detail::resolve_damage_dt(std::numeric_limits<double>::quiet_NaN()) ==
              doctest::Approx(0.0));
        CHECK(ground_damage_detail::resolve_damage_dt(std::numeric_limits<double>::infinity()) ==
              doctest::Approx(0.0));
    }

} // TEST_SUITE("ground_damage_system")
