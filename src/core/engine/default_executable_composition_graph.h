#pragma once

#include <string>

namespace runtime::composition_contracts {
struct ResolvedSimulationComposition;
}

namespace runtime::engine {

// Bind the executable fields of a resolved default graph to the only native
// component/system registration functions that SimulationKernel can invoke.
[[nodiscard]] bool validate_default_executable_composition_graph(
    const composition_contracts::ResolvedSimulationComposition &resolved,
    std::string *error = nullptr) noexcept;

} // namespace runtime::engine
