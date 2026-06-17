#pragma once

#include <vector>

struct AeroTuning {
    bool enabled = false;

    double cl_alpha_per_deg = 0.1;
    double cl0 = 0.0;
    double cd0_clean = 0.02;
    double induced_drag_k = 0.1;
    double cm_alpha_per_rad = -0.8;
    double cm_q = -12.0;

    double alpha_stall_clean_deg = 15.0;
    double alpha_stall_flaps_full_deg = 21.0;
    double alpha_peak_offset_deg = 8.0;
    double alpha_deep_offset_deg = 18.0;

    double cl_peak_clean = 1.25;
    double cl_peak_flaps_full = 1.70;
    double cl_deep_clean = 0.22;
    double cl_deep_flaps_full = 0.32;

    double pitch_break_onset_deg = 16.0;
    double pitch_break_full_deg = 28.0;
    double pitch_break_cm_nose_down = -0.35;
    double post_stall_damp_floor = 0.25;
    double aoa_rate_pitch_break_gain = 0.0035;

    std::vector<double> mach_breakpoints;
    std::vector<double> cl_alpha_scale_vs_mach;
    std::vector<double> cd0_add_vs_mach;
    std::vector<double> induced_drag_scale_vs_mach;
    std::vector<double> cm_alpha_scale_vs_mach;
    std::vector<double> stall_alpha_delta_deg_vs_mach;
};

struct EngineTuning {
    bool enabled = false;

    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;

    double throttle_ab_threshold = 0.9;
    double throttle_idle_bias = 0.08;

    double tau_spool_up_s = 2.5;
    double tau_spool_down_s = 1.5;
    double tau_ab_light_s = 1.0;
    double tau_ab_extinguish_s = 0.5;

    double ram_rise_gain = 0.3;
    double ram_rise_mach_cap = 1.2;
    double ram_decay_start_mach = 1.5;
    double ram_decay_gain = 0.2;

    double thrust_sigma_exponent = 1.0;
    double thrust_theta_exponent = 0.0;

    double tsfc_mil_kg_per_nh = 0.10;
    double tsfc_ab_kg_per_nh = 0.25;
};

struct StallState {
    double stall_progress = 0.0;
    double time_in_stall_s = 0.0;
    bool is_stalled = false;
    bool pitch_break_active = false;
};

namespace flight_dynamics {
inline const AeroTuning &default_aero_tuning() {
    static const AeroTuning tuning = [] {
        AeroTuning value;
        value.enabled = true;
        value.mach_breakpoints = {0.0, 0.8, 0.95, 1.1, 1.6, 2.0};
        value.cl_alpha_scale_vs_mach = {1.00, 1.04, 1.10, 0.96, 0.82, 0.72};
        value.cd0_add_vs_mach = {0.00, 0.005, 0.025, 0.040, 0.030, 0.025};
        value.induced_drag_scale_vs_mach = {1.00, 1.00, 1.05, 1.12, 1.05, 1.00};
        value.cm_alpha_scale_vs_mach = {1.00, 1.00, 0.96, 0.92, 0.86, 0.82};
        value.stall_alpha_delta_deg_vs_mach = {0.0, -0.5, -1.5, -2.5, -3.0, -3.0};
        return value;
    }();
    return tuning;
}

inline const EngineTuning &default_engine_tuning() {
    static const EngineTuning tuning = [] {
        EngineTuning value;
        value.enabled = true;
        return value;
    }();
    return tuning;
}
} // namespace flight_dynamics
