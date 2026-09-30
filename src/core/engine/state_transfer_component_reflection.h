#pragma once

namespace flecs {
struct world;
}

// Registers the maintained value schema used by P4-B ECS state transfer.
// Component admission remains owned by system_contribution_registry; this
// function only adds Flecs meta descriptions to those already-admitted types.
void register_state_transfer_component_reflection(flecs::world &ecs);
