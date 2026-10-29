#pragma once

#include <cstdint>
#include <string>
#include <vector>

class SimulationKernel;

namespace runtime::contracts {

// Shared codec entrypoints used by the maintained facade and host adapters.
// Implementations live with the native state codec and preserve the existing
// state-owner validation rules.
[[nodiscard]] std::string serialize_native_world_state(SimulationKernel &kernel);
[[nodiscard]] bool restore_native_world_state(SimulationKernel &kernel,
                                              const std::vector<std::uint8_t> &payload);
[[nodiscard]] std::string serialize_native_rng_state(SimulationKernel &kernel);
[[nodiscard]] bool restore_native_rng_state(SimulationKernel &kernel,
                                            const std::vector<std::uint8_t> &payload);
[[nodiscard]] std::string serialize_native_clock_state(SimulationKernel &kernel,
                                                       std::uint64_t step_sequence,
                                                       std::uint64_t barrier_sequence);
[[nodiscard]] bool restore_native_clock_state(SimulationKernel &kernel,
                                              const std::vector<std::uint8_t> &payload);

} // namespace runtime::contracts
