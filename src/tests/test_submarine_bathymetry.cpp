#include "components/basic/common.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "core/interfaces/environment_model.h"
#include "systems/domains/naval/submarine_motion_system.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <cmath>
#include <algorithm>
#include <limits>
#include <string>

namespace {

struct BathymetryTestEnvironment final : IEnvironmentModel {
    BathymetrySegmentObservation observation{};
    double last_from_x = 0.0;
    double last_from_y = 0.0;
    double last_to_x = 0.0;
    double last_to_y = 0.0;
    bool interior_shoal = false;

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
        auto result = observation;
        // Analytic fixture: water is 200 m deep at both step endpoints,
        // but has a 40 m shoal throughout 2 <= y <= 3. This is an exact
        // segment minimum, not endpoint-only sampling.
        if (interior_shoal && std::min(from_y, to_y) <= 3.0 && std::max(from_y, to_y) >= 2.0) {
            result.minimum_water_depth_m = 40.0;
        }
        return result;
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

    SubmarineRig invalid_clearance(20.0);
    set_valid_observation(invalid_clearance.environment, 80.0);
    invalid_clearance.unit.get_mut<SubmarineBathymetryPolicy>()->min_keel_clearance_m =
        std::numeric_limits<double>::quiet_NaN();
    invalid_clearance.step();
    CHECK(invalid_clearance.unit.get<Transform>()->x == doctest::Approx(0.0));
    CHECK(invalid_clearance.unit.get<Transform>()->y == doctest::Approx(0.0));
    CHECK(invalid_clearance.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::InvalidPolicy);
}

TEST_CASE("valid metadata still rejects a hull that cannot fit in the water column") {
    SubmarineRig rig(0.0);
    set_valid_observation(rig.environment, 4.0);
    rig.step();
    CHECK(rig.unit.get<Transform>()->x == doctest::Approx(0.0));
    CHECK(rig.unit.get<Transform>()->y == doctest::Approx(0.0));
    CHECK(rig.unit.get<Transform>()->z == doctest::Approx(0.0));
    CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::RejectedTrajectory);
}

TEST_CASE("dry and time-inconsistent observations are not treated as deep water") {
    SubmarineRig dry(20.0);
    dry.environment.observation.availability = IEnvironmentModel::BathymetryAvailability::Dry;
    dry.environment.observation.horizontal_frame = "local_xy";
    dry.environment.observation.vertical_datum = "MSL";
    dry.environment.observation.source = "synthetic_fixture";
    dry.environment.observation.time_invariant_for_step = true;
    dry.step();
    CHECK(dry.unit.get<Transform>()->y == doctest::Approx(0.0));
    CHECK(dry.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::UnknownBathymetry);

    SubmarineRig time_varying(20.0);
    set_valid_observation(time_varying.environment, 200.0);
    time_varying.environment.observation.time_invariant_for_step = false;
    time_varying.step();
    CHECK(time_varying.unit.get<Transform>()->y == doctest::Approx(0.0));
    CHECK(time_varying.unit.get<SubmarineBathymetryPolicy>()->last_status ==
          SubmarineDepthConstraintStatus::UnknownBathymetry);
}

TEST_CASE("interior shoal rejects a sweep whose deep endpoints would appear safe") {
    SubmarineRig rig(50.0);
    set_valid_observation(rig.environment, 200.0);
    rig.environment.interior_shoal = true;
    rig.environment.observation.source = "analytic_shoal.v1";
    rig.step();
    CHECK(rig.environment.last_from_y == doctest::Approx(0.0));
    CHECK(rig.environment.last_to_y == doctest::Approx(5.0));
    CHECK(rig.unit.get<Transform>()->y == doctest::Approx(0.0));
    CHECK(rig.unit.get<Transform>()->z == doctest::Approx(-40.0));
    CHECK(rig.unit.get<Velocity>()->vy == doctest::Approx(0.0));
    const auto *policy = rig.unit.get<SubmarineBathymetryPolicy>();
    REQUIRE(policy != nullptr);
    CHECK(policy->last_allowed_depth_m == doctest::Approx(27.0));
    CHECK(policy->last_status == SubmarineDepthConstraintStatus::RejectedTrajectory);
    CHECK(policy->last_source == "analytic_shoal.v1");
}

