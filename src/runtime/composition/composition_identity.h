#pragma once

#include "runtime/composition/composition_error.h"
#include "runtime/contracts/simulation_composition_contract.h"

#include <string>

namespace runtime::composition {

struct CompositionIdentity {
    std::string requested_manifest_sha256;
    std::string resolved_manifest_sha256;
};

using CompositionIdentityResult = CompositionResult<CompositionIdentity>;

[[nodiscard]] CompositionIdentityResult
compute_composition_identity(const composition_contracts::ResolvedSimulationComposition &resolved);

} // namespace runtime::composition
