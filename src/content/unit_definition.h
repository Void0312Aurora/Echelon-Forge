#pragma once

#include <string>
#include <unordered_map>
#include <vector>

#include "components/basic/common.h"
#include "components/combat/health.h"
#include "components/command/command_link.h"
#include "components/physics/performance.h"
#include "components/combat/scoring.h"
#include "components/systems/sensor.h"
#include "components/combat/weapon.h"
#include "components/combat/damage.h"
#include "components/systems/ew.h"
#include "components/systems/sonar.h"
#include "components/naval/embarked_air_ops.h"
#include "components/naval/ship_platform.h"
#include "components/naval/submarine_platform.h"
#include "components/physics/flight_dynamics_tuning.h"



// Data Structs for Modules
struct Engine {
    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;
    double sfc_mil = 0.0;
    double sfc_ab = 0.0;
    double bypass_ratio = 0.0;
    bool has_tuning = false;
    EngineTuning tuning;
};

struct Hardpoint {
    int station_id;
    std::vector<std::string> supported_types; 
    double capacity_kg;
};

struct Airframe {
    double empty_mass_kg = 0.0;
    double max_fuel_kg = 0.0;
    double drag_coefficient = 0.02;
    double reference_area = 27.0;
    
    // Procedural Gen Data
    double length_m = 0.0;
    double wingspan_m = 0.0;
    double height_m = 0.0;
    std::string configuration = "Conventional"; // "Conventional", "Delta", "Flanker", "Bomber"
    bool has_tuning = false;
    AeroTuning tuning;
};

struct NavalStoresDefinition {
    double fuel_units_current{0.0};
    double fuel_units_max{0.0};
    double missile_units_current{0.0};
    double missile_units_max{0.0};
    double dry_cargo_units_current{0.0};
    double dry_cargo_units_max{0.0};
    bool can_receive_underway{false};
    bool can_provide_underway{false};
};

struct NavalLogisticsDefinition {
    bool underway_replenishment_enabled{false};
    double min_separation_m{0.0};
    double max_separation_m{0.0};
    double max_relative_speed_mps{0.0};
    double transfer_rate_fuel_units_per_s{0.0};
    double transfer_rate_missile_units_per_s{0.0};
    double transfer_rate_dry_cargo_units_per_s{0.0};
};

struct UnitDefinition {
    UnitType type;
    std::string name;
    
    // Component References (Modular)
    std::string sensor_ref;
    std::vector<std::string> sensor_refs;
    std::string engine_ref;
    std::string ew_suite_ref;
    std::string rcs_profile_ref;
    
    // Modular Data
    std::vector<Hardpoint> hardpoints;
    std::unordered_map<int, std::string> default_loadout;
    
    // Module Definitions (if type == Engine)
    Engine engine_data;
    
    // EW Data (if type == EWSuite)
    // We can reuse UnitDefinition as a generic container or add specific structs
    // For simplicity, let's keep them here for now
    // Actually, to keep it clean, let's add these to components/systems/ew.h and include here?
    // They are already included.
    // We need to store the *loaded data* in the definition map.
    // So if "Generic_EW" is loaded, it stores RWR/Jammer configs here.
    Jammer jammer_data;
    RWR rwr_data;
    bool has_esm_data = false;
    ESMReceiver esm_data;
    Countermeasures cms_data;
    
    // RCS Data
    RCSProfile rcs_data;
    
    // Platform Data
    Airframe airframe;
    bool has_ship_platform;
    ShipPlatform ship_platform;
    bool has_submarine_platform = false;
    SubmarinePlatform submarine_platform;
    bool has_naval_stores = false;
    NavalStoresDefinition naval_stores;
    bool has_naval_logistics = false;
    NavalLogisticsDefinition naval_logistics;
    bool has_naval_weapon_system = false;
    NavalWeaponSystem naval_weapon_system;
    bool has_embarked_air_ops = false;
    EmbarkedAirOps embarked_air_ops;
    HitboxConfig damage_model;
    
    // Legacy Inline Components (Backwards Compat)
    Health health;
    bool has_sensor;
    Sensor sensor;
    MountedSensors mounted_sensors;
    bool has_sonar = false;
    Sonar sonar;
    MountedSonars mounted_sonars;

    bool has_flight_model;
    FlightModel flight_model;

    bool has_landing_gear;
    LandingGear landing_gear;

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
    int data_link_max_reports_per_update = 16;
    int data_link_max_messages_per_update = -1;
};

struct UnitTypeHash {
    std::size_t operator()(UnitType type) const {
        return static_cast<std::size_t>(type);
    }
};
