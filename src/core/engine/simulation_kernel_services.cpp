#include "simulation_kernel_services.h"

#include "simulation_kernel_weapon_release_service.h"

std::unique_ptr<IWeaponReleaseService> make_simulation_kernel_weapon_release_service(
    flecs::world &ecs, const std::unique_ptr<IUnitFactory> &unit_factory,
    MissileTuning &missile_tuning, std::mt19937 &rng, IEngagementLaunchRecorder &launch_recorder,
    IEngagementEventRecorder &damage_recorder, IWeaponReleaseDamageBridge &damage_bridge) {
    return std::make_unique<SimulationKernelWeaponReleaseService>(
        ecs, unit_factory, missile_tuning, rng, launch_recorder, damage_recorder, damage_bridge);
}
