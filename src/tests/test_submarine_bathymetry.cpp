#include "components/basic/common.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "core/interfaces/environment_model.h"
#include "systems/domains/naval/submarine_motion_system.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <cmath>
#include <string>

namespace {

struct BathymetryTestEnvironment final : IEnvironmentModel {
    BathymetrySegmentObservation observation{};

    AtmosphericData get_atmosphere_at(double, double, double) override {
        return {1.225, 340.0, 101325.0, 288.15, {0.0, 0.0, 0.0}};
    }
    double get_terrain_elevation(double, double) override { return 0.0; }
    bool check_line_of_sight(double, double, double, double, double, double) override {
        return true;
    }
    double get_weather_attenuation(double, double, double, double, double, double, int) override {
        return 0.0;
    }
    Vec3 get_sun_direction() override { return {0.0, 0.0, 1.0}; }
    TerrainCell get_terrain_at(double, double) override {
        return {0.0, SurfaceType::Water, 1.0, 0.0, 0.0, 0.0};
    }
    void clear_zones() override {}
    void add_zone(const std::string &, double, double, double, double, double,
                  SurfaceType) override {}
    BathymetrySegmentObservation get_bathymetry_along_segment(double, double, double,
                                                              double) override {
        return observation;
    }
};

struct SubmarineRig {
    flecs::world world;
    BathymetryTestEnvironment environment;
    flecs::entity unit;

    explicit SubmarineRig(double initial_depth_m) {
        runtime::systems::register_default_component_contributions(world);
        register_submarine_motion_system(world);
        world.set<EnvironmentModelRef>({&environment});
        SubmarinePlatform platform{};
        platform.draft_m = 8.0;
        platform.max_depth_rate_mps = 10.0;
        platform.max_operating_depth_m = 300.0;
        unit = world.entity()
                   .set<Transform>({0.0, 0.0, -initial_depth_m, 0.0, 0.0, 0.0})
                   .set<Velocity>({0.0, 5.0, 0.0})
                   .set<SubmarinePlatform>(platform)
                   .set<SubmarineBathymetryPolicy>(SubmarineBathymetryPolicy{});
        auto *policy = unit.get_mut<SubmarineBathymetryPolicy>();
        REQUIRE(policy != nullptr);
        policy->enabled = true;
        policy->min_keel_clearance_m = 5.0;
        NavalCommandIntent command{};
        command.active = true;
        command.cmd_speed_mps = 5.0;
        command.cmd_depth_m = 100.0;
        unit.set<NavalCommandIntent>(command);
    }

    void step() { world.progress(1.0); }
};

} // namespace

TEST_CASE("bathymetry limits a commanded depth using draft and keel clearance") {
    SubmarineRig rig(20.0);
    rig.environment.observation.availability = IEnvironmentModel::BathymetryAvailability::Valid;
    rig.environment.observation.minimum_water_depth_m = 80.0;
    rig.environment.observation.vertical_datum = "MSL";

    rig.step();

    // Depth rate limits the move toward the allowed 67 m center depth; the
    // command is observable as a deterministic seabed limitation.
    CHECK(rig.unit.get<Transform>()->z == doctest::Approx(-30.0));
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::LimitedBySeabed);
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_allowed_depth_m == doctest::Approx(67.0));
}

TEST_CASE("deep water preserves the requested depth trajectory") {
    SubmarineRig rig(20.0);
    rig.environment.observation.availability = IEnvironmentModel::BathymetryAvailability::Valid;
    rig.environment.observation.minimum_water_depth_m = 200.0;
    rig.environment.observation.vertical_datum = "MSL";

    rig.step();

    CHECK(rig.unit.get<Transform>()->z == doctest::Approx(-30.0));
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::Allowed);
}

TEST_CASE("rising seabed is represented by the segment minimum") {
    SubmarineRig rig(20.0);
    rig.environment.observation.availability = IEnvironmentModel::BathymetryAvailability::Valid;
    rig.environment.observation.minimum_water_depth_m = 40.0;
    rig.environment.observation.vertical_datum = "MSL";

    rig.step();

    // The segment's 40 m minimum allows only 27 m center depth, so the
    // one-second step is limited to 27 m rather than entering the shallow cell.
    CHECK(rig.unit.get<Transform>()->z == doctest::Approx(-27.0));
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::LimitedBySeabed);
}

TEST_CASE("unknown bathymetry holds depth and reports conservative status") {
    SubmarineRig rig(20.0);
    rig.environment.observation.availability =
        IEnvironmentModel::BathymetryAvailability::OutOfCoverage;
    rig.environment.observation.vertical_datum = "MSL";

    rig.step();

    CHECK(rig.unit.get<Transform>()->z == doctest::Approx(-20.0));
    CHECK(rig.unit.get<Velocity>()->vz == doctest::Approx(0.0));
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::UnknownBathymetry);
}
