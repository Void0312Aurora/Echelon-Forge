// X-macro list of SafetyRuntimeInputs fields.
//
// Consumers define EF_SAFETY_INPUT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.
// Expansion sites: struct definition (termination_runtime.h) and
// SafetyRuntimeInputs Python bindings (bindings_episode.cpp).
//
// Field order is load-bearing: it fixes the member layout of the struct.

EF_SAFETY_INPUT(bool, finite_state_valid, true)
EF_SAFETY_INPUT(double, crash_penalty, -1000.0)
EF_SAFETY_INPUT(double, survival_reward, 0.01)
EF_SAFETY_INPUT(double, health, 100.0)
EF_SAFETY_INPUT(bool, airborne, false)
EF_SAFETY_INPUT(bool, aoa_valid, false)
EF_SAFETY_INPUT(double, aoa_abs_deg, 0.0)
EF_SAFETY_INPUT(double, stall_threshold_deg, 15.0)
EF_SAFETY_INPUT(double, stall_penalty_weight, -1.0)
EF_SAFETY_INPUT(double, stall_penalty_clip, 0.0)
EF_SAFETY_INPUT(double, g_abs, 1.0)
EF_SAFETY_INPUT(double, overload_g_threshold, 6.0)
EF_SAFETY_INPUT(double, overload_penalty_weight, -1.0)
EF_SAFETY_INPUT(double, overload_penalty_clip, 0.0)
EF_SAFETY_INPUT(double, curr_alt_agl_m, 0.0)
EF_SAFETY_INPUT(double, overload_min_alt_agl_m, 5.0)
EF_SAFETY_INPUT(double, altitude_m, 0.0)
EF_SAFETY_INPUT(double, roll_abs_deg, 0.0)
EF_SAFETY_INPUT(double, pitch_abs_deg, 0.0)
EF_SAFETY_INPUT(double, failfast_penalty, -50.0)
EF_SAFETY_INPUT(bool, gear_collapsed, false)
EF_SAFETY_INPUT(double, gear_collapse_penalty, -500.0)
EF_SAFETY_INPUT(bool, runway_surface_phase, false)
EF_SAFETY_INPUT(bool, on_runway_task, true)
EF_SAFETY_INPUT(double, gear_stress, 0.0)
EF_SAFETY_INPUT(double, gear_stress_penalty_weight, -10.0)
EF_SAFETY_INPUT(double, off_runway_penalty, -1.0)
EF_SAFETY_INPUT(double, speed_mps, 0.0)
EF_SAFETY_INPUT(int, off_runway_steps, 0)
EF_SAFETY_INPUT(double, off_runway_terminate_speed, 0.0)
EF_SAFETY_INPUT(double, off_runway_terminate_grace_s, 0.0)
EF_SAFETY_INPUT(double, time_step_s, 0.05)
EF_SAFETY_INPUT(double, off_runway_terminate_penalty, -200.0)

#undef EF_SAFETY_INPUT
