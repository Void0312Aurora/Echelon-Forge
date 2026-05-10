#include "core/mission/execution_episode_controller.h"

#include <algorithm>
#include <cmath>
#include <utility>
#include <vector>

#include "core/mission/episode_reward_breakdown.h"
#include "core/mission/episode_transition_runtime.h"
#include "core/mission/termination_runtime.h"

namespace {

double safe_get(const std::vector<double>& values, std::size_t index, double fallback = 0.0) {
    return index < values.size() ? values[index] : fallback;
}

}  // namespace

using episode_controller_detail::apply_pre_step_behavior_updates;
using episode_controller_detail::build_episode_reward_breakdown_json;
using episode_controller_detail::maybe_apply_post_waypoint_transition;

void ExecutionEpisodeController::clear_state() noexcept {
    has_state_ = false;
    state_ = ExecutionEpisodeState{};
}

bool ExecutionEpisodeController::has_state() const noexcept {
    return has_state_;
}

void ExecutionEpisodeController::import_state(const ExecutionEpisodeState& state) {
    state_ = state;
    has_state_ = true;
}

ExecutionEpisodeState ExecutionEpisodeController::export_state() const {
    return state_;
}

void ExecutionEpisodeController::apply_episode_state_overrides(
    const ExecutionEpisodeState& episode_state,
    StepEvaluationBatchEnvState* env_state
) {
    if (env_state == nullptr) {
        return;
    }

    env_state->prev_altitude_m = episode_state.prev_altitude_m;
    env_state->prev_ias_mps = episode_state.prev_ias_mps;
    env_state->liftoff_awarded = episode_state.liftoff_awarded;
    env_state->gear_bonus_awarded = episode_state.gear_bonus_awarded;

    if (env_state->has_safety) {
        env_state->safety.off_runway_steps = (
            env_state->safety.runway_surface_phase && !env_state->safety.on_runway_task
        )
            ? std::max(0, episode_state.off_runway_steps + 1)
            : 0;
    }

    if (env_state->has_waypoint) {
        env_state->waypoint.waypoint_index = episode_state.waypoint_index;
        env_state->waypoint.has_prev_dist = episode_state.has_waypoint_prev_dist_m;
        env_state->waypoint.prev_dist_m = episode_state.has_waypoint_prev_dist_m
            ? episode_state.waypoint_prev_dist_m
            : 0.0;
    }

    if (env_state->has_approach) {
        env_state->approach.has_prev_dme = episode_state.has_approach_prev_dme_m;
        env_state->approach.prev_dme_m = episode_state.has_approach_prev_dme_m
            ? episode_state.approach_prev_dme_m
            : 0.0;
        env_state->approach.has_prev_loc = episode_state.has_approach_prev_loc_abs;
        env_state->approach.prev_loc_abs = episode_state.has_approach_prev_loc_abs
            ? episode_state.approach_prev_loc_abs
            : 0.0;
        env_state->approach.has_prev_gs = episode_state.has_approach_prev_gs_abs;
        env_state->approach.prev_gs_abs = episode_state.has_approach_prev_gs_abs
            ? episode_state.approach_prev_gs_abs
            : 0.0;
    }

    if (env_state->has_flight_shaping) {
        env_state->flight_shaping.prev_altitude_m = episode_state.prev_altitude_m;
        env_state->flight_shaping.prev_ias_mps = episode_state.prev_ias_mps;
        env_state->flight_shaping.liftoff_awarded = episode_state.liftoff_awarded;
        env_state->flight_shaping.gear_bonus_awarded = episode_state.gear_bonus_awarded;
    }
}

StepEvaluationBatchEnvState ExecutionEpisodeController::resolve_env_state(
    const StepEvaluationBatchEnvState& env_state
) const {
    StepEvaluationBatchEnvState resolved = env_state;
    if (!resolved.has_episode_state && has_state_) {
        resolved.has_episode_state = true;
        resolved.episode_state = state_;
    }
    if (resolved.has_episode_state) {
        apply_episode_state_overrides(resolved.episode_state, &resolved);
    }
    return resolved;
}

