#pragma once

struct Mass {
    double empty_mass_kg;
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
    double current_thrust_n;
    bool afterburner_active;
};

// Landing Gear State (for damage modeling)
struct GearState {
    bool gear_down = true;       // Physical position (controls drag/ground contact)
    double stress = 0.0;         // Accumulated stress (0.0-1.0), collapse at 1.0
    bool collapsed = false;      // Has the gear failed?
    double stress_rate = 0.0;    // Current stress accumulation rate (for observation)
    bool on_runway = true;       // Is aircraft currently on paved surface?
};
