#pragma once
#include <vector>
#include "components/basic/common.h" // For UnitType

struct FuelSystem {
    double internal_fuel_kg;     // Current Internal Fuel
    double max_internal_fuel_kg; // Capacity

    double external_fuel_kg;     // Current External Fuel
    double max_external_fuel_kg; // Capacity

    double current_flow_rate; // kg/s
    bool afterburner_active;  // State flag

    // Config parameters
    double mil_power_flow_rate;     // kg/s at 100% throttle
    double ab_flow_rate_multiplier; // Multiplier ~3-5x
};

struct MassProperties {
    double empty_mass_kg;          // Mirrored from Mass until a future single-authority migration
    double current_total_mass_kg;  // Mirrored total-mass readout for aero/logistics consumers
    double base_drag_index;        // Clean config drag
    double current_drag_index;     // Calculated drag
    double reference_area_m2{0.0}; // Reference area for aero drag calculations

    // Aerodynamic References
    double wing_span_m{10.0}; // [NEW] Span b
    double chord_m{3.0};      // [NEW] Mean Aerodynamic Chord c_bar
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
    double supply_radius_m; // e.g. 500m for Base, 50m for Tanker
    bool infinite_supply;
    bool underway_replenishment_enabled{false};
    double underway_min_separation_m{0.0};
    double underway_max_separation_m{0.0};
    double underway_max_relative_speed_mps{0.0};
    double transfer_rate_fuel_units_per_s{0.0};
    double transfer_rate_missile_units_per_s{0.0};
    double transfer_rate_dry_cargo_units_per_s{0.0};
};

struct NavalStores {
    double fuel_units_current{0.0};
    double fuel_units_max{0.0};
    double missile_units_current{0.0};
    double missile_units_max{0.0};
    double dry_cargo_units_current{0.0};
    double dry_cargo_units_max{0.0};
    bool can_receive_underway{false};
    bool can_provide_underway{false};
};

enum class ResupplyKind {
    BaseRefuel = 0,
    NavalUnderway = 1,
};

enum class NavalResupplyStage {
    None = 0,
    ApproachWindow = 1,
    Connected = 2,
    Transferring = 3,
    Complete = 4,
    Aborted = 5,
};

struct ResupplyState {
    double time_remaining_s; // Implementation of "Turnaround Time"
    bool is_refueling;
    bool is_rearming;
    ResupplyKind kind{ResupplyKind::BaseRefuel};
    uint64_t partner_entity_id{0};
    NavalResupplyStage naval_stage{NavalResupplyStage::None};
};

enum class GroundImpactLifecycle : int {
    None = 0,
    LandedAirframe = 1,
    CrashedWreck = 2,
    DebrisFragmentResidue = 3,
};

// Ground Contact State
struct GroundState {
    bool on_ground;
    double terrain_elevation;
    double surface_friction{0.6}; // Default friction
    GroundImpactLifecycle lifecycle{GroundImpactLifecycle::None};
    double impact_horizontal_speed_mps{0.0};
    double impact_sink_rate_mps{0.0};
    double impact_severity{0.0};
};
