#include "simulation_kernel.h"
#include "simulation_kernel_engagement_event_store.h"

#include "components/combat/scoring.h"
#include "components/combat/structural_failure.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/health.h"
#include "components/domains/air/combat/weapon_air.h"
#include "components/combat/common/weapon_common.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/command/command_link_qos.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/physics/control_law.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/domains/air/platform/flight_dynamics_tuning.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/systems/comm.h"
#include "components/systems/data_link.h"
#include "components/systems/ew.h"
#include "components/systems/logistics.h"
#include "components/systems/navigation.h"
#include "components/systems/sonar.h"
#include "components/systems/track_management.h"
#include "components/domains/naval/platform/embarked_air_ops.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/acoustic_model.h"
#include "core/interfaces/control_model.h"
#include "core/interfaces/effects_model.h"
#include "core/interfaces/guidance_model.h"
#include "core/interfaces/sensor_model.h"
#include "systems/combat/pilot_weapon_release_system.h"
#include "systems/domains/air/propulsion_system.h"
#include "systems/domains/naval/naval_mission_weapon_release_system.h"
#include "systems/domains/naval/naval_logistics_system.h"
#include "systems/system_contribution_registry.h"
#include "runtime/contracts/composition/runtime_composition_evidence.v1.generated.h"
#include "runtime/contracts/runtime_composition_projection_contract.h"

#include <nlohmann/json.hpp>
#include <algorithm>
#include <functional>
#include <unordered_set>

void SimulationKernel::register_components_and_systems() {

    // Components and systems are admitted through the owner-derived registry.
    // The registry validates the frozen default artifact before touching Flecs.
    runtime::systems::register_default_component_contributions(ecs);

    // Service references are components too; they are installed by the same
    // contribution registry so the component graph has one admission path.

    // Contribution ordinals govern factory admission. Flecs phase dependencies
    // govern normal progress; a factory can install multiple executable nodes.
    // The manually selected exact-stage trace has its own direct ecs_run order.
    // Record actual installed nodes without altering either execution path.
    runtime::systems::register_default_system_contributions(ecs, &installed_system_nodes_);
}

std::string SimulationKernel::executable_composition_graph_sha256() const {
    using Json = nlohmann::json;
    Json components = Json::array();
    for (const auto &row : runtime::systems::default_component_contributions()) {
        components.push_back({
            {"component_id", row.component_id},
            {"registration_id", row.registration_id},
        });
    }

    Json kernel_systems = Json::array();
    for (const auto &row : runtime::systems::kernel_system_contributions()) {
        kernel_systems.push_back({
            {"contribution_id", row.contribution_id},
            {"stage_id", row.stage_id},
            {"stage_order", row.stage_order},
        });
    }

    Json resolved_systems = Json::array();
    for (const auto &row : runtime::systems::default_system_contributions()) {
        resolved_systems.push_back({
            {"after_contribution_id", row.after_contribution_id},
            {"contribution_id", row.contribution_id},
            {"domain", row.domain},
            {"registration_factory_id", row.registration_factory_id},
            {"stage_id", row.stage_id},
            {"stage_order", row.stage_order},
        });
    }

    const Json payload = {
        {"component_contributions", std::move(components)},
        {"graph_contract_version", "echelon_forge.executable_system_graph.v1"},
        {"kernel_system_contributions", std::move(kernel_systems)},
        {"resolved_system_contributions", std::move(resolved_systems)},
        {"stage_contract_version",
         runtime::composition_evidence_contracts::generated::kStageContractVersion},
    };
    return runtime::projection_contracts::canonical_sha256_hex(payload.dump());
}

std::string SimulationKernel::realized_cpu_scheduler_topology_json() const {
    const auto lock = acquire_composition_operation();
    using Json = nlohmann::json;
    // Anonymous Flecs phase-chain nodes are normalized by their dependencies,
    // never by allocation IDs. Named nodes retain their full namespace path.
    std::unordered_set<ecs_entity_t> visiting;
    std::function<Json(ecs_entity_t)> dependency = [&](ecs_entity_t id) -> Json {
        if (!visiting.insert(id).second) {
            return {{"cycle", true}};
        }
        Json targets = Json::array();
        for (int i = 0; auto target = ecs_get_target(ecs.c_ptr(), id, EcsDependsOn, i); ++i) {
            targets.push_back(dependency(target));
        }
        std::sort(targets.begin(), targets.end(),
                  [](const Json &a, const Json &b) { return a.dump() < b.dump(); });
        visiting.erase(id);
        Json result = {{"depends_on", std::move(targets)},
                       {"disabled", ecs_has_id(ecs.c_ptr(), id, EcsDisabled)}};
        if (ecs_get_name(ecs.c_ptr(), id) != nullptr) {
            result["path"] = ecs.entity(id).path().c_str();
        }
        return result;
    };

    Json nodes = Json::array();
    auto it = ecs_each_id(ecs.c_ptr(), EcsSystem);
    while (ecs_each_next(&it)) {
        for (int i = 0; i < it.count; ++i) {
            const auto id = it.entities[i];
            const std::string path = ecs.entity(id).path().c_str();
            const auto owner =
                std::find_if(installed_system_nodes_.begin(), installed_system_nodes_.end(),
                             [&](const auto &entry) { return entry.first == path; });
            const auto *system = ecs_system_get(ecs.c_ptr(), id);
            char *query = ecs_query_str(system->query);
            nodes.push_back(
                {{"path", path},
                 {"owner", owner == installed_system_nodes_.end() ? "unowned" : owner->second},
                 {"dependencies", dependency(id)},
                 {"query", query == nullptr ? "" : query},
                 {"multi_threaded", system->multi_threaded},
                 {"immediate", system->immediate}});
            ecs_os_free(query);
        }
    }
    std::sort(nodes.begin(), nodes.end(), [](const Json &a, const Json &b) {
        return a.at("path").get<std::string>() < b.at("path").get<std::string>();
    });
    Json candidates = Json::array();
    Json active = Json::array();
    const auto pipeline = ecs_get_pipeline(ecs.c_ptr());
    auto pipeline_query = ecs.query(ecs.entity(pipeline));
    pipeline_query.each([&](flecs::entity node) {
        const std::string path = node.path().c_str();
        candidates.push_back(path);
        if (!node.has(flecs::Empty)) {
            active.push_back(path);
        }
    });
    Json admission = Json::array();
    for (const auto &[node, owner] : installed_system_nodes_) {
        admission.push_back({{"node", node}, {"owner", owner}});
    }
    const Json topology = {{"contract", "echelon_forge.cpu_scheduler_topology.v1"},
                           {"installed_factory_nodes", std::move(admission)},
                           {"nodes", std::move(nodes)},
                           {"pipeline_candidate_order", std::move(candidates)}};
    return Json({{"topology", topology},
                 {"sha256", runtime::projection_contracts::canonical_sha256_hex(topology.dump())},
                 {"active_pipeline_order", std::move(active)}})
        .dump();
}
