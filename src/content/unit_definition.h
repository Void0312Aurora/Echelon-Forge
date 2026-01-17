#pragma once

#include <string>
#include <unordered_map>

#include "components/common.h"
#include "components/health.h"
#include "components/action.h"
#include "components/performance.h"
#include "components/scoring.h"
#include "components/sensor.h"
#include "components/weapon.h"

struct UnitDefinition {
    UnitType type;
    std::string name;

    Health health;
    bool has_sensor;
    Sensor sensor;

    bool has_flight_model;
    FlightModel flight_model;

    bool has_score;
    Score score;

    bool has_ammo;
    Ammo ammo;

    bool has_command_link;
    CommandLink command_link;
};

struct UnitTypeHash {
    std::size_t operator()(UnitType type) const {
        return static_cast<std::size_t>(type);
    }
};
