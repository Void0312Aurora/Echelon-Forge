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

    // --- Control surface effectiveness ---
    // Maximum physical deflection per axis (degrees) used to map the normalized
    // surface position [-1, 1] onto a real deflection angle.
    double elevator_max_deflection_deg = 25.0;
    double aileron_max_deflection_deg = 21.5;
    double rudder_max_deflection_deg = 30.0;

    // Control-effectiveness derivatives (per radian of physical deflection).
    // Sign conventions match ControlSurfaceState:
    //   cm_delta_e > 0: positive elevator -> nose-up pitching moment.
    //   cl_delta_a > 0: positive aileron  -> right rolling moment.
    //   cn_delta_r > 0: positive rudder   -> positive (sim) yawing moment.
    // F-16-magnitude defaults: the all-moving stabilator is powerful, so
    // cm_delta_e is large enough to preserve takeoff rotation authority at
    // takeoff dynamic pressure. Roll/yaw effectiveness is sized to give
    // realistic (not over-powered) rates relative to the old direct rate-torque.
    double cm_delta_e_per_rad = 1.2;
    double cl_delta_a_per_rad = 0.10;
    double cn_delta_r_per_rad = 0.13;

    // FBW proportional gain mapping a body-rate error (rad/s) onto a normalized
    // surface command. Sized so that moderate rate errors approach full surface
    // travel, preserving the rate-command feel of the prior FBW while routing it
    // through a physical, q-bar/Mach-scaled surface.
    double fbw_elevator_cmd_per_rate_err = 3.0;
    double fbw_aileron_cmd_per_rate_err = 2.0;
    double fbw_rudder_cmd_per_rate_err = 2.5;

    // Aileron-rudder interconnect (ARI). Feeds the aileron command forward into
    // the rudder command to trim out the transient sideslip peak during a roll
    // onset, instead of relying solely on reactive sideslip damping (which must
    // wait for beta to build and is delayed by rudder actuator lag).
    //
    // Sign (re-verified empirically against the physical control-surface path,
    // 2026-06-20): in a sustained right roll the reactive beta damper alone
    // drives a small POSITIVE rudder_pos and beta converges to a small steady
    // value. The previous negative gain (-0.55) forced rudder the opposite way,
    // fighting the damper and driving a monotonic sideslip divergence (beta to
    // ~10 deg and departure) once the rudder actuator lag was modeled. The ARI
    // must therefore add rudder in the SAME direction the beta damper wants for
    // a given aileron command, i.e. a positive gain. It is a transient-peak
    // trim, not a stability requirement: a bisection with gain=0 already keeps
    // beta bounded, so the magnitude is kept small to shave the onset peak
    // without over-yawing.
    double ari_rudder_cmd_per_aileron_cmd = 0.25;

    // Pitch-axis g-command FBW (F-16-style normal-acceleration command).
    // Center stick commands 1 g (level, sustained flight); full aft stick
    // commands fbw_g_command_max. The outer loop converts the (commanded g -
    // measured Nz) error into a pitch-rate command for the inner rate loop, so
    // a neutral stick physically holds 1 g instead of merely damping pitch rate
    // (which cannot sustain level flight on the physical-surface path). Uses
    // only the sensor-like normal load factor (InstrumentState.g_load_normal),
    // never god state.
    bool fbw_g_command_enabled = true;
    double fbw_g_command_neutral = 1.0;   // g held at center stick
    double fbw_g_command_max = 8.0;        // g at full aft stick
    double fbw_g_command_min = -2.0;       // g at full forward stick
    double fbw_pitch_rate_per_g_err = 0.30; // (rad/s) pitch-rate cmd per g of error

    // Control effectiveness fades at high Mach (transonic/supersonic loss of
    // surface authority). Scaled against mach_breakpoints when provided.
    std::vector<double> control_effectiveness_scale_vs_mach;

    // Actuator first-order time constants (seconds). Surface positions chase the
    // commanded value with these lags so control inputs are gradual, not
    // instantaneous, and so high-frequency command noise cannot inject
    // unrealistic torque spikes.
    double actuator_tau_elevator_s = 0.10;
    double actuator_tau_aileron_s = 0.08;
    double actuator_tau_rudder_s = 0.12;

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
        value.control_effectiveness_scale_vs_mach = {1.00, 1.00, 0.92, 0.78, 0.68, 0.60};
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
