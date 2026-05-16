#pragma once
#include <vector>
#include "components/basic/common.h" // For UnitType

struct FuelSystem {
    double internal_fuel_kg;    // Current Internal Fuel
    double max_internal_fuel_kg;// Capacity
    
    double external_fuel_kg;    // Current External Fuel
    double max_external_fuel_kg;// Capacity
    
    double current_flow_rate;   // kg/s
    bool afterburner_active;    // State flag
    
    // Config parameters
    double mil_power_flow_rate; // kg/s at 100% throttle
    double ab_flow_rate_multiplier; // Multiplier ~3-5x
};

struct MassProperties {
    double empty_mass_kg;       // Mirrored from Mass until a future single-authority migration
    double current_total_mass_kg; // Mirrored total-mass readout for aero/logistics consumers
    double base_drag_index;     // Clean config drag
    double current_drag_index;  // Calculated drag
    double reference_area_m2{0.0}; // Reference area for aero drag calculations
    
    // Aerodynamic References
    double wing_span_m{10.0};       // [NEW] Span b
    double chord_m{3.0};            // [NEW] Mean Aerodynamic Chord c_bar
};

struct WeaponStation {
    int station_id;
    bool is_occupied;
    UnitType weapon_type; // Simplified type enum
    double drag_index;
    double weight_kg;
};

struct Loadout {
    std::vector<WeaponStation> stations;
};

// Base / Tanker Component
struct LogisticsNode {
    double supply_radius_m;     // e.g. 500m for Base, 50m for Tanker
    bool infinite_supply;       
    // Could add fuel/ammo stocks here later
};

struct ResupplyState {
    double time_remaining_s;    // Implementation of "Turnaround Time"
    bool is_refueling;
    bool is_rearming;
};

// Ground Contact State
struct GroundState {
    bool on_ground;
    double terrain_elevation;
    double surface_friction{0.6}; // Default friction
};
