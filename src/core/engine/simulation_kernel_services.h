#pragma once

#include <memory>

#include <flecs.h>

class IEngagementEventRecorder;
class IEngagementLaunchRecorder;
class IUnitFactory;
class IWeaponReleaseDamageBridge;
class IWeaponReleaseService;
struct MissileTuning;

std::unique_ptr<IWeaponReleaseService> make_simulation_kernel_weapon_release_service(
    flecs::world& ecs,
    const std::unique_ptr<IUnitFactory>& unit_factory,
    MissileTuning& missile_tuning,
    IEngagementLaunchRecorder& launch_recorder,
    IEngagementEventRecorder& damage_recorder,
    IWeaponReleaseDamageBridge& damage_bridge
);
