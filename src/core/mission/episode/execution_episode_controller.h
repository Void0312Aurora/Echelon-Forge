#pragma once

#include "core/mission/episode/execution_episode_batch_prepare.h"

struct ExecutionEpisodeControllerStepResult {
    bool valid = false;
    ExecutionEpisodeState controller_state{};
    double reward_total = 0.0;
    bool terminated = false;
    bool truncated = false;
    double status0 = 0.0;
    double status1 = 0.0;
    double status2 = 0.0;
    double status3 = 0.0;
    bool step_info_valid = false;
    StepInfoProducts step_info{};
    bool structural_state_changed = false;
};

class ExecutionEpisodeController {
public:
    ExecutionEpisodeController() = default;

    void clear_state() noexcept;
    bool has_state() const noexcept;

    void import_state(const ExecutionEpisodeState& state);
    ExecutionEpisodeState export_state() const;

    ExecutionEpisodeRuntimeInputs prepare_runtime_inputs(
        const StepEvaluationBatchConfig& config,
        const StepEvaluationBatchEnvState& env_state
    ) const;

    ExecutionEpisodeRuntimeProducts evaluate(
        const StepEvaluationBatchConfig& config,
        const StepEvaluationBatchEnvState& env_state
    ) const;

    ExecutionEpisodeRuntimeProducts step(
        const StepEvaluationBatchConfig& config,
        const StepEvaluationBatchEnvState& env_state
    );
    ExecutionEpisodeControllerStepResult step_result(
        const StepEvaluationBatchConfig& config,
        const StepEvaluationBatchEnvState& env_state
    );

private:
    StepEvaluationBatchEnvState resolve_env_state(const StepEvaluationBatchEnvState& env_state) const;
    static void apply_episode_state_overrides(
        const ExecutionEpisodeState& episode_state,
        StepEvaluationBatchEnvState* env_state
    );
    static void apply_runtime_products_to_state(
        const StepEvaluationBatchEnvState& env_state,
        const ExecutionEpisodeRuntimeInputs& runtime_inputs,
        const ExecutionEpisodeRuntimeProducts& products,
        ExecutionEpisodeState* state,
        ExecutionEpisodeControllerStepResult* result = nullptr
    );

    bool has_state_ = false;
    ExecutionEpisodeState state_{};
};
