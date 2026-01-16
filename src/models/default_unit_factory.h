#pragma once

#include <cmath>
#include <unordered_map>

#include <spdlog/spdlog.h>

#include "components/action.h"
#include "components/common.h"
#include "components/health.h"
#include "components/performance.h"
#include "components/scoring.h"
#include "components/sensor.h"
#include "content/unit_definition_loader.h"
#include "core/unit_factory.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

inline double default_factory_wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

inline double default_factory_math_deg_to_nav_deg(double math_deg) {
    return default_factory_wrap_angle_360(90.0 - math_deg);
}

class DefaultUnitFactory : public IUnitFactory {
public:
    explicit DefaultUnitFactory(const std::string& config_path = std::string()) {
        UnitDefinition aircraft{};
        aircraft.type = UnitType::Aircraft;
        aircraft.name = "Aircraft";
        aircraft.health = {100.0, 100.0};
        aircraft.has_sensor = true;
        aircraft.sensor = {30000.0, 120.0, 1.0, -1.0, 0.9, 2.0, 1.0, 25.0, 2.0, 0.3};
        aircraft.has_flight_model = true;
        aircraft.flight_model = {600.0, 50.0, 20.0, 50.0, 300.0, 9.0};
        aircraft.has_score = true;
        aircraft.score = {0.0, 0, 0, 0};
        aircraft.has_ammo = true;
        aircraft.ammo = {4, 4};
        definitions_.emplace(aircraft.type, aircraft);

        UnitDefinition missile{};
        missile.type = UnitType::Missile;
        missile.name = "Missile";
        missile.health = {100.0, 100.0};
        missile.has_sensor = true;
        missile.sensor = {30000.0, 120.0, 0.2, -1.0, 0.95, 2.0, 0.5, 15.0, 0.5, 0.2};
        missile.has_flight_model = true;
        missile.flight_model = {1200.0, 100.0, 40.0, 100.0, 600.0, 30.0};
        missile.has_score = true;
        missile.score = {0.0, 0, 0, 0};
        missile.has_ammo = false;
        missile.ammo = {0, 0};
        definitions_.emplace(missile.type, missile);

        UnitDefinition ship{};
        ship.type = UnitType::Ship;
        ship.name = "Ship";
        ship.health = {100.0, 100.0};
        ship.has_sensor = true;
        ship.sensor = {30000.0, 120.0, 2.0, -1.0, 0.9, 2.0, 2.0, 50.0, 3.0, 0.2};
        ship.has_flight_model = false;
        ship.has_score = true;
        ship.score = {0.0, 0, 0, 0};
        ship.has_ammo = false;
        ship.ammo = {0, 0};
        definitions_.emplace(ship.type, ship);

        UnitDefinition facility{};
        facility.type = UnitType::Facility;
        facility.name = "Facility";
        facility.health = {100.0, 100.0};
        facility.has_sensor = true;
        facility.sensor = {30000.0, 120.0, 2.0, -1.0, 0.9, 2.0, 2.0, 50.0, 3.0, 0.2};
        facility.has_flight_model = false;
        facility.has_score = true;
        facility.score = {0.0, 0, 0, 0};
        facility.has_ammo = false;
        facility.ammo = {0, 0};
        definitions_.emplace(facility.type, facility);

        if (!config_path.empty()) {
            std::string error;
            if (!load_definitions(config_path, &error)) {
                spdlog::warn("Unit definition load failed: {}", error);
            }
        }
    }

    const UnitDefinition* get_definition(UnitType type) const override {
        auto it = definitions_.find(type);
        if (it == definitions_.end()) return nullptr;
        return &it->second;
    }

    flecs::entity spawn(flecs::world& ecs,
                        const UnitDefinition& def,
                        const SpawnParams& params) override {
        double heading_init = 0.0;
        double h_speed_sq = params.vx * params.vx + params.vy * params.vy;
        if (h_speed_sq > 1e-12) {
            double math_deg = std::atan2(params.vy, params.vx) * 180.0 / M_PI;
            heading_init = default_factory_math_deg_to_nav_deg(math_deg);
        }

        auto e = ecs.entity()
            .set<Transform>({params.x, params.y, params.z, heading_init, 0, 0})
            .set<Velocity>({params.vx, params.vy, params.vz})
            .set<Alliance>({params.side})
            .set<KeyEntity>({def.type})
            .set<Health>({def.health.current_hp, def.health.max_hp});

        if (def.has_sensor) {
            e.set<Sensor>(def.sensor);
            e.set<ContactList>({});
        }
        if (def.has_score) {
            e.set<Score>(def.score);
        }
        if (def.has_ammo) {
            e.set<Ammo>(def.ammo);
        }
        if (def.has_flight_model) {
            e.set<FlightModel>(def.flight_model);
            double speed = std::sqrt(params.vx * params.vx +
                                     params.vy * params.vy +
                                     params.vz * params.vz);
            e.set<MovementCommand>({heading_init, speed, params.z, true});
            e.set<LaggedCommand>({heading_init, speed, params.z, true});
            e.set<ActionSpaceConfig>({
                def.flight_model.max_turn_rate,
                def.flight_model.max_accel,
                def.flight_model.max_climb_rate,
                def.flight_model.min_speed,
                def.flight_model.max_speed,
                0.0,
                20000.0
            });
            e.set<CommandLag>({0.5, 1.0, 1.5});
        }

        return e;
    }

    bool load_definitions(const std::string& path,
                          std::string* error) override {
        std::unordered_map<UnitType, UnitDefinition, UnitTypeHash> loaded;
        if (!load_unit_definitions_json(path, loaded, error)) {
            return false;
        }

        for (const auto& pair : loaded) {
            definitions_[pair.first] = pair.second;
        }
        return true;
    }

private:
    std::unordered_map<UnitType, UnitDefinition, UnitTypeHash> definitions_;
};
