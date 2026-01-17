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
