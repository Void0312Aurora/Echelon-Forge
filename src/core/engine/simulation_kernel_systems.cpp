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

void SimulationKernel::register_components_and_systems() {

    // Components and systems are admitted through the owner-derived registry.
    // The registry validates the frozen default artifact before touching Flecs.
    runtime::systems::register_default_component_contributions(ecs);

    // Service references are components too; they are installed by the same
    // contribution registry so the component graph has one admission path.

    // Define Pipeline Phases (explicit ordering)
    // Phase 1: Control - writes platform Velocity based on commands
    // Phase 2: Guidance - writes weapon Velocity (missiles)
    // Phase 3: Movement - integrates Velocity → Transform
    // Phase 4: Sensor - scans for contacts
    // Phase 5: Damage - proximity fuse, hit effects

    // Note: With flecs, systems registered on OnUpdate run in registration order.
    // For guaranteed ordering, we use .kind() with custom phases or depends_on.
    // For MVP, registration order is sufficient as long as it's explicit.

    // The native stage owner executes the admitted contribution order.  A
    // Cordis package can request contributions, but cannot turn package order
    // into Flecs execution order or install a private pipeline.
    runtime::systems::register_default_system_contributions(ecs);
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
