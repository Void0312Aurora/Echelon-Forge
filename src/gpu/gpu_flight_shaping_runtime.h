#pragma once

#include <cstddef>
#include <vector>

#include "core/mission/runtime/reward_runtime.h"

namespace gpu {

constexpr int kFlightShapingOutputCount = 33;

struct FlightShapingExperimentStats {
    bool used_cuda = false;
    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double total_ms = 0.0;
};

FlightShapingExperimentStats last_flight_shaping_stats();
const void* last_flight_shaping_output_device_ptr();
std::size_t last_flight_shaping_output_float_count();

std::vector<float> compute_flight_shaping_reference_cpu_batch(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
);

std::vector<float> compute_flight_shaping_experiment_batch(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
);

bool compute_flight_shaping_experiment_batch_device_resident(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
);

}  // namespace gpu
