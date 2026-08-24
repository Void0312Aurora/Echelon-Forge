#pragma once

#include "runtime/composition/composition_error.h"
#include "runtime/contracts/simulation_composition_contract.h"

#include <string_view>

namespace runtime::composition {

using ManifestParseResult = CompositionResult<composition_contracts::SimulationCompositionManifest>;
using ResolvedCompositionParseResult =
    CompositionResult<composition_contracts::ResolvedSimulationComposition>;

// These parsers are the native ingestion boundary for the host-neutral JSON
// contract. They reject missing/extra fields, floating-point numbers, invalid
// JSON types, and unknown scopes before any provider factory is consulted.
[[nodiscard]] ManifestParseResult
parse_simulation_composition_manifest_json(std::string_view json_text);

[[nodiscard]] ResolvedCompositionParseResult
parse_resolved_composition_json(std::string_view json_text);

} // namespace runtime::composition
