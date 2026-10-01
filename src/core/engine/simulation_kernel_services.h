#pragma once

#include <memory>

#include <flecs.h>

class IEngagementEventRecorder;
class IEngagementLaunchRecorder;
class IUnitFactory;
class IWeaponReleaseDamageBridge;
class IWeaponReleaseService;
class SimulationKernelRngStream;
struct MissileTuning;

std::unique_ptr<IWeaponReleaseService> make_simulation_kernel_weapon_release_service(
    flecs::world &ecs, IUnitFactory &unit_factory, MissileTuning &missile_tuning,
    SimulationKernelRngStream &rng, IEngagementLaunchRecorder &launch_recorder,
    IEngagementEventRecorder &damage_recorder, IWeaponReleaseDamageBridge &damage_bridge);