TEST_CASE("bathymetry rejects unavailable or inconsistent numeric and reference metadata") {
    for (int failure = 0; failure < 9; ++failure) {
        INFO("negative fixture ", failure);
        SubmarineRig rig(20.0);
        set_valid_observation(rig.environment, 200.0);
        auto &observation = rig.environment.observation;
        switch (failure) {
        case 0:
            observation.availability = IEnvironmentModel::BathymetryAvailability::Unavailable;
            break;
        case 1:
            observation.availability = IEnvironmentModel::BathymetryAvailability::InvalidDatum;
            break;
        case 2:
            observation.vertical_datum = "other_datum";
            break;
        case 3:
            observation.horizontal_frame = "other_frame";
            break;
        case 4:
            observation.water_surface_elevation_m = 1.0;
            break;
        case 5:
            observation.water_surface_elevation_m = std::numeric_limits<double>::quiet_NaN();
            break;
        case 6:
            observation.minimum_water_depth_m = std::numeric_limits<double>::quiet_NaN();
            break;
        case 7:
            observation.minimum_water_depth_m = -1.0;
            break;
        case 8:
            observation.source.clear();
            break;
        }
        rig.step();
        CHECK(rig.unit.get<Transform>()->y == doctest::Approx(0.0));
        CHECK(rig.unit.get<Transform>()->z == doctest::Approx(-20.0));
        CHECK(rig.unit.get<Velocity>()->vz == doctest::Approx(0.0));
        CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
              SubmarineDepthConstraintStatus::UnknownBathymetry);
    }
}

TEST_CASE("deep water constant-depth transit preserves speed and bounded heading evolution") {
    SubmarineRig rig(30.0);
    set_valid_observation(rig.environment, 200.0);
    auto *command = rig.unit.get_mut<NavalCommandIntent>();
    command->cmd_depth_m = 30.0;
    command->cmd_heading_deg = 90.0;
    for (int step = 1; step <= 5; ++step) {
        rig.step();
        const auto *position = rig.unit.get<Transform>();
        const auto *velocity = rig.unit.get<Velocity>();
        CHECK(position->z == doctest::Approx(-30.0));
        CHECK(position->heading == doctest::Approx(1.5 * step));
        CHECK(std::hypot(velocity->vx, velocity->vy) == doctest::Approx(5.0));
        CHECK(velocity->vz == doctest::Approx(0.0));
        CHECK(rig.unit.get<SubmarineBathymetryPolicy>()->last_status ==
              SubmarineDepthConstraintStatus::Allowed);
    }
}

TEST_CASE("absent and disabled bathymetry policies preserve the legacy open-water trace") {
    SubmarineRig absent(20.0);
    SubmarineRig disabled(20.0);
    absent.unit.remove<SubmarineBathymetryPolicy>();
    disabled.unit.get_mut<SubmarineBathymetryPolicy>()->enabled = false;
    for (int step = 1; step <= 3; ++step) {
        absent.step();
        disabled.step();
        const auto *legacy = absent.unit.get<Transform>();
        const auto *opt_out = disabled.unit.get<Transform>();
        CHECK(legacy->y == doctest::Approx(5.0 * step));
        CHECK(legacy->z == doctest::Approx(-20.0 - 10.0 * step));
        CHECK(opt_out->x == legacy->x);
        CHECK(opt_out->y == legacy->y);
        CHECK(opt_out->z == legacy->z);
        CHECK(opt_out->heading == legacy->heading);
        CHECK(disabled.unit.get<SubmarineBathymetryPolicy>()->last_status ==
              SubmarineDepthConstraintStatus::Disabled);
    }
}
