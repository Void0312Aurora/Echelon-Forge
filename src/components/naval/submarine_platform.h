#pragma once

struct SubmarinePlatform {
    double submerged_displacement_kg = 0.0;
    double length_m = 0.0;
    double beam_m = 0.0;
    double draft_m = 0.0;
    double max_speed_submerged_mps = 0.0;
    double quiet_speed_mps = 0.0;
    double max_accel_mps2 = 0.05;
    double max_decel_mps2 = 0.08;
    double max_turn_rate_deg_s = 1.5;
    double max_depth_rate_mps = 3.0;
    double nominal_patrol_depth_m = 60.0;
    double max_operating_depth_m = 300.0;
    double acoustic_stealth_bias_db = 0.0;
    double self_noise_per_speed_db = 1.2;
    int crew = 0;
};
