#pragma once

#include <memory>

class IWeaponReleaseService;
class SimulationKernel;

std::unique_ptr<IWeaponReleaseService> make_simulation_kernel_weapon_release_service(
    SimulationKernel& kernel
);
