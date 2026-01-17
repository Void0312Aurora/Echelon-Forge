#pragma once

#include <string>
#include <unordered_map>
#include <vector>

#include "components/basic/common.h"
#include "components/combat/health.h"
#include "components/physics/action.h"
#include "components/physics/performance.h"
#include "components/combat/scoring.h"
#include "components/systems/sensor.h"
#include "components/combat/weapon.h"
#include "components/combat/damage.h"



// Data Structs for Modules
struct Engine {
    double mil_thrust_n;
    double ab_thrust_n;
    double sfc_mil;
    double sfc_ab;
    double bypass_ratio;
};

struct Hardpoint {
    int station_id;
    std::vector<std::string> supported_types; 
    double capacity_kg;
};

struct Airframe {
    double empty_mass_kg;
    double max_fuel_kg;
    double drag_coefficient;
    double reference_area;
    
    // Procedural Gen Data
    double length_m;
    double wingspan_m;
    double height_m;
    std::string configuration; // "Conventional", "Delta", "Flanker", "Bomber"
};

struct UnitDefinition {
    UnitType type;
    std::string name;
    
    // Component References (Modular)
    std::string sensor_ref;
    std::string engine_ref;
    
    // Modular Data
    std::vector<Hardpoint> hardpoints;
    std::unordered_map<int, std::string> default_loadout;
    
    // Module Definitions (if type == Engine)
    Engine engine_data;
    
    // Platform Data
    Airframe airframe;
    HitboxConfig damage_model;
    
    // Legacy Inline Components (Backwards Compat)
    Health health;
    bool has_sensor;
    Sensor sensor;

    bool has_flight_model;
    FlightModel flight_model;

    bool has_score;
    Score score;

    // Generic Data
    double mass_kg; // For missiles/bombs, or components

    bool has_ammo;
    Ammo ammo;

    bool has_command_link;
    CommandLink command_link;

    bool has_data_link;
    int data_link_network_id;
};

struct UnitTypeHash {
    std::size_t operator()(UnitType type) const {
        return static_cast<std::size_t>(type);
    }
};
