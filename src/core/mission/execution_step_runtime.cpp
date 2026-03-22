#include "core/mission/execution_step_runtime.h"

#include <cmath>

namespace {

void add_reward_term(double value, double* total) {
    if (total == nullptr) {
        return;
    }
    *total += value;
}

}  // namespace

ExecutionStepRuntimeProducts compute_execution_step_runtime(const ExecutionStepRuntimeInputs& inputs) {
    ExecutionStepRuntimeProducts out{};
    out.valid = true;

    out.safety = compute_safety_runtime(inputs.safety);
    if (out.safety.crash_penalty != 0.0) {
        add_reward_term(out.safety.crash_penalty, &out.compiled_reward_total);
        out.terminated = true;
        out.status3 = out.safety.status_flag;
        out.reason_code = out.safety.reason_code;
        out.final_reason_code = finalize_termination_reason(
            out.reason_code,
            out.terminated,
            inputs.truncated,
            out.status3
        );
        return out;
    }

    add_reward_term(out.safety.survival, &out.compiled_reward_total);

    if (out.safety.stall_penalty != 0.0) {
        add_reward_term(out.safety.stall_penalty, &out.compiled_reward_total);
    }
    if (out.safety.overload_penalty != 0.0) {
        add_reward_term(out.safety.overload_penalty, &out.compiled_reward_total);
    }
    if (out.safety.failfast_penalty != 0.0) {
        add_reward_term(out.safety.failfast_penalty, &out.compiled_reward_total);
        out.terminated = true;
        out.status3 = out.safety.status_flag;
        out.reason_code = out.safety.reason_code;
    }
    if (out.safety.gear_collapse_penalty != 0.0) {
        add_reward_term(out.safety.gear_collapse_penalty, &out.compiled_reward_total);
        out.terminated = true;
        out.status3 = out.safety.status_flag;
        out.reason_code = out.safety.reason_code;
    }
    if (out.safety.off_runway_penalty != 0.0) {
        add_reward_term(out.safety.off_runway_penalty, &out.compiled_reward_total);
    }
    if (out.safety.gear_stress_penalty != 0.0) {
        add_reward_term(out.safety.gear_stress_penalty, &out.compiled_reward_total);
    }
    if (out.safety.off_runway_terminate_penalty != 0.0) {
        add_reward_term(out.safety.off_runway_terminate_penalty, &out.compiled_reward_total);
        out.terminated = true;
        out.status3 = out.safety.status_flag;
        out.reason_code = out.safety.reason_code;
    }

    if (inputs.has_approach) {
        out.approach_evaluated = true;
        out.approach = compute_approach_reward_terms(inputs.approach);
        add_reward_term(out.approach.approach_localizer, &out.compiled_reward_total);
        add_reward_term(out.approach.approach_localizer_improve, &out.compiled_reward_total);
        add_reward_term(out.approach.approach_glideslope, &out.compiled_reward_total);
        add_reward_term(out.approach.approach_glideslope_improve, &out.compiled_reward_total);
        add_reward_term(out.approach.approach_dme_progress, &out.compiled_reward_total);
        add_reward_term(out.approach.approach_capture_bonus, &out.compiled_reward_total);
        add_reward_term(out.approach.landing_sink_rate_penalty, &out.compiled_reward_total);
    }

    if (!out.terminated && inputs.has_waypoint) {
        out.waypoint_evaluated = true;
        out.waypoint = compute_waypoint_reward_terms(inputs.waypoint);
        add_reward_term(out.waypoint.waypoint_progress, &out.compiled_reward_total);
        add_reward_term(out.waypoint.waypoint_distance, &out.compiled_reward_total);
        add_reward_term(out.waypoint.waypoint_cross_track, &out.compiled_reward_total);
        add_reward_term(out.waypoint.waypoint_proximity, &out.compiled_reward_total);
        add_reward_term(out.waypoint.waypoint_reached_bonus, &out.compiled_reward_total);
        if (out.waypoint.arrived && inputs.waypoint_episode_success) {
            out.waypoint_episode_success = true;
            out.waypoint_episode_success_bonus = inputs.waypoint_episode_success_bonus;
            add_reward_term(out.waypoint_episode_success_bonus, &out.compiled_reward_total);
            out.terminated = true;
            out.status3 = 1.0;
            out.reason_code = TerminationReasonCode::SuccessWaypoint;
        }
    }

    if (!out.terminated && inputs.has_objectives) {
        out.objective_evaluated = true;
        for (size_t idx = 0; idx < inputs.objectives.size(); ++idx) {
            ConditionalObjectiveProducts products = evaluate_conditional_objective(
                inputs.objectives[idx],
                inputs.objective_inputs,
                inputs.objective_shaping
            );
            out.objective_status_count = products.status_count;
            if (products.status_count >= 1) {
                out.status0 = products.status0;
            }
            if (products.status_count >= 2) {
                out.status1 = products.status1;
            }
            if (products.status_count >= 3) {
                out.status2 = products.status2;
            }
            if (!products.matched) {
                continue;
            }
            out.objective = products;
            out.matched_objective_index = static_cast<int>(idx);
            add_reward_term(out.objective.success_runway_cross_penalty, &out.compiled_reward_total);
            add_reward_term(out.objective.success_ground_track_error_penalty, &out.compiled_reward_total);
            add_reward_term(out.objective.objective_bonus, &out.compiled_reward_total);
            out.terminated = true;
            out.status3 = 1.0;
            out.reason_code = TerminationReasonCode::SuccessObjective;
            break;
        }
    }

    out.final_reason_code = finalize_termination_reason(
        out.reason_code,
        out.terminated,
        inputs.truncated,
        out.status3
    );
    return out;
}
