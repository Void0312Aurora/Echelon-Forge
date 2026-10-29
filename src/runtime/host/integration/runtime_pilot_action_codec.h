#pragma once

#include "core/engine/world_batch_runtime.h"

#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace runtime::host::integration {

// Candidate action transport, using the maintained DTO and canonical JSON
// authority. This is neither a state payload nor a new checkpoint format.
[[nodiscard]] std::optional<std::vector<std::uint8_t>>
encode_pilot_actions(const std::vector<WorldPilotActionAssignment> &actions);
[[nodiscard]] std::optional<std::vector<WorldPilotActionAssignment>>
decode_pilot_actions(const std::vector<std::uint8_t> &payload);
[[nodiscard]] bool
pilot_action_entities_valid(SimulationKernel &kernel,
                            const std::vector<WorldPilotActionAssignment> &actions);
[[nodiscard]] std::uint64_t resolve_pilot_entity(SimulationKernel &kernel,
                                                 std::string_view logical_name);

} // namespace runtime::host::integration
