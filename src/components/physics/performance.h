#pragma once

struct FlightModel {
    double max_speed;       // m/s
    double min_speed;       // m/s (Stall speed)
    double max_turn_rate;   // deg/s
    double max_accel;       // m/s^2
    double max_climb_rate;  // m/s
    double max_g;           // Max Load Factor (9.0)
    double min_g;           // Min Load Factor (-3.0)
    // Ground Ops
    double takeoff_speed;   // m/s (Rotation speed)
    double landing_speed;   // m/s (Touchdown speed limit)
    double taxi_turn_rate;  // deg/s (Max turn rate on ground)
};

struct LandingGear {
    bool can_use_unpaved = false;         // Helper/Transport aircraft feature
    double rolling_friction_coeff = 0.02; // Default for concrete
    double max_load_factor = 3.0;         // G-limit before collapse
    double contact_height_m = 2.0;        // Gear contact reference height from CG to wheel contact (extended)
    
    // Dynamic State
    double extension_state = 1.0;         // 0.0=Retracted, 1.0=Extended
    bool is_jammed = false;               // Failure state
    double transit_time_s = 5.0;          // Time to extend/retract
};
