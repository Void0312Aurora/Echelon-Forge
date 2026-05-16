#pragma once

struct Mass {
    double empty_mass_kg;   // Runtime mass authority for physics-side mass decomposition
    double fuel_mass_kg;
    double stores_mass_kg;
    double fuel_leak_rate_kg_s{0.0};

    double get_total_kg() const {
        return empty_mass_kg + fuel_mass_kg + stores_mass_kg;
    }
};

struct Propulsion {
    double mil_thrust_n;
    double ab_thrust_n;
    
    // State
    double current_thrust_n = 0.0;
    bool afterburner_active = false;

    double throttle_command = 0.0;
    double throttle_state = 0.0;
    double dry_thrust_command_n = 0.0;
    double dry_thrust_state_n = 0.0;
    double ab_command = 0.0;
    double ab_state = 0.0;
    double current_tsfc = 0.10;
};

// Landing Gear State (for damage modeling)
struct GearState {
    bool gear_down = true;       // Physical position (controls drag/ground contact)
    double stress = 0.0;         // Accumulated stress (0.0-1.0), collapse at 1.0
    bool collapsed = false;      // Has the gear failed?
    double stress_rate = 0.0;    // Current stress accumulation rate (for observation)
    bool on_runway = true;       // Is aircraft currently on paved surface?
};
