#include "core/mission/termination_runtime.h"

#include <algorithm>
#include <cmath>

namespace {

double clamp_value(double value, double lo, double hi) {
    return std::min(std::max(value, lo), hi);
}

}  // namespace

SafetyRuntimeProducts compute_safety_runtime(const SafetyRuntimeInputs& inputs) {
    SafetyRuntimeProducts out{};
    out.valid = true;

    if (!inputs.finite_state_valid) {
        out.early_return = true;
        out.terminated = true;
        out.status_flag = -1.0;
        out.reason_code = TerminationReasonCode::NanGuard;
        out.crash_penalty = inputs.crash_penalty;
        out.nan_guard_marker = 1.0;
        return out;
    }

    if (inputs.health <= 0.0) {
        out.terminated = true;
        out.status_flag = -1.0;
        out.reason_code = TerminationReasonCode::CrashHealth;
        out.crash_penalty = inputs.crash_penalty;
        return out;
    }

    out.survival = inputs.survival_reward;

    if (inputs.airborne && inputs.aoa_valid && inputs.aoa_abs_deg > inputs.stall_threshold_deg) {
        double stall_term = inputs.stall_penalty_weight * (inputs.aoa_abs_deg - inputs.stall_threshold_deg);
        if (inputs.stall_penalty_clip > 0.0 && stall_term < -inputs.stall_penalty_clip) {
            stall_term = -inputs.stall_penalty_clip;
        }
        out.stall_penalty = stall_term;
    }

    if (
        inputs.airborne
        && inputs.curr_alt_agl_m > inputs.overload_min_alt_agl_m
        && inputs.g_abs > inputs.overload_g_threshold
    ) {
        double overload_term = inputs.overload_penalty_weight * (inputs.g_abs - inputs.overload_g_threshold);
        if (inputs.overload_penalty_clip > 0.0 && overload_term < -inputs.overload_penalty_clip) {
            overload_term = -inputs.overload_penalty_clip;
        }
        out.overload_penalty = overload_term;
    }

    if (inputs.airborne && inputs.aoa_valid && inputs.aoa_abs_deg > 50.0) {
        out.failfast_penalty = inputs.failfast_penalty;
        out.terminated = true;
        out.status_flag = -1.0;
        out.reason_code = TerminationReasonCode::FailfastDeepStall;
    } else if (inputs.airborne && inputs.altitude_m < 100.0 && inputs.roll_abs_deg > 135.0) {
        out.failfast_penalty = inputs.failfast_penalty;
        out.terminated = true;
        out.status_flag = -1.0;
        out.reason_code = TerminationReasonCode::FailfastInvertedLowAlt;
    } else if (inputs.airborne && inputs.pitch_abs_deg > 85.0) {
        out.failfast_penalty = inputs.failfast_penalty;
        out.terminated = true;
        out.status_flag = -1.0;
        out.reason_code = TerminationReasonCode::FailfastExtremePitch;
    }

    if (inputs.gear_collapsed) {
        out.gear_collapse_penalty = inputs.gear_collapse_penalty;
        out.terminated = true;
        out.status_flag = -1.0;
        out.reason_code = TerminationReasonCode::GearCollapse;
    } else if (inputs.runway_surface_phase && (!inputs.on_runway_task)) {
        out.off_runway_penalty = inputs.off_runway_penalty;
        if (inputs.gear_stress > 0.1) {
            out.gear_stress_penalty = inputs.gear_stress * inputs.gear_stress_penalty_weight;
        }
        if (inputs.off_runway_terminate_speed > 0.0 && inputs.speed_mps >= inputs.off_runway_terminate_speed) {
            const double dt = inputs.time_step_s > 1.0e-6 ? inputs.time_step_s : 0.05;
            const int grace_steps = static_cast<int>(std::max(0.0, inputs.off_runway_terminate_grace_s) / dt);
            if (inputs.off_runway_steps > grace_steps) {
                out.off_runway_terminate_penalty = inputs.off_runway_terminate_penalty;
                out.terminated = true;
                out.status_flag = -1.0;
                out.reason_code = TerminationReasonCode::OffRunwayTerminate;
            }
        }
    }

    return out;
}

TerminationReasonCode finalize_termination_reason(
    TerminationReasonCode current_reason,
    bool terminated,
    bool truncated,
    double status_flag
) {
    if (terminated) {
        if (current_reason == TerminationReasonCode::Running) {
            if (status_flag > 0.5) {
                return TerminationReasonCode::Success;
            }
            if (status_flag < -0.5) {
                return TerminationReasonCode::FailureUnknown;
            }
            return TerminationReasonCode::TerminatedUnknown;
        }
        return current_reason;
    }
    if (truncated) {
        return TerminationReasonCode::Timeout;
    }
    return TerminationReasonCode::Running;
}

std::string termination_reason_name(TerminationReasonCode reason) {
    switch (reason) {
        case TerminationReasonCode::Running:
            return "running";
        case TerminationReasonCode::NanGuard:
            return "nan_guard";
        case TerminationReasonCode::CrashHealth:
            return "crash_health";
        case TerminationReasonCode::FailfastDeepStall:
            return "failfast_deep_stall";
        case TerminationReasonCode::FailfastInvertedLowAlt:
            return "failfast_inverted_low_alt";
        case TerminationReasonCode::FailfastExtremePitch:
            return "failfast_extreme_pitch";
        case TerminationReasonCode::GearCollapse:
            return "gear_collapse";
        case TerminationReasonCode::OffRunwayTerminate:
            return "off_runway_terminate";
        case TerminationReasonCode::SuccessWaypoint:
            return "success_waypoint";
        case TerminationReasonCode::SuccessObjective:
            return "success_objective";
        case TerminationReasonCode::Success:
            return "success";
        case TerminationReasonCode::FailureUnknown:
            return "failure_unknown";
        case TerminationReasonCode::TerminatedUnknown:
            return "terminated_unknown";
        case TerminationReasonCode::Timeout:
            return "timeout";
        default:
            return "running";
    }
}
