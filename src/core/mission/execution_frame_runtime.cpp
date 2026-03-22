#include "core/mission/execution_frame_runtime.h"

ExecutionFrameRuntimeProducts compute_execution_frame_runtime(const ExecutionFrameRuntimeInputs& inputs) {
    ExecutionFrameRuntimeProducts out{};
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
