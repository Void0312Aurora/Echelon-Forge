#pragma once

#include <memory>
#include <random>

#include <flecs.h>

class IEngagementEventRecorder;
class IEngagementLaunchRecorder;
class IUnitFactory;
class IWeaponReleaseDamageBridge;
class IWeaponReleaseService;
class SimulationKernel;
struct MissileTuning;

std::unique_ptr<IWeaponReleaseService> make_simulation_kernel_weapon_release_service(
    SimulationKernel &kernel, flecs::world &ecs, IUnitFactory &unit_factory,
    MissileTuning &missile_tuning, std::mt19937 &rng, IEngagementLaunchRecorder &launch_recorder,
    IEngagementEventRecorder &damage_recorder, IWeaponReleaseDamageBridge &damage_bridge);
