#pragma once

#include "core/mission/runtime/execution_step_runtime.h"
#include "core/mission/runtime/mission_runtime.h"
#include "core/mission/runtime/reward_runtime.h"
#include <vector>

struct ExecutionFrameRuntimeInputs {
    bool has_mission_observation = false;
    MissionObservationInputs mission_observation;

    bool has_step_info = false;
    StepInfoInputs step_info;

    bool has_execution_step = false;
    ExecutionStepRuntimeInputs execution_step;

    bool has_flight_shaping = false;
    FlightShapingRuntimeInputs flight_shaping;
};

struct ExecutionFrameRuntimeProducts {
    bool valid = false;

    bool mission_observation_evaluated = false;
    MissionObservationProducts mission_observation;

    bool step_info_evaluated = false;
    StepInfoProducts step_info;

    bool execution_step_evaluated = false;
    ExecutionStepRuntimeProducts execution_step;

    bool flight_shaping_evaluated = false;
    FlightShapingRuntimeProducts flight_shaping;
};

ExecutionFrameRuntimeProducts compute_execution_frame_runtime(const ExecutionFrameRuntimeInputs& inputs);
std::vector<ExecutionFrameRuntimeProducts> compute_execution_frame_runtime_batch(
    const std::vector<ExecutionFrameRuntimeInputs>& inputs_batch
);
