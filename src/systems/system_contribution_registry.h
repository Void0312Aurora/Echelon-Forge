#pragma once

#include <cstddef>
#include <span>
#include <string>
#include <string_view>

namespace flecs {
class world;
}

namespace runtime::systems {

using RegistrationFunction = void (*)(flecs::world &);

struct ComponentContribution {
    std::string_view component_id;
    std::string_view registration_id;
    RegistrationFunction register_component;
};

struct SystemContribution {
    std::string_view contribution_id;
    std::string_view registration_factory_id;
    std::string_view domain;
    std::string_view stage_id;
    std::size_t stage_order;
    std::string_view after_contribution_id;
    RegistrationFunction register_system;
};

struct KernelSystemContribution {
    std::string_view contribution_id;
    std::string_view stage_id;
    std::size_t stage_order;
    RegistrationFunction register_system;
};

// This is the native admission surface for the built-in graph.  Cordis or a
// host may describe a candidate package, but only this owner-derived registry
// can install components and systems into the Flecs world.
[[nodiscard]] std::span<const ComponentContribution> default_component_contributions() noexcept;
[[nodiscard]] std::span<const SystemContribution> default_system_contributions() noexcept;
[[nodiscard]] std::span<const KernelSystemContribution> kernel_system_contributions() noexcept;

// Both functions fail closed if the registry no longer matches the frozen
// default compatibility artifact.  They are intentionally the only runtime
// entry points used by SimulationKernel for built-in registration.
void register_default_component_contributions(flecs::world &ecs);
void register_default_system_contributions(flecs::world &ecs);

[[nodiscard]] bool validate_default_contribution_graph(std::string *error = nullptr) noexcept;

} // namespace runtime::systems
