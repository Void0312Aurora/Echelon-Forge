#pragma once

#include <vector>

#include "components/physics/instruments.h"
#include "core/interfaces/observation.h"

struct ExecutionObservationRuntimeProducts {
    bool valid = false;
    std::vector<float> instrument_values;
    std::vector<float> contact_values;
    std::vector<float> rwr_values;
};

ExecutionObservationRuntimeProducts compute_execution_observation_runtime(
    const InstrumentState& inst,
    const AgentObservation& truth,
    double ils_valid,
    double ils_loc,
    double ils_gs,
    double ils_dme,
    int max_contacts,
    int max_rwr
);