ExecutionEpisodeRuntimeInputs ExecutionEpisodeController::prepare_runtime_inputs(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& env_state
) const {
    auto resolved = resolve_env_state(env_state);
    ExecutionEpisodeState working_state{};
    if (resolved.has_episode_state) {
        working_state = resolved.episode_state;
    } else if (has_state_) {
        working_state = state_;
    }
    apply_pre_step_behavior_updates(&resolved, &working_state);
    auto batch = prepare_step_evaluations_batch(config, {resolved});
    if (batch.empty()) {
        return ExecutionEpisodeRuntimeInputs{};
    }
    return batch.front();
}

ExecutionEpisodeRuntimeProducts ExecutionEpisodeController::evaluate(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& env_state
) const {
    return compute_execution_episode_runtime(prepare_runtime_inputs(config, env_state));
}

ExecutionEpisodeRuntimeProducts ExecutionEpisodeController::step(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& env_state
) {
    auto resolved = resolve_env_state(env_state);
    ExecutionEpisodeState next_state{};
    if (resolved.has_episode_state) {
        next_state = resolved.episode_state;
    } else if (has_state_) {
        next_state = state_;
    }
    apply_pre_step_behavior_updates(&resolved, &next_state);
    auto batch = prepare_step_evaluations_batch(config, {resolved});
    const auto runtime_inputs = batch.empty() ? ExecutionEpisodeRuntimeInputs{} : batch.front();
    const auto products = compute_execution_episode_runtime(runtime_inputs);
    apply_runtime_products_to_state(resolved, runtime_inputs, products, &next_state);
    state_ = std::move(next_state);
    has_state_ = true;
    return products;
}

ExecutionEpisodeControllerStepResult ExecutionEpisodeController::step_result(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& env_state
) {
    auto resolved = resolve_env_state(env_state);
    ExecutionEpisodeState next_state{};
    if (resolved.has_episode_state) {
        next_state = resolved.episode_state;
    } else if (has_state_) {
        next_state = state_;
    }
    apply_pre_step_behavior_updates(&resolved, &next_state);
    auto batch = prepare_step_evaluations_batch(config, {resolved});
    const auto runtime_inputs = batch.empty() ? ExecutionEpisodeRuntimeInputs{} : batch.front();
    const auto products = compute_execution_episode_runtime(runtime_inputs);

    ExecutionEpisodeControllerStepResult result{};
    apply_runtime_products_to_state(resolved, runtime_inputs, products, &next_state, &result);
    state_ = next_state;
    has_state_ = true;
    result.valid = products.valid;
    result.controller_state = state_;
    return result;
}

