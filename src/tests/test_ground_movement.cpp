#include "components/basic/common.h"
#include "components/command/mission_command.h"
#include "components/domains/ground/ground_capabilities.h"
#include "core/interfaces/environment_model.h"
#include "systems/domains/ground/movement_system.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <cmath>
#include <string>

namespace {

struct GroundMovementEnvironment final : IEnvironmentModel {
    bool passable = true;

    AtmosphericData get_atmosphere_at(double, double, double) override {
        return {1.225, 340.0, 101325.0, 288.15, {0.0, 0.0, 0.0}};
    }

    double get_terrain_elevation(double x, double y) override { return 0.1 * x + 0.2 * y; }

    double get_ground_slope_deg(double, double) override { return 0.0; }

    bool check_line_of_sight(double, double, double, double, double, double) override {
        return true;
    }

    double get_weather_attenuation(double, double, double, double, double, double, int) override {
        return 0.0;
    }

    Vec3 get_sun_direction() override { return {0.0, 0.0, 1.0}; }

    TerrainCell get_terrain_at(double x, double y) override {
        return {get_terrain_elevation(x, y), SurfaceType::Concrete, 1.0, 0.0, 0.0, 0.0};
    }

    void clear_zones() override {}

    void add_zone(const std::string &, double, double, double, double, double,
                  SurfaceType) override {}

    GroundTransitionObservation get_ground_transition_observation(double from_x, double from_y,
                                                                  double to_x,
                                                                  double to_y) override {
        GroundTransitionObservation observation{};
        observation.configured = true;
        observation.passable = passable;
        observation.destination_surface = get_terrain_at(to_x, to_y).type;
        observation.distance_m = std::hypot(to_x - from_x, to_y - from_y);
        return observation;
    }
};

struct GroundMovementRig {
    flecs::world world;
    GroundMovementEnvironment environment;
    flecs::entity unit;

    GroundMovementRig() {
        runtime::systems::register_default_component_contributions(world);
        world.set<EnvironmentModelRef>({&environment});
        register_ground_infantry_movement_system(world);
        unit = world.entity()
                   .set<KeyEntity>({UnitType::Ground})
                   .add<GroundInfantryCapability>()
                   .set<Transform>({0.0, 0.0, 99.0, 123.0, 0.0, 0.0})
                   .set<Velocity>({0.0, 0.0, 0.0})
                   .set<MissionCommand>(MissionCommand{});
    }
};

} // namespace

TEST_SUITE("ground_movement") {
    TEST_CASE("move projects absolute terrain elevation and commanded heading") {
        GroundMovementRig rig;
        MissionCommand command{};
        command.active = true;
        command.cmd_heading_deg = 90.0;
        command.cmd_speed_mps = 10.0;
        command.ground_task_mode = GroundTaskMode::MoveStatic;
        rig.unit.set<MissionCommand>(command);

        rig.world.progress(1.0);

        const auto &transform = *rig.unit.get<Transform>();
        const auto &velocity = *rig.unit.get<Velocity>();
        CHECK(transform.x == doctest::Approx(10.0));
        CHECK(transform.y == doctest::Approx(0.0));
        CHECK(transform.z == doctest::Approx(1.0));
        CHECK(transform.heading == doctest::Approx(90.0));
        CHECK(velocity.vx == doctest::Approx(10.0));
        CHECK(velocity.vy == doctest::Approx(0.0));
    }

    TEST_CASE("static hold projects terrain without changing facing") {
        GroundMovementRig rig;
        rig.unit.set<Transform>({5.0, 2.0, 99.0, 37.0, 0.0, 0.0});
        MissionCommand command{};
        command.active = true;
        command.cmd_heading_deg = 180.0;
        command.cmd_speed_mps = 20.0;
        command.ground_task_mode = GroundTaskMode::OccupyStatic;
        rig.unit.set<MissionCommand>(command);

        rig.world.progress(1.0);

        const auto &transform = *rig.unit.get<Transform>();
        CHECK(transform.x == doctest::Approx(5.0));
        CHECK(transform.y == doctest::Approx(2.0));
        CHECK(transform.z == doctest::Approx(0.9));
        CHECK(transform.heading == doctest::Approx(37.0));
        CHECK(rig.unit.get<Velocity>()->vx == 0.0);
        CHECK(rig.unit.get<Velocity>()->vy == 0.0);
    }

    TEST_CASE("blocked move keeps position, updates requested facing, and grounds anchor") {
        GroundMovementRig rig;
        rig.environment.passable = false;
        rig.unit.set<Transform>({2.0, 3.0, 99.0, 37.0, 0.0, 0.0});
        MissionCommand command{};
        command.active = true;
        command.cmd_heading_deg = 225.0;
        command.cmd_speed_mps = 10.0;
        command.ground_task_mode = GroundTaskMode::MoveStatic;
        rig.unit.set<MissionCommand>(command);

        rig.world.progress(1.0);

        const auto &transform = *rig.unit.get<Transform>();
        CHECK(transform.x == doctest::Approx(2.0));
        CHECK(transform.y == doctest::Approx(3.0));
        CHECK(transform.z == doctest::Approx(0.8));
        CHECK(transform.heading == doctest::Approx(225.0));
        CHECK(rig.unit.get<Velocity>()->vx == 0.0);
        CHECK(rig.unit.get<Velocity>()->vy == 0.0);
    }
}
