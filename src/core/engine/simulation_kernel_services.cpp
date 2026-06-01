#include "simulation_kernel_services.h"

#include "simulation_kernel_weapon_release_service.h"

#include <utility>

std::unique_ptr<IWeaponReleaseService> make_simulation_kernel_weapon_release_service(
    flecs::world& ecs,
    const std::unique_ptr<IUnitFactory>& unit_factory,
    MissileTuning& missile_tuning,
    IEngagementLaunchRecorder& launch_recorder,
    IEngagementEventRecorder& damage_recorder,
    std::function<bool(std::uint64_t, std::uint64_t, double, double)> apply_proximity_hit
) {
    return std::make_unique<SimulationKernelWeaponReleaseService>(
        ecs,
        unit_factory,
        missile_tuning,
        launch_recorder,
        damage_recorder,
        std::move(apply_proximity_hit));
}
