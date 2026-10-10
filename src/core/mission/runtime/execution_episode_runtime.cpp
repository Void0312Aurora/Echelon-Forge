#include "core/mission/runtime/execution_episode_runtime.h"
#include "core/mission/runtime/execution_frame_runtime.h"
#include "core/engine/parallel_for_index.h"

namespace {
template <typename Fn> void parallel_for_index(size_t task_count, Fn &&fn) {
    if (task_count == 0) {
        return;
    }
    // Keep small batches on one thread to avoid scheduling overhead.
    if (task_count < 64) {
        for (size_t i = 0; i < task_count; ++i) {
            fn(i);
        }
        return;
    }

    runtime::detail::parallel_for_index(task_count, 0, std::forward<Fn>(fn));
}

template <typename Products, typename Inputs>
Products compute_common_execution_runtime(const Inputs &inputs) {
    Products out{};
    out.valid = true;

    if (inputs.has_mission_observation) {
        out.mission_observation_evaluated = true;
        out.mission_observation = compute_mission_observation(inputs.mission_observation);
    }

    if (inputs.has_step_info) {
        out.step_info_evaluated = true;
        out.step_info = compute_step_info_runtime(inputs.step_info);
    }

    if (inputs.has_execution_step) {
        out.execution_step_evaluated = true;
        out.execution_step = compute_execution_step_runtime(inputs.execution_step);
    }

    if (inputs.has_flight_shaping) {
        out.flight_shaping_evaluated = true;
        out.flight_shaping = compute_flight_shaping_terms(inputs.flight_shaping);
    }

    return out;
}

template <typename Inputs, typename Products>
std::vector<Products> compute_runtime_batch(const std::vector<Inputs> &inputs_batch,
                                            Products (*compute_one)(const Inputs &)) {
    std::vector<Products> out(inputs_batch.size());
    parallel_for_index(inputs_batch.size(),
                       [&](size_t i) { out[i] = compute_one(inputs_batch[i]); });
    return out;
}

double sum_flight_shaping_terms(const FlightShapingRuntimeProducts &products,
                                bool include_roll_stability) {
    double total = 0.0;
    total += products.altitude_progress;
    total += products.low_alt_descent_penalty;
    total += products.speed_progress;
    total += products.speed_regress;
    total += products.stationary_penalty;
    total += products.liftoff_bonus;
    total += products.rotation_reward;
    total += products.rotation_overpitch_penalty;
    total += products.gear_up_bonus;
    total += products.heading_error_penalty;
    total += products.heading_hold_bonus;
    total += products.altitude_error_penalty;
    total += products.altitude_hold_bonus;
    total += products.speed_error_penalty;
    total += products.speed_hold_bonus;
    total += products.roll_abs_penalty;
    total += products.pitch_abs_penalty;
    total += products.yaw_rate_abs_penalty;
    total += products.beta_abs_penalty;
    total += products.g_deviation_penalty;
    total += products.speed_reward;
    total += products.runway_centerline_m_penalty;
    total += products.runway_centerline_penalty;
    total += products.runway_centerline_barrier;
    total += products.departure_centerline_m_penalty;
    total += products.departure_centerline_reward;
    total += products.departure_track_error_penalty;
    total += products.departure_track_reward;
    total += products.alignment_reward;
    if (include_roll_stability) {
        total += products.roll_stability;
    }
    return total;
}

void apply_default_waypoint_status(const ExecutionStepRuntimeInputs &inputs,
                                   const ExecutionStepRuntimeProducts &step_products,
                                   ExecutionEpisodeRuntimeProducts *out) {
    if (out == nullptr || !inputs.has_waypoint) {
        return;
    }
    if (step_products.objective_evaluated && step_products.objective_status_count > 0) {
        return;
    }
    out->status0 = inputs.waypoint.dist_m;
    out->status1 = static_cast<double>(inputs.waypoint.waypoint_index);
    out->status2 = static_cast<double>(inputs.waypoint.waypoint_count);
}

} // namespace

ExecutionFrameRuntimeProducts
compute_execution_frame_runtime(const ExecutionFrameRuntimeInputs &inputs) {
    return compute_common_execution_runtime<ExecutionFrameRuntimeProducts>(inputs);
}

std::vector<ExecutionFrameRuntimeProducts> compute_execution_frame_runtime_batch(
    const std::vector<ExecutionFrameRuntimeInputs> &inputs_batch) {
    return compute_runtime_batch(inputs_batch, &compute_execution_frame_runtime);
}

ExecutionEpisodeRuntimeProducts
compute_execution_episode_runtime(const ExecutionEpisodeRuntimeInputs &inputs) {
    auto out = compute_common_execution_runtime<ExecutionEpisodeRuntimeProducts>(inputs);

    if (!out.execution_step_evaluated && !out.flight_shaping_evaluated) {
        return out;
    }

    out.outcome_evaluated = true;

    if (out.execution_step_evaluated) {
        out.compiled_reward_total = out.execution_step.compiled_reward_total;
        out.terminated = out.execution_step.terminated;
        out.status0 = out.execution_step.status0;
        out.status1 = out.execution_step.status1;
        out.status2 = out.execution_step.status2;
        out.status3 = out.execution_step.status3;
        out.reason_code = out.execution_step.reason_code;
        out.final_reason_code = out.execution_step.final_reason_code;
        apply_default_waypoint_status(inputs.execution_step, out.execution_step, &out);
        if (out.flight_shaping_evaluated && out.execution_step.safety.crash_penalty == 0.0) {
            out.compiled_reward_total +=
                sum_flight_shaping_terms(out.flight_shaping, inputs.include_roll_stability);
        }
        return out;
    }

    out.compiled_reward_total =
        sum_flight_shaping_terms(out.flight_shaping, inputs.include_roll_stability);
    return out;
}

std::vector<ExecutionEpisodeRuntimeProducts> compute_execution_episode_runtime_batch(
    const std::vector<ExecutionEpisodeRuntimeInputs> &inputs_batch) {
    return compute_runtime_batch(inputs_batch, &compute_execution_episode_runtime);
}
