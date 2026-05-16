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
    double max_accel_mps2 = 0.12;
    double max_decel_mps2 = 0.18;
    double max_turn_rate_deg_s = 2.0;
    double low_speed_turn_factor = 0.25;
    double steerageway_speed_mps = 0.5;
    double sea_state = 0.0;
    double wave_heading_deg = 0.0;
    double wave_period_s = 8.0;
    double max_roll_deg_sea_state_6 = 8.0;
    double max_pitch_deg_sea_state_6 = 3.0;
    double added_resistance_fraction_sea_state_6 = 0.12;
    int crew = 0;
};
