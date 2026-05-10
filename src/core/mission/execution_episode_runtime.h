#pragma once

#include "core/mission/execution_step_runtime.h"
#include "core/mission/mission_runtime.h"
#include "core/mission/reward_runtime.h"
#include <vector>

struct ExecutionEpisodeRuntimeInputs {
    bool has_mission_observation = false;
    MissionObservationInputs mission_observation;

    bool has_step_info = false;
    StepInfoInputs step_info;

    bool has_execution_step = false;
    ExecutionStepRuntimeInputs execution_step;

    bool has_flight_shaping = false;
    FlightShapingRuntimeInputs flight_shaping;
    bool include_roll_stability = false;
};

struct ExecutionEpisodeRuntimeProducts {
    bool valid = false;

    bool mission_observation_evaluated = false;
    MissionObservationProducts mission_observation;

    bool step_info_evaluated = false;
    StepInfoProducts step_info;

    bool execution_step_evaluated = false;
    ExecutionStepRuntimeProducts execution_step;

    bool flight_shaping_evaluated = false;
    FlightShapingRuntimeProducts flight_shaping;

    bool outcome_evaluated = false;
    double compiled_reward_total = 0.0;
    bool terminated = false;
    double status0 = 0.0;
    double status1 = 0.0;
    double status2 = 0.0;
    double status3 = 0.0;
    TerminationReasonCode reason_code = TerminationReasonCode::Running;
    TerminationReasonCode final_reason_code = TerminationReasonCode::Running;
};

ExecutionEpisodeRuntimeProducts compute_execution_episode_runtime(const ExecutionEpisodeRuntimeInputs& inputs);
std::vector<ExecutionEpisodeRuntimeProducts> compute_execution_episode_runtime_batch(
    const std::vector<ExecutionEpisodeRuntimeInputs>& inputs_batch
);