void ExecutionEpisodeController::apply_runtime_products_to_state(
    const StepEvaluationBatchEnvState& env_state,
    const ExecutionEpisodeRuntimeInputs& runtime_inputs,
    const ExecutionEpisodeRuntimeProducts& products,
    ExecutionEpisodeState* state,
    ExecutionEpisodeControllerStepResult* result
) {
    if (state == nullptr) {
        return;
    }

    double reward_total = double(products.compiled_reward_total);
    const bool truncated = runtime_inputs.has_execution_step
        ? bool(runtime_inputs.execution_step.truncated)
        : bool(env_state.truncated);
    double status0 = double(products.status0);
    double status1 = double(products.status1);
    double status2 = double(products.status2);
    double status3 = double(products.status3);
    bool structural_state_changed = false;
    bool objective_has_status = false;
    const bool had_post_waypoint_transition_before = state->has_post_waypoint_transition_json;
    bool waypoint_arrived = false;
    double phase_transition_bonus = 0.0;
    bool landing_transition_pending = false;

    state->step_count = int(env_state.steps);
    state->prev_altitude_m = runtime_inputs.has_flight_shaping
        ? double(runtime_inputs.flight_shaping.truth_altitude_m)
        : env_state.truth_z;
    state->prev_ias_mps = runtime_inputs.has_flight_shaping
        ? double(runtime_inputs.flight_shaping.curr_ias_mps)
        : safe_get(env_state.inst_vec, 0, env_state.truth_speed);
    state->last_termination_reason = termination_reason_name(products.final_reason_code);

    if (runtime_inputs.has_execution_step) {
        state->off_runway_steps = int(runtime_inputs.execution_step.safety.off_runway_steps);
    }

    if (products.flight_shaping_evaluated) {
        state->liftoff_awarded = bool(products.flight_shaping.next_liftoff_awarded);
        state->gear_bonus_awarded = bool(products.flight_shaping.next_gear_bonus_awarded);
    }

    if (products.execution_step_evaluated) {
        const auto& step_products = products.execution_step;
        objective_has_status = step_products.objective_evaluated &&
            step_products.objective_status_count > 0;

        if (step_products.approach_evaluated) {
            if (bool(step_products.approach.clear_history)) {
                state->has_approach_prev_dme_m = false;
                state->approach_prev_dme_m = 0.0;
                state->has_approach_prev_loc_abs = false;
                state->approach_prev_loc_abs = 0.0;
                state->has_approach_prev_gs_abs = false;
                state->approach_prev_gs_abs = 0.0;
            } else if (bool(step_products.approach.next_prev_valid)) {
                state->has_approach_prev_dme_m = true;
                state->approach_prev_dme_m = double(step_products.approach.next_prev_dme_m);
                state->has_approach_prev_loc_abs = true;
                state->approach_prev_loc_abs = double(step_products.approach.next_prev_loc_abs);
                state->has_approach_prev_gs_abs = true;
                state->approach_prev_gs_abs = double(step_products.approach.next_prev_gs_abs);
            }
        }

        if (step_products.waypoint_evaluated) {
            const int prior_waypoint_index = state->waypoint_index;
            const int waypoint_count = runtime_inputs.execution_step.has_waypoint
                ? int(runtime_inputs.execution_step.waypoint.waypoint_count)
                : int(state->route_waypoints.size());
            if (!objective_has_status) {
                status0 = runtime_inputs.execution_step.has_waypoint
                    ? double(runtime_inputs.execution_step.waypoint.dist_m)
                    : status0;
                status1 = double(prior_waypoint_index);
                status2 = double(waypoint_count);
            }
            if (bool(step_products.waypoint.arrived)) {
                waypoint_arrived = true;
                state->waypoint_index = std::min(state->waypoint_index + 1, std::max(0, waypoint_count));
                state->has_waypoint_prev_dist_m = false;
                state->waypoint_prev_dist_m = 0.0;
                if (!objective_has_status) {
                    status1 = double(state->waypoint_index);
                    if (
                        state->waypoint_index >= 0 &&
                        state->waypoint_index < waypoint_count &&
                        static_cast<std::size_t>(state->waypoint_index) < state->route_waypoints.size()
                    ) {
                        const auto& next_waypoint = state->route_waypoints[static_cast<std::size_t>(state->waypoint_index)];
                        const double next_dx = next_waypoint.x_m - env_state.truth_x;
                        const double next_dy = next_waypoint.y_m - env_state.truth_y;
                        status0 = std::hypot(next_dx, next_dy);
                    } else {
                        status0 = 0.0;
                    }
                }
            } else if (bool(step_products.waypoint.next_prev_dist_valid)) {
                state->has_waypoint_prev_dist_m = true;
                state->waypoint_prev_dist_m = double(step_products.waypoint.next_prev_dist_m);
            }
        }
    }

    const auto post_transition = maybe_apply_post_waypoint_transition(env_state, runtime_inputs, state);
    if (post_transition.activated) {
        phase_transition_bonus = post_transition.transition_reward_bonus;
        reward_total += phase_transition_bonus;
    }
    if (post_transition.structural_state_changed) {
        structural_state_changed = true;
    }
    landing_transition_pending = post_transition.pending;
    if (!objective_has_status) {
        if (post_transition.activated) {
            status0 = 0.0;
            status1 = 0.0;
        } else if (landing_transition_pending) {
            status0 = 0.0;
            status1 = double(state->waypoint_index);
        }
    }

    const std::string reward_breakdown_json = build_episode_reward_breakdown_json(
        runtime_inputs,
        products,
        reward_total,
        waypoint_arrived,
        had_post_waypoint_transition_before,
        phase_transition_bonus
    );

    state->last_reward_total = reward_total;
    state->last_reward_breakdown_json = reward_breakdown_json;
    if (result != nullptr) {
        result->valid = products.valid;
        result->reward_total = reward_total;
        result->terminated = bool(products.terminated);
        result->truncated = truncated;
        result->status0 = status0;
        result->status1 = status1;
        result->status2 = status2;
        result->status3 = status3;
        result->step_info_valid = bool(products.step_info_evaluated);
        if (products.step_info_evaluated) {
            result->step_info = products.step_info;
        }
        result->structural_state_changed = structural_state_changed;
    }
}
