#pragma once

#include "runtime/contracts/simulation_composition_contract.h"

#include <string_view>

namespace runtime::world_batch_backend_contracts {

inline constexpr std::string_view kRequestSchemaVersion =
    "echelon_forge.runtime_backend_provider_request.v1";
inline constexpr std::string_view kDefaultProviderId = "builtin.backend.flecs_cpu";
inline constexpr std::string_view kDefaultImplementationVersion = "1.0.0";
inline constexpr std::string_view kSemanticServiceId =
    composition_contracts::kServiceWorldBatchBackend;
inline constexpr std::string_view kCpuExactCapabilityId = "runtime.cpu_exact";

} // namespace runtime::world_batch_backend_contracts
