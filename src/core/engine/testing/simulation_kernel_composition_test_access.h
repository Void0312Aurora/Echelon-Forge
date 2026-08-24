#pragma once

#include <string>

class SimulationKernel;

struct SimulationKernelCompositionFailureProbeResult {
    std::string error_code;
    bool singleton_references_restored = false;
};

// This accessor is linked only into ef_test. SimulationKernel grants it private
// access without carrying a public fault-injection entry point in production.
class SimulationKernelCompositionTestAccess {
  public:
    [[nodiscard]] static SimulationKernelCompositionFailureProbeResult
    probe_default_provider_publication_failure_for_testing(SimulationKernel &kernel);
};
