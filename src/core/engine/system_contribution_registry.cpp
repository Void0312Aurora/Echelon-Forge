#include "systems/system_contribution_registry.h"

#include "simulation_kernel.h"

#include "components/combat/health.h"
#include "components/combat/scoring.h"
#include "components/combat/structural_failure.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/common/weapon_common.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/domains/air/combat/weapon_air.h"
#include "components/domains/air/platform/flight_dynamics_tuning.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/domains/naval/platform/embarked_air_ops.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "components/command/command_link_qos.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/physics/control_law.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/systems/comm.h"
#include "components/systems/data_link.h"
#include "components/systems/ew.h"
#include "components/systems/logistics.h"
#include "components/systems/navigation.h"
#include "components/systems/sonar.h"
#include "components/systems/track_management.h"

#include "systems/combat/damage_system_air.h"
#include "systems/combat/damage_system_common.h"
#include "systems/combat/damage_system_ground.h"
#include "systems/combat/damage_system_naval.h"
#include "systems/combat/guidance_system.h"
#include "systems/combat/pilot_weapon_release_system.h"
#include "systems/combat/structural_consequence_system.h"
#include "systems/combat/structural_failure_system.h"
#include "systems/core/operation_system.h"
#include "systems/domains/air/aero_state_system.h"
#include "systems/domains/air/actuator_system.h"
#include "systems/domains/air/aerodynamics_system.h"
#include "systems/domains/air/control_system.h"
#include "systems/domains/air/propulsion_system.h"
#include "systems/domains/naval/embarked_air_ops_system.h"
#include "systems/domains/naval/naval_logistics_system.h"
#include "systems/domains/naval/naval_mission_weapon_release_system.h"
#include "systems/domains/naval/ship_motion_system.h"
#include "systems/domains/naval/submarine_motion_system.h"
#include "systems/physics/force_clear_system.h"
#include "systems/physics/force_system.h"
#include "systems/physics/ground_contact_system.h"
#include "systems/physics/instrument_system.h"
#include "systems/physics/leapfrog_system.h"
#include "systems/physics/rotational_system.h"
#include "systems/systems/command_link_system.h"
#include "systems/systems/data_link_system.h"
#include "systems/systems/ew_system.h"
#include "systems/systems/logistics_system.h"
#include "systems/systems/navigation_system.h"
#include "systems/systems/sensor_system.h"
#include "systems/systems/sonar_system.h"
#include "systems/systems/track_manager_system.h"

#include <algorithm>
#include <stdexcept>
#include <string>
#include <unordered_set>

