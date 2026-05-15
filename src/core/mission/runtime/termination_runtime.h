#pragma once

#include <string>

enum class TerminationReasonCode {
    Running = 0,
    NanGuard,
    CrashHealth,
    FailfastDeepStall,
    FailfastInvertedLowAlt,
    FailfastExtremePitch,
    GearCollapse,
    OffRunwayTerminate,
    SuccessWaypoint,
    SuccessObjective,
    Success,
    FailureUnknown,
    TerminatedUnknown,
    Timeout,
};

struct SafetyRuntimeInputs {
    bool finite_state_valid = true;
    double crash_penalty = -1000.0;
    double survival_reward = 0.01;
    double health = 100.0;

    bool airborne = false;
    bool aoa_valid = false;
    double aoa_abs_deg = 0.0;
    double stall_threshold_deg = 15.0;
    double stall_penalty_weight = -1.0;
    double stall_penalty_clip = 0.0;

    double g_abs = 1.0;
    double overload_g_threshold = 6.0;
    double overload_penalty_weight = -1.0;
    double overload_penalty_clip = 0.0;
    double curr_alt_agl_m = 0.0;
    double overload_min_alt_agl_m = 5.0;

    double altitude_m = 0.0;
    double roll_abs_deg = 0.0;
    double pitch_abs_deg = 0.0;
    double failfast_penalty = -50.0;

    bool gear_collapsed = false;
    double gear_collapse_penalty = -500.0;

    bool runway_surface_phase = false;
    bool on_runway_task = true;
    double gear_stress = 0.0;
    double gear_stress_penalty_weight = -10.0;
    double off_runway_penalty = -1.0;
    double speed_mps = 0.0;
    int off_runway_steps = 0;
    double off_runway_terminate_speed = 0.0;
    double off_runway_terminate_grace_s = 0.0;
    double time_step_s = 0.05;
    double off_runway_terminate_penalty = -200.0;
};

struct SafetyRuntimeProducts {
    bool valid = false;
    bool early_return = false;
    bool terminated = false;
    double status_flag = 0.0;
    TerminationReasonCode reason_code = TerminationReasonCode::Running;

    double survival = 0.0;
    double crash_penalty = 0.0;
    double nan_guard_marker = 0.0;
    double stall_penalty = 0.0;
    double overload_penalty = 0.0;
    double failfast_penalty = 0.0;
    double gear_collapse_penalty = 0.0;
    double off_runway_penalty = 0.0;
    double gear_stress_penalty = 0.0;
    double off_runway_terminate_penalty = 0.0;
};

SafetyRuntimeProducts compute_safety_runtime(const SafetyRuntimeInputs& inputs);
TerminationReasonCode finalize_termination_reason(
    TerminationReasonCode current_reason,
    bool terminated,
    bool truncated,
    double status_flag
);
std::string termination_reason_name(TerminationReasonCode reason);
