#pragma once

#include <vector>

#include "core/mission/objective_runtime.h"
#include "core/mission/reward_runtime.h"
#include "core/mission/termination_runtime.h"

struct ExecutionStepRuntimeInputs {
    SafetyRuntimeInputs safety;

    bool has_waypoint = false;
    WaypointRewardInputs waypoint;
    bool waypoint_episode_success = false;
    double waypoint_episode_success_bonus = 0.0;

    bool has_approach = false;
    ApproachRewardInputs approach;

    bool has_objectives = false;
    std::vector<ConditionalObjectiveSpec> objectives;
    ConditionalObjectiveInputs objective_inputs;
    ObjectiveShapingConfig objective_shaping;

    bool truncated = false;
};

struct ExecutionStepRuntimeProducts {
    bool valid = false;

    SafetyRuntimeProducts safety;

    bool waypoint_evaluated = false;
    WaypointRewardProducts waypoint;
    bool waypoint_episode_success = false;
    double waypoint_episode_success_bonus = 0.0;

    bool approach_evaluated = false;
    ApproachRewardProducts approach;

    bool objective_evaluated = false;
    int matched_objective_index = -1;
    int objective_status_count = 0;
    ConditionalObjectiveProducts objective;

    double compiled_reward_total = 0.0;
    bool terminated = false;
    double status0 = 0.0;
    double status1 = 0.0;
    double status2 = 0.0;
    double status3 = 0.0;
    TerminationReasonCode reason_code = TerminationReasonCode::Running;
    TerminationReasonCode final_reason_code = TerminationReasonCode::Running;
};

ExecutionStepRuntimeProducts compute_execution_step_runtime(const ExecutionStepRuntimeInputs& inputs);
