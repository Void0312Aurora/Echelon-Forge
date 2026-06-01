#pragma once

#include <cstdint>
#include <functional>
#include <memory>

#include <flecs.h>

class IEngagementEventRecorder;
class IEngagementLaunchRecorder;
class IUnitFactory;
class IWeaponReleaseService;
struct MissileTuning;

std::unique_ptr<IWeaponReleaseService> make_simulation_kernel_weapon_release_service(
    flecs::world& ecs,
    const std::unique_ptr<IUnitFactory>& unit_factory,
    MissileTuning& missile_tuning,
    IEngagementLaunchRecorder& launch_recorder,
    IEngagementEventRecorder& damage_recorder,
    std::function<bool(std::uint64_t, std::uint64_t, double, double)> apply_proximity_hit
);
