#pragma once

#if !defined(EF_RUNTIME_COMPOSITION_TESTING)
#error "default simulation provider test access is available only in test builds"
#endif

#include "runtime/providers/default_simulation_provider_catalog.h"

namespace runtime::providers {

[[nodiscard]] DefaultSimulationCompositionResult
build_default_simulation_composition_for_testing(SimulationKernel &kernel, flecs::world &world,
                                                 MissileTuning &missile_tuning, std::mt19937 &rng);

} // namespace runtime::providers
