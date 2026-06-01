#include "simulation_kernel_services.h"

#include "simulation_kernel.h"

#include <cstdint>
#include <memory>

class SimulationKernelWeaponReleaseService final : public IWeaponReleaseService {
public:
    explicit SimulationKernelWeaponReleaseService(SimulationKernel& kernel)
        : kernel_(kernel) {}

    flecs::entity fire_weapon_from_pilot_action(std::uint64_t attacker_id) override {
        return kernel_.fire_weapon_from_pilot_action(attacker_id);
    }

    bool fire_naval_weapon_from_mission_command(std::uint64_t attacker_id) override {
        return kernel_.fire_naval_weapon_from_mission_command(attacker_id);
    }

private:
    SimulationKernel& kernel_;
};

std::unique_ptr<IWeaponReleaseService> make_simulation_kernel_weapon_release_service(
    SimulationKernel& kernel
) {
    return std::make_unique<SimulationKernelWeaponReleaseService>(kernel);
}
