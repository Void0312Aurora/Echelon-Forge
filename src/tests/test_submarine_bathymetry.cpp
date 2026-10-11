#include "components/basic/common.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "core/interfaces/environment_model.h"
#include "systems/domains/naval/submarine_motion_system.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <cmath>
#include <limits>
#include <string>

namespace {

struct BathymetryTestEnvironment final : IEnvironmentModel {
    BathymetrySegmentObservation observation{};
    double last_from_x = 0.0;
    double last_from_y = 0.0;
    double last_to_x = 0.0;
    double last_to_y = 0.0;

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
    BathymetrySegmentObservation get_bathymetry_along_segment(double from_x, double from_y,
                                                              double to_x, double to_y) override {
        last_from_x = from_x;
        last_from_y = from_y;
        last_to_x = to_x;
        last_to_y = to_y;
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
        platform.max_speed_submerged_mps = 5.0;
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
        policy->hull_reference_to_keel_m = 8.0;
        policy->horizontal_frame = "local_xy";
        policy->vertical_datum = "MSL";
        NavalCommandIntent command{};
        command.active = true;
        command.cmd_speed_mps = 5.0;
        command.cmd_depth_m = 100.0;
        unit.set<NavalCommandIntent>(command);
    }

    void step() { world.progress(1.0); }
};

void set_valid_observation(BathymetryTestEnvironment &environment, double depth_m) {
    environment.observation.availability = IEnvironmentModel::BathymetryAvailability::Valid;
    environment.observation.minimum_water_depth_m = depth_m;
    environment.observation.horizontal_frame = "local_xy";
    environment.observation.vertical_datum = "MSL";
    environment.observation.source = "synthetic_fixture";
    environment.observation.water_surface_elevation_m = 0.0;
    environment.observation.time_invariant_for_step = true;
}

} // namespace

TEST_CASE("bathymetry limits a commanded depth using explicit keel clearance") {
    SubmarineRig rig(20.0);
    set_valid_observation(rig.environment, 80.0);

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
    set_valid_observation(rig.environment, 200.0);

    rig.step();

    CHECK(rig.unit.get<Transform>()->z == doctest::Approx(-30.0));
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::Allowed);
}

TEST_CASE("rising seabed is represented by the segment minimum") {
    SubmarineRig rig(20.0);
    set_valid_observation(rig.environment, 40.0);

    rig.step();

    // The segment's 40 m minimum allows only 27 m center depth, so the
    // one-second step is limited to 27 m rather than entering the shallow cell.
    CHECK(rig.environment.last_from_x == doctest::Approx(0.0));
    CHECK(rig.environment.last_from_y == doctest::Approx(0.0));
    CHECK(rig.environment.last_to_x == doctest::Approx(0.0));
    CHECK(rig.environment.last_to_y == doctest::Approx(5.0));
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

    CHECK(rig.unit.get<Transform>()->x == doctest::Approx(0.0));
    CHECK(rig.unit.get<Transform>()->y == doctest::Approx(0.0));
    CHECK(rig.unit.get<Transform>()->z == doctest::Approx(-20.0));
    CHECK(rig.unit.get<Velocity>()->vz == doctest::Approx(0.0));
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::UnknownBathymetry);
}

TEST_CASE("bathymetry metadata and hull reference are required") {
    SubmarineRig rig(20.0);
    rig.environment.observation.availability = IEnvironmentModel::BathymetryAvailability::Valid;
    rig.environment.observation.minimum_water_depth_m = 200.0;
    rig.environment.observation.vertical_datum = "MSL";
    // Missing horizontal frame, source, and temporal declaration must not be
    // interpreted as a deep-water observation.
    rig.step();

    CHECK(rig.unit.get<Transform>()->x == doctest::Approx(0.0));
    CHECK(rig.unit.get<Transform>()->y == doctest::Approx(0.0));
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::UnknownBathymetry);

    SubmarineRig missing_keel(20.0);
    set_valid_observation(missing_keel.environment, 80.0);
    missing_keel.unit.get_mut<SubmarineBathymetryPolicy>()->hull_reference_to_keel_m =
        std::numeric_limits<double>::quiet_NaN();
    missing_keel.step();

    CHECK(missing_keel.unit.get<Transform>()->x == doctest::Approx(0.0));
    CHECK(missing_keel.unit.get<Transform>()->y == doctest::Approx(0.0));
    CHECK(missing_keel.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::InvalidPolicy);
}
