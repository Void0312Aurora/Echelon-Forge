#pragma once

struct ShipPlatform {
    double displacement_light_kg = 0.0;
    double displacement_full_load_kg = 0.0;
    double length_m = 0.0;
    double beam_m = 0.0;
    double draft_m = 0.0;
    double height_above_waterline_m = 0.0;
    double max_speed_mps = 0.0;
    double economical_speed_mps = 0.0;
    double range_nm = 0.0;
    double range_speed_mps = 0.0;
    // Surge and steering law: components/domains/naval/platform/ship_maneuvering.h.
    // Full-ahead acceleration from rest; with quadratic resistance it also fixes
    // the resistance coefficient a / U_max^2.
    double max_accel_mps2 = 0.12;
    // Full-astern (backing) deceleration authority, added to resistance.
    double max_decel_mps2 = 0.18;
    // Steady full-rudder turning diameter. 0 declares no rudder authority.
    double steady_turning_diameter_m = 0.0;
    // Non-dimensional Nomoto yaw time constant T' (T = T' L / U).
    double nomoto_time_constant = 1.0;
    // Speed in a steady full-rudder turn as a fraction of the approach speed at
    // an unchanged engine order. 1 declares no turn speed loss.
    double steady_turn_speed_ratio = 1.0;
    double steerageway_speed_mps = 0.5;
    double sea_state = 0.0;
    double wave_heading_deg = 0.0;
    double wave_period_s = 8.0;
    double max_roll_deg_sea_state_6 = 8.0;
    double max_pitch_deg_sea_state_6 = 3.0;
    double added_resistance_fraction_sea_state_6 = 0.12;
    int crew = 0;
};
