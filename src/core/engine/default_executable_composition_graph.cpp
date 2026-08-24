#include "core/engine/default_executable_composition_graph.h"

#include "runtime/contracts/simulation_composition_contract.h"
#include "systems/system_contribution_registry.h"

#include <algorithm>
#include <exception>

namespace runtime::engine {

bool validate_default_executable_composition_graph(
    const composition_contracts::ResolvedSimulationComposition &resolved,
    std::string *error) noexcept {
    try {
        if (!systems::validate_default_contribution_graph(error)) {
            return false;
        }

        const auto components = systems::default_component_contributions();
        if (components.size() != resolved.manifest.component_contributions.size()) {
            if (error != nullptr) *error = "component registry/resolved count mismatch";
            return false;
        }
        for (const auto &native : components) {
            const auto row = std::find_if(resolved.manifest.component_contributions.begin(),
                                          resolved.manifest.component_contributions.end(),
                                          [&](const auto &candidate) {
                                              return candidate.component_id == native.component_id;
                                          });
            if (row == resolved.manifest.component_contributions.end() ||
                row->registration_id != native.registration_id) {
                if (error != nullptr) *error = "component registry/resolved identity mismatch";
                return false;
            }
        }

        const auto native_systems = systems::default_system_contributions();
        if (native_systems.size() != resolved.manifest.system_contributions.size() ||
            native_systems.size() != resolved.system_registration_order.size()) {
            if (error != nullptr) *error = "system registry/resolved count mismatch";
            return false;
        }
        for (std::size_t index = 0; index < native_systems.size(); ++index) {
            const auto &native = native_systems[index];
            if (resolved.system_registration_order[index] != native.contribution_id) {
                if (error != nullptr) *error = "system registry/resolved order mismatch";
                return false;
            }
            const auto row = std::find_if(
                resolved.manifest.system_contributions.begin(),
                resolved.manifest.system_contributions.end(), [&](const auto &candidate) {
                    return candidate.contribution_id == native.contribution_id;
                });
            const bool after_matches =
                native.after_contribution_id.empty()
                    ? row != resolved.manifest.system_contributions.end() && row->after.empty()
                    : row != resolved.manifest.system_contributions.end() &&
                          row->after.size() == 1 &&
                          row->after.front() == native.after_contribution_id;
            if (row == resolved.manifest.system_contributions.end() ||
                row->registration_factory_id != native.registration_factory_id ||
                row->domain != native.domain || !after_matches) {
                if (error != nullptr) {
                    *error = "system registry/resolved execution metadata mismatch";
                }
                return false;
            }
        }
        return true;
    } catch (const std::exception &exception) {
        if (error != nullptr) {
            *error = std::string("default graph admission failed: ") + exception.what();
        }
        return false;
    } catch (...) {
        if (error != nullptr) {
            *error = "default graph admission failed with an unknown exception";
        }
        return false;
    }
}

} // namespace runtime::engine
