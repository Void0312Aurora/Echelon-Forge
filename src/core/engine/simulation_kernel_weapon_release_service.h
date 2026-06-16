#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <random>
#include <string>

#include <flecs.h>

#include "core/interfaces/weapon_release_damage_bridge.h"
#include "core/interfaces/weapon_release_service.h"

class IEngagementEventRecorder;
class IEngagementLaunchRecorder;
class IUnitFactory;
struct MissileTuning;
struct PilotAction;
struct UnitDefinition;

class SimulationKernelWeaponReleaseService final : public IWeaponReleaseService {
  public:
    SimulationKernelWeaponReleaseService(flecs::world &ecs,
                                         const std::unique_ptr<IUnitFactory> &unit_factory,
                                         MissileTuning &missile_tuning, std::mt19937 &rng,
                                         IEngagementLaunchRecorder &launch_recorder,
                                         IEngagementEventRecorder &damage_recorder,
                                         IWeaponReleaseDamageBridge &damage_bridge);

    flecs::entity fire_missile(std::uint64_t attacker_id, std::uint64_t target_id) override;
    bool fire_naval_weapon(std::uint64_t attacker_id, std::uint64_t target_id,
                           int weapon_type_code) override;
    flecs::entity fire_weapon_from_pilot_action(std::uint64_t attacker_id) override;
    bool fire_naval_weapon_from_mission_command(std::uint64_t attacker_id) override;

  private:
    struct ResolvedMissileLaunchDefinition {
        std::uint64_t munition_entity_id = 0;
        std::string platform_definition_name;
        std::string weapon_definition_name;
        int station_id = 0;
        const UnitDefinition *platform_definition = nullptr;
        const UnitDefinition *weapon_definition = nullptr;
    };

    std::optional<ResolvedMissileLaunchDefinition>
    resolve_missile_launch_definition(flecs::entity attacker, const PilotAction *pilot) const;

    flecs::world &ecs_;
    const std::unique_ptr<IUnitFactory> &unit_factory_;
    MissileTuning &missile_tuning_;
    std::mt19937 &rng_;
    IEngagementLaunchRecorder &launch_recorder_;
    IEngagementEventRecorder &damage_recorder_;
    IWeaponReleaseDamageBridge &damage_bridge_;
};
