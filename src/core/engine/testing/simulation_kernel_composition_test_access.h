#pragma once

#include "core/engine/simulation_kernel.h"
#include <sstream>
#include <string>
#include <string_view>

struct SimulationKernelCompositionFailureProbeResult {
    std::string error_code;
    bool singleton_references_restored = false;
};

// This accessor is used only by ef_test and the native fault probe. SimulationKernel
// grants it private access without a production fault-injection/inspection API.
class SimulationKernelCompositionTestAccess {
  public:
    [[nodiscard]] static bool rebuild_world_composition_for_testing(SimulationKernel &kernel,
                                                                    std::string_view barrier,
                                                                    std::string *error = nullptr);

    [[nodiscard]] static SimulationKernelCompositionFailureProbeResult
    probe_default_provider_publication_failure_for_testing(SimulationKernel &kernel);

    [[nodiscard]] static std::string rng_state_for_testing(SimulationKernel &kernel) {
        auto guard = kernel.acquire_composition_operation();
        kernel.ensure_active("testing_rng_state");
        // Reading the engine and draw position never consumes the stream.
        std::ostringstream state;
        state << kernel.rng.draw_position() << '\n' << kernel.rng.engine();
        return state.str();
    }

};
