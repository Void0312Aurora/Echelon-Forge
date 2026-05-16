#pragma once

#include <cstdint>
#include <string>
#include <vector>

enum class SonarMode {
    Passive = 0,
    Active = 1
};

struct Sonar {
    double max_range_m = 0.0;
    double scan_period_s = 5.0;
    double last_scan_time_s = -1.0;
    double detection_threshold_db = 6.0;
    double track_memory_s = 20.0;
    double bearing_noise_std_deg = 3.0;
    double range_noise_std_m = 800.0;
    double directivity_gain_db = 0.0;
    double self_noise_per_speed_db = 1.2;
    double ambient_noise_db = 72.0;
    double source_level_reference_db = 118.0;
    double source_level_speed_factor_db = 1.6;
    double transmission_loss_alpha_db_per_km = 0.08;
    double layer_break_penalty_db = 4.0;
    double convergence_zone_bonus_m = 0.0;
    double baffle_exclusion_deg = 40.0;
    double ownship_quieting_speed_mps = 5.0;
    double active_ping_source_level_db = 210.0;
    int confirm_hits_m = 2;
    int confirm_window_n = 3;
    int mode = static_cast<int>(SonarMode::Passive);
    bool passive_only = true;
    bool bearing_only = false;
};

struct SonarMount {
    Sonar sonar{};
    std::string label{};
};

struct MountedSonars {
    std::vector<SonarMount> mounts{};
};