namespace runtime::systems {
namespace {

template <typename T> void register_component(flecs::world &ecs) {
    ecs.component<T>();
}

void register_rwr_reset_system(flecs::world &ecs) {
    ecs.system<RWR>("RWR_Reset").kind(flecs::PreUpdate).each([](flecs::entity, RWR &rwr) {
        rwr.detected_radar_ids.clear();
        rwr.locking_radar_ids.clear();
        rwr.is_missile_launch = false;
    });
}

void register_esm_reset_system(flecs::world &ecs) {
    ecs.system<ESMReceiver>("ESM_Reset")
        .kind(flecs::PreUpdate)
        .each([](flecs::entity, ESMReceiver &esm) { esm.detections.clear(); });
}

#define EF_DEFAULT_COMPONENT_CONTRIBUTIONS(X)                                                      \
    X(Transform, "Transform", "flecs.component.transform")                                         \
    X(Velocity, "Velocity", "flecs.component.velocity")                                            \
    X(Alliance, "Alliance", "flecs.component.alliance")                                            \
    X(KeyEntity, "KeyEntity", "flecs.component.key_entity")                                        \
    X(MovementCommand, "MovementCommand", "flecs.component.movement_command")                      \
    X(MissionCommandControlState, "MissionCommandControlState",                                    \
      "flecs.component.mission_command_control_state")                                             \
    X(PilotAction, "PilotAction", "flecs.component.pilot_action")                                  \
    X(MissionCommand, "MissionCommand", "flecs.component.mission_command")                         \
    X(TaskOrder, "TaskOrder", "flecs.component.task_order")                                        \
    X(LeaderIntent, "LeaderIntent", "flecs.component.leader_intent")                               \
    X(PendingMissionCommand, "PendingMissionCommand", "flecs.component.pending_mission_command")   \
    X(MissionCommandPendingQueue, "MissionCommandPendingQueue",                                    \
      "flecs.component.mission_command_pending_queue")                                             \
    X(ActionCommand, "ActionCommand", "flecs.component.action_command")                            \
    X(ActionSpaceConfig, "ActionSpaceConfig", "flecs.component.action_space_config")               \
    X(CommandLag, "CommandLag", "flecs.component.command_lag")                                     \
    X(LaggedCommand, "LaggedCommand", "flecs.component.lagged_command")                            \
    X(CommandLink, "CommandLink", "flecs.component.command_link")                                  \
    X(PendingMovementCommand, "PendingMovementCommand",                                            \
      "flecs.component.pending_movement_command")                                                  \
    X(PendingActionCommand, "PendingActionCommand", "flecs.component.pending_action_command")      \
    X(LandingGear, "LandingGear", "flecs.component.landing_gear")                                  \
    X(Health, "Health", "flecs.component.health")                                                  \
    X(Mass, "Mass", "flecs.component.mass")                                                        \
    X(MassProperties, "MassProperties", "flecs.component.mass_properties")                         \
    X(ShipPlatform, "ShipPlatform", "flecs.component.ship_platform")                               \
    X(SubmarinePlatform, "SubmarinePlatform", "flecs.component.submarine_platform")                \
    X(Propulsion, "Propulsion", "flecs.component.propulsion")                                      \
    X(AeroTuning, "AeroTuning", "flecs.component.aero_tuning")                                     \
    X(EngineTuning, "EngineTuning", "flecs.component.engine_tuning")                               \
    X(StallState, "StallState", "flecs.component.stall_state")                                     \
    X(ForceAccumulator, "ForceAccumulator", "flecs.component.force_accumulator")                   \
    X(AeroState, "AeroState", "flecs.component.aero_state")                                        \
    X(ControlLawState, "ControlLawState", "flecs.component.control_law_state")                     \
    X(ControlSurfaceState, "ControlSurfaceState", "flecs.component.control_surface_state")         \
    X(Inertia, "Inertia", "flecs.component.inertia")                                               \
    X(AngularVelocity, "AngularVelocity", "flecs.component.angular_velocity")                      \
    X(GroundState, "GroundState", "flecs.component.ground_state")                                  \
    X(GearState, "GearState", "flecs.component.gear_state")                                        \
    X(Missile, "Missile", "flecs.component.missile")                                               \
    X(Munition, "Munition", "flecs.component.munition")                                            \
    X(Ammo, "Ammo", "flecs.component.ammo")                                                        \
    X(WeaponCooldown, "WeaponCooldown", "flecs.component.weapon_cooldown")                         \
    X(PilotWeaponReleaseState, "PilotWeaponReleaseState",                                          \
      "flecs.component.pilot_weapon_release_state")                                                \
    X(NavalWeaponSystem, "NavalWeaponSystem", "flecs.component.naval_weapon_system")               \
    X(Jammer, "Jammer", "flecs.component.jammer")                                                  \
    X(Countermeasures, "Countermeasures", "flecs.component.countermeasures")                       \
    X(RWR, "RWR", "flecs.component.rwr")                                                           \
    X(ESMReceiver, "ESMReceiver", "flecs.component.esmreceiver")                                   \
    X(RCSProfile, "RCSProfile", "flecs.component.rcsprofile")                                      \
    X(Lifetime, "Lifetime", "flecs.component.lifetime")                                            \
    X(FuelSystem, "FuelSystem", "flecs.component.fuel_system")                                     \
    X(Loadout, "Loadout", "flecs.component.loadout")                                               \
    X(LogisticsNode, "LogisticsNode", "flecs.component.logistics_node")                            \
    X(NavalStores, "NavalStores", "flecs.component.naval_stores")                                  \
    X(ResupplyState, "ResupplyState", "flecs.component.resupply_state")                            \
    X(Sensor, "Sensor", "flecs.component.sensor")                                                  \
    X(MountedSensors, "MountedSensors", "flecs.component.mounted_sensors")                         \
    X(Sonar, "Sonar", "flecs.component.sonar")                                                     \
    X(MountedSonars, "MountedSonars", "flecs.component.mounted_sonars")                            \
    X(ContactList, "ContactList", "flecs.component.contact_list")                                  \
    X(FlightModel, "FlightModel", "flecs.component.flight_model")                                  \
    X(Score, "Score", "flecs.component.score")                                                     \
    X(DataLink, "DataLink", "flecs.component.data_link")                                           \
    X(CommQueue, "CommQueue", "flecs.component.comm_queue")                                        \
    X(PilotReport, "PilotReport", "flecs.component.pilot_report")                                  \
    X(InstrumentState, "InstrumentState", "flecs.component.instrument_state")                      \
    X(EGI, "EGI", "flecs.component.egi")                                                           \
    X(TrackDatabase, "TrackDatabase", "flecs.component.track_database")                            \
    X(EmbarkedAirOps, "EmbarkedAirOps", "flecs.component.embarked_air_ops")                        \
    X(HitboxConfig, "HitboxConfig", "flecs.component.hitbox_config")                               \
    X(SystemHealth, "SystemHealth", "flecs.component.system_health")                               \
    X(ComponentDamageState, "ComponentDamageState", "flecs.component.component_damage_state")      \
    X(StructuralBreakupState, "StructuralBreakupState",                                            \
      "flecs.component.structural_breakup_state")                                                  \
    X(PlatformDamageState, "PlatformDamageState", "flecs.component.platform_damage_state")         \
    X(AircraftDamageState, "AircraftDamageState", "flecs.component.aircraft_damage_state")         \
    X(AircraftDamageBaseline, "AircraftDamageBaseline",                                            \
      "flecs.component.aircraft_damage_baseline")                                                  \
    X(EffectsModelRef, "EffectsModelRef", "flecs.component.effects_model_ref")                     \
    X(EngagementEventRecorderRef, "EngagementEventRecorderRef",                                    \
      "flecs.component.engagement_event_recorder_ref")                                             \
    X(SensorModelRef, "SensorModelRef", "flecs.component.sensor_model_ref")                        \
    X(AcousticModelRef, "AcousticModelRef", "flecs.component.acoustic_model_ref")                  \
    X(ControlModelRef, "ControlModelRef", "flecs.component.control_model_ref")                     \
    X(GuidanceModelRef, "GuidanceModelRef", "flecs.component.guidance_model_ref")                  \
    X(EnvironmentModelRef, "EnvironmentModelRef", "flecs.component.environment_model_ref")         \
    X(WeaponReleaseServiceRef, "WeaponReleaseServiceRef",                                          \
      "flecs.component.weapon_release_service_ref")

#define EF_DEFAULT_SYSTEM_CONTRIBUTIONS(X)                                                         \
    X("builtin.system.command_link", "register_command_link_system", "common", "legacy.stage.00",  \
      0, "", register_command_link_system)                                                         \
    X("builtin.system.action_mapping", "register_action_mapping_system", "common",                 \
      "legacy.stage.01", 1, "builtin.system.command_link", register_action_mapping_system)         \
    X("builtin.system.command_lag", "register_command_lag_system", "common", "legacy.stage.02", 2, \
      "builtin.system.action_mapping", register_command_lag_system)                                \
    X("builtin.system.control", "register_control_system", "air", "legacy.stage.03", 3,            \
      "builtin.system.command_lag", register_control_system)                                       \
    X("builtin.system.force_clear", "register_force_clear_system", "air", "legacy.stage.04", 4,    \
      "builtin.system.control", register_force_clear_system)                                       \
    X("builtin.system.aero_state", "register_aero_state_system", "air", "legacy.stage.05", 5,      \
      "builtin.system.force_clear", register_aero_state_system)                                    \
    X("builtin.system.propulsion", "flight_dynamics.register_propulsion_system", "air",            \
      "legacy.stage.06", 6, "builtin.system.aero_state",                                           \
      flight_dynamics::register_propulsion_system)                                                 \
    X("builtin.system.force", "register_force_system", "air", "legacy.stage.07", 7,                \
      "builtin.system.propulsion", register_force_system)                                          \
    X("builtin.system.actuator", "flight_dynamics.register_actuator_system", "air",                \
      "legacy.stage.08", 8, "builtin.system.force", flight_dynamics::register_actuator_system)     \
    X("builtin.system.aerodynamics", "register_aerodynamics_system", "air", "legacy.stage.09", 9,  \
      "builtin.system.actuator", register_aerodynamics_system)                                     \
    X("builtin.system.ground_contact", "register_ground_contact_system", "ground",                 \
      "legacy.stage.10", 10, "builtin.system.aerodynamics", register_ground_contact_system)        \
    X("builtin.system.rotational_integration", "register_rotational_integration_system", "air",    \
      "legacy.stage.11", 11, "builtin.system.ground_contact",                                      \
      register_rotational_integration_system)                                                      \
    X("builtin.system.guidance", "register_guidance_system", "cross_domain", "legacy.stage.12",    \
      12, "builtin.system.rotational_integration", register_guidance_system)                       \
    X("builtin.system.leapfrog_integration", "register_leapfrog_integration_system", "common",     \
      "legacy.stage.13", 13, "builtin.system.guidance", register_leapfrog_integration_system)      \
    X("builtin.system.ship_motion", "register_ship_motion_system", "naval", "legacy.stage.14", 14, \
      "builtin.system.leapfrog_integration", register_ship_motion_system)                          \
    X("builtin.system.submarine_motion", "register_submarine_motion_system", "naval",              \
      "legacy.stage.15", 15, "builtin.system.ship_motion", register_submarine_motion_system)       \
    X("builtin.system.navigation", "register_navigation_system", "common", "legacy.stage.16", 16,  \
      "builtin.system.submarine_motion", register_navigation_system)                               \
    X("builtin.system.sensor", "register_sensor_system", "cross_domain", "legacy.stage.17", 17,    \
      "builtin.system.navigation", register_sensor_system)                                         \
    X("builtin.system.sonar", "register_sonar_system", "naval", "legacy.stage.18", 18,             \
      "builtin.system.sensor", register_sonar_system)                                              \
    X("builtin.system.track_manager", "register_track_manager_system", "common",                   \
      "legacy.stage.19", 19, "builtin.system.sonar", register_track_manager_system)                \
    X("builtin.system.data_link", "register_data_link_system", "common", "legacy.stage.20", 20,    \
      "builtin.system.track_manager", register_data_link_system)                                   \
    X("builtin.system.embarked_air_ops", "register_embarked_air_ops_system", "naval",              \
      "legacy.stage.21", 21, "builtin.system.data_link", register_embarked_air_ops_system)         \
    X("builtin.system.pilot_weapon_release", "register_pilot_weapon_release_system", "air",        \
      "legacy.stage.22", 22, "builtin.system.embarked_air_ops",                                    \
      register_pilot_weapon_release_system)                                                        \
    X("builtin.system.naval_weapon_release", "register_naval_mission_weapon_release_system",       \
      "naval", "legacy.stage.23", 23, "builtin.system.pilot_weapon_release",                       \
      register_naval_mission_weapon_release_system)                                                \
    X("builtin.system.instrument", "register_instrument_system", "common", "legacy.stage.24", 24,  \
      "builtin.system.naval_weapon_release", register_instrument_system)                           \
    X("builtin.system.damage_common", "register_damage_system_common", "common",                   \
      "legacy.stage.25", 25, "builtin.system.instrument", register_damage_system_common)           \
    X("builtin.system.aircraft_damage", "register_aircraft_damage_system", "air",                  \
      "legacy.stage.26", 26, "builtin.system.damage_common", register_aircraft_damage_system)      \
    X("builtin.system.structural_failure", "register_structural_failure_system", "air",            \
      "legacy.stage.27", 27, "builtin.system.aircraft_damage", register_structural_failure_system) \
    X("builtin.system.structural_consequence", "register_structural_consequence_system", "air",    \
      "legacy.stage.28", 28, "builtin.system.structural_failure",                                  \
      register_structural_consequence_system)                                                      \
    X("builtin.system.naval_damage", "register_naval_damage_system", "naval", "legacy.stage.29",   \
      29, "builtin.system.structural_consequence", register_naval_damage_system)                   \
    X("builtin.system.ground_damage", "register_ground_damage_system", "ground",                   \
      "legacy.stage.30", 30, "builtin.system.naval_damage", register_ground_damage_system)         \
    X("builtin.system.ew", "register_ew_system", "cross_domain", "legacy.stage.31", 31,            \
      "builtin.system.ground_damage", register_ew_system)                                          \
    X("builtin.system.logistics", "register_logistics_system", "common", "legacy.stage.32", 32,    \
      "builtin.system.ew", register_logistics_system)                                              \
    X("builtin.system.naval_logistics", "register_naval_logistics_system", "naval",                \
      "legacy.stage.33", 33, "builtin.system.logistics", register_naval_logistics_system)

#define EF_KERNEL_SYSTEM_CONTRIBUTIONS(X)                                                          \
    X("builtin.kernel.system.rwr_reset", "kernel.pre_update.00", 0, register_rwr_reset_system)     \
    X("builtin.kernel.system.esm_reset", "kernel.pre_update.01", 1, register_esm_reset_system)

#define EF_COMPONENT_ROW(type, id, registration)                                                   \
    ComponentContribution{id, registration, &register_component<type>},
const ComponentContribution kDefaultComponents[] = {
    EF_DEFAULT_COMPONENT_CONTRIBUTIONS(EF_COMPONENT_ROW)};
#undef EF_COMPONENT_ROW

#define EF_SYSTEM_ROW(id, factory, domain, stage, order, after, function)                          \
    SystemContribution{id, factory, domain, stage, order, after, &function},
const SystemContribution kDefaultSystems[] = {EF_DEFAULT_SYSTEM_CONTRIBUTIONS(EF_SYSTEM_ROW)};
#undef EF_SYSTEM_ROW

#define EF_KERNEL_SYSTEM_ROW(id, stage, order, function)                                           \
    KernelSystemContribution{id, stage, order, &function},
const KernelSystemContribution kKernelSystems[] = {
    EF_KERNEL_SYSTEM_CONTRIBUTIONS(EF_KERNEL_SYSTEM_ROW)};
#undef EF_KERNEL_SYSTEM_ROW

struct ValidationResult {
    bool ok;
    std::string error;
};

ValidationResult validate_registry() {
    if (std::size(kDefaultComponents) != 83) {
        return {false, "component contribution count is not the admitted default count"};
    }
    std::unordered_set<std::string_view> component_ids;
    for (const auto &row : kDefaultComponents) {
        if (row.component_id.empty() || row.registration_id.empty() ||
            row.register_component == nullptr || !component_ids.insert(row.component_id).second) {
            return {false, "component contribution registry is empty or duplicated"};
        }
    }
    if (std::size(kDefaultSystems) != 34) {
        return {false, "system contribution count is not the admitted default count"};
    }
    if (std::size(kKernelSystems) != 2 || kKernelSystems[0].stage_order != 0 ||
        kKernelSystems[1].stage_order != 1) {
        return {false, "kernel-owned pre-update system admission mismatch"};
    }
    std::unordered_set<std::string_view> system_ids;
    for (std::size_t index = 0; index < std::size(kDefaultSystems); ++index) {
        const auto &candidate = kDefaultSystems[index];
        if (candidate.stage_order != index || candidate.contribution_id.empty() ||
            candidate.registration_factory_id.empty() || candidate.domain.empty() ||
            candidate.stage_id.empty() || candidate.register_system == nullptr ||
            !system_ids.insert(candidate.contribution_id).second) {
            return {false, "system contribution registry has an invalid or duplicated row"};
        }
        if (!candidate.after_contribution_id.empty()) {
            const auto prior =
                std::find_if(std::begin(kDefaultSystems), std::begin(kDefaultSystems) + index,
                             [&](const auto &row) {
                                 return row.contribution_id == candidate.after_contribution_id;
                             });
            if (prior == std::begin(kDefaultSystems) + index) {
                return {false,
                        "system contribution dependency is not admitted before its consumer"};
            }
        }
    }
    return {true, {}};
}

const ValidationResult &cached_validation() {
    static const ValidationResult result = validate_registry();
    return result;
}

void require_valid_registry() {
    const auto &result = cached_validation();
    if (!result.ok) {
        throw std::logic_error(result.error);
    }
}

} // namespace

std::span<const ComponentContribution> default_component_contributions() noexcept {
    return kDefaultComponents;
}

std::span<const SystemContribution> default_system_contributions() noexcept {
    return kDefaultSystems;
}

std::span<const KernelSystemContribution> kernel_system_contributions() noexcept {
    return kKernelSystems;
}

void register_default_component_contributions(flecs::world &ecs) {
    require_valid_registry();
    for (const auto &contribution : kDefaultComponents) {
        contribution.register_component(ecs);
    }
}

void register_default_system_contributions(flecs::world &ecs) {
    require_valid_registry();
    for (const auto &contribution : kKernelSystems) {
        contribution.register_system(ecs);
    }
    for (const auto &contribution : kDefaultSystems) {
        contribution.register_system(ecs);
    }
}

bool validate_default_contribution_graph(std::string *error) noexcept {
    const auto &result = cached_validation();
    if (!result.ok && error != nullptr) {
        *error = result.error;
    }
    return result.ok;
}

} // namespace runtime::systems
